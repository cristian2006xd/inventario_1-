from flask import Blueprint, flash, redirect, render_template, request, send_file, url_for
from sqlalchemy import or_

from app.extensions import db
from app.models.inventario import ESTADO_EN_REVISION, Inventario
from app.models.usuario import Usuario
from app.utils.auditoria import registrar
from app.utils.campos import CAMPOS_BIEN, TABS, TIPO_TEXTO
from app.utils.decorators import login_required, usuario_actual
from app.utils.excel_export import exportar_inventario_excel, nombre_archivo_exportacion
from app.utils.parsing import limpiar_texto_corto, parse_decimal, parse_entero, parse_fecha
from app.utils.permisos import campos_bloqueados_para, es_administrador

inventario_bp = Blueprint("inventario", __name__)

ITEMS_POR_PAGINA = 10


def _query_busqueda(termino: str):
    consulta = Inventario.query
    if termino:
        patron = f"%{termino}%"
        consulta = consulta.filter(or_(
            Inventario.codigo_bien.ilike(patron),
            Inventario.codigo_anterior.ilike(patron),
            Inventario.identificador.ilike(patron),
            Inventario.bien.ilike(patron),
            Inventario.serie_identificacion.ilike(patron),
            Inventario.marca_otros.ilike(patron),
            Inventario.estado_bien.ilike(patron),
            Inventario.bodega.ilike(patron),
            Inventario.ubicacion_bodega.ilike(patron),
            Inventario.custodio_actual.ilike(patron),
            Inventario.custodio_activo.ilike(patron),
            Inventario.nro_cedula_ruc.ilike(patron),
            Inventario.usuario_registro.ilike(patron),
        ))
    return consulta.order_by(Inventario.id.desc())


@inventario_bp.route("/inventario", methods=["GET"])
@login_required
def listar():
    termino = (request.args.get("q") or "").strip()
    pagina = request.args.get("pagina", 1, type=int)

    consulta = _query_busqueda(termino)
    total = consulta.count()
    total_paginas = max(1, (total + ITEMS_POR_PAGINA - 1) // ITEMS_POR_PAGINA)
    pagina = min(max(1, pagina), total_paginas)

    bienes = consulta.offset((pagina - 1) * ITEMS_POR_PAGINA).limit(ITEMS_POR_PAGINA).all()
    tecnicos = Usuario.query.filter_by(activo=True).order_by(Usuario.username).all()

    return render_template(
        "inventario.html",
        bienes=bienes,
        termino=termino,
        pagina=pagina,
        total_paginas=total_paginas,
        total=total,
        tabs=TABS,
        campos=CAMPOS_BIEN,
        tecnicos=tecnicos,
        campos_bloqueados=campos_bloqueados_para(usuario_actual()),
    )


@inventario_bp.route("/inventario/nuevo", methods=["POST"])
@login_required
def nuevo():
    usuario = usuario_actual()
    codigo_bien = (request.form.get("codigo_bien") or "").strip()

    if not codigo_bien:
        flash("El Código del Bien es obligatorio para crear un nuevo registro.", "danger")
        return redirect(url_for("inventario.listar"))

    if Inventario.query.filter_by(codigo_bien=codigo_bien).first():
        flash(f"Ya existe un bien con el código '{codigo_bien}'.", "danger")
        return redirect(url_for("inventario.listar"))

    bien = Inventario(codigo_bien=codigo_bien, estado=ESTADO_EN_REVISION, usuario_registro=usuario.username)
    _aplicar_campos_formulario(bien, request.form, incluir_codigo=False, campos_bloqueados=campos_bloqueados_para(usuario))

    db.session.add(bien)
    db.session.commit()

    registrar(usuario=usuario.username, accion="Creación de bien", codigo_bien=codigo_bien,
              detalle="Nuevo registro creado desde el formulario de inventario")

    flash(f"Bien '{codigo_bien}' creado correctamente con estado En Revisión.", "success")
    return redirect(url_for("inventario.listar"))


@inventario_bp.route("/inventario/eliminar/<codigo>", methods=["POST"])
@login_required
def eliminar(codigo):
    usuario = usuario_actual()
    if not es_administrador(usuario):
        flash("Acceso denegado: solo el Administrador puede eliminar bienes.", "danger")
        return redirect(url_for("inventario.listar"))

    bien = Inventario.query.filter_by(codigo_bien=codigo).first_or_404()
    db.session.delete(bien)
    db.session.commit()

    registrar(usuario=usuario.username, accion="Eliminación de bien", codigo_bien=codigo,
              detalle=f"Bien '{codigo}' eliminado del inventario")

    flash(f"Bien '{codigo}' eliminado correctamente.", "success")
    return redirect(url_for("inventario.listar"))


@inventario_bp.route("/inventario/exportar", methods=["GET"])
@login_required
def exportar():
    termino = (request.args.get("q") or "").strip()
    bienes = _query_busqueda(termino).all()

    buffer = exportar_inventario_excel(bienes)
    nombre_archivo = nombre_archivo_exportacion(termino)

    registrar(usuario=usuario_actual().username, accion="Exportación de Excel", detalle=(
        f"Exportadas {len(bienes)} filas" + (f" (filtro: '{termino}')" if termino else "")
    ))

    return send_file(
        buffer,
        as_attachment=True,
        download_name=nombre_archivo,
        mimetype="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
    )


def _aplicar_campos_formulario(
    bien: Inventario, form, incluir_codigo: bool = True, campos_bloqueados: frozenset = frozenset()
) -> None:
    from app.utils.campos import TIPO_DECIMAL, TIPO_ENTERO, TIPO_FECHA

    for campo in CAMPOS_BIEN:
        if campo["attr"] == "codigo_bien" and not incluir_codigo:
            continue
        if campo["attr"] in campos_bloqueados:
            continue
        if campo["attr"] not in form:
            continue
        valor_crudo = form.get(campo["attr"])
        if campo["tipo"] == TIPO_DECIMAL:
            valor = parse_decimal(valor_crudo)
        elif campo["tipo"] == TIPO_ENTERO:
            valor = parse_entero(valor_crudo)
        elif campo["tipo"] == TIPO_FECHA:
            valor = parse_fecha(valor_crudo)
        elif campo["tipo"] == TIPO_TEXTO:
            valor = limpiar_texto_corto(valor_crudo)
        else:
            valor = (valor_crudo or "").strip() or None
        setattr(bien, campo["attr"], valor)
