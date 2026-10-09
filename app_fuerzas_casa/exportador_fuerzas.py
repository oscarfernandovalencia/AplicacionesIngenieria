#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
exportador_fuerzas.py
===============================================================================
Módulo para empaquetar y exportar las solicitaciones estructurales críticas
(cargas axiales Pu, momentos Mux/Muy, cortantes Vu y longitudes efectivas)
obtenidas del análisis de la casa de 2 niveles.

Estos valores son los que requiere la aplicación de diseño de perfiles metálicos
(app_diseno_perfiles) para verificar y dimensionar los perfiles tubulares HSS.
===============================================================================
"""

import os
import json
from datetime import datetime
from typing import Dict, Any, List, Optional
import pandas as pd


def generar_paquete_solicitaciones(df_columnas: pd.DataFrame,
                                   df_vigas: pd.DataFrame,
                                   df_reacciones: Optional[pd.DataFrame] = None,
                                   combo_origen: str = "ENV (Envolvente Crítica)") -> Dict[str, Any]:
    """
    Identifica los elementos gobernantes de cada nivel y genera el paquete
    estructurado de solicitaciones listas para el diseño de perfiles.
    """
    paquete: Dict[str, Any] = {
        "fecha_generacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "combo_origen": combo_origen,
        "descripcion_proyecto": "Vivienda de 2 Niveles en Ladera (Nivel 1: Nivelación / Nivel 2: Habitable)",
        "elementos_criticos": {},
        "resumen_columnas": [],
        "resumen_vigas": [],
        "reacciones_zapatas": []
    }

    # 1. Separar Columnas por Niveles
    # Nivel 1 = Nivelación de ladera
    cols_n1 = df_columnas[df_columnas["Nivel"].str.contains("Piso 1", na=False)]
    cols_n2 = df_columnas[df_columnas["Nivel"].str.contains("Piso 2", na=False)]

    if cols_n1.empty: cols_n1 = df_columnas.iloc[:15]
    if cols_n2.empty: cols_n2 = df_columnas.iloc[15:]

    # Columna Crítica Nivel 1 (Mayor Pu)
    if not cols_n1.empty:
        idx_c1 = cols_n1["Pu_kN"].idxmax()
        row_c1 = cols_n1.loc[idx_c1]
        paquete["elementos_criticos"]["columna_nivel1_nivelacion"] = {
            "nombre": str(row_c1["Columna"]),
            "rol": "Columna Crítica Nivel 1 (Piso de Nivelación en Ladera)",
            "Pu_kN": float(row_c1["Pu_kN"]),
            "Mux_kNm": float(row_c1["Mu_eje_fuerte_kNm"]),
            "Muy_kNm": float(row_c1["Mu_eje_debil_kNm"]),
            "Vu_kN": float(row_c1["Vu_kN"]),
            "L_m": float(row_c1["Longitud_m"]),
            "K_recomendado": float(row_c1.get("K_sugerido", 1.85)),
            "seccion_actual": str(row_c1["Seccion"]),
            "tipo_axial": str(row_c1.get("Tipo_Axial", "Compresión")),
            "explicacion_ingenieril": (
                "Esta columna se ubica en el piso inferior de nivelación del terreno. "
                "Al estar en pendiente, absorbe altos empujes laterales y cargas verticales "
                "de toda la superestructura. Requiere verificación rigurosa de pandeo y flexo-compresión."
            )
        }

    # Columna Crítica Nivel 2 (Mayor Pu en Nivel Habitable)
    if not cols_n2.empty:
        idx_c2 = cols_n2["Pu_kN"].idxmax()
        row_c2 = cols_n2.loc[idx_c2]
        paquete["elementos_criticos"]["columna_nivel2_habitable"] = {
            "nombre": str(row_c2["Columna"]),
            "rol": "Columna Crítica Nivel 2 (Nivel Habitable)",
            "Pu_kN": float(row_c2["Pu_kN"]),
            "Mux_kNm": float(row_c2["Mu_eje_fuerte_kNm"]),
            "Muy_kNm": float(row_c2["Mu_eje_debil_kNm"]),
            "Vu_kN": float(row_c2["Vu_kN"]),
            "L_m": float(row_c2["Longitud_m"]),
            "K_recomendado": float(row_c2.get("K_sugerido", 1.55)),
            "seccion_actual": str(row_c2["Seccion"]),
            "tipo_axial": str(row_c2.get("Tipo_Axial", "Compresión")),
            "explicacion_ingenieril": (
                "Columna del nivel habitable superior. Soporta cargas vivas de habitaciones, "
                "acabados y peso de cubierta. Su altura es constante y suele ser más esbelta."
            )
        }

    # 2. Separar Vigas por Niveles
    vigas_n1 = df_vigas[df_vigas["Nivel"].str.contains("Piso 1", na=False)]
    vigas_n2 = df_vigas[df_vigas["Nivel"].str.contains("Piso 2", na=False)]

    if vigas_n1.empty: vigas_n1 = df_vigas.iloc[:22]
    if vigas_n2.empty: vigas_n2 = df_vigas.iloc[22:]

    # Viga Crítica Nivel 1 (Mayor Momento Flector)
    if not vigas_n1.empty:
        idx_v1 = vigas_n1["Mu_max_kNm"].idxmax()
        row_v1 = vigas_n1.loc[idx_v1]
        paquete["elementos_criticos"]["viga_nivel1_entrepiso"] = {
            "nombre": str(row_v1["Viga"]),
            "rol": "Viga Crítica Entrepiso Nivel 1 (Plataforma)",
            "Mux_kNm": float(row_v1["Mu_max_kNm"]),
            "Muy_kNm": float(row_v1["Mu_debil_kNm"]),
            "Vu_kN": float(row_v1["Vu_max_kN"]),
            "Pu_kN": float(row_v1.get("Pu_kN", 0.0)),
            "L_m": float(row_v1["Longitud_m"]),
            "seccion_actual": str(row_v1["Seccion"]),
            "explicacion_ingenieril": (
                "Viga principal que soporta la losa de entrepiso y sobrecargas de uso. "
                "Diseño gobernado por momento plástico Mp, cortante y control de deflexión."
            )
        }

    # Viga Crítica Nivel 2 (Mayor Momento Flector en Cubierta)
    if not vigas_n2.empty:
        idx_v2 = vigas_n2["Mu_max_kNm"].idxmax()
        row_v2 = vigas_n2.loc[idx_v2]
        paquete["elementos_criticos"]["viga_nivel2_cubierta"] = {
            "nombre": str(row_v2["Viga"]),
            "rol": "Viga Crítica Cubierta Nivel 2",
            "Mux_kNm": float(row_v2["Mu_max_kNm"]),
            "Muy_kNm": float(row_v2["Mu_debil_kNm"]),
            "Vu_kN": float(row_v2["Vu_max_kN"]),
            "Pu_kN": float(row_v2.get("Pu_kN", 0.0)),
            "L_m": float(row_v2["Longitud_m"]),
            "seccion_actual": str(row_v2["Seccion"]),
            "explicacion_ingenieril": (
                "Viga de coronación y apoyo de correas/cubierta. Resiste cargas de viento "
                "y peso propio de teja y cerchas ligeras."
            )
        }

    # 3. Zapata Crítica de Cimentación
    if df_reacciones is not None and not df_reacciones.empty:
        idx_z = df_reacciones["Pu_vertical_kN"].idxmax()
        row_z = df_reacciones.loc[idx_z]
        paquete["elementos_criticos"]["zapata_critica"] = {
            "nodo_apoyo": str(row_z["Zapata_Nodo"]),
            "Pu_vertical_kN": float(row_z["Pu_vertical_kN"]),
            "Vux_kN": float(row_z["Vux_kN"]),
            "Vuz_kN": float(row_z["Vuz_kN"]),
            "Mux_kNm": float(row_z["Mux_kNm"]),
            "Muz_kNm": float(row_z["Muz_kNm"]),
            "explicacion_ingenieril": (
                "Reacción mayorada sobre el pedestal y zapata en ladera. Define el área "
                "de la placa base metálica y las dimensiones del concreto de cimentación."
            )
        }
        paquete["reacciones_zapatas"] = df_reacciones.to_dict(orient="records")

    # Listas completas tabulares
    paquete["resumen_columnas"] = df_columnas.to_dict(orient="records")
    paquete["resumen_vigas"] = df_vigas.to_dict(orient="records")

    return paquete


def guardar_paquete_solicitaciones(paquete: Dict[str, Any],
                                   rutas_destino: Optional[List[str]] = None) -> List[str]:
    """
    Guarda el archivo JSON en múltiples rutas para que la App 2 pueda cargarlo directamente.
    """
    if rutas_destino is None:
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        rutas_destino = [
            os.path.join(base_dir, "solicitaciones_casa_para_diseno.json"),
            os.path.join(base_dir, "app_fuerzas_casa", "solicitaciones_casa_para_diseno.json"),
            os.path.join(base_dir, "app_diseno_perfiles", "solicitaciones_casa_para_diseno.json"),
        ]

    rutas_guardadas = []
    for r in rutas_destino:
        try:
            d = os.path.dirname(r)
            if d and not os.path.exists(d):
                os.makedirs(d, exist_ok=True)
            with open(r, "w", encoding="utf-8") as f:
                json.dump(paquete, f, indent=2, ensure_ascii=False)
            rutas_guardadas.append(r)
        except Exception as e:
            print(f"Aviso: no se pudo guardar en {r}: {e}")

    return rutas_guardadas


def generar_texto_resumen_exportacion(paquete: Dict[str, Any]) -> str:
    """Genera un resumen técnico legible para el usuario en pantalla."""
    crit = paquete.get("elementos_criticos", {})
    c1 = crit.get("columna_nivel1_nivelacion", {})
    c2 = crit.get("columna_nivel2_habitable", {})
    v1 = crit.get("viga_nivel1_entrepiso", {})
    v2 = crit.get("viga_nivel2_cubierta", {})
    zap = crit.get("zapata_critica", {})

    lineas = [
        "=" * 78,
        "  📦 VALORES DE FUERZAS EXTRAÍDOS PARA EL DISEÑO DE PERFILES HSS",
        "=" * 78,
        f"• Fecha: {paquete.get('fecha_generacion', '')} | Combinación: {paquete.get('combo_origen', '')}",
        f"• Proyecto: {paquete.get('descripcion_proyecto', '')}",
        "-" * 78,
        "1. COLUMNA CRÍTICA NIVEL 1 (Nivelación Terreno en Ladera):",
        f"   - Miembro: {c1.get('nombre', 'N/A')} ({c1.get('seccion_actual', 'HSS6x6x3/16')})",
        f"   - Carga Axial Pu:         {c1.get('Pu_kN', 0.0):.2f} kN ({c1.get('tipo_axial', 'Compresión')})",
        f"   - Momento Flector Mux:    {c1.get('Mux_kNm', 0.0):.2f} kN·m (Eje Fuerte)",
        f"   - Momento Flector Muy:    {c1.get('Muy_kNm', 0.0):.2f} kN·m (Eje Débil)",
        f"   - Cortante Vu:            {c1.get('Vu_kN', 0.0):.2f} kN",
        f"   - Longitud Real L:        {c1.get('L_m', 0.0):.2f} m | Factor K sugerido: {c1.get('K_recomendado', 1.85)}",
        "",
        "2. COLUMNA CRÍTICA NIVEL 2 (Nivel Habitable Superior):",
        f"   - Miembro: {c2.get('nombre', 'N/A')} ({c2.get('seccion_actual', 'HSS4x4x3/16')})",
        f"   - Carga Axial Pu:         {c2.get('Pu_kN', 0.0):.2f} kN",
        f"   - Momento Flector Mux:    {c2.get('Mux_kNm', 0.0):.2f} kN·m",
        f"   - Cortante Vu:            {c2.get('Vu_kN', 0.0):.2f} kN",
        f"   - Longitud Real L:        {c2.get('L_m', 0.0):.2f} m | Factor K sugerido: {c2.get('K_recomendado', 1.55)}",
        "",
        "3. VIGA CRÍTICA NIVEL 1 (Entrepiso Principal):",
        f"   - Miembro: {v1.get('nombre', 'N/A')} ({v1.get('seccion_actual', 'HSS10x6x3/16')})",
        f"   - Momento Flector Mux:    {v1.get('Mux_kNm', 0.0):.2f} kN·m",
        f"   - Cortante Vu:            {v1.get('Vu_kN', 0.0):.2f} kN | Longitud L: {v1.get('L_m', 0.0):.2f} m",
        "",
        "4. VIGA CRÍTICA NIVEL 2 (Cubierta):",
        f"   - Miembro: {v2.get('nombre', 'N/A')} ({v2.get('seccion_actual', 'HSS4x2x3/16')})",
        f"   - Momento Flector Mux:    {v2.get('Mux_kNm', 0.0):.2f} kN·m | Cortante Vu: {v2.get('Vu_kN', 0.0):.2f} kN",
        "",
        "5. REACCIÓN CRÍTICA EN ZAPATA (Cimentación / Placa Base):",
        f"   - Apoyo: {zap.get('nodo_apoyo', 'N/A')}",
        f"   - Pu vertical: {zap.get('Pu_vertical_kN', 0.0):.2f} kN | Cortante Vux: {zap.get('Vux_kN', 0.0):.2f} kN",
        "=" * 78,
        "➡ Estos valores ya fueron exportados a 'solicitaciones_casa_para_diseno.json'",
        "➡ Puedes cargarlos directamente en la Aplicación 2 (Diseñador Didáctico de Perfiles HSS).",
        "=" * 78
    ]
    return "\n".join(lineas)
