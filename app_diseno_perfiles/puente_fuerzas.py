#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
puente_fuerzas.py
===============================================================================
Módulo puente que permite a la aplicación de diseño de perfiles cargar
automáticamente las fuerzas calculadas por la App 1 (Casa de 2 Niveles).
===============================================================================
"""

import os
import json
from typing import Dict, Any, Optional, List


def buscar_archivo_solicitaciones() -> Optional[str]:
    """Busca el archivo JSON de solicitaciones generado por la App 1."""
    dir_actual = os.path.dirname(os.path.abspath(__file__))
    dir_raiz = os.path.dirname(dir_actual)

    rutas = [
        os.path.join(dir_actual, "solicitaciones_casa_para_diseno.json"),
        os.path.join(dir_raiz, "solicitaciones_casa_para_diseno.json"),
        os.path.join(dir_raiz, "app_fuerzas_casa", "solicitaciones_casa_para_diseno.json"),
        "solicitaciones_casa_para_diseno.json"
    ]

    for r in rutas:
        if os.path.exists(r):
            return r
    return None


def cargar_paquete_solicitaciones(ruta_especifica: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Carga el paquete de datos JSON."""
    ruta = ruta_especifica or buscar_archivo_solicitaciones()
    if not ruta or not os.path.exists(ruta):
        return None

    try:
        with open(ruta, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al leer archivo de solicitaciones: {e}")
        return None


def obtener_elementos_disponibles() -> Dict[str, Dict[str, Any]]:
    """
    Retorna un diccionario de elementos listos para ser seleccionados y diseñados.
    """
    paquete = cargar_paquete_solicitaciones()
    if not paquete:
        # Valores de respaldo por defecto si aún no se ha ejecutado la App 1
        return {
            "Columna Nivel 1 (Nivelación - Defecto)": {
                "nombre": "C4",
                "rol": "Columna Nivelación Ladera (Referencia)",
                "Pu_kN": 161.67, "Mux_kNm": 10.11, "Muy_kNm": 0.85, "Vu_kN": 6.69,
                "L_m": 3.02, "K_recomendado": 1.85, "seccion_actual": "HSS6x6x3/16"
            },
            "Columna Nivel 2 (Habitable - Defecto)": {
                "nombre": "C19",
                "rol": "Columna Nivel Habitable (Referencia)",
                "Pu_kN": 49.55, "Mux_kNm": 9.28, "Muy_kNm": 0.50, "Vu_kN": 6.18,
                "L_m": 3.00, "K_recomendado": 1.55, "seccion_actual": "HSS4x4x3/16"
            },
            "Viga Nivel 1 (Entrepiso - Defecto)": {
                "nombre": "V0",
                "rol": "Viga Entrepiso Nivel 1 (Referencia)",
                "Pu_kN": 0.0, "Mux_kNm": 20.88, "Muy_kNm": 0.0, "Vu_kN": 23.51,
                "L_m": 3.50, "K_recomendado": 1.0, "seccion_actual": "HSS10x6x3/16"
            },
            "Viga Nivel 2 (Cubierta - Defecto)": {
                "nombre": "V42",
                "rol": "Viga Cubierta Nivel 2 (Referencia)",
                "Pu_kN": 0.0, "Mux_kNm": 0.36, "Muy_kNm": 0.0, "Vu_kN": 0.37,
                "L_m": 3.50, "K_recomendado": 1.0, "seccion_actual": "HSS4x2x3/16"
            }
        }

    criticos = paquete.get("elementos_criticos", {})
    elementos = {}

    for k, item in criticos.items():
        if k == "zapata_critica":
            continue
        etiqueta = f"{item.get('rol', k)} [{item.get('nombre', '')}]"
        elementos[etiqueta] = item

    return elementos
