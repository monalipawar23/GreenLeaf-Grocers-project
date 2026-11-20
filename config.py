import os
BASE_DIR = os.path.abspath(os.path.dirname(__file__))
DATABASE = os.path.join(BASE_DIR, "greenleaf.db")
SECRET_KEY = os.environ.get("SECRET_KEY", "change-this-secret-key-before-deployment")
