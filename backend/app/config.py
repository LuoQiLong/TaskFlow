import os
from datetime import timedelta

# JWT settings
SECRET_KEY = os.getenv("TASKFLOW_SECRET_KEY", "taskflow-dev-key-change-in-production")
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 1440  # 24 hours

# Database
DATABASE_URL = os.getenv("TASKFLOW_DATABASE_URL", "sqlite:///./taskflow.db")

# CORS
CORS_ORIGINS = [
    "http://localhost:5173",
    "http://127.0.0.1:5173",
]
