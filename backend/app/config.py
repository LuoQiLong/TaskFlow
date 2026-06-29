import os
from datetime import timedelta
from pathlib import Path

# Load .env file (if it exists)
_env_path = Path(__file__).resolve().parent.parent / ".env"
if _env_path.exists():
    with open(_env_path, encoding="utf-8") as _f:
        for _line in _f:
            _line = _line.strip()
            if _line and not _line.startswith("#") and "=" in _line:
                _key, _val = _line.split("=", 1)
                _key = _key.strip()
                _val = _val.strip().strip('"').strip("'")
                if _key and _key not in os.environ:
                    os.environ[_key] = _val

# JWT settings
SECRET_KEY = os.getenv("TASKFLOW_SECRET_KEY", "taskflow-dev-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Database — SQL Server
import urllib.parse

DB_HOST = os.getenv("TASKFLOW_DB_HOST", "localhost")
DB_PORT = os.getenv("TASKFLOW_DB_PORT", "")
DB_USER = os.getenv("TASKFLOW_DB_USER", "")
DB_PASSWORD = os.getenv("TASKFLOW_DB_PASSWORD", "")
DB_NAME = os.getenv("TASKFLOW_DB_NAME", "taskflow")
DB_DRIVER = os.getenv("TASKFLOW_DB_DRIVER", "ODBC Driver 17 for SQL Server")

def _build_conn_str(database: str) -> str:
    port_part = f",{DB_PORT}" if DB_PORT else ""
    return f"DRIVER={{{DB_DRIVER}}};SERVER={DB_HOST}{port_part};DATABASE={{{database}}};UID={DB_USER};PWD={DB_PASSWORD};TrustServerCertificate=yes"

def _build_url(database: str) -> str:
    quoted = urllib.parse.quote_plus(_build_conn_str(database))
    return f"mssql+pyodbc:///?odbc_connect={quoted}"

DATABASE_URL = _build_url(DB_NAME)

# SMTP email config (QQ邮箱)
SMTP_HOST = os.getenv("TASKFLOW_SMTP_HOST", "smtp.qq.com")
SMTP_PORT = int(os.getenv("TASKFLOW_SMTP_PORT", "587"))
SMTP_USER = os.getenv("TASKFLOW_SMTP_USER", "")
SMTP_PASSWORD = os.getenv("TASKFLOW_SMTP_PASSWORD", "")
SMTP_FROM_NAME = os.getenv("TASKFLOW_SMTP_FROM_NAME", "TaskFlow")

# CORS
# CORS origins — override via env for production, defaults for local dev
_CORS_ENV = os.getenv("TASKFLOW_CORS_ORIGINS", "")
if _CORS_ENV:
    CORS_ORIGINS = [o.strip() for o in _CORS_ENV.split(",") if o.strip()]
else:
    CORS_ORIGINS = [
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ]
