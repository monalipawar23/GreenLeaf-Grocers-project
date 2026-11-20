import pandas as pd
from database import db

def sales_frame(start=None, end=None):
    query = """SELECT s.sale_id, s.sale_date, s.total_amount, si.product_id,
                      p.name AS product_name, p.category, si.quantity
               FROM sales s JOIN sale_items si ON s.sale_id=si.sale_id
               JOIN products p ON p.product_id=si.product_id WHERE 1=1"""
    params = []
    if start:
        query += " AND s.sale_date >= ?"; params.append(start)
    if end:
        query += " AND s.sale_date <= ?"; params.append(end)
    with db() as conn:
        rows = conn.execute(query, params).fetchall()
    return pd.DataFrame([dict(r) for r in rows])

def summary(start=None, end=None):
    frame = sales_frame(start, end)
    if frame.empty:
        return {"revenue": 0.0, "bills": 0, "avg_bill": 0.0,
                "top_products": [], "categories": [], "daily": [], "monthly": []}
    with db() as conn:
        q = "SELECT COUNT(*) n, COALESCE(SUM(total_amount),0) revenue FROM sales WHERE 1=1"
        p=[]
        if start: q += " AND sale_date>=?"; p.append(start)
        if end: q += " AND sale_date<=?"; p.append(end)
        row=conn.execute(q,p).fetchone()
    top=(frame.groupby("product_name")["quantity"].sum().sort_values(ascending=False).head(10))
    cat=(frame.groupby("category")["quantity"].sum())
    cat_total=float(cat.sum()) or 1
    daily=frame.groupby("sale_date")["sale_id"].nunique().reset_index(name="bills")
    daily_rev=frame.groupby("sale_date")["sale_id"].nunique()
    # Revenue is aggregated from unique bills to avoid repeating a bill total per item.
    with db() as conn:
        q="SELECT sale_date, SUM(total_amount) revenue FROM sales WHERE 1=1"
        p=[]
        if start: q+=" AND sale_date>=?"; p.append(start)
        if end: q+=" AND sale_date<=?"; p.append(end)
        q+=" GROUP BY sale_date ORDER BY sale_date"
        daily_revenue=[dict(r) for r in conn.execute(q,p).fetchall()]
        q="SELECT substr(sale_date,1,7) month, SUM(total_amount) revenue FROM sales WHERE 1=1"
        p=[]
        if start: q+=" AND sale_date>=?"; p.append(start)
        if end: q+=" AND sale_date<=?"; p.append(end)
        q+=" GROUP BY substr(sale_date,1,7) ORDER BY month"
        monthly=[dict(r) for r in conn.execute(q,p).fetchall()]
    return {"revenue":float(row["revenue"]), "bills":int(row["n"]),
            "avg_bill":float(row["revenue"])/(int(row["n"]) or 1),
            "top_products":[{"name":k,"quantity":int(v)} for k,v in top.items()],
            "categories":[{"name":k,"quantity":int(v),"share":round(float(v)/cat_total*100,1)} for k,v in cat.items()],
            "daily":daily_revenue, "monthly":monthly}

def slow_moving_products(days=30):
    with db() as conn:
        return conn.execute("""
          SELECT p.*, MAX(s.sale_date) last_sold
          FROM products p LEFT JOIN sale_items si ON p.product_id=si.product_id
          LEFT JOIN sales s ON si.sale_id=s.sale_id
          GROUP BY p.product_id
          HAVING last_sold IS NULL OR last_sold < date('now', ?)
          ORDER BY last_sold
        """, (f"-{days} days",)).fetchall()
