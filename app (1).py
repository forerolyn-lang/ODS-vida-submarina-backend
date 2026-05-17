from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_migrate import Migrate
from config import Config
from extensions import db
from routes.auth import auth_bp
from routes.species import species_bp
from routes.observations import observations_bp
from routes.zones import zones_bp
from routes.users import users_bp
from routes.reports import reports_bp
from routes.dashboard import dashboard_bp


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(config_class)

    # Inicializar extensiones
    db.init_app(app)
    JWTManager(app)
    Migrate(app, db)
    CORS(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    # Registrar blueprints
    app.register_blueprint(auth_bp,         url_prefix="/api/auth")
    app.register_blueprint(species_bp,      url_prefix="/api/species")
    app.register_blueprint(observations_bp, url_prefix="/api/observations")
    app.register_blueprint(zones_bp,        url_prefix="/api/zones")
    app.register_blueprint(users_bp,        url_prefix="/api/users")
    app.register_blueprint(reports_bp,      url_prefix="/api/reports")
    app.register_blueprint(dashboard_bp,    url_prefix="/api/dashboard")

    # Health check
    @app.route("/api/health")
    def health():
        return {"status": "ok", "app": "OceanLearn API"}

    return app


if __name__ == "__main__":
    app = create_app()
    with app.app_context():
        db.create_all()
    app.run(debug=True, host="0.0.0.0", port=5000)
