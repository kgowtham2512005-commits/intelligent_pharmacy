import os
import pymysql
from flask import Flask, render_template, jsonify
from config import Config
from models.database import db
from routes.user_routes import user_bp
from routes.admin_routes import admin_bp
from routes.voice_routes import voice_bp
from routes.alerts_routes import alerts_bp

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Check database connectivity on boot if running in auto mode without explicit DATABASE_URL
    env_db_url = os.getenv("DATABASE_URL") or os.getenv("SQLALCHEMY_DATABASE_URI")
    db_type = os.getenv("DB_TYPE", "auto").lower()

    if not env_db_url and db_type not in ("sqlite", "postgres", "postgresql"):
        try:
            conn = pymysql.connect(
                host=app.config.get("MYSQL_HOST", "localhost"),
                port=int(app.config.get("MYSQL_PORT", 3306)),
                user=app.config.get("MYSQL_USER", "root"),
                password=app.config.get("MYSQL_PASSWORD", "root"),
                database=app.config.get("MYSQL_DB", "ruralcare_ai"),
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
            print(f"Database table check notice: {e}")

    # Register blueprints
    app.register_blueprint(user_bp)
    app.register_blueprint(admin_bp)
    app.register_blueprint(voice_bp)
    app.register_blueprint(alerts_bp)

    # Health check endpoint for deployment platforms (Render, Railway, AWS, Docker)
    @app.route('/health')
    def health_check():
        return jsonify({
            'status': 'healthy',
            'service': 'RuralCare AI',
            'database': 'connected'
        }), 200

    @app.errorhandler(404)
    def page_not_found(e):
        return render_template('errors/404.html'), 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return render_template('errors/500.html'), 500

    return app

app = create_app()

if __name__ == '__main__':
    port = int(os.getenv("PORT", 5000))
    debug_mode = os.getenv("FLASK_DEBUG", "False").lower() in ("1", "true")
    print(f"Starting RuralCare AI server on port {port} (debug={debug_mode})")
    app.run(host='0.0.0.0', port=port, debug=debug_mode)

