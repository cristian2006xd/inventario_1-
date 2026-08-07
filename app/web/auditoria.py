from flask import Blueprint, render_template

from app.models.bitacora import BitacoraAuditoria
from app.utils.decorators import admin_required

auditoria_bp = Blueprint("auditoria", __name__)


@auditoria_bp.route("/auditoria", methods=["GET"])
@admin_required
def listar():
    eventos = BitacoraAuditoria.query.order_by(BitacoraAuditoria.fecha.desc()).limit(200).all()
    return render_template("auditoria.html", eventos=eventos)
