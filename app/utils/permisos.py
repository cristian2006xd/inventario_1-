"""Reglas de autorización, compartidas entre las páginas HTML (sesión) y la API (JWT).

Los checks de rol se hacen siempre normalizados (lowercase + strip), y el rol
técnico matchea por subcadena ("tecnico" o "técnico"), tal como en el sistema original.
"""
from app.models.inventario import ESTADO_APROBADO
from app.models.usuario import ROL_ADMINISTRADOR, Usuario


def normalizar_rol(rol: str | None) -> str:
    return (rol or "").strip().lower()


def es_administrador(usuario: Usuario | None) -> bool:
    return bool(usuario) and normalizar_rol(usuario.rol) == ROL_ADMINISTRADOR.lower()


def es_tecnico(usuario: Usuario | None) -> bool:
    if not usuario:
        return False
    rol = normalizar_rol(usuario.rol)
    return "tecnico" in rol or "técnico" in rol


def puede_editar_bien(usuario: Usuario, bien) -> bool:
    """Un bien Aprobado queda bloqueado salvo para el Administrador.

    Puede editar: el Administrador, quien registró el bien, el custodio actual
    asignado, o cualquier usuario con rol Técnico Levantamiento.
    """
    if es_administrador(usuario):
        return True

    if bien.estado == ESTADO_APROBADO:
        return False

    if bien.usuario_registro and bien.usuario_registro == usuario.username:
        return True

    if bien.custodio_actual and bien.custodio_actual == usuario.username:
        return True

    if es_tecnico(usuario):
        return True

    return False
