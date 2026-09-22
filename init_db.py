import os
import pymysql
from dotenv import load_dotenv

load_dotenv()

def ensure_database():
    env_db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    db_type = os.getenv("DB_TYPE", "auto").lower()

    if env_db_url or db_type == "sqlite":
        return "configured"

    host = os.getenv("MYSQL_HOST", "localhost")
    port = int(os.getenv("MYSQL_PORT", "3306"))
    user = os.getenv("MYSQL_USER", "root")
    password = os.getenv("MYSQL_PASSWORD", "root")
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

def init_tables(seed=True):
    ensure_database()
    
    from app import create_app
    from models.database import db

    app = create_app()

    with app.app_context():
        print(f"Ensuring database tables using {app.config['SQLALCHEMY_DATABASE_URI']}...")
        db.create_all()
        print("Database tables initialized successfully!")

        if seed:
            from import_dataset import import_data
            import_data()

if __name__ == "__main__":
    init_tables()

