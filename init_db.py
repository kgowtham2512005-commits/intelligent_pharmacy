import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def ensure_database():
    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "")
    db_name = os.getenv("MYSQL_DB", "ruralcare_ai")

    print(f"Connecting to MySQL server at {host}:{port} as user '{user}'...")
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            connect_timeout=3
        )
        with connection.cursor() as cursor:
            cursor.execute(f"CREATE DATABASE IF NOT EXISTS `{db_name}` CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;")
            print(f"MySQL Database '{db_name}' ensured.")
        connection.close()
        return "mysql"
    except Exception as e:
        print(f"Notice: Could not connect to MySQL server ({e}). Falling back to local SQLite database.")
        os.environ["DB_TYPE"] = "sqlite"
        return "sqlite"

def init_tables():
    db_engine = ensure_database()
    
    from app import create_app
    from models.database import db
    from config import Config

    app = create_app()
    
    if db_engine == "sqlite":
        app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLITE_URI

    with app.app_context():
        print(f"Recreating database tables using {app.config['SQLALCHEMY_DATABASE_URI']}...")
        db.drop_all()
        db.create_all()
        print("Database tables initialized successfully!")

if __name__ == "__main__":
    init_tables()
