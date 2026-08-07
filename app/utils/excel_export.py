"""Exportación del inventario a Excel (.xlsx) con los encabezados oficiales
en español, en el mismo orden que la tabla real, para que el archivo se
pueda reabrir/reimportar sin fricción.
"""
import io
from datetime import datetime

import pandas as pd

from app.utils.campos import CAMPOS_EN_ORDEN_OFICIAL


def exportar_inventario_excel(bienes: list) -> io.BytesIO:
    columnas = [c["label"] for c in CAMPOS_EN_ORDEN_OFICIAL]
    filas = []
    for bien in bienes:
        fila = {}
        for campo in CAMPOS_EN_ORDEN_OFICIAL:
            valor = getattr(bien, campo["attr"])
            if hasattr(valor, "isoformat"):
                valor = valor.isoformat()
            elif valor is not None and not isinstance(valor, (str, int, float, bool)):
                valor = float(valor)
            fila[campo["label"]] = valor
        filas.append(fila)

    df = pd.DataFrame(filas, columns=columnas)

    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine="openpyxl") as writer:
        df.to_excel(writer, index=False, sheet_name="Inventario")
    buffer.seek(0)
    return buffer


def nombre_archivo_exportacion(termino_busqueda: str | None) -> str:
    marca_tiempo = datetime.now().strftime("%Y%m%d_%H%M%S")
    if termino_busqueda:
        return f"inventario_filtrado_{marca_tiempo}.xlsx"
    return f"inventario_completo_{marca_tiempo}.xlsx"
