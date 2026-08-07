from flask import Flask

from app.config import get_config
from app.extensions import bcrypt, cors, db, jwt


def create_app():
    app = Flask(__name__)
    app.config.from_object(get_config())

    db.init_app(app)
    bcrypt.init_app(app)
    jwt.init_app(app)
    cors.init_app(app, resources={r"/api/*": {"origins": app.config["CORS_ORIGINS"]}})

    with app.app_context():
        from app import models  # noqa: F401  registra los modelos en SQLAlchemy

    from app.api import register_api_blueprints
    from app.web import register_web_blueprints

    register_web_blueprints(app)
    register_api_blueprints(app)

    from app.utils.decorators import usuario_actual

    @app.context_processor
    def inyectar_usuario():
        return {"usuario_actual": usuario_actual()}

    return app
