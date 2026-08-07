"""Decoradores de autenticación/autorización para las páginas HTML (sesión de Flask).

La capa /api/ usa JWT y sus propios decoradores (flask_jwt_extended), definidos
en app/api/auth.py — comparten el mismo modelo Usuario pero no esta sesión de cookies.
"""
from functools import wraps

from flask import flash, redirect, session, url_for

from app.models.usuario import Usuario
from app.utils.permisos import es_administrador


def usuario_actual() -> Usuario | None:
    usuario_id = session.get("usuario_id")
    if not usuario_id:
        return None
    return Usuario.query.get(usuario_id)


def login_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None or not usuario.activo:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("auth.login"))
        return vista(*args, **kwargs)

    return envoltura


def admin_required(vista):
    @wraps(vista)
    def envoltura(*args, **kwargs):
        usuario = usuario_actual()
        if usuario is None or not usuario.activo:
            flash("Debes iniciar sesión para continuar.", "warning")
            return redirect(url_for("auth.login"))
        if not es_administrador(usuario):
            flash("Acceso denegado: se requiere rol Administrador.", "danger")
            return redirect(url_for("inventario.listar"))
        return vista(*args, **kwargs)

    return envoltura
