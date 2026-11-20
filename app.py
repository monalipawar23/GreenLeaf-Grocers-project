import csv, io, os
from datetime import date, datetime
from functools import wraps
from flask import Flask, render_template, request, redirect, url_for, session, flash, make_response
from werkzeug.security import generate_password_hash, check_password_hash
from config import SECRET_KEY
from database import db, init_db
from utils import parse_positive_int, valid_iso_date, alert_dates
from reports import summary, slow_moving_products

app = Flask(__name__)
app.secret_key = SECRET_KEY
init_db()

def login_required(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        if not session.get("user_id"):
            return redirect(url_for("login"))
        return fn(*args, **kwargs)
    return wrapper

def admin_required(fn):
    @wraps(fn)
    @login_required
    def wrapper(*args, **kwargs):
        if session.get("role") != "admin":
            flash("Admin access is required.", "error")
            return redirect(url_for("dashboard"))
        return fn(*args, **kwargs)
    return wrapper

@app.route("/")
def index():
    return redirect(url_for("dashboard") if session.get("user_id") else url_for("login"))

@app.route("/login", methods=["GET","POST"])
def login():
    if request.method == "POST":
        with db() as conn:
            user=conn.execute("SELECT * FROM users WHERE username=?", (request.form.get("username","").strip(),)).fetchone()
        if user and check_password_hash(user["password_hash"], request.form.get("password","")):
            session.update(user_id=user["user_id"], username=user["username"], role=user["role"])
            return redirect(url_for("dashboard"))
        flash("Incorrect username or password.", "error")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for("login"))

@app.route("/dashboard")
@login_required
def dashboard():
    low, near=alert_dates()
    with db() as conn:
        products=conn.execute("SELECT * FROM products ORDER BY name").fetchall()
        low_items=conn.execute("SELECT * FROM products WHERE stock_qty <= reorder_level ORDER BY stock_qty").fetchall()
        expiry=conn.execute("SELECT * FROM products WHERE expiry_date IS NOT NULL AND expiry_date BETWEEN ? AND ? ORDER BY expiry_date",(date.today().isoformat(),near)).fetchall()
        today_sales=conn.execute("SELECT COUNT(*) bills, COALESCE(SUM(total_amount),0) revenue FROM sales WHERE sale_date=?",(date.today().isoformat(),)).fetchone()
    return render_template("dashboard.html", products=products, low_items=low_items, expiry=expiry, today_sales=today_sales)

@app.route("/products")
@admin_required
def products():
    q=request.args.get("q","").strip()
    with db() as conn:
        rows=conn.execute("SELECT * FROM products WHERE name LIKE ? OR category LIKE ? ORDER BY name",(f"%{q}%",f"%{q}%")).fetchall()
    return render_template("products.html", products=rows, q=q)

@app.route("/products/add", methods=["GET","POST"])
@app.route("/products/<int:pid>/edit", methods=["GET","POST"])
@admin_required
def product_form(pid=None):
    with db() as conn:
        product=conn.execute("SELECT * FROM products WHERE product_id=?",(pid,)).fetchone() if pid else None
    if pid and not product:
        flash("Product not found.","error"); return redirect(url_for("products"))
    if request.method=="POST":
        try:
            name=request.form.get("name","").strip()
            category=request.form.get("category","").strip()
            price=float(request.form.get("unit_price",""))
            stock=int(request.form.get("stock_qty",""))
            reorder=int(request.form.get("reorder_level",""))
            expiry=valid_iso_date(request.form.get("expiry_date",""))
            if not name or not category or price<0 or stock<0 or reorder<0: raise ValueError("Enter valid product details.")
            with db() as conn:
                vals=(name,category,price,stock,reorder,expiry)
                if pid: conn.execute("UPDATE products SET name=?,category=?,unit_price=?,stock_qty=?,reorder_level=?,expiry_date=? WHERE product_id=?", vals+(pid,))
                else: conn.execute("INSERT INTO products(name,category,unit_price,stock_qty,reorder_level,expiry_date) VALUES(?,?,?,?,?,?)",vals)
            flash("Product saved successfully.","success"); return redirect(url_for("products"))
        except (ValueError, TypeError):
            flash("Please enter valid price, stock, reorder level and date.","error")
    return render_template("product_form.html", product=product)

@app.route("/products/<int:pid>/delete", methods=["POST"])
@admin_required
def delete_product(pid):
    try:
        with db() as conn: conn.execute("DELETE FROM products WHERE product_id=?",(pid,))
        flash("Product deleted.","success")
    except Exception:
        flash("This product is used in past sales and cannot be deleted. Set stock to zero instead.","error")
    return redirect(url_for("products"))

