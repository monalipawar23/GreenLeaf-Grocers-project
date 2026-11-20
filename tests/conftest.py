import pytest
import app as app_module
from database import init_db
@pytest.fixture
def client(tmp_path, monkeypatch):
    db_path=tmp_path/"test.db"
    monkeypatch.setattr("database.DATABASE", str(db_path))
    # app imports the DATABASE value in database module at runtime via connect()
    init_db()
    app_module.app.config.update(TESTING=True, SECRET_KEY="test")
    return app_module.app.test_client()
