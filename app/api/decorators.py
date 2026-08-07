"""Decoradores de autorización para la capa /api/ (JWT). Comparten el mismo
modelo Usuario y el mismo hash bcrypt que las páginas HTML, pero validan
mediante el token en vez de la cookie de sesión.
"""
from functools import wraps

from flask import jsonify
from flask_jwt_extended import get_jwt_identity, jwt_required

from app.models.usuario import Usuario
from app.utils.permisos import es_administrador


def usuario_desde_jwt() -> Usuario | None:
    identidad = get_jwt_identity()
    if not identidad:
        return None
    return Usuario.query.get(int(identidad))


def admin_required_api(vista):
    @wraps(vista)
    @jwt_required()
    def envoltura(*args, **kwargs):
        usuario = usuario_desde_jwt()
        if usuario is None or not usuario.activo:
            return jsonify({"error": "Usuario no encontrado o inactivo"}), 401
        if not es_administrador(usuario):
            return jsonify({"error": "Acceso denegado: se requiere rol Administrador"}), 403
        return vista(*args, **kwargs)

    return envoltura
