import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ruralcare-ai-super-secret-key-2026")
    
    # Session & Security Settings
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    
    # MySQL Specific Configuration
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DB = os.getenv("MYSQL_DB", "ruralcare_ai")

    # Primary Database URIs
    MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    SQLITE_URI = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ruralcare_ai.db')}"

    # Database resolution (supports standard DATABASE_URL from PaaS like Render, Railway, Heroku)
    env_db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    DB_TYPE = os.getenv("DB_TYPE", "auto").lower()

    if env_db_url:
        # Standardize postgres:// to postgresql:// for SQLAlchemy 2.0+
        if env_db_url.startswith("postgres://"):
            env_db_url = env_db_url.replace("postgres://", "postgresql://", 1)
        SQLALCHEMY_DATABASE_URI = env_db_url
    elif DB_TYPE == "sqlite":
        SQLALCHEMY_DATABASE_URI = SQLITE_URI
    elif DB_TYPE == "mysql":
        SQLALCHEMY_DATABASE_URI = MYSQL_URI
    else:
        # 'auto' mode defaults to MySQL URI initially, app.py validates connectivity
        SQLALCHEMY_DATABASE_URI = MYSQL_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False
    SQLALCHEMY_ENGINE_OPTIONS = {
        "pool_pre_ping": True,
        "pool_recycle": 300,
    }

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False

class TestingConfig(Config):
    TESTING = True
    SQLALCHEMY_DATABASE_URI = "sqlite:///:memory:"
    WTF_CSRF_ENABLED = False

