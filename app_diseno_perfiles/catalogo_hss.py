"""
hss_catalog.py
Catálogo de perfiles tubulares estructurales HSS (cuadrados SHS y rectangulares RHS)
según normas AISC 360 / ASTM A500 Grado B/C y ASTM A1085.

Sincronizado con la hoja técnica:
'Propiedades Geometricas Perfiles HSS (AISC - Estructuras Metalicas).ods'

Contiene propiedades geométricas en sistema Imperial y Métrico (SI),
así como funciones de consulta, carga dinámica desde archivo ODS y filtrado.
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from dataclasses import dataclass
from typing import Dict, List, Optional


@dataclass
class HSSProfile:
    name: str             # e.g. "HSS6x6x3/16" o "HSS10x6x3/16"
    H: float              # Altura exterior total (in)
    B: float              # Ancho exterior total (in)
    t_nom: float          # Espesor nominal (in)
    t_des: float          # Espesor de diseño (in) = 0.93*t_nom para A500, 1.0*t_nom para A1085
    weight_lb_ft: float   # Peso nominal (lb/ft)
    A_in2: float          # Área de la sección bruta (in^2)
    Ix_in4: float         # Momento de inercia eje fuerte (in^4)
    Sx_in3: float         # Módulo elástico de sección eje fuerte (in^3)
    Zx_in3: float         # Módulo plástico de sección eje fuerte (in^3)
    rx_in: float          # Radio de giro eje fuerte (in)
    Iy_in4: float         # Momento de inercia eje débil (in^4)
    Sy_in3: float         # Módulo elástico de sección eje débil (in^3)
    Zy_in3: float         # Módulo plástico de sección eje débil (in^3)
    ry_in: float          # Radio de giro eje débil (in)
    J_in4: float          # Constante torsional de St. Venant (in^4)
    C_in3: float          # Módulo torsional de sección (in^3)
    b_t: float            # Relación ancho/espesor patín comprimido (b/t)
    h_t: float            # Relación altura/espesor alma comprimida (h/t)
    shape_type: str = "HSS" # "SHS" (cuadrado) o "RHS" (rectangular)
    
    # Propiedades calculadas en sistema métrico (SI)
    @property
    def H_mm(self) -> float:
        return self.H * 25.4

    @property
    def B_mm(self) -> float:
        return self.B * 25.4

    @property
    def t_mm(self) -> float:
        return self.t_nom * 25.4

    @property
    def t_des_mm(self) -> float:
        return self.t_des * 25.4

    @property
    def weight_kg_m(self) -> float:
        return self.weight_lb_ft * 1.48816

    @property
    def A_cm2(self) -> float:
        return self.A_in2 * 6.4516

    @property
    def Ix_cm4(self) -> float:
        return self.Ix_in4 * 41.6231

    @property
    def Sx_cm3(self) -> float:
        return self.Sx_in3 * 16.3871

    @property
    def Zx_cm3(self) -> float:
        return self.Zx_in3 * 16.3871

    @property
    def rx_cm(self) -> float:
        return self.rx_in * 2.54

    @property
    def Iy_cm4(self) -> float:
        return self.Iy_in4 * 41.6231

    @property
    def Sy_cm3(self) -> float:
        return self.Sy_in3 * 16.3871

    @property
    def Zy_cm3(self) -> float:
        return self.Zy_in3 * 16.3871

    @property
    def ry_cm(self) -> float:
        return self.ry_in * 2.54

    @property
    def J_cm4(self) -> float:
        return self.J_in4 * 41.6231

    @property
    def is_square(self) -> bool:
        return abs(self.H - self.B) < 0.05

    @property
    def shape_type_label(self) -> str:
        return "Cuadrado (SHS)" if self.is_square else "Rectangular (RHS)"

    @property
    def dimensions_str(self) -> str:
        return f"{self.H:.0f}x{self.B:.0f}" if (self.H.is_integer() and self.B.is_integer()) else f"{self.H}x{self.B}"


# =========================================================================
# BASE DE DATOS PRINCIPAL DE PERFILES HSS AISC 360-16 / ASTM A500
# Extraídos y validados con 'Propiedades Geometricas Perfiles HSS (AISC - Estructuras Metalicas).ods'
# =========================================================================
HSS_DATABASE: Dict[str, HSSProfile] = {
    "HSS4x4x1/8": HSSProfile(
        name="HSS4x4x1/8", H=4.0, B=4.0, t_nom=0.125, t_des=0.11625,
        weight_lb_ft=6.02, A_in2=1.77,
        Ix_in4=4.54, Sx_in3=2.27, Zx_in3=2.63, rx_in=1.60,
        Iy_in4=4.54, Sy_in3=2.27, Zy_in3=2.63, ry_in=1.60,
        J_in4=6.81, C_in3=3.51, b_t=31.4, h_t=31.4, shape_type="SHS"
    ),
    "HSS4x4x3/16": HSSProfile(
        name="HSS4x4x3/16", H=4.0, B=4.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=8.81, A_in2=2.59,
        Ix_in4=6.52, Sx_in3=3.26, Zx_in3=3.83, rx_in=1.59,
        Iy_in4=6.52, Sy_in3=3.26, Zy_in3=3.83, ry_in=1.59,
        J_in4=9.76, C_in3=5.1, b_t=19.9, h_t=19.9, shape_type="SHS"
    ),
    "HSS4x4x1/4": HSSProfile(
        name="HSS4x4x1/4", H=4.0, B=4.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=11.44, A_in2=3.36,
        Ix_in4=8.32, Sx_in3=4.16, Zx_in3=4.96, rx_in=1.57,
        Iy_in4=8.32, Sy_in3=4.16, Zy_in3=4.96, ry_in=1.57,
        J_in4=12.43, C_in3=6.6, b_t=14.2, h_t=14.2, shape_type="SHS"
    ),
    "HSS5x5x3/16": HSSProfile(
        name="HSS5x5x3/16", H=5.0, B=5.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=11.18, A_in2=3.29,
        Ix_in4=13.08, Sx_in3=5.23, Zx_in3=6.09, rx_in=1.99,
        Iy_in4=13.08, Sy_in3=5.23, Zy_in3=6.09, ry_in=1.99,
        J_in4=19.59, C_in3=8.12, b_t=25.7, h_t=25.7, shape_type="SHS"
    ),
    "HSS5x5x1/4": HSSProfile(
        name="HSS5x5x1/4", H=5.0, B=5.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=14.60, A_in2=4.29,
        Ix_in4=16.84, Sx_in3=6.73, Zx_in3=7.93, rx_in=1.98,
        Iy_in4=16.84, Sy_in3=6.73, Zy_in3=7.93, ry_in=1.98,
        J_in4=25.19, C_in3=10.57, b_t=18.5, h_t=18.5, shape_type="SHS"
    ),
    "HSS5x5x5/16": HSSProfile(
        name="HSS5x5x5/16", H=5.0, B=5.0, t_nom=0.3125, t_des=0.290625,
        weight_lb_ft=17.87, A_in2=5.26,
        Ix_in4=20.31, Sx_in3=8.13, Zx_in3=9.68, rx_in=1.97,
        Iy_in4=20.31, Sy_in3=8.13, Zy_in3=9.68, ry_in=1.97,
        J_in4=30.35, C_in3=12.89, b_t=14.2, h_t=14.2, shape_type="SHS"
    ),
    "HSS6x6x3/16": HSSProfile(
        name="HSS6x6x3/16", H=6.0, B=6.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=13.55, A_in2=3.99,
        Ix_in4=23.00, Sx_in3=7.67, Zx_in3=8.88, rx_in=2.40,
        Iy_in4=23.00, Sy_in3=7.67, Zy_in3=8.88, ry_in=2.40,
        J_in4=34.48, C_in3=11.84, b_t=31.4, h_t=31.4, shape_type="SHS"
    ),
    "HSS6x6x1/4": HSSProfile(
        name="HSS6x6x1/4", H=6.0, B=6.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=17.76, A_in2=5.22,
        Ix_in4=29.79, Sx_in3=9.93, Zx_in3=11.61, rx_in=2.39,
        Iy_in4=29.79, Sy_in3=9.93, Zy_in3=11.61, ry_in=2.39,
        J_in4=44.61, C_in3=15.47, b_t=22.8, h_t=22.8, shape_type="SHS"
    ),
    "HSS6x6x3/8": HSSProfile(
        name="HSS6x6x3/8", H=6.0, B=6.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=25.74, A_in2=7.57,
        Ix_in4=42.12, Sx_in3=14.04, Zx_in3=16.73, rx_in=2.36,
        Iy_in4=42.12, Sy_in3=14.04, Zy_in3=16.73, ry_in=2.36,
        J_in4=62.94, C_in3=22.28, b_t=14.2, h_t=14.2, shape_type="SHS"
    ),
    "HSS6x6x1/2": HSSProfile(
        name="HSS6x6x1/2", H=6.0, B=6.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=33.11, A_in2=9.74,
        Ix_in4=52.94, Sx_in3=17.65, Zx_in3=21.42, rx_in=2.33,
        Iy_in4=52.94, Sy_in3=17.65, Zy_in3=21.42, ry_in=2.33,
        J_in4=78.85, C_in3=28.49, b_t=9.9, h_t=9.9, shape_type="SHS"
    ),
    "HSS8x8x1/4": HSSProfile(
        name="HSS8x8x1/4", H=8.0, B=8.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=24.09, A_in2=7.08,
        Ix_in4=72.71, Sx_in3=18.18, Zx_in3=21.05, rx_in=3.20,
        Iy_in4=72.71, Sy_in3=18.18, Zy_in3=21.05, ry_in=3.20,
        J_in4=108.96, C_in3=28.06, b_t=31.4, h_t=31.4, shape_type="SHS"
    ),
    "HSS8x8x5/16": HSSProfile(
        name="HSS8x8x5/16", H=8.0, B=8.0, t_nom=0.3125, t_des=0.290625,
        weight_lb_ft=29.73, A_in2=8.74,
        Ix_in4=88.90, Sx_in3=22.23, Zx_in3=25.92, rx_in=3.19,
        Iy_in4=88.90, Sy_in3=22.23, Zy_in3=25.92, ry_in=3.19,
        J_in4=133.17, C_in3=34.55, b_t=24.5, h_t=24.5, shape_type="SHS"
    ),
    "HSS8x8x3/8": HSSProfile(
        name="HSS8x8x3/8", H=8.0, B=8.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=35.23, A_in2=10.36,
        Ix_in4=104.36, Sx_in3=26.09, Zx_in3=30.65, rx_in=3.17,
        Iy_in4=104.36, Sy_in3=26.09, Zy_in3=30.65, ry_in=3.17,
        J_in4=156.21, C_in3=40.83, b_t=19.9, h_t=19.9, shape_type="SHS"
    ),
    "HSS8x8x1/2": HSSProfile(
        name="HSS8x8x1/2", H=8.0, B=8.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=45.76, A_in2=13.46,
        Ix_in4=133.13, Sx_in3=33.28, Zx_in3=39.65, rx_in=3.15,
        Iy_in4=133.13, Sy_in3=33.28, Zy_in3=39.65, ry_in=3.15,
        J_in4=198.93, C_in3=52.8, b_t=14.2, h_t=14.2, shape_type="SHS"
    ),
    "HSS10x10x1/4": HSSProfile(
        name="HSS10x10x1/4", H=10.0, B=10.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=30.41, A_in2=8.94,
        Ix_in4=144.52, Sx_in3=28.90, Zx_in3=33.28, rx_in=4.02,
        Iy_in4=144.52, Sy_in3=28.90, Zy_in3=33.28, ry_in=4.02,
        J_in4=216.66, C_in3=44.36, b_t=40.0, h_t=40.0, shape_type="SHS"
    ),
    "HSS10x10x3/8": HSSProfile(
        name="HSS10x10x3/8", H=10.0, B=10.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=44.71, A_in2=13.15,
        Ix_in4=209.29, Sx_in3=41.86, Zx_in3=48.75, rx_in=3.99,
        Iy_in4=209.29, Sy_in3=41.86, Zy_in3=48.75, ry_in=3.99,
        J_in4=313.52, C_in3=64.97, b_t=25.7, h_t=25.7, shape_type="SHS"
    ),
    "HSS10x10x1/2": HSSProfile(
        name="HSS10x10x1/2", H=10.0, B=10.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=58.41, A_in2=17.18,
        Ix_in4=269.37, Sx_in3=53.87, Zx_in3=63.46, rx_in=3.96,
        Iy_in4=269.37, Sy_in3=53.87, Zy_in3=63.46, ry_in=3.96,
        J_in4=403.10, C_in3=84.55, b_t=18.5, h_t=18.5, shape_type="SHS"
    ),
    "HSS4x2x1/8": HSSProfile(
        name="HSS4x2x1/8", H=4.0, B=2.0, t_nom=0.125, t_des=0.11625,
        weight_lb_ft=4.44, A_in2=1.31,
        Ix_in4=2.79, Sx_in3=1.40, Zx_in3=1.73, rx_in=1.46,
        Iy_in4=0.93, Sy_in3=0.93, Zy_in3=1.06, ry_in=0.85,
        J_in4=2.16, C_in3=1.7, b_t=14.2, h_t=31.4, shape_type="RHS"
    ),
    "HSS4x2x3/16": HSSProfile(
        name="HSS4x2x3/16", H=4.0, B=2.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=6.43, A_in2=1.89,
        Ix_in4=3.97, Sx_in3=1.98, Zx_in3=2.50, rx_in=1.45,
        Iy_in4=1.30, Sy_in3=1.30, Zy_in3=1.51, ry_in=0.83,
        J_in4=3.01, C_in3=2.44, b_t=8.5, h_t=19.9, shape_type="RHS"
    ),
    "HSS4x2x1/4": HSSProfile(
        name="HSS4x2x1/4", H=4.0, B=2.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=8.28, A_in2=2.43,
        Ix_in4=5.02, Sx_in3=2.51, Zx_in3=3.20, rx_in=1.44,
        Iy_in4=1.60, Sy_in3=1.60, Zy_in3=1.92, ry_in=0.81,
        J_in4=3.73, C_in3=3.1, b_t=5.6, h_t=14.2, shape_type="RHS"
    ),
    "HSS6x2x1/8": HSSProfile(
        name="HSS6x2x1/8", H=6.0, B=2.0, t_nom=0.125, t_des=0.11625,
        weight_lb_ft=6.02, A_in2=1.77,
        Ix_in4=7.74, Sx_in3=2.58, Zx_in3=3.30, rx_in=2.09,
        Iy_in4=1.35, Sy_in3=1.35, Zy_in3=1.50, ry_in=0.87,
        J_in4=3.68, C_in3=2.58, b_t=14.2, h_t=48.6, shape_type="RHS"
    ),
    "HSS6x2x3/16": HSSProfile(
        name="HSS6x2x3/16", H=6.0, B=2.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=8.81, A_in2=2.59,
        Ix_in4=11.16, Sx_in3=3.72, Zx_in3=4.82, rx_in=2.08,
        Iy_in4=1.88, Sy_in3=1.88, Zy_in3=2.15, ry_in=0.85,
        J_in4=5.16, C_in3=3.71, b_t=8.5, h_t=31.4, shape_type="RHS"
    ),
    "HSS6x2x1/4": HSSProfile(
        name="HSS6x2x1/4", H=6.0, B=2.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=11.44, A_in2=3.36,
        Ix_in4=14.31, Sx_in3=4.77, Zx_in3=6.24, rx_in=2.06,
        Iy_in4=2.33, Sy_in3=2.33, Zy_in3=2.74, ry_in=0.83,
        J_in4=6.41, C_in3=4.74, b_t=5.6, h_t=22.8, shape_type="RHS"
    ),
    "HSS6x3x3/16": HSSProfile(
        name="HSS6x3x3/16", H=6.0, B=3.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=9.99, A_in2=2.94,
        Ix_in4=14.12, Sx_in3=4.71, Zx_in3=5.83, rx_in=2.19,
        Iy_in4=4.72, Sy_in3=3.15, Zy_in3=3.57, ry_in=1.27,
        J_in4=10.92, C_in3=5.74, b_t=14.2, h_t=31.4, shape_type="RHS"
    ),
    "HSS6x3x1/4": HSSProfile(
        name="HSS6x3x1/4", H=6.0, B=3.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=13.02, A_in2=3.83,
        Ix_in4=18.18, Sx_in3=6.06, Zx_in3=7.58, rx_in=2.18,
        Iy_in4=5.99, Sy_in3=3.99, Zy_in3=4.61, ry_in=1.25,
        J_in4=13.88, C_in3=7.42, b_t=9.9, h_t=22.8, shape_type="RHS"
    ),
    "HSS6x3x5/16": HSSProfile(
        name="HSS6x3x5/16", H=6.0, B=3.0, t_nom=0.3125, t_des=0.290625,
        weight_lb_ft=15.90, A_in2=4.68,
        Ix_in4=21.93, Sx_in3=7.31, Zx_in3=9.24, rx_in=2.17,
        Iy_in4=7.11, Sy_in3=4.74, Zy_in3=5.57, ry_in=1.23,
        J_in4=16.52, C_in3=8.99, b_t=7.3, h_t=17.6, shape_type="RHS"
    ),
    "HSS6x4x3/16": HSSProfile(
        name="HSS6x4x3/16", H=6.0, B=4.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=11.18, A_in2=3.29,
        Ix_in4=17.08, Sx_in3=5.69, Zx_in3=6.85, rx_in=2.28,
        Iy_in4=9.08, Sy_in3=4.54, Zy_in3=5.16, ry_in=1.66,
        J_in4=17.95, C_in3=7.77, b_t=19.9, h_t=31.4, shape_type="RHS"
    ),
    "HSS6x4x1/4": HSSProfile(
        name="HSS6x4x1/4", H=6.0, B=4.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=14.60, A_in2=4.29,
        Ix_in4=22.05, Sx_in3=7.35, Zx_in3=8.93, rx_in=2.27,
        Iy_in4=11.62, Sy_in3=5.81, Zy_in3=6.71, ry_in=1.65,
        J_in4=23.03, C_in3=10.1, b_t=14.2, h_t=22.8, shape_type="RHS"
    ),
    "HSS6x4x3/8": HSSProfile(
        name="HSS6x4x3/8", H=6.0, B=4.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=21.00, A_in2=6.18,
        Ix_in4=30.97, Sx_in3=10.32, Zx_in3=12.79, rx_in=2.24,
        Iy_in4=16.08, Sy_in3=8.04, Zy_in3=9.54, ry_in=1.61,
        J_in4=31.92, C_in3=14.39, b_t=8.5, h_t=14.2, shape_type="RHS"
    ),
    "HSS8x4x3/16": HSSProfile(
        name="HSS8x4x3/16", H=8.0, B=4.0, t_nom=0.1875, t_des=0.174375,
        weight_lb_ft=13.55, A_in2=3.99,
        Ix_in4=34.38, Sx_in3=8.59, Zx_in3=10.56, rx_in=2.94,
        Iy_in4=11.63, Sy_in3=5.81, Zy_in3=6.50, ry_in=1.71,
        J_in4=26.83, C_in3=10.44, b_t=19.9, h_t=42.9, shape_type="RHS"
    ),
    "HSS8x4x1/4": HSSProfile(
        name="HSS8x4x1/4", H=8.0, B=4.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=17.76, A_in2=5.22,
        Ix_in4=44.64, Sx_in3=11.16, Zx_in3=13.82, rx_in=2.92,
        Iy_in4=14.93, Sy_in3=7.46, Zy_in3=8.46, ry_in=1.69,
        J_in4=34.52, C_in3=13.61, b_t=14.2, h_t=31.4, shape_type="RHS"
    ),
    "HSS8x4x3/8": HSSProfile(
        name="HSS8x4x3/8", H=8.0, B=4.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=25.74, A_in2=7.57,
        Ix_in4=63.50, Sx_in3=15.87, Zx_in3=19.97, rx_in=2.90,
        Iy_in4=20.75, Sy_in3=10.37, Zy_in3=12.09, ry_in=1.66,
        J_in4=48.16, C_in3=19.49, b_t=8.5, h_t=19.9, shape_type="RHS"
    ),
    "HSS8x4x1/2": HSSProfile(
        name="HSS8x4x1/2", H=8.0, B=4.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=33.11, A_in2=9.74,
        Ix_in4=80.26, Sx_in3=20.06, Zx_in3=25.64, rx_in=2.87,
        Iy_in4=25.62, Sy_in3=12.81, Zy_in3=15.34, ry_in=1.62,
        J_in4=59.60, C_in3=24.77, b_t=5.6, h_t=14.2, shape_type="RHS"
    ),
    "HSS8x6x1/4": HSSProfile(
        name="HSS8x6x1/4", H=8.0, B=6.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=20.93, A_in2=6.15,
        Ix_in4=58.67, Sx_in3=14.67, Zx_in3=17.44, rx_in=3.09,
        Iy_in4=37.52, Sy_in3=12.51, Zy_in3=14.29, ry_in=2.47,
        J_in4=68.95, C_in3=20.83, b_t=22.8, h_t=31.4, shape_type="RHS"
    ),
    "HSS8x6x3/8": HSSProfile(
        name="HSS8x6x3/8", H=8.0, B=6.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=30.48, A_in2=8.97,
        Ix_in4=83.93, Sx_in3=20.98, Zx_in3=25.31, rx_in=3.06,
        Iy_in4=53.27, Sy_in3=17.76, Zy_in3=20.67, ry_in=2.44,
        J_in4=98.03, C_in3=30.16, b_t=14.2, h_t=19.9, shape_type="RHS"
    ),
    "HSS8x6x1/2": HSSProfile(
        name="HSS8x6x1/2", H=8.0, B=6.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=39.43, A_in2=11.60,
        Ix_in4=106.69, Sx_in3=26.67, Zx_in3=32.64, rx_in=3.03,
        Iy_in4=67.22, Sy_in3=22.41, Zy_in3=26.57, ry_in=2.41,
        J_in4=123.77, C_in3=38.79, b_t=9.9, h_t=14.2, shape_type="RHS"
    ),
    "HSS10x4x1/4": HSSProfile(
        name="HSS10x4x1/4", H=10.0, B=4.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=20.93, A_in2=6.15,
        Ix_in4=77.96, Sx_in3=15.59, Zx_in3=19.65, rx_in=3.56,
        Iy_in4=18.23, Sy_in3=9.12, Zy_in3=10.21, ry_in=1.72,
        J_in4=46.52, C_in3=17.11, b_t=14.2, h_t=40.0, shape_type="RHS"
    ),
    "HSS10x4x3/8": HSSProfile(
        name="HSS10x4x3/8", H=10.0, B=4.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=30.48, A_in2=8.97,
        Ix_in4=111.79, Sx_in3=22.36, Zx_in3=28.55, rx_in=3.53,
        Iy_in4=25.41, Sy_in3=12.71, Zy_in3=14.64, ry_in=1.68,
        J_in4=65.11, C_in3=24.58, b_t=8.5, h_t=25.7, shape_type="RHS"
    ),
    "HSS10x4x1/2": HSSProfile(
        name="HSS10x4x1/2", H=10.0, B=4.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=39.43, A_in2=11.60,
        Ix_in4=142.45, Sx_in3=28.49, Zx_in3=36.86, rx_in=3.50,
        Iy_in4=31.46, Sy_in3=15.73, Zy_in3=18.63, ry_in=1.65,
        J_in4=80.84, C_in3=31.35, b_t=5.6, h_t=18.5, shape_type="RHS"
    ),
    "HSS10x6x1/4": HSSProfile(
        name="HSS10x6x1/4", H=10.0, B=6.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=24.09, A_in2=7.08,
        Ix_in4=100.15, Sx_in3=20.03, Zx_in3=24.19, rx_in=3.76,
        Iy_in4=45.26, Sy_in3=15.09, Zy_in3=16.97, ry_in=2.53,
        J_in4=94.99, C_in3=26.2, b_t=22.8, h_t=40.0, shape_type="RHS"
    ),
    "HSS10x6x3/8": HSSProfile(
        name="HSS10x6x3/8", H=10.0, B=6.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=35.23, A_in2=10.36,
        Ix_in4=144.29, Sx_in3=28.86, Zx_in3=35.29, rx_in=3.73,
        Iy_in4=64.43, Sy_in3=21.48, Zy_in3=24.61, ry_in=2.49,
        J_in4=135.59, C_in3=38.04, b_t=14.2, h_t=25.7, shape_type="RHS"
    ),
    "HSS10x6x1/2": HSSProfile(
        name="HSS10x6x1/2", H=10.0, B=6.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=45.76, A_in2=13.46,
        Ix_in4=184.75, Sx_in3=36.95, Zx_in3=45.73, rx_in=3.71,
        Iy_in4=81.50, Sy_in3=27.17, Zy_in3=31.71, ry_in=2.46,
        J_in4=171.89, C_in3=49.08, b_t=9.9, h_t=18.5, shape_type="RHS"
    ),
    "HSS12x6x1/4": HSSProfile(
        name="HSS12x6x1/4", H=12.0, B=6.0, t_nom=0.25, t_des=0.2325,
        weight_lb_ft=27.25, A_in2=8.01,
        Ix_in4=156.07, Sx_in3=26.01, Zx_in3=31.88, rx_in=4.41,
        Iy_in4=53.00, Sy_in3=17.67, Zy_in3=19.65, ry_in=2.57,
        J_in4=122.15, C_in3=31.56, b_t=22.8, h_t=48.6, shape_type="RHS"
    ),
    "HSS12x6x3/8": HSSProfile(
        name="HSS12x6x3/8", H=12.0, B=6.0, t_nom=0.375, t_des=0.34875,
        weight_lb_ft=39.97, A_in2=11.76,
        Ix_in4=226.00, Sx_in3=37.67, Zx_in3=46.66, rx_in=4.38,
        Iy_in4=75.58, Sy_in3=25.19, Zy_in3=28.55, ry_in=2.54,
        J_in4=174.77, C_in3=45.93, b_t=14.2, h_t=31.4, shape_type="RHS"
    ),
    "HSS12x6x1/2": HSSProfile(
        name="HSS12x6x1/2", H=12.0, B=6.0, t_nom=0.5, t_des=0.465,
        weight_lb_ft=52.08, A_in2=15.32,
        Ix_in4=290.85, Sx_in3=48.47, Zx_in3=60.67, rx_in=4.36,
        Iy_in4=95.78, Sy_in3=31.93, Zy_in3=36.86, ry_in=2.50,
        J_in4=222.09, C_in3=59.38, b_t=9.9, h_t=22.8, shape_type="RHS"
    ),
    # Perfiles estándar adicionales (AISC 15th Ed.)
    "HSS2x2x1/8": HSSProfile(
        name="HSS2x2x1/8", H=2.0, B=2.0, t_nom=0.125, t_des=0.116,
        weight_lb_ft=3.05, A_in2=0.897,
        Ix_in4=0.514, Sx_in3=0.514, Zx_in3=0.612, rx_in=0.757,
        Iy_in4=0.514, Sy_in3=0.514, Zy_in3=0.612, ry_in=0.757,
        J_in4=0.840, C_in3=0.735, b_t=14.2, h_t=14.2, shape_type="SHS"
    ),
    "HSS2x2x3/16": HSSProfile(
        name="HSS2x2x3/16", H=2.0, B=2.0, t_nom=0.1875, t_des=0.174,
        weight_lb_ft=4.32, A_in2=1.27,
        Ix_in4=0.675, Sx_in3=0.675, Zx_in3=0.835, rx_in=0.729,
        Iy_in4=0.675, Sy_in3=0.675, Zy_in3=0.835, ry_in=0.729,
        J_in4=1.14, C_in3=0.983, b_t=8.5, h_t=8.5, shape_type="SHS"
    ),
    "HSS3x3x1/8": HSSProfile(
        name="HSS3x3x1/8", H=3.0, B=3.0, t_nom=0.125, t_des=0.116,
        weight_lb_ft=4.75, A_in2=1.40,
        Ix_in4=1.87, Sx_in3=1.25, Zx_in3=1.47, rx_in=1.16,
        Iy_in4=1.87, Sy_in3=1.25, Zy_in3=1.47, ry_in=1.16,
        J_in4=3.01, C_in3=1.84, b_t=22.8, h_t=22.8, shape_type="SHS"
    ),
    "HSS3x3x3/16": HSSProfile(
        name="HSS3x3x3/16", H=3.0, B=3.0, t_nom=0.1875, t_des=0.174,
        weight_lb_ft=6.87, A_in2=2.02,
        Ix_in4=2.56, Sx_in3=1.71, Zx_in3=2.06, rx_in=1.13,
        Iy_in4=2.56, Sy_in3=1.71, Zy_in3=2.06, ry_in=1.13,
        J_in4=4.22, C_in3=2.54, b_t=14.2, h_t=14.2, shape_type="SHS"
    ),
    "HSS3x3x1/4": HSSProfile(
        name="HSS3x3x1/4", H=3.0, B=3.0, t_nom=0.250, t_des=0.233,
        weight_lb_ft=8.81, A_in2=2.59,
        Ix_in4=3.10, Sx_in3=2.07, Zx_in3=2.56, rx_in=1.09,
        Iy_in4=3.10, Sy_in3=2.07, Zy_in3=2.56, ry_in=1.09,
        J_in4=5.23, C_in3=3.10, b_t=9.9, h_t=9.9, shape_type="SHS"
    ),
    "HSS5x3x3/16": HSSProfile(
        name="HSS5x3x3/16", H=5.0, B=3.0, t_nom=0.1875, t_des=0.174,
        weight_lb_ft=9.42, A_in2=2.78,
        Ix_in4=9.46, Sx_in3=3.78, Zx_in3=4.67, rx_in=1.85,
        Iy_in4=4.34, Sy_in3=2.89, Zy_in3=3.35, ry_in=1.25,
        J_in4=9.83, C_in3=4.51, b_t=14.2, h_t=25.7, shape_type="RHS"
    ),
    "HSS6x6x5/16": HSSProfile(
        name="HSS6x6x5/16", H=6.0, B=6.0, t_nom=0.3125, t_des=0.291,
        weight_lb_ft=23.34, A_in2=6.86,
        Ix_in4=36.2, Sx_in3=12.1, Zx_in3=14.5, rx_in=2.30,
        Iy_in4=36.2, Sy_in3=12.1, Zy_in3=14.5, ry_in=2.30,
        J_in4=59.5, C_in3=17.6, b_t=17.6, h_t=17.6, shape_type="SHS"
    ),
    "HSS8x6x3/16": HSSProfile(
        name="HSS8x6x3/16", H=8.0, B=6.0, t_nom=0.1875, t_des=0.174,
        weight_lb_ft=17.08, A_in2=5.03,
        Ix_in4=48.2, Sx_in3=12.0, Zx_in3=14.7, rx_in=3.10,
        Iy_in4=30.6, Sy_in3=10.2, Zy_in3=11.9, ry_in=2.47,
        J_in4=56.2, C_in3=15.6, b_t=31.5, h_t=43.0, shape_type="RHS"
    ),
    "HSS10x6x3/16": HSSProfile(
        name="HSS10x6x3/16", H=10.0, B=6.0, t_nom=0.1875, t_des=0.174,
        weight_lb_ft=19.63, A_in2=5.78,
        Ix_in4=80.0, Sx_in3=16.0, Zx_in3=19.3, rx_in=3.72,
        Iy_in4=36.5, Sy_in3=12.2, Zy_in3=13.6, ry_in=2.51,
        J_in4=79.3, C_in3=20.1, b_t=31.5, h_t=54.5, shape_type="RHS"
    ),
    "HSS10x6x5/16": HSSProfile(
        name="HSS10x6x5/16", H=10.0, B=6.0, t_nom=0.3125, t_des=0.291,
        weight_lb_ft=31.84, A_in2=9.36,
        Ix_in4=127.0, Sx_in3=25.4, Zx_in3=31.4, rx_in=3.68,
        Iy_in4=57.5, Sy_in3=19.2, Zy_in3=22.6, ry_in=2.48,
        J_in4=126.0, C_in3=31.1, b_t=17.6, h_t=31.3, shape_type="RHS"
    ),
    "HSS12x8x5/16": HSSProfile(
        name="HSS12x8x5/16", H=12.0, B=8.0, t_nom=0.3125, t_des=0.291,
        weight_lb_ft=40.35, A_in2=11.9,
        Ix_in4=254.0, Sx_in3=42.3, Zx_in3=51.5, rx_in=4.63,
        Iy_in4=136.0, Sy_in3=34.0, Zy_in3=39.5, ry_in=3.39,
        J_in4=269.0, C_in3=50.1, b_t=24.5, h_t=38.3, shape_type="RHS"
    ),
}


def parse_ods_hss(ods_path: str) -> Dict[str, HSSProfile]:
    """
    Lector nativo ultra-rápido (<0.05s) para archivos .ods de LibreOffice/OpenOffice
    sin requerir dependencias externas pesadas. Lee las hojas 'HSS Cuadrados (SHS)'
    y 'HSS Rectangulares (RHS)'.
    """
    if not os.path.exists(ods_path):
        raise FileNotFoundError(f"No se encontró el archivo: {ods_path}")

    with zipfile.ZipFile(ods_path) as z:
        root = ET.fromstring(z.read('content.xml'))

    ns = {
        'table': 'urn:oasis:names:tc:opendocument:xmlns:table:1.0',
        'text': 'urn:oasis:names:tc:opendocument:xmlns:text:1.0',
        'office': 'urn:oasis:names:tc:opendocument:xmlns:office:1.0'
    }

    sheets = {}
    for table in root.iter(f'{{urn:oasis:names:tc:opendocument:xmlns:table:1.0}}table'):
        sheet_name = table.attrib.get(f'{{urn:oasis:names:tc:opendocument:xmlns:table:1.0}}name')
        rows_data = []
        for row in table.iter(f'{{urn:oasis:names:tc:opendocument:xmlns:table:1.0}}table-row'):
            row_vals = []
            for cell in row.iter(f'{{urn:oasis:names:tc:opendocument:xmlns:table:1.0}}table-cell'):
                repeat = int(cell.attrib.get(f'{{urn:oasis:names:tc:opendocument:xmlns:table:1.0}}number-columns-repeated', 1))
                val_type = cell.attrib.get(f'{{urn:oasis:names:tc:opendocument:xmlns:office:1.0}}value-type')
                if val_type in ('float', 'currency', 'percentage'):
                    val = float(cell.attrib.get(f'{{urn:oasis:names:tc:opendocument:xmlns:office:1.0}}value', 0.0))
                else:
                    texts = [t.text for t in cell.iter(f'{{urn:oasis:names:tc:opendocument:xmlns:text:1.0}}p') if t.text]
                    val = ' '.join(texts).strip() if texts else None
                for _ in range(repeat):
                    row_vals.append(val)
            while row_vals and row_vals[-1] is None:
                row_vals.pop()
            if row_vals:
                rows_data.append(row_vals)
        if rows_data:
            sheets[sheet_name] = rows_data

    profiles: Dict[str, HSSProfile] = {}

    # 1. HSS Cuadrados (SHS)
    if 'HSS Cuadrados (SHS)' in sheets:
        rows = sheets['HSS Cuadrados (SHS)']
        header = rows[0]
        col_idx = {h: i for i, h in enumerate(header)}
        for r in rows[1:]:
            if len(r) < len(header):
                continue
            name_raw = str(r[col_idx['Designación']]).strip()
            norm_name = name_raw.replace(' ', '')
            dims = str(r[col_idx['Dimensiones BxH [in]']]).strip().split('x')
            B = float(dims[0])
            H = float(dims[1])
            t_nom = float(r[col_idx['Espesor t_nom [in]']])
            t_des = float(r[col_idx['Espesor t_des [in]']])
            w_lb = float(r[col_idx['Peso lineal [lb/ft]']])
            Ag_cm2 = float(r[col_idx['Área Ag [cm²]']])
            Ix_cm4 = float(r[col_idx['Inercia Ix=Iy [cm⁴]']])
            Sx_cm3 = float(r[col_idx['Módulo elástico Sx=Sy [cm³]']])
            Zx_cm3 = float(r[col_idx['Módulo plástico Zx=Zy [cm³]']])
            rx_cm = float(r[col_idx['Radio de giro rx=ry [cm]']])
            J_cm4 = float(r[col_idx['Constante torsional J [cm⁴]']])

            A_in2 = Ag_cm2 / 6.4516
            Ix_in4 = Ix_cm4 / 41.6231
            Sx_in3 = Sx_cm3 / 16.3871
            Zx_in3 = Zx_cm3 / 16.3871
            rx_in = rx_cm / 2.54
            Iy_in4 = Ix_in4
            Sy_in3 = Sx_in3
            Zy_in3 = Zx_in3
            ry_in = rx_in
            J_in4 = J_cm4 / 41.6231
            b_t = round((B - 3 * t_des) / t_des, 1)
            h_t = round((H - 3 * t_des) / t_des, 1)
            C_in3 = round(2.0 * (B - t_des) * (H - t_des) * t_des, 2)

            profiles[norm_name] = HSSProfile(
                name=norm_name, H=H, B=B, t_nom=t_nom, t_des=t_des,
                weight_lb_ft=w_lb, A_in2=A_in2,
                Ix_in4=Ix_in4, Sx_in3=Sx_in3, Zx_in3=Zx_in3, rx_in=rx_in,
                Iy_in4=Iy_in4, Sy_in3=Sy_in3, Zy_in3=Zy_in3, ry_in=ry_in,
                J_in4=J_in4, C_in3=C_in3, b_t=b_t, h_t=h_t, shape_type="SHS"
            )

    # 2. HSS Rectangulares (RHS)
    if 'HSS Rectangulares (RHS)' in sheets:
        rows = sheets['HSS Rectangulares (RHS)']
        header = rows[0]
        col_idx = {h: i for i, h in enumerate(header)}
        for r in rows[1:]:
            if len(r) < len(header):
                continue
            name_raw = str(r[col_idx['Designación']]).strip()
            norm_name = name_raw.replace(' ', '')
            dims = str(r[col_idx['Dimensiones HxB [in]']]).strip().split('x')
            H = float(dims[0])
            B = float(dims[1])
            t_nom = float(r[col_idx['Espesor t_nom [in]']])
            t_des = float(r[col_idx['Espesor t_des [in]']])
            w_lb = float(r[col_idx['Peso lineal [lb/ft]']])
            Ag_cm2 = float(r[col_idx['Área Ag [cm²]']])
            Ix_cm4 = float(r[col_idx['Inercia Ix [cm⁴]']])
            Sx_cm3 = float(r[col_idx['Módulo Sx [cm³]']])
            Zx_cm3 = float(r[col_idx['Módulo Zx [cm³]']])
            rx_cm = float(r[col_idx['Radio rx [cm]']])
            Iy_cm4 = float(r[col_idx['Inercia Iy [cm⁴]']])
            Sy_cm3 = float(r[col_idx['Módulo Sy [cm³]']])
            Zy_cm3 = float(r[col_idx['Módulo Zy [cm³]']])
            ry_cm = float(r[col_idx['Radio ry [cm]']])
            J_cm4 = float(r[col_idx['Constante torsional J [cm⁴]']])

            A_in2 = Ag_cm2 / 6.4516
            Ix_in4 = Ix_cm4 / 41.6231
            Sx_in3 = Sx_cm3 / 16.3871
            Zx_in3 = Zx_cm3 / 16.3871
            rx_in = rx_cm / 2.54
            Iy_in4 = Iy_cm4 / 41.6231
            Sy_in3 = Sy_cm3 / 16.3871
            Zy_in3 = Zy_cm3 / 16.3871
            ry_in = ry_cm / 2.54
            J_in4 = J_cm4 / 41.6231
            b_t = round((B - 3 * t_des) / t_des, 1)
            h_t = round((H - 3 * t_des) / t_des, 1)
            C_in3 = round(2.0 * (B - t_des) * (H - t_des) * t_des, 2)

            profiles[norm_name] = HSSProfile(
                name=norm_name, H=H, B=B, t_nom=t_nom, t_des=t_des,
                weight_lb_ft=w_lb, A_in2=A_in2,
                Ix_in4=Ix_in4, Sx_in3=Sx_in3, Zx_in3=Zx_in3, rx_in=rx_in,
                Iy_in4=Iy_in4, Sy_in3=Sy_in3, Zy_in3=Zy_in3, ry_in=ry_in,
                J_in4=J_in4, C_in3=C_in3, b_t=b_t, h_t=h_t, shape_type="RHS"
            )

    return profiles


def load_profiles_from_ods(ods_path: Optional[str] = None) -> int:
    """
    Carga o sincroniza los perfiles HSS desde el archivo .ods en HSS_DATABASE.
    Retorna el número de perfiles cargados.
    """
    global HSS_DATABASE
    if ods_path is None:
        candidatos = [
            "Propiedades Geometricas Perfiles HSS (AISC - Estructuras Metalicas).ods",
            os.path.join(os.path.dirname(os.path.abspath(__file__)), "Propiedades Geometricas Perfiles HSS (AISC - Estructuras Metalicas).ods")
        ]
        for c in candidatos:
            if os.path.exists(c):
                ods_path = c
                break

    if not ods_path or not os.path.exists(ods_path):
        return 0

    profs = parse_ods_hss(ods_path)
    for k, v in profs.items():
        HSS_DATABASE[k] = v
    return len(profs)


def get_profile(name: str) -> Optional[HSSProfile]:
    """
    Obtiene un perfil por su nombre estándar (e.g. 'HSS6x6x3/16', 'HSS 6x6x3/16', '6x6x3/16').
    Búsqueda robusta insensible a mayúsculas, espacios y prefijos.
    """
    if not name:
        return None
    cleaned = str(name).replace("A1085-", "").replace("A500-", "").replace("ASTM-", "").strip()
    cleaned = re.sub(r"(\d+)-(\d+)", r"\1/\2", cleaned)
    cleaned = cleaned.replace(" ", "")
    if not cleaned.upper().startswith("HSS"):
        cleaned = "HSS" + cleaned

    # 1. Búsqueda directa
    for k, v in HSS_DATABASE.items():
        if k.upper() == cleaned.upper():
            return v

    # 2. Búsqueda normalizada
    norm_target = re.sub(r'[^A-Z0-9]', '', cleaned.upper())
    for k, v in HSS_DATABASE.items():
        norm_k = re.sub(r'[^A-Z0-9]', '', k.upper())
        if norm_k == norm_target:
            return v
    return None


def list_all_profiles(sort_by_weight: bool = True) -> List[HSSProfile]:
    """Retorna la lista de todos los perfiles disponibles en el catálogo."""
    profiles = list(HSS_DATABASE.values())
    if sort_by_weight:
        profiles.sort(key=lambda p: p.weight_lb_ft)
    return profiles


def list_square_profiles(sort_by_weight: bool = True) -> List[HSSProfile]:
    """Retorna la lista de perfiles cuadrados (SHS)."""
    profs = [p for p in HSS_DATABASE.values() if p.is_square]
    if sort_by_weight:
        profs.sort(key=lambda p: p.weight_lb_ft)
    return profs


def list_rectangular_profiles(sort_by_weight: bool = True) -> List[HSSProfile]:
    """Retorna la lista de perfiles rectangulares (RHS)."""
    profs = [p for p in HSS_DATABASE.values() if not p.is_square]
    if sort_by_weight:
        profs.sort(key=lambda p: p.weight_lb_ft)
    return profs


# Sincronización automática silenciosa al importar si el archivo ODS existe
_default_ods = os.path.join(os.path.dirname(os.path.abspath(__file__)), "Propiedades Geometricas Perfiles HSS (AISC - Estructuras Metalicas).ods")
if os.path.exists(_default_ods):
    try:
        load_profiles_from_ods(_default_ods)
    except Exception:
        pass
