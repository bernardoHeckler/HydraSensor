import os


DB_PATH = os.getenv("APP_DB_PATH", "rfid_access.db")
CSV_PATH = os.getenv("APP_CSV_PATH", "rfid_access_log.csv")
ADMIN_TOKEN = os.getenv("ADMIN_TOKEN", "admin-demo-token")
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
