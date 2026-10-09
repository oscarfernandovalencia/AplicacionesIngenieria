#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
motor_analisis.py
===============================================================================
Motor de Análisis Estructural 3D por Elementos Finitos (PyNite FEA)
Específico para Vivienda de Dos Niveles en Terreno Inclinado / Ladera:
- Nivel 1: Nivelación del terreno (columnas de longitud variable entre z=0m y z=-8.08m).
- Nivel 2: Nivel habitable (columnas de altura constante y entrepiso/cubierta).

Normativas incorporadas:
- NSR-10 Título A: Sismo por Fuerza Horizontal Equivalente.
- NSR-10 Título B: Viento con presión de barlovento y sotavento.
- AISC 360-16 / NSR-10 B.2.4: Combinaciones LRFD completas y Envolvente Crítica (ENV).
===============================================================================
"""

import os
import math
from typing import Dict, List, Tuple, Optional, Any
import pandas as pd
import numpy as np
from Pynite import FEModel3D

# Combinaciones LRFD estándar
DEFAULT_LOAD_COMBINATIONS: List[Tuple[str, Dict[str, float]]] = [
    ('1.4D', {'D': 1.4}),
    ('1.2D + 1.6L', {'D': 1.2, 'L': 1.6, 'Lr': 1.6}),
    ('1.2D + 1.6L + 0.5Lr', {'D': 1.2, 'L': 1.6, 'Lr': 0.5}),
    ('1.2D + 1.6Lr + 1.0L', {'D': 1.2, 'L': 1.0, 'Lr': 1.6}),
    ('1.2D + 1.6Lr + 0.8W', {'D': 1.2, 'Lr': 1.6, 'W': 0.8}),
    ('1.2D + 1.6Lr - 0.8W', {'D': 1.2, 'Lr': 1.6, 'W': -0.8}),
    ('1.2D + 1.6W + 1.0L + 0.5Lr', {'D': 1.2, 'L': 1.0, 'Lr': 0.5, 'W': 1.6}),
    ('1.2D - 1.6W + 1.0L + 0.5Lr', {'D': 1.2, 'L': 1.0, 'Lr': 0.5, 'W': -1.6}),
    ('0.9D + 1.6W', {'D': 0.9, 'W': 1.6}),
    ('0.9D - 1.6W', {'D': 0.9, 'W': -1.6}),
    ('1.2D + 1.0E + 1.0L', {'D': 1.2, 'L': 1.0, 'E': 1.0}),
    ('1.2D - 1.0E + 1.0L', {'D': 1.2, 'L': 1.0, 'E': -1.0}),
    ('0.9D + 1.0E', {'D': 0.9, 'E': 1.0}),
    ('0.9D - 1.0E', {'D': 0.9, 'E': -1.0}),
    ('PP (Servicio D)', {'D': 1.0}),
]


def cargar_datos_estructura(ruta_archivo: str) -> Dict[str, pd.DataFrame]:
    """Carga hojas de geometría, materiales, secciones y cargas desde un archivo ODS o Excel."""
    if not os.path.exists(ruta_archivo):
        raise FileNotFoundError(f"No se encontró el archivo de estructura: '{ruta_archivo}'")

    engine = "odf" if ruta_archivo.lower().endswith(".ods") else "openpyxl"
    excel = pd.ExcelFile(ruta_archivo, engine=engine)

    hojas_requeridas = ["Nodos", "Materiales", "Secciones", "Columnas", "Vigas"]
    datos = {}
    for h in hojas_requeridas:
        if h in excel.sheet_names:
            datos[h] = excel.parse(h)
        else:
            raise ValueError(f"Falta la hoja requerida '{h}' en '{ruta_archivo}'")

    for opcional in ["Losas", "Datos", "Cargas"]:
        if opcional in excel.sheet_names:
            datos[opcional] = excel.parse(opcional)
        else:
            datos[opcional] = pd.DataFrame()

    return datos


def extraer_parametros_proyecto(datos: Dict[str, pd.DataFrame]) -> Dict[str, Any]:
    """Extrae parámetros sísmicos, de viento y geométricos de la vivienda."""
    params = {
        "Aa": 0.15,
        "Av": 0.20,
        "Fa": 2.2,
        "Fv": 3.3,
        "I": 1.0,
        "R": 4.0,
        "N_pisos": 2,
        "Altura_piso": 3.0,
        "Ancho": 6.0,
        "Largo": 14.0,
        "Peso_Primer_Piso": 231.122,  # kN (~23.56 tonf)
        "Peso_Segundo_Piso": 367.720,  # kN (~37.49 tonf)
        "Viento": 0.40,               # kN/m² (NSR-10 B.6 mínima)
    }

    if "Datos" in datos and not datos["Datos"].empty:
        df_d = datos["Datos"]
        col_k = df_d.columns[0]
        col_v = df_d.columns[1] if len(df_d.columns) > 1 else df_d.columns[0]

        for _, row in df_d.iterrows():
            k = str(row[col_k]).strip().lower()
            try:
                val = float(row[col_v])
            except (ValueError, TypeError):
                continue

            if "aceleración" in k or "aa" in k: params["Aa"] = val
            elif "velocidad" in k or "av" in k: params["Av"] = val
            elif k == "fa": params["Fa"] = val
            elif k == "fv": params["Fv"] = val
            elif "coeficiente i" in k: params["I"] = val
            elif "altura" in k: params["Altura_piso"] = val
            elif "ancho" in k: params["Ancho"] = val
            elif "largo" in k: params["Largo"] = val

    return params


def calcular_parametros_sismicos(params: Dict[str, Any]) -> Dict[str, float]:
    """Calcula espectro y cortante basal sísmico según NSR-10 Título A."""
    Aa, Av = float(params.get("Aa", 0.15)), float(params.get("Av", 0.20))
    Fa, Fv = float(params.get("Fa", 2.2)), float(params.get("Fv", 3.3))
    I, R = float(params.get("I", 1.0)), float(params.get("R", 4.0))
    n_pisos = int(params.get("N_pisos", 2))
    periodo = 0.1 * n_pisos

    T0 = 0.1 * Av * Fv / (Aa * Fa) if (Aa * Fa) > 0 else 0.20
    Tc = 0.48 * Av * Fv / (Aa * Fa) if (Aa * Fa) > 0 else 0.96
    Tl = 2.4 * Fv

    if periodo <= T0:
        Sa_e = 2.5 * Aa * Fa * I * (0.4 + 0.6 * periodo / T0)
    elif periodo <= Tc:
        Sa_e = 2.5 * Aa * Fa * I
    elif periodo <= Tl:
        Sa_e = 1.2 * Av * Fv * I / periodo
    else:
        Sa_e = 1.2 * Av * Fv * Tl * I / (periodo ** 2)

    Sa = Sa_e / R if R > 0 else Sa_e
    p1 = float(params.get("Peso_Primer_Piso", 231.122))
    p2 = float(params.get("Peso_Segundo_Piso", 367.720))
    p_tot = p1 + p2

    Vs = Sa * p_tot
    h = float(params.get("Altura_piso", 3.0))
    k_exp = 1.0 if periodo <= 0.5 else min(2.0, 0.75 + 0.5 * periodo)
    den = p1 * (h ** k_exp) + p2 * ((2.0 * h) ** k_exp)

    f1 = (p1 * (h ** k_exp) / den) * Vs if den > 0 else Vs * 0.4
    f2 = (p2 * ((2.0 * h) ** k_exp) / den) * Vs if den > 0 else Vs * 0.6

    return {
        "Aa": Aa, "Av": Av, "Fa": Fa, "Fv": Fv, "I": I, "R": R,
        "T": periodo, "T0": T0, "Tc": Tc, "Tl": Tl,
        "Sa_elastica": Sa_e, "Sa": Sa, "Vs": Vs, "Fs": Sa_e * p_tot,
        "F_piso_1": f1, "F_piso_2": f2, "peso_total": p_tot
    }


def calcular_parametros_viento(params: Dict[str, Any]) -> Dict[str, float]:
    """Calcula cargas de viento según NSR-10 Título B."""
    q = float(params.get("Viento", 0.40))  # kN/m²
    ancho = float(params.get("Ancho", 6.0))
    largo = float(params.get("Largo", 14.0))
    h_piso = float(params.get("Altura_piso", 3.0))

    area_x_p1 = largo * h_piso
    area_x_p2 = largo * h_piso
    area_z_p1 = ancho * h_piso
    area_z_p2 = ancho * h_piso

    cf = 1.3  # Coeficiente de fuerza típico (0.8 barlovento + 0.5 sotavento)
    return {
        "q": q,
        "Fx_piso_1": q * cf * area_x_p1,
        "Fx_piso_2": q * cf * area_x_p2,
        "Fz_piso_1": q * cf * area_z_p1,
        "Fz_piso_2": q * cf * area_z_p2,
    }


def construir_modelo_estructural(datos: Dict[str, pd.DataFrame],
                                 combos: Optional[List[Tuple[str, Dict[str, float]]]] = None,
                                 direccion_lateral: str = "+X",
                                 incluir_sismo_viento: bool = True) -> Tuple[FEModel3D, Dict[str, Any]]:
    """
    Construye el modelo 3D en PyNite con la geometría de la casa en ladera.
    """
    modelo = FEModel3D()
    nodos_df = datos["Nodos"]
    materiales_df = datos["Materiales"]
    secciones_df = datos["Secciones"]
    columnas_df = datos["Columnas"]
    vigas_df = datos["Vigas"]
    losas_df = datos.get("Losas", pd.DataFrame())

    # 1. Nodos: PyNite X=x, Y=z (cota vertical de elevación), Z=y (longitud en planta)
    for indice, nodo in nodos_df.iterrows():
        nombre_nodo = f"N{indice}"
        x = float(nodo["x"])
        y = float(nodo["y"])
        z = float(nodo["z"])
        modelo.add_node(nombre_nodo, x, z, y)

    # 2. Detección automática de apoyos de cimentación (nodos base en la ladera)
    nodos_inicio_col = set(columnas_df["Nodo1"].astype(str))
    nodos_fin_col = set(columnas_df["Nodo2"].astype(str))
    nodos_apoyo = sorted(list(nodos_inicio_col - nodos_fin_col), key=lambda n: int(n.replace("N", "")))
    if not nodos_apoyo:
        z_min = nodos_df["z"].min()
        nodos_apoyo = [f"N{i}" for i, r in nodos_df.iterrows() if math.isclose(r["z"], z_min, abs_tol=0.01)]

    for nodo_fijo in nodos_apoyo:
        modelo.def_support(nodo_fijo, support_DX=True, support_DY=True, support_DZ=True,
                           support_RX=True, support_RY=True, support_RZ=True)

    # 3. Materiales
    for _, mat in materiales_df.iterrows():
        modelo.add_material(
            str(mat["Nombre"]),
            float(mat["Modulo_E"]),
            float(mat["Modulo_G"]),
            float(mat["Poisson"]),
            float(mat["Densidad"])
        )

    # 4. Secciones
    for _, sec in secciones_df.iterrows():
        modelo.add_section(
            str(sec["Nombre"]),
            float(sec["Area"]),
            float(sec["Inercia_y"]),
            float(sec["Inercia_z"]),
            float(sec["Polar"])
        )

    # 5. Columnas
    for indice, col in columnas_df.iterrows():
        nombre_col = f"C{indice}"
        modelo.add_member(nombre_col, str(col["Nodo1"]), str(col["Nodo2"]), str(col["Material"]), str(col["Seccion"]))

    # 6. Vigas y Cargas Distribuidas
    for indice, viga in vigas_df.iterrows():
        nombre_viga = f"V{indice}"
        modelo.add_member(nombre_viga, str(viga["Nodo1"]), str(viga["Nodo2"]), str(viga["Material"]), str(viga["Seccion"]))

        if "Carga" in viga and pd.notna(viga["Carga"]) and float(viga["Carga"]) > 0:
            carga_val = float(viga["Carga"])
            dist = float(viga.get("Distancia", 0.0))
            if dist <= 0:
                dist = modelo.members[nombre_viga].L()
            # Carga gravitacional en -Y local/global
            modelo.add_member_dist_load(nombre_viga, 'FY', -carga_val, -carga_val, 0, dist, case='D')

    # 7. Losas de entrepiso y cubierta
    if not losas_df.empty:
        for indice, losa in losas_df.iterrows():
            nombre_losa = f"P{indice}"
            nA, nB, nC, nD = str(losa["Nodo1"]), str(losa["Nodo2"]), str(losa["Nodo3"]), str(losa["Nodo4"])
            esp = float(losa.get("Espesor", 0.15))
            mat = str(losa.get("Material", "Concreto"))
            cD = float(losa.get("Carga_Muerta", 3.5))
            cL = float(losa.get("Carga_Viva", 1.8))
            is_cubierta = indice >= 8
            case_live = 'Lr' if is_cubierta else 'L'

            modelo.add_plate(nombre_losa, nA, nB, nC, nD, t=esp, material_name=mat, kx_mod=1.0, ky_mod=1.0)
            modelo.add_plate_surface_pressure(nombre_losa, pressure=cD, case='D')
            modelo.add_plate_surface_pressure(nombre_losa, pressure=cL, case=case_live)

    # 8. Peso propio de elementos estructurales de acero
    modelo.add_member_self_weight('FY', -1.0, 'D')

    # 9. Parámetros de sismo y viento
    params_proy = extraer_parametros_proyecto(datos)
    sismo_info = calcular_parametros_sismicos(params_proy)
    viento_info = calcular_parametros_viento(params_proy)

    # 10. Cargas laterales en nudos de diafragma
    if incluir_sismo_viento:
        dir_lat = direccion_lateral.upper().strip()
        axis = dir_lat[-1] if dir_lat[-1] in ["X", "Z"] else "X"
        sign = 1.0 if dir_lat.startswith("+") else -1.0
        dof = "FX" if axis == "X" else "FZ"

        nodos_apoyo_set = set(nodos_apoyo)
        nodos_super = [f"N{i}" for i in range(len(nodos_df)) if f"N{i}" not in nodos_apoyo_set]
        nodos_p1 = [n for n in nodos_super if float(nodos_df.loc[int(n.replace("N", "")), "z"]) <= 2.0]
        nodos_p2 = [n for n in nodos_super if float(nodos_df.loc[int(n.replace("N", "")), "z"]) > 2.0]

        load_s1 = sign * sismo_info["F_piso_1"] / len(nodos_p1) if nodos_p1 else 0.0
        load_s2 = sign * sismo_info["F_piso_2"] / len(nodos_p2) if nodos_p2 else 0.0
        for n in nodos_p1: modelo.add_node_load(n, dof, load_s1, case="E")
        for n in nodos_p2: modelo.add_node_load(n, dof, load_s2, case="E")

        load_w1 = sign * viento_info["Fx_piso_1" if axis == "X" else "Fz_piso_1"] / len(nodos_p1) if nodos_p1 else 0.0
        load_w2 = sign * viento_info["Fx_piso_2" if axis == "X" else "Fz_piso_2"] / len(nodos_p2) if nodos_p2 else 0.0
        for n in nodos_p1: modelo.add_node_load(n, dof, load_w1, case="W")
        for n in nodos_p2: modelo.add_node_load(n, dof, load_w2, case="W")

    # 11. Combinaciones de Carga
    if combos is None:
        combos = DEFAULT_LOAD_COMBINATIONS

    for nombre_c, factores in combos:
        modelo.add_load_combo(nombre_c, factors=factores)

    info = {
        "nodos_apoyo": nodos_apoyo,
        "total_nodos": len(nodos_df),
        "total_columnas": len(columnas_df),
        "total_vigas": len(vigas_df),
        "total_losas": len(losas_df),
        "combos": [c[0] for c in combos],
        "sismo": sismo_info,
        "viento": viento_info,
        "direccion_lateral": direccion_lateral,
        "parametros_proyecto": params_proy,
    }

    return modelo, info


def extraer_reacciones_apoyos(modelo: FEModel3D, combo: str, nodos_apoyo: List[str]) -> pd.DataFrame:
    """Extrae las reacciones en apoyos para zapatas."""
    es_env = combo.upper() in ["ENV", "ENVELOPE"]
    lista_combos = list(modelo.load_combos.keys()) if es_env else [combo]

    filas = []
    for nombre_nodo in nodos_apoyo:
        nodo = modelo.nodes.get(nombre_nodo)
        if not nodo: continue

        if not es_env:
            filas.append({
                'Zapata_Nodo': nombre_nodo,
                'Pu_vertical_kN': round(nodo.RxnFY.get(combo, 0.0) or 0.0, 2),
                'Vux_kN': round(nodo.RxnFX.get(combo, 0.0) or 0.0, 2),
                'Vuz_kN': round(nodo.RxnFZ.get(combo, 0.0) or 0.0, 2),
                'Mux_kNm': round(nodo.RxnMX.get(combo, 0.0) or 0.0, 2),
                'Muz_kNm': round(nodo.RxnMZ.get(combo, 0.0) or 0.0, 2),
                'Combo_Gov': combo
            })
        else:
            max_Ry = max(abs(nodo.RxnFY.get(c, 0.0) or 0.0) for c in lista_combos)
            max_Rx = max(abs(nodo.RxnFX.get(c, 0.0) or 0.0) for c in lista_combos)
            max_Rz = max(abs(nodo.RxnFZ.get(c, 0.0) or 0.0) for c in lista_combos)
            max_Mx = max(abs(nodo.RxnMX.get(c, 0.0) or 0.0) for c in lista_combos)
            max_Mz = max(abs(nodo.RxnMZ.get(c, 0.0) or 0.0) for c in lista_combos)
            gov_c = max(lista_combos, key=lambda c: abs(nodo.RxnFY.get(c, 0.0) or 0.0))

            filas.append({
                'Zapata_Nodo': nombre_nodo,
                'Pu_vertical_kN': round(max_Ry, 2),
                'Vux_kN': round(max_Rx, 2),
                'Vuz_kN': round(max_Rz, 2),
                'Mux_kNm': round(max_Mx, 2),
                'Muz_kNm': round(max_Mz, 2),
                'Combo_Gov': gov_c
            })

    return pd.DataFrame(filas)


def extraer_solicitaciones_columnas(modelo: FEModel3D, columnas_df: pd.DataFrame,
                                    nodos_df: pd.DataFrame, combo: str) -> pd.DataFrame:
    """Extrae solicitaciones axiales, momentos y cortantes en columnas."""
    es_env = combo.upper() in ["ENV", "ENVELOPE"]
    lista_combos = list(modelo.load_combos.keys()) if es_env else [combo]

    filas = []
    for indice, col in columnas_df.iterrows():
        nombre_col = f"C{indice}"
        miembro = modelo.members.get(nombre_col)
        if not miembro: continue

        nB_idx = int(str(col["Nodo2"]).replace("N", ""))
        zB = float(nodos_df.loc[nB_idx, "z"])
        L_m = miembro.L()

        # Nivel 1 = Nivelación de ladera (C0 a C14), Nivel 2 = Habitable (C15 a C29)
        nivel = "Piso 1 (Nivelación Terreno)" if indice < 15 else "Piso 2 (Nivel Habitable)"

        # Factor de longitud efectiva K sugerido según esbeltez y rigidez en ladera
        if indice < 15:
            # En ladera, las columnas cortas sufren más rigidez y cortante
            K_sugerido = 1.85 if L_m > 3.0 else 1.50
        else:
            K_sugerido = 1.55

        if not es_env:
            P_max = miembro.max_axial(combo) or 0.0
            P_min = miembro.min_axial(combo) or 0.0
            Pu = max(abs(P_max), abs(P_min))
            tipo_axial = 'Compresión' if P_min < 0 and abs(P_min) >= abs(P_max) else 'Tensión'

            Mz = max(abs(miembro.max_moment('Mz', combo) or 0.0), abs(miembro.min_moment('Mz', combo) or 0.0))
            My = max(abs(miembro.max_moment('My', combo) or 0.0), abs(miembro.min_moment('My', combo) or 0.0))
            Vy = max(abs(miembro.max_shear('Fy', combo) or 0.0), abs(miembro.min_shear('Fy', combo) or 0.0))
            Vz = max(abs(miembro.max_shear('Fz', combo) or 0.0), abs(miembro.min_shear('Fz', combo) or 0.0))

            filas.append({
                'Columna': nombre_col,
                'Nivel': nivel,
                'Nodo1': col["Nodo1"],
                'Nodo2': col["Nodo2"],
                'Longitud_m': round(L_m, 2),
                'K_sugerido': K_sugerido,
                'Seccion': col['Seccion'],
                'Pu_kN': round(Pu, 2),
                'Tipo_Axial': tipo_axial,
                'Mu_eje_fuerte_kNm': round(Mz, 2),
                'Mu_eje_debil_kNm': round(My, 2),
                'Vu_kN': round(max(Vy, Vz), 2),
                'Combo_Gov': combo
            })
        else:
            Pu_max = 0.0
            tipo_ax = 'Compresión'
            Mz_max, My_max, Vu_max = 0.0, 0.0, 0.0
            gov_c = lista_combos[0]

            for c in lista_combos:
                p_max = miembro.max_axial(c) or 0.0
                p_min = miembro.min_axial(c) or 0.0
                cand_p = max(abs(p_max), abs(p_min))
                if cand_p > Pu_max:
                    Pu_max = cand_p
                    tipo_ax = 'Compresión' if p_min < 0 and abs(p_min) >= abs(p_max) else 'Tensión'
                    gov_c = c

                mz = max(abs(miembro.max_moment('Mz', c) or 0.0), abs(miembro.min_moment('Mz', c) or 0.0))
                my = max(abs(miembro.max_moment('My', c) or 0.0), abs(miembro.min_moment('My', c) or 0.0))
                vy = max(abs(miembro.max_shear('Fy', c) or 0.0), abs(miembro.min_shear('Fy', c) or 0.0))
                vz = max(abs(miembro.max_shear('Fz', c) or 0.0), abs(miembro.min_shear('Fz', c) or 0.0))

                Mz_max = max(Mz_max, mz)
                My_max = max(My_max, my)
                Vu_max = max(Vu_max, vy, vz)

            filas.append({
                'Columna': nombre_col,
                'Nivel': nivel,
                'Nodo1': col["Nodo1"],
                'Nodo2': col["Nodo2"],
                'Longitud_m': round(L_m, 2),
                'K_sugerido': K_sugerido,
                'Seccion': col['Seccion'],
                'Pu_kN': round(Pu_max, 2),
                'Tipo_Axial': tipo_ax,
                'Mu_eje_fuerte_kNm': round(Mz_max, 2),
                'Mu_eje_debil_kNm': round(My_max, 2),
                'Vu_kN': round(Vu_max, 2),
                'Combo_Gov': gov_c
            })

    return pd.DataFrame(filas)


def extraer_solicitaciones_vigas(modelo: FEModel3D, vigas_df: pd.DataFrame,
                                 nodos_df: pd.DataFrame, combo: str) -> pd.DataFrame:
    """Extrae solicitaciones de flexión, cortante y axial en vigas."""
    es_env = combo.upper() in ["ENV", "ENVELOPE"]
    lista_combos = list(modelo.load_combos.keys()) if es_env else [combo]

    filas = []
    for indice, viga in vigas_df.iterrows():
        nombre_viga = f"V{indice}"
        miembro = modelo.members.get(nombre_viga)
        if not miembro: continue

        L_m = miembro.L()
        nivel = "Piso 1 (Entrepiso)" if indice < 22 else "Piso 2 (Cubierta)"

        if not es_env:
            M_max_z = max(abs(miembro.max_moment('Mz', combo) or 0.0), abs(miembro.min_moment('Mz', combo) or 0.0))
            M_max_y = max(abs(miembro.max_moment('My', combo) or 0.0), abs(miembro.min_moment('My', combo) or 0.0))
            Vu_y = max(abs(miembro.max_shear('Fy', combo) or 0.0), abs(miembro.min_shear('Fy', combo) or 0.0))
            Vu_z = max(abs(miembro.max_shear('Fz', combo) or 0.0), abs(miembro.min_shear('Fz', combo) or 0.0))
            Pu = max(abs(miembro.max_axial(combo) or 0.0), abs(miembro.min_axial(combo) or 0.0))

            filas.append({
                'Viga': nombre_viga,
                'Nivel': nivel,
                'Nodo1': viga["Nodo1"],
                'Nodo2': viga["Nodo2"],
                'Longitud_m': round(L_m, 2),
                'Seccion': viga['Seccion'],
                'Mu_max_kNm': round(M_max_z, 2),
                'Mu_debil_kNm': round(M_max_y, 2),
                'Vu_max_kN': round(max(Vu_y, Vu_z), 2),
                'Pu_kN': round(Pu, 2),
                'Combo_Gov': combo
            })
        else:
            Mz_max, My_max, Vu_max, Pu_max = 0.0, 0.0, 0.0, 0.0
            gov_c = lista_combos[0]

            for c in lista_combos:
                mz = max(abs(miembro.max_moment('Mz', c) or 0.0), abs(miembro.min_moment('Mz', c) or 0.0))
                my = max(abs(miembro.max_moment('My', c) or 0.0), abs(miembro.min_moment('My', c) or 0.0))
                vy = max(abs(miembro.max_shear('Fy', c) or 0.0), abs(miembro.min_shear('Fy', c) or 0.0))
                vz = max(abs(miembro.max_shear('Fz', c) or 0.0), abs(miembro.min_shear('Fz', c) or 0.0))
                p = max(abs(miembro.max_axial(c) or 0.0), abs(miembro.min_axial(c) or 0.0))

                if mz > Mz_max:
                    Mz_max = mz
                    gov_c = c
                My_max = max(My_max, my)
                Vu_max = max(Vu_max, vy, vz)
                Pu_max = max(Pu_max, p)

            filas.append({
                'Viga': nombre_viga,
                'Nivel': nivel,
                'Nodo1': viga["Nodo1"],
                'Nodo2': viga["Nodo2"],
                'Longitud_m': round(L_m, 2),
                'Seccion': viga['Seccion'],
                'Mu_max_kNm': round(Mz_max, 2),
                'Mu_debil_kNm': round(My_max, 2),
                'Vu_max_kN': round(Vu_max, 2),
                'Pu_kN': round(Pu_max, 2),
                'Combo_Gov': gov_c
            })

    return pd.DataFrame(filas)
