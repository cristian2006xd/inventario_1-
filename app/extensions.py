"""Instancias únicas de extensiones, compartidas entre la app web y la API.

Se definen aquí (sin importar app/__init__.py) para evitar imports circulares:
los modelos y blueprints importan `db`, `bcrypt`, `jwt` desde este módulo.
"""
from flask_bcrypt import Bcrypt
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy

db = SQLAlchemy()
bcrypt = Bcrypt()
jwt = JWTManager()
cors = CORS()
