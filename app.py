import os
import pymysql
from flask import Flask, render_template
from config import Config
from models.database import db
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.voice_routes import voice_bp
from routes.alerts_routes import alerts_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Check database connectivity on boot
    db_type = os.getenv("DB_TYPE", "auto")
    if db_type != "sqlite":
        try:
            conn = pymysql.connect(
                host=app.config["MYSQL_HOST"],
                port=int(app.config["MYSQL_PORT"]),
                user=app.config["MYSQL_USER"],
                password=app.config["MYSQL_PASSWORD"],
                database=app.config["MYSQL_DB"],
                connect_timeout=2
            )
            conn.close()
        except Exception:
            # Fallback to SQLite if MySQL service/credentials are unavailable
            app.config["SQLALCHEMY_DATABASE_URI"] = Config.SQLITE_URI

    # Initialize database extension
    db.init_app(app)

    # Auto-create tables if they don't exist
    with app.app_context():
        try:
            db.create_all()
        except Exception as e:
            print(f"Database table check: {e}")

    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(alerts_bp)

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500


    return app

app = create_app()

if __name__ == '__main__':
    print("Starting RuralCare AI server on http://127.0.0.1:5000")
    app.run(host='0.0.0.0', port=5000, debug=True)
