import pytest
from werkzeug.security import generate_password_hash
from database import db
from utils import parse_positive_int, valid_iso_date
from app import app

def setup_user():
    with db() as conn:
        conn.execute("INSERT OR IGNORE INTO users(username,password_hash,role) VALUES(?,?,?)",
                     ("tester",generate_password_hash("pass"),"admin"))

def test_positive_quantity():
    assert parse_positive_int("3")==3
def test_zero_quantity_rejected():
    with pytest.raises(ValueError): parse_positive_int("0")
def test_negative_quantity_rejected():
    with pytest.raises(ValueError): parse_positive_int("-2")
def test_invalid_quantity_rejected():
    with pytest.raises(ValueError): parse_positive_int("abc")
def test_valid_date():
    assert valid_iso_date("2026-01-15")=="2026-01-15"
def test_invalid_date():
    with pytest.raises(ValueError): valid_iso_date("15-01-2026")
def test_login_page(client):
    assert client.get("/login").status_code==200
def test_unauthenticated_dashboard_redirect(client):
    assert client.get("/dashboard").status_code==302
def test_bad_login(client):
    response=client.post("/login",data={"username":"nobody","password":"bad"})
    assert response.status_code==200
def test_logout_redirect(client):
    assert client.get("/logout").status_code==302
