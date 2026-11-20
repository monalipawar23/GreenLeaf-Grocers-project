import random
from datetime import date, timedelta
from werkzeug.security import generate_password_hash
from database import db, init_db

random.seed(42)
NAMES = [
 ("Organic Apples","Fruits",120),("Banana","Fruits",50),("Tomato","Vegetables",35),
 ("Potato","Vegetables",30),("Onion","Vegetables",40),("Milk 1L","Dairy",60),
 ("Paneer 200g","Dairy",95),("Curd 500g","Dairy",45),("Rice 1kg","Grains",75),
 ("Wheat Flour 1kg","Grains",55),("Toor Dal 1kg","Pulses",140),("Moong Dal 1kg","Pulses",115),
 ("Sunflower Oil 1L","Essentials",145),("Sugar 1kg","Essentials",48),("Tea 250g","Beverages",110),
 ("Coffee 100g","Beverages",160),("Orange Juice","Beverages",85),("Bread","Bakery",40),
 ("Biscuits","Snacks",25),("Potato Chips","Snacks",20),("Dish Soap","Household",65),
 ("Detergent 1kg","Household",125),("Toothpaste","Personal Care",55),("Shampoo","Personal Care",99)
]

def seed():
    init_db()
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO users(username,password_hash,role) VALUES(?,?,?)",
                     ("admin",generate_password_hash("admin123"),"admin"))
        conn.execute("INSERT OR IGNORE INTO users(username,password_hash,role) VALUES(?,?,?)",
                     ("cashier",generate_password_hash("cashier123"),"cashier"))
        if conn.execute("SELECT COUNT(*) FROM products").fetchone()[0] == 0:
            for i in range(60):
                name,cat,price=NAMES[i%len(NAMES)]
                suffix=f" {i//len(NAMES)+1}" if i>=len(NAMES) else ""
                expiry=(date.today()+timedelta(days=random.randint(2,240))).isoformat() if i%4==0 else None
                conn.execute("INSERT INTO products(name,category,unit_price,stock_qty,reorder_level,expiry_date) VALUES(?,?,?,?,?,?)",
                    (name+suffix,cat,price+random.randint(0,20),random.randint(5,100),random.randint(5,15),expiry))
        if conn.execute("SELECT COUNT(*) FROM sales").fetchone()[0] == 0:
            pids=[r[0] for r in conn.execute("SELECT product_id FROM products").fetchall()]
            users=[r[0] for r in conn.execute("SELECT user_id FROM users").fetchall()]
            for _ in range(550):
                d=date.today()-timedelta(days=random.randint(0,150))
                chosen=random.sample(pids,random.randint(1,4)); total=0; lines=[]
                for pid in chosen:
                    p=conn.execute("SELECT unit_price,stock_qty FROM products WHERE product_id=?",(pid,)).fetchone()
                    qty=random.randint(1,3); price=p["unit_price"]; total+=qty*price; lines.append((pid,qty,price))
                cur=conn.execute("INSERT INTO sales(sale_date,sale_time,user_id,total_amount,discount) VALUES(?,?,?,?,0)",
                    (d.isoformat(),f"{random.randint(8,21):02d}:{random.randint(0,59):02d}:00",random.choice(users),round(total,2)))
                for pid,qty,price in lines:
                    conn.execute("INSERT INTO sale_items(sale_id,product_id,quantity,price) VALUES(?,?,?,?)",(cur.lastrowid,pid,qty,price))
    print("Demo data created: 60 products and 550 sales. Login: admin/admin123 or cashier/cashier123")

if __name__=="__main__": seed()