@app.route("/billing", methods=["GET","POST"])
@login_required
def billing():
    with db() as conn: products=conn.execute("SELECT * FROM products WHERE stock_qty>0 ORDER BY name").fetchall()
    if request.method=="POST":
        try:
            ids=request.form.getlist("product_id[]"); qtys=request.form.getlist("quantity[]")
            discount=float(request.form.get("discount",0))
            if not ids or discount<0: raise ValueError("Add at least one item and a valid discount.")
            items=[]; subtotal=0
            with db() as conn:
                for pid, raw_qty in zip(ids,qtys):
                    qty=parse_positive_int(raw_qty)
                    p=conn.execute("SELECT * FROM products WHERE product_id=?",(int(pid),)).fetchone()
                    if not p: raise ValueError("A selected product does not exist.")
                    if p["stock_qty"]<qty: raise ValueError(f"Not enough stock for {p['name']} (available: {p['stock_qty']}).")
                    items.append((p,qty)); subtotal += p["unit_price"]*qty
                if discount>subtotal: raise ValueError("Discount cannot exceed subtotal.")
                total=round(subtotal-discount,2); now=datetime.now()
                cur=conn.execute("INSERT INTO sales(sale_date,sale_time,user_id,total_amount,discount) VALUES(?,?,?,?,?)",
                    (now.date().isoformat(),now.strftime("%H:%M:%S"),session["user_id"],total,discount))
                sale_id=cur.lastrowid
                for p,qty in items:
                    conn.execute("INSERT INTO sale_items(sale_id,product_id,quantity,price) VALUES(?,?,?,?)",(sale_id,p["product_id"],qty,p["unit_price"]))
                    conn.execute("UPDATE products SET stock_qty=stock_qty-? WHERE product_id=?",(qty,p["product_id"]))
            return redirect(url_for("bill", sale_id=sale_id))
        except (ValueError, TypeError) as e:
            flash(str(e),"error")
    return render_template("billing.html", products=products)

@app.route("/bill/<int:sale_id>")
@login_required
def bill(sale_id):
    with db() as conn:
        sale=conn.execute("SELECT s.*,u.username FROM sales s JOIN users u ON s.user_id=u.user_id WHERE sale_id=?",(sale_id,)).fetchone()
        items=conn.execute("SELECT p.name,si.quantity,si.price,si.quantity*si.price line_total FROM sale_items si JOIN products p ON p.product_id=si.product_id WHERE si.sale_id=?",(sale_id,)).fetchall()
    if not sale: return "Bill not found",404
    return render_template("bill.html",sale=sale,items=items)

@app.route("/reports")
@admin_required
def reports():
    start=request.args.get("start") or None; end=request.args.get("end") or None
    data=summary(start,end)
    with db() as conn:
        low=conn.execute("SELECT * FROM products WHERE stock_qty<=reorder_level ORDER BY stock_qty").fetchall()
        _,near=alert_dates()
        expiry=conn.execute("SELECT * FROM products WHERE expiry_date BETWEEN ? AND ? ORDER BY expiry_date",(date.today().isoformat(),near)).fetchall()
    slow=slow_moving_products()
    return render_template("reports.html", data=data, low=low, expiry=expiry, slow=slow, start=start or "", end=end or "")

@app.route("/export/sales.csv")
@admin_required
def export_sales():
    start=request.args.get("start"); end=request.args.get("end")
    with db() as conn:
        q="SELECT s.sale_id,s.sale_date,s.sale_time,u.username,s.total_amount,s.discount FROM sales s JOIN users u ON u.user_id=s.user_id WHERE 1=1"; params=[]
        if start: q+=" AND sale_date>=?"; params.append(start)
        if end: q+=" AND sale_date<=?"; params.append(end)
        rows=conn.execute(q+" ORDER BY sale_date DESC,sale_id DESC",params).fetchall()
    out=io.StringIO(); writer=csv.writer(out); writer.writerow(["Sale ID","Date","Time","Cashier","Total","Discount"])
    writer.writerows([tuple(r) for r in rows])
    resp=make_response(out.getvalue()); resp.headers["Content-Disposition"]="attachment; filename=sales_report.csv"; resp.headers["Content-Type"]="text/csv"
    return resp

@app.route("/import/products", methods=["GET","POST"])
@admin_required
def import_products():
    if request.method=="POST":
        f=request.files.get("file")
        if not f: flash("Choose a CSV file.","error")
        else:
            try:
                reader=csv.DictReader(io.StringIO(f.stream.read().decode("utf-8-sig")))
                count=0
                with db() as conn:
                    for row in reader:
                        price=float(row["unit_price"]); stock=int(row["stock_qty"]); reorder=int(row.get("reorder_level",5))
                        if price<0 or stock<0 or reorder<0: raise ValueError()
                        conn.execute("INSERT INTO products(name,category,unit_price,stock_qty,reorder_level,expiry_date) VALUES(?,?,?,?,?,?)",
                            (row["name"],row["category"],price,stock,reorder,valid_iso_date(row.get("expiry_date",""))))
                        count+=1
                flash(f"Imported {count} products.","success"); return redirect(url_for("products"))
            except Exception:
                flash("CSV format is invalid. Required columns: name,category,unit_price,stock_qty. Optional: reorder_level,expiry_date.","error")
    return render_template("import.html")


if __name__ == "__main__":
    import webbrowser
    from threading import Timer

    url = "http://127.0.0.1:5000/login"

    Timer(1.5, lambda: webbrowser.open(url)).start()

    app.run(debug=False, port=5000)

