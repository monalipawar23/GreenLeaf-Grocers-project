# GreenLeaf Grocers — Inventory & Sales Management

A Flask + SQLite student project with role-based login, product CRUD, billing, automatic stock deduction, low-stock/expiry alerts, CSV import/export, analytics and tests.

## 1. Requirements
- Python 3.10 or newer
- VS Code or another editor
- Internet only for installing Python packages

## 2. Setup on Windows (PowerShell)
Open PowerShell in this project folder:

```powershell
python -m venv venv
.\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python seed_data.py
python app.py
```

If PowerShell blocks activation, run:
```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
.\venv\Scripts\Activate.ps1
```

Open `http://127.0.0.1:5000` in Chrome.

## 3. Demo login
- Admin: `admin` / `admin123`
- Cashier: `cashier` / `cashier123`

Change these passwords and set a strong `SECRET_KEY` before deployment. This is a learning/demo project; do not expose the Flask development server publicly.

## 4. How to use
1. Sign in as admin.
2. Open Products → add/edit/search products. Admin can import CSV.
3. Open Billing → select multiple products and quantities → optional discount → Create Bill.
4. The bill is saved and stock is deducted in the same database transaction.
5. Dashboard shows today's sales, low-stock and expiry alerts.
6. Reports shows revenue, average bill value, daily/monthly totals, top products, category share, low-stock, expiry and slow-moving lists.
7. Export sales from Reports as CSV. Use Print Bill to print or save a bill as PDF from the browser print dialog.
8. Sign in as cashier to test billing-only access.

## 5. CSV import format
```csv
name,category,unit_price,stock_qty,reorder_level,expiry_date
Green Apples,Fruits,130,30,8,2027-02-15
```
Date must use `YYYY-MM-DD`.

## 6. Run tests
```powershell
python -m pytest -v
```
Tests use a temporary SQLite database. The project tests validation and route access; add integration tests for your own changes.

## 7. Project structure
```text
GreenLeaf_Grocers_Project/
├── app.py                 # Flask routes and business logic
├── config.py              # app configuration and database path
├── database.py            # SQLite schema and connection helper
├── reports.py             # pandas-based analytics
├── seed_data.py           # demo users, 60 products, 550 sales
├── utils.py               # input/date validation
├── requirements.txt
├── greenleaf.db           # created after setup (not included)
├── templates/             # HTML pages
├── static/style.css
└── tests/                 # pytest tests
```

## 8. Database design
- `users(user_id PK, username UNIQUE, password_hash, role)`
- `suppliers(supplier_id PK, name, phone, email)`
- `products(product_id PK, supplier_id FK, name, category, unit_price, stock_qty, reorder_level, expiry_date)`
- `sales(sale_id PK, user_id FK, sale_date, sale_time, total_amount, discount)`
- `sale_items(sale_item_id PK, sale_id FK, product_id FK, quantity, price)`

Each sale can contain many sale_items. Each product can appear in many sale_items. Each user can create many sales. Passwords are stored as Werkzeug hashes, not plain text.

## 9. Important implementation notes
- Stock checks and stock deductions happen inside one SQLite transaction.
- The app rejects zero/negative quantities, invalid dates, negative prices and insufficient stock.
- Low-stock means `stock_qty <= reorder_level`.
- Expiry alert means expiry date from today through the next 15 days.
- Slow-moving means no sale in the last 30 days.
- Average bill value = total revenue / bill count.
- Category share is based on quantities sold in this starter version.
- Stock turnover can be added once you decide whether to calculate it by cost of goods sold or units sold and have opening/average inventory data.

## 10. Four-week development plan
**Week 1:** Understand schema, run seed script, inspect login, add/edit/search products.  
**Week 2:** Test multi-item billing, discount, stock deduction, CSV import/export and validations.  
**Week 3:** Review pandas reports, date filters, alerts and KPIs; add charts if required by your guide.  
**Week 4:** Run tests, take screenshots, prepare ER diagram, write report, push meaningful Git commits and rehearse demo.

## 11. Suggested viva topics
- Why Flask? Lightweight Python web framework.
- Why SQLite? Simple relational database with no separate server.
- Why password hashing? The original password should not be stored.
- Why foreign keys? Preserve relationships between users, sales and products.
- Why a transaction in billing? Either the whole bill and stock deduction succeeds, or none of it does.
- What is a KPI? A measurable value used to evaluate performance.
