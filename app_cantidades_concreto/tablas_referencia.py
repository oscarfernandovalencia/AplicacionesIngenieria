#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tablas_referencia.py
Tablas de consulta técnica de dosificaciones de concreto, mortero y barras de acero.
"""

import os
import sys

# Permitir importación tanto como paquete como archivo directo
dir_actual = os.path.dirname(os.path.abspath(__file__))
if dir_actual not in sys.path:
    sys.path.insert(0, dir_actual)

try:
    from .concreto_core import DOSIFICACIONES_CONCRETO_REF, DOSIFICACIONES_MORTERO_REF, TABLA_VARILLAS_ACERO
except ImportError:
    from concreto_core import DOSIFICACIONES_CONCRETO_REF, DOSIFICACIONES_MORTERO_REF, TABLA_VARILLAS_ACERO


def texto_tabla_varillas() -> str:
    lineas = [
        "=" * 78,
        f"{'#':<4} | {'DIÁMETRO':<10} | {'DIÁMETRO (mm)':<14} | {'MASA (kg/m)':<12} | {'ÁREA (cm²)':<10} | {'PERÍMETRO (cm)'}",
        "=" * 78
    ]
    for n, d in TABLA_VARILLAS_ACERO.items():
        lineas.append(
            f"#{n:<3} | {d['pulgadas']:<10} | {d['diam_mm']:<14.1f} | {d['masa_kg_m']:<12.3f} | {d['area_cm2']:<10.2f} | {d['perimetro_cm']:<12.2f}"
        )
    lineas.append("=" * 78)
    return "\n".join(lineas)


def texto_tabla_dosificaciones() -> str:
    lineas = [
        "=" * 85,
        "  TABLA DE DOSIFICACIONES DE CONCRETO (CEMENTO : ARENA : GRAVA)",
        "=" * 85,
        f"{'PROPORCIÓN':<12} | {'RESISTENCIA APROX.':<30} | {'USO RECOMENDADO'}",
        "-" * 85
    ]
    for prop, inf in DOSIFICACIONES_CONCRETO_REF.items():
        lineas.append(f"{prop:<12} | {inf['fc_aprox']:<30} | {inf['uso']}")

    lineas.extend([
        "=" * 85,
        "  TABLA DE DOSIFICACIONES DE MORTERO (CEMENTO : ARENA)",
        "=" * 85,
        f"{'PROPORCIÓN':<12} | {'RESISTENCIA APROX.':<30} | {'USO RECOMENDADO'}",
        "-" * 85
    ])
    for prop, inf in DOSIFICACIONES_MORTERO_REF.items():
        lineas.append(f"{prop:<12} | {inf['resistencia']:<30} | {inf['uso']}")
    lineas.append("=" * 85)
    return "\n".join(lineas)
