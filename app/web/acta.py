from flask import Blueprint, send_file

from app.models.inventario import Inventario
from app.utils.auditoria import registrar
from app.utils.decorators import login_required, usuario_actual
from app.utils.pdf_acta import generar_acta_pdf

acta_bp = Blueprint("acta", __name__)


@acta_bp.route("/descargar_acta_pdf/<codigo>", methods=["GET"])
@login_required
def descargar(codigo):
    bien = Inventario.query.filter_by(codigo_bien=codigo).first_or_404()
    buffer = generar_acta_pdf(bien)

    registrar(usuario=usuario_actual().username, accion="Descarga de acta", codigo_bien=codigo,
              detalle="Acta de custodia PDF descargada")

    nombre_archivo = f"acta_custodia_{codigo}.pdf"
    return send_file(buffer, as_attachment=True, download_name=nombre_archivo, mimetype="application/pdf")
