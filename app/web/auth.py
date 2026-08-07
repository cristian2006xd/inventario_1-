from flask import Blueprint, flash, redirect, render_template, request, session, url_for

from app.models.usuario import Usuario
from app.utils.auditoria import registrar

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if session.get("usuario_id"):
        return redirect(url_for("inventario.listar"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        password = request.form.get("password") or ""

        usuario = Usuario.query.filter_by(username=username).first()
        if usuario is None or not usuario.activo or not usuario.check_password(password):
            flash("Usuario o contraseña incorrectos.", "danger")
            return render_template("login.html"), 401

        session.clear()
        session["usuario_id"] = usuario.id
        session["username"] = usuario.username
        session["rol"] = usuario.rol
        registrar(usuario=usuario.username, accion="Inicio de sesión", detalle=None)

        flash(f"Bienvenido, {usuario.nombre_completo or usuario.username}.", "success")
        return redirect(url_for("inventario.listar"))

    return render_template("login.html")


@auth_bp.route("/logout")
def logout():
    username = session.get("username")
    if username:
        registrar(usuario=username, accion="Cierre de sesión", detalle=None)
    session.clear()
    flash("Sesión cerrada correctamente.", "info")
    return redirect(url_for("auth.login"))
