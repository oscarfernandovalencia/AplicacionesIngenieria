#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
concreto_core.py
===============================================================================
Motor de cálculo y dosificación de concreto, mortero y propiedades de acero
de refuerzo para obras civiles y edificación en general.

Características:
- Cálculo general de mezclas de concreto por volumen (m³) o dimensiones de
  elementos constructivos (losas, columnas rectangulares/circulares, vigas,
  zapatas, muros).
- Dosificación de morteros para revoques, pañetes y pegas.
- Factores de contracción volumétrica (esponjamiento seco -> húmedo).
- Presentación de materiales en kg, bultos (50 kg y 42.5 kg), latas (5 galones = 18.93 L)
  y volumen en m³ / viajes comerciales de arena y grava.
- Consulta de aceros y varillas comerciales (#2 a #11 según ASTM A615 / NTC 2289).
===============================================================================
"""

from dataclasses import dataclass
import math
from typing import Dict, List, Tuple, Optional, Any

# Constantes físicas y comerciales estándar en construcción
VOLUMEN_LATA_M3 = 0.01892705       # 1 Lata de construcción (5 galones US = 18.927 litros)
DENSIDAD_CEMENTO_KG_M3 = 1440.0   # Densidad aparente seca del cemento Portland (kg/m³)
FACTOR_CONTRACCION_MORTERO = 1.52  # Relación volumen seco / volumen mezclado húmedo
FACTOR_CONTRACCION_CONCRETO = 1.57 # Relación volumen seco / volumen mezclado húmedo
VOLUMEN_VIAJE_M3 = 6.0             # Capacidad típica de volqueta sencilla (6 m³)


# =============================================================================
# DOSIFICACIONES TÍPICAS DE REFERENCIA
# =============================================================================
DOSIFICACIONES_CONCRETO_REF = {
    "1:2:2": {
        "cemento": 1.0, "arena": 2.0, "grava": 2.0,
        "fc_aprox": "28 MPa (~280 kg/cm² / 4000 psi)",
        "uso": "Columnas, vigas principales, elementos de alta resistencia"
    },
    "1:2:3": {
        "cemento": 1.0, "arena": 2.0, "grava": 3.0,
        "fc_aprox": "21 MPa (~210 kg/cm² / 3000 psi)",
        "uso": "Estructuras convencionales, losas macizas/aligeradas, zapatas, vigas de amarre"
    },
    "1:2:4": {
        "cemento": 1.0, "arena": 2.0, "grava": 4.0,
        "fc_aprox": "17.5 MPa (~175 kg/cm² / 2500 psi)",
        "uso": "Concreto estructural liviano, andenes, pisos peatonales, bordillos"
    },
    "1:3:5": {
        "cemento": 1.0, "arena": 3.0, "grava": 5.0,
        "fc_aprox": "14 MPa (~140 kg/cm² / 2000 psi)",
        "uso": "Concreto simple, solados, ciclópeo, rellenos y sobrecimientos"
    }
}

DOSIFICACIONES_MORTERO_REF = {
    "1:3": {
        "cemento": 1.0, "arena": 3.0,
        "resistencia": "~12.5 MPa (~125 kg/cm²)",
        "uso": "Revoques o pañetes impermeables, tanques, pega de alta exigencia"
    },
    "1:4": {
        "cemento": 1.0, "arena": 4.0,
        "resistencia": "~9.0 MPa (~90 kg/cm²)",
        "uso": "Revoques exteriores, pega de muros estructurales o perimetrales"
    },
    "1:5": {
        "cemento": 1.0, "arena": 5.0,
        "resistencia": "~6.0 MPa (~60 kg/cm²)",
        "uso": "Revoques interiores, pañetes comunes, nivelación de pisos"
    },
    "1:6": {
        "cemento": 1.0, "arena": 6.0,
        "resistencia": "~4.0 MPa (~40 kg/cm²)",
        "uso": "Pega de mampostería no estructural, rellenos ligeros"
    }
}

TABLA_VARILLAS_ACERO = {
    2:  {"pulgadas": "1/4\"",  "diam_mm": 6.4,  "masa_kg_m": 0.250, "area_cm2": 0.32,  "perimetro_cm": 2.00},
    3:  {"pulgadas": "3/8\"",  "diam_mm": 9.5,  "masa_kg_m": 0.560, "area_cm2": 0.71,  "perimetro_cm": 2.99},
    4:  {"pulgadas": "1/2\"",  "diam_mm": 12.7, "masa_kg_m": 0.994, "area_cm2": 1.29,  "perimetro_cm": 3.99},
    5:  {"pulgadas": "5/8\"",  "diam_mm": 15.9, "masa_kg_m": 1.552, "area_cm2": 1.99,  "perimetro_cm": 4.99},
    6:  {"pulgadas": "3/4\"",  "diam_mm": 19.1, "masa_kg_m": 2.235, "area_cm2": 2.84,  "perimetro_cm": 5.98},
    7:  {"pulgadas": "7/8\"",  "diam_mm": 22.2, "masa_kg_m": 3.042, "area_cm2": 3.87,  "perimetro_cm": 6.98},
    8:  {"pulgadas": "1\"",    "diam_mm": 25.4, "masa_kg_m": 3.973, "area_cm2": 5.10,  "perimetro_cm": 7.98},
    9:  {"pulgadas": "1-1/8\"", "diam_mm": 28.7, "masa_kg_m": 5.060, "area_cm2": 6.45,  "perimetro_cm": 9.00},
    10: {"pulgadas": "1-1/4\"", "diam_mm": 32.3, "masa_kg_m": 6.404, "area_cm2": 8.19,  "perimetro_cm": 10.13},
    11: {"pulgadas": "1-3/8\"", "diam_mm": 35.8, "masa_kg_m": 7.907, "area_cm2": 10.06, "perimetro_cm": 11.25},
}


# =============================================================================
# FUNCIONES DE CÁLCULO GEOMÉTRICO DE ELEMENTOS ESTRUCTURALES
# =============================================================================
def volumen_losa(largo_m: float, ancho_m: float, espesor_m: float, cantidad: int = 1) -> float:
    """Calcula el volumen de una losa o piso en m³."""
    return max(0.0, float(largo_m) * float(ancho_m) * float(espesor_m) * int(cantidad))

def volumen_columna_rectangular(lado_a_m: float, lado_b_m: float, altura_m: float, cantidad: int = 1) -> float:
    """Calcula el volumen de columnas prismáticas rectangulares o cuadradas en m³."""
    return max(0.0, float(lado_a_m) * float(lado_b_m) * float(altura_m) * int(cantidad))

def volumen_columna_circular(diametro_m: float, altura_m: float, cantidad: int = 1) -> float:
    """Calcula el volumen de columnas cilíndricas en m³."""
    radio = float(diametro_m) / 2.0
    return max(0.0, math.pi * (radio ** 2) * float(altura_m) * int(cantidad))

def volumen_viga(base_m: float, altura_m: float, longitud_m: float, cantidad: int = 1) -> float:
    """Calcula el volumen de vigas en m³."""
    return max(0.0, float(base_m) * float(altura_m) * float(longitud_m) * int(cantidad))

def volumen_zapata(largo_m: float, ancho_m: float, peralte_m: float, cantidad: int = 1) -> float:
    """Calcula el volumen de zapatas aisladas o dados de cimentación en m³."""
    return max(0.0, float(largo_m) * float(ancho_m) * float(peralte_m) * int(cantidad))

def volumen_muro(longitud_m: float, altura_m: float, espesor_m: float, cantidad: int = 1) -> float:
    """Calcula el volumen de muros de contención o sobrecimientos de concreto en m³."""
    return max(0.0, float(longitud_m) * float(altura_m) * float(espesor_m) * int(cantidad))


# =============================================================================
# CÁLCULO DE MEZCLA DE CONCRETO
# =============================================================================
@dataclass
class ResultadoConcreto:
    volumen_diseno_m3: float
    desperdicio_pct: float
    volumen_total_m3: float
    proporcion_str: str
    cemento_kg: float
    bultos_50kg: float
    bultos_42_5kg: float
    cemento_latas: float
    arena_m3: float
    arena_latas: float
    arena_viajes_6m3: float
    grava_m3: float
    grava_latas: float
    grava_viajes_6m3: float
    agua_litros: float
    agua_latas: float

    def generar_reporte_texto(self, titulo: str = "Cálculo de Concreto") -> str:
        lineas = [
            "=" * 68,
            f"  🧱 REPORTE DE CANTIDADES DE CONCRETO - {titulo.upper()}",
            "=" * 68,
            f"• Volumen de Diseño:      {self.volumen_diseno_m3:.3f} m³",
            f"• Desperdicio Considerado: {self.desperdicio_pct:.1f}%",
            f"• Volumen Total a Vaciar:  {self.volumen_total_m3:.3f} m³",
            f"• Proporción C:A:G:        {self.proporcion_str}",
            "-" * 68,
            f"{'MATERIAL':<22} | {'CANTIDAD PRINCIPAL':<20} | {'EQUIVALENCIA PRÁCTICA'}",
            "-" * 68,
            f"{'Cemento Portland':<22} | {self.cemento_kg:<12.1f} kg     | {self.bultos_50kg:<5.1f} bultos (50 kg) / {self.cemento_latas:<5.1f} latas",
            f"{'':<22} | {'':<20} | ({self.bultos_42_5kg:.1f} bultos de 42.5 kg)",
            f"{'Arena Limpia':<22} | {self.arena_m3:<12.3f} m³     | {self.arena_latas:<5.1f} latas ({self.arena_viajes_6m3:.2f} viajes de 6m³)",
            f"{'Grava / Triturado':<22} | {self.grava_m3:<12.3f} m³     | {self.grava_latas:<5.1f} latas ({self.grava_viajes_6m3:.2f} viajes de 6m³)",
            f"{'Agua Estimada':<22} | {self.agua_litros:<12.1f} Litros | {self.agua_latas:<5.1f} latas (a/c aprox. 0.55)",
            "=" * 68,
        ]
        return "\n".join(lineas)


def calcular_concreto(volumen_m3: float, 
                      proporcion: Tuple[float, float, float] = (1.0, 2.0, 3.0),
                      desperdicio_pct: float = 5.0,
                      densidad_cemento_kg_m3: float = DENSIDAD_CEMENTO_KG_M3) -> ResultadoConcreto:
    """
    Calcula los materiales requeridos para un volumen dado de concreto.
    """
    vol_base = max(0.0, float(volumen_m3))
    factor_desp = 1.0 + (max(0.0, float(desperdicio_pct)) / 100.0)
    vol_total = vol_base * factor_desp

    p_cem, p_are, p_gra = proporcion
    suma = p_cem + p_are + p_gra
    if suma <= 0:
        raise ValueError("La suma de las proporciones debe ser mayor a 0.")

    # Volumen seco total considerando contracción al hidratar
    volumen_seco_total = vol_total * FACTOR_CONTRACCION_CONCRETO
    vol_cemento = (p_cem / suma) * volumen_seco_total
    vol_arena = (p_are / suma) * volumen_seco_total
    vol_grava = (p_gra / suma) * volumen_seco_total

    cemento_kg = vol_cemento * densidad_cemento_kg_m3
    bultos_50 = cemento_kg / 50.0
    bultos_42_5 = cemento_kg / 42.5
    cemento_latas = (cemento_kg / densidad_cemento_kg_m3) / VOLUMEN_LATA_M3

    arena_latas = vol_arena / VOLUMEN_LATA_M3
    arena_viajes = vol_arena / VOLUMEN_VIAJE_M3

    grava_latas = vol_grava / VOLUMEN_LATA_M3
    grava_viajes = vol_grava / VOLUMEN_VIAJE_M3

    # Agua aproximada basada en relación agua/cemento w/c ~ 0.55
    agua_litros = cemento_kg * 0.55
    agua_latas = agua_litros / (VOLUMEN_LATA_M3 * 1000.0)

    prop_str = f"{p_cem:g}:{p_are:g}:{p_gra:g}"

    return ResultadoConcreto(
        volumen_diseno_m3=round(vol_base, 4),
        desperdicio_pct=round(desperdicio_pct, 1),
        volumen_total_m3=round(vol_total, 4),
        proporcion_str=prop_str,
        cemento_kg=round(cemento_kg, 2),
        bultos_50kg=round(bultos_50, 2),
        bultos_42_5kg=round(bultos_42_5, 2),
        cemento_latas=round(cemento_latas, 2),
        arena_m3=round(vol_arena, 4),
        arena_latas=round(arena_latas, 2),
        arena_viajes_6m3=round(arena_viajes, 2),
        grava_m3=round(vol_grava, 4),
        grava_latas=round(grava_latas, 2),
        grava_viajes_6m3=round(grava_viajes, 2),
        agua_litros=round(agua_litros, 1),
        agua_latas=round(agua_latas, 2)
    )


# =============================================================================
# CÁLCULO DE MEZCLA DE MORTERO
# =============================================================================
@dataclass
class ResultadoMortero:
    volumen_diseno_m3: float
    desperdicio_pct: float
    volumen_total_m3: float
    proporcion_str: str
    cemento_kg: float
    bultos_50kg: float
    bultos_42_5kg: float
    cemento_latas: float
    arena_m3: float
    arena_latas: float
    arena_viajes_6m3: float
    agua_litros: float
    agua_latas: float

    def generar_reporte_texto(self, titulo: str = "Cálculo de Mortero") -> str:
        lineas = [
            "=" * 68,
            f"  🏗️ REPORTE DE CANTIDADES DE MORTERO - {titulo.upper()}",
            "=" * 68,
            f"• Volumen de Diseño:      {self.volumen_diseno_m3:.3f} m³",
            f"• Desperdicio Considerado: {self.desperdicio_pct:.1f}%",
            f"• Volumen Total a Mezclar: {self.volumen_total_m3:.3f} m³",
            f"• Proporción C:A:          {self.proporcion_str}",
            "-" * 68,
            f"{'MATERIAL':<22} | {'CANTIDAD PRINCIPAL':<20} | {'EQUIVALENCIA PRÁCTICA'}",
            "-" * 68,
            f"{'Cemento Portland':<22} | {self.cemento_kg:<12.1f} kg     | {self.bultos_50kg:<5.1f} bultos (50 kg) / {self.cemento_latas:<5.1f} latas",
            f"{'':<22} | {'':<20} | ({self.bultos_42_5kg:.1f} bultos de 42.5 kg)",
            f"{'Arena Fina/Media':<22} | {self.arena_m3:<12.3f} m³     | {self.arena_latas:<5.1f} latas ({self.arena_viajes_6m3:.2f} viajes de 6m³)",
            f"{'Agua Estimada':<22} | {self.agua_litros:<12.1f} Litros | {self.agua_latas:<5.1f} latas (a/c aprox. 0.60)",
            "=" * 68,
        ]
        return "\n".join(lineas)


def calcular_mortero(volumen_m3: float,
                     proporcion: Tuple[float, float] = (1.0, 4.0),
                     desperdicio_pct: float = 5.0,
                     densidad_cemento_kg_m3: float = DENSIDAD_CEMENTO_KG_M3) -> ResultadoMortero:
    """
    Calcula los materiales requeridos para mortero de pañete, revoque o pega.
    """
    vol_base = max(0.0, float(volumen_m3))
    factor_desp = 1.0 + (max(0.0, float(desperdicio_pct)) / 100.0)
    vol_total = vol_base * factor_desp

    p_cem, p_are = proporcion
    suma = p_cem + p_are
    if suma <= 0:
        raise ValueError("La suma de las proporciones debe ser mayor a 0.")

    volumen_seco_total = vol_total * FACTOR_CONTRACCION_MORTERO
    vol_cemento = (p_cem / suma) * volumen_seco_total
    vol_arena = (p_are / suma) * volumen_seco_total

    cemento_kg = vol_cemento * densidad_cemento_kg_m3
    bultos_50 = cemento_kg / 50.0
    bultos_42_5 = cemento_kg / 42.5
    cemento_latas = (cemento_kg / densidad_cemento_kg_m3) / VOLUMEN_LATA_M3

    arena_latas = vol_arena / VOLUMEN_LATA_M3
    arena_viajes = vol_arena / VOLUMEN_VIAJE_M3

    # Relación a/c típica para mortero ~ 0.60
    agua_litros = cemento_kg * 0.60
    agua_latas = agua_litros / (VOLUMEN_LATA_M3 * 1000.0)

    prop_str = f"{p_cem:g}:{p_are:g}"

    return ResultadoMortero(
        volumen_diseno_m3=round(vol_base, 4),
        desperdicio_pct=round(desperdicio_pct, 1),
        volumen_total_m3=round(vol_total, 4),
        proporcion_str=prop_str,
        cemento_kg=round(cemento_kg, 2),
        bultos_50kg=round(bultos_50, 2),
        bultos_42_5kg=round(bultos_42_5, 2),
        cemento_latas=round(cemento_latas, 2),
        arena_m3=round(vol_arena, 4),
        arena_latas=round(arena_latas, 2),
        arena_viajes_6m3=round(arena_viajes, 2),
        agua_litros=round(agua_litros, 1),
        agua_latas=round(agua_latas, 2)
    )


# =============================================================================
# CÁLCULO DE ACERO DE REFUERZO COMERCIAL
# =============================================================================
def calcular_acero_refuerzo(numero_varilla: int,
                            longitud_total_m: float,
                            longitud_varilla_comercial_m: float = 6.0) -> Dict[str, Any]:
    """
    Calcula peso total y número de varillas comerciales para una barra estándar dada.
    """
    if numero_varilla not in TABLA_VARILLAS_ACERO:
        raise ValueError(f"Varilla #{numero_varilla} no válida. Use varillas del #2 al #11.")

    info = TABLA_VARILLAS_ACERO[numero_varilla]
    masa_metro = info["masa_kg_m"]
    peso_total_kg = longitud_total_m * masa_metro
    numero_barras_comerciales = math.ceil(longitud_total_m / longitud_varilla_comercial_m)

    return {
        "numero": numero_varilla,
        "pulgadas": info["pulgadas"],
        "diam_mm": info["diam_mm"],
        "area_cm2": info["area_cm2"],
        "masa_kg_m": masa_metro,
        "longitud_total_m": round(longitud_total_m, 2),
        "peso_total_kg": round(peso_total_kg, 2),
        "peso_total_ton": round(peso_total_kg / 1000.0, 3),
        "barras_comerciales_6m": numero_barras_comerciales,
        "barras_comerciales_12m": math.ceil(longitud_total_m / 12.0)
    }
