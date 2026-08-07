from datetime import datetime

from flask import Blueprint, flash, redirect, render_template, request, url_for
from sqlalchemy import or_

from app.extensions import db
from app.models.inventario import ESTADO_APROBADO, ESTADO_BORRADOR, ESTADO_EN_REVISION, ESTADO_OBSERVADO, Inventario
from app.utils.auditoria import registrar
from app.utils.decorators import admin_required, usuario_actual

tic_bp = Blueprint("tic", __name__)

ESTADOS_FILTRO = {ESTADO_EN_REVISION, ESTADO_OBSERVADO, ESTADO_APROBADO}


@tic_bp.route("/tic/bandeja", methods=["GET"])
@admin_required
def bandeja():
    termino = (request.args.get("q") or "").strip()
    estado_filtro = (request.args.get("estado") or "").strip()

    pendientes = Inventario.query.filter(
        or_(Inventario.estado == ESTADO_EN_REVISION, Inventario.estado == ESTADO_BORRADOR, Inventario.estado.is_(None))
    ).count()
    observados = Inventario.query.filter_by(estado=ESTADO_OBSERVADO).count()
    aprobados = Inventario.query.filter_by(estado=ESTADO_APROBADO).count()
    total = Inventario.query.count()

    consulta = Inventario.query
    if estado_filtro and estado_filtro in ESTADOS_FILTRO:
        consulta = consulta.filter_by(estado=estado_filtro)
    elif estado_filtro not in ("", "TODOS"):
        estado_filtro = ""

    if termino:
        patron = f"%{termino}%"
        consulta = consulta.filter(or_(
            Inventario.codigo_bien.ilike(patron),
            Inventario.bien.ilike(patron),
            Inventario.custodio_actual.ilike(patron),
            Inventario.usuario_registro.ilike(patron),
        ))

    bienes = consulta.order_by(Inventario.id.desc()).all()

    return render_template(
        "bandeja_tic.html",
        bienes=bienes,
        kpi_pendientes=pendientes,
        kpi_observados=observados,
        kpi_aprobados=aprobados,
        kpi_total=total,
        termino=termino,
        estado_filtro=estado_filtro,
    )


@tic_bp.route("/tic/aprobar/<codigo>", methods=["POST"])
@admin_required
def aprobar(codigo):
    usuario = usuario_actual()
    bien = Inventario.query.filter_by(codigo_bien=codigo).first_or_404()
    nota = (request.form.get("nota") or "").strip()

    bien.estado = ESTADO_APROBADO
    bien.observaciones_tic = None
    bien.revisado_por_tic = usuario.username
    bien.fecha_revision_tic = datetime.utcnow()
    db.session.commit()

    registrar(usuario=usuario.username, accion="Aprobación TIC", codigo_bien=codigo,
              detalle=nota or "Bien aprobado sin observaciones adicionales")

    flash(f"Bien '{codigo}' aprobado correctamente.", "success")
    return redirect(url_for("tic.bandeja"))


@tic_bp.route("/tic/observar/<codigo>", methods=["POST"])
@admin_required
def observar(codigo):
    usuario = usuario_actual()
    bien = Inventario.query.filter_by(codigo_bien=codigo).first_or_404()
    motivo = (request.form.get("motivo") or "").strip()

    if not motivo:
        flash("Debes indicar un motivo para observar el bien.", "danger")
        return redirect(url_for("tic.bandeja"))

    bien.estado = ESTADO_OBSERVADO
    bien.observaciones_tic = motivo
    bien.revisado_por_tic = usuario.username
    bien.fecha_revision_tic = datetime.utcnow()
    db.session.commit()

    registrar(usuario=usuario.username, accion="Observación TIC", codigo_bien=codigo, detalle=motivo)

    flash(f"Bien '{codigo}' marcado como Observado.", "warning")
    return redirect(url_for("tic.bandeja"))
