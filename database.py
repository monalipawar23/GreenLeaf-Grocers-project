import sqlite3
from contextlib import contextmanager
from config import DATABASE

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS users (
 user_id INTEGER PRIMARY KEY AUTOINCREMENT,
 username TEXT UNIQUE NOT NULL,
 password_hash TEXT NOT NULL,
 role TEXT NOT NULL CHECK(role IN ('admin','cashier'))
);
CREATE TABLE IF NOT EXISTS suppliers (
 supplier_id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL, phone TEXT, email TEXT
);
CREATE TABLE IF NOT EXISTS products (
 product_id INTEGER PRIMARY KEY AUTOINCREMENT,
 name TEXT NOT NULL, category TEXT NOT NULL,
 unit_price REAL NOT NULL CHECK(unit_price >= 0),
 stock_qty INTEGER NOT NULL DEFAULT 0 CHECK(stock_qty >= 0),
 reorder_level INTEGER NOT NULL DEFAULT 5 CHECK(reorder_level >= 0),
 expiry_date TEXT,
 supplier_id INTEGER,
 FOREIGN KEY(supplier_id) REFERENCES suppliers(supplier_id) ON DELETE SET NULL
);
CREATE TABLE IF NOT EXISTS sales (
 sale_id INTEGER PRIMARY KEY AUTOINCREMENT,
 sale_date TEXT NOT NULL, sale_time TEXT NOT NULL,
 user_id INTEGER NOT NULL, total_amount REAL NOT NULL,
 discount REAL NOT NULL DEFAULT 0,
 FOREIGN KEY(user_id) REFERENCES users(user_id)
);
CREATE TABLE IF NOT EXISTS sale_items (
 sale_item_id INTEGER PRIMARY KEY AUTOINCREMENT,
 sale_id INTEGER NOT NULL, product_id INTEGER NOT NULL,
 quantity INTEGER NOT NULL CHECK(quantity > 0), price REAL NOT NULL,
 FOREIGN KEY(sale_id) REFERENCES sales(sale_id) ON DELETE CASCADE,
 FOREIGN KEY(product_id) REFERENCES products(product_id)
);
"""

def connect():
    conn = sqlite3.connect(DATABASE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

@contextmanager
def db():
    conn = connect()
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    with db() as conn:
        conn.executescript(SCHEMA)
