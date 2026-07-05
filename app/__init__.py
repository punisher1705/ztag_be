"""
Application factory.

Kept intentionally minimal at this stage — just enough to prove the
container boots, connects to its config, and responds to a health
check. Blueprints (auth, gateway, admin), middleware pipeline, and the
AI anomaly agent get registered here incrementally as they're built.
"""
from apiflask import APIFlask

from app.core.config import get_settings


def create_app() -> APIFlask:
    settings = get_settings()

    app = APIFlask(
        __name__,
        title=settings.app_name,
        version="0.1.0",
        docs_path="/docs",
        spec_path="/openapi.json",
    )
    app.config["SECRET_KEY"] = settings.app_secret_key
    app.config["DEBUG"] = settings.app_debug

    _register_blueprints(app)

    return app


def _register_blueprints(app: APIFlask) -> None:
    from app.api.health.routes import health_bp

    app.register_blueprint(health_bp)

    # Registered incrementally as each is built:
    # from app.api.auth.routes import auth_bp
    # from app.api.gateway.routes import gateway_bp
    # from app.api.admin.routes import admin_bp
    # app.register_blueprint(auth_bp, url_prefix="/api/auth")
    # app.register_blueprint(gateway_bp, url_prefix="/api")
    # app.register_blueprint(admin_bp, url_prefix="/api/admin")