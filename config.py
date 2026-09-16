import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    SECRET_KEY = os.getenv("SECRET_KEY", "ruralcare-ai-super-secret-key-2026")
    
    MYSQL_HOST = os.getenv("MYSQL_HOST", "localhost")
    MYSQL_PORT = os.getenv("MYSQL_PORT", "3306")
    MYSQL_USER = os.getenv("MYSQL_USER", "root")
    MYSQL_PASSWORD = os.getenv("MYSQL_PASSWORD", "root")
    MYSQL_DB = os.getenv("MYSQL_DB", "ruralcare_ai")

    # Primary MySQL connection string
    MYSQL_URI = f"mysql+pymysql://{MYSQL_USER}:{MYSQL_PASSWORD}@{MYSQL_HOST}:{MYSQL_PORT}/{MYSQL_DB}"
    SQLITE_URI = f"sqlite:///{os.path.join(os.path.abspath(os.path.dirname(__file__)), 'ruralcare_ai.db')}"

    # Default to MYSQL_URI; can be overridden by env variable DB_TYPE
    DB_TYPE = os.getenv("DB_TYPE", "auto")
    
    if DB_TYPE == "sqlite":
        SQLALCHEMY_DATABASE_URI = SQLITE_URI
    else:
        SQLALCHEMY_DATABASE_URI = MYSQL_URI

    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True

class ProductionConfig(Config):
    DEBUG = False
