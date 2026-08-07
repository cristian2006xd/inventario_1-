"""Generación del acta de custodia en PDF (reportlab) con código QR (qrcode)
para verificación rápida del bien.
"""
import io

import qrcode
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import cm
from reportlab.platypus import Image, Paragraph, SimpleDocTemplate, Spacer, Table, TableStyle
from reportlab.lib.styles import ParagraphStyle, getSampleStyleSheet


def _valor(v) -> str:
    if v is None:
        return "-"
    return str(v)


def generar_qr(bien) -> io.BytesIO:
    contenido = (
        f"Código: {_valor(bien.codigo_bien)}\n"
        f"Bien: {_valor(bien.bien)}\n"
        f"Serie: {_valor(bien.serie_identificacion)}\n"
        f"Custodio: {_valor(bien.custodio_actual)}\n"
        f"Estado: {_valor(bien.estado_bien)}"
    )
    qr = qrcode.QRCode(box_size=6, border=2)
    qr.add_data(contenido)
    qr.make(fit=True)
    imagen = qr.make_image(fill_color="black", back_color="white")
    buffer = io.BytesIO()
    imagen.save(buffer, format="PNG")
    buffer.seek(0)
    return buffer


def generar_acta_pdf(bien) -> io.BytesIO:
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=letter,
        topMargin=2 * cm, bottomMargin=2 * cm, leftMargin=2 * cm, rightMargin=2 * cm,
    )
    estilos = getSampleStyleSheet()
    titulo_style = ParagraphStyle(
        "TituloInstitucional", parent=estilos["Heading1"], textColor=colors.HexColor("#2c3e50"),
        alignment=1, fontSize=16,
    )
    subtitulo_style = ParagraphStyle(
        "Subtitulo", parent=estilos["Normal"], alignment=1, textColor=colors.HexColor("#555555"),
    )

    elementos = [
        Paragraph("INAMHI | Control de Activos", titulo_style),
        Paragraph("Acta de Custodia de Bien", subtitulo_style),
        Spacer(1, 1 * cm),
    ]

    datos = [
        ["Código del Bien", _valor(bien.codigo_bien)],
        ["Categoría / Item", _valor(bien.item_renglon)],
        ["Nombre del Bien", _valor(bien.bien)],
        ["Estado del Bien", _valor(bien.estado_bien)],
        ["Serie / Identificación", _valor(bien.serie_identificacion)],
        ["Modelo / Características", _valor(bien.modelo_caracteristicas)],
        ["Marca / Otros", _valor(bien.marca_otros)],
        ["Custodio Actual", _valor(bien.custodio_actual)],
        ["Ubicación de Bodega", _valor(bien.ubicacion_bodega)],
        ["Valor de Compra", _valor(bien.valor_compra)],
        ["Estado de Revisión", _valor(bien.estado)],
    ]
    tabla = Table(datos, colWidths=[6 * cm, 9 * cm])
    tabla.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (0, -1), colors.HexColor("#2c3e50")),
        ("TEXTCOLOR", (0, 0), (0, -1), colors.white),
        ("FONTNAME", (0, 0), (0, -1), "Helvetica-Bold"),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("ROWBACKGROUNDS", (1, 0), (1, -1), [colors.white, colors.HexColor("#f4f6f7")]),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING", (0, 0), (-1, -1), 8),
    ]))
    elementos.append(tabla)
    elementos.append(Spacer(1, 1 * cm))

    qr_buffer = generar_qr(bien)
    elementos.append(Paragraph("Código QR de verificación:", estilos["Heading4"]))
    elementos.append(Image(qr_buffer, width=3.5 * cm, height=3.5 * cm))

    doc.build(elementos)
    buffer.seek(0)
    return buffer
