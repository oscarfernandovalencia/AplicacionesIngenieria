#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
visualizador_3d.py
===============================================================================
Módulo de visualización 3D interactiva para la estructura en ladera:
- Renderizado interactivo en Matplotlib 3D embebido en la GUI.
- Renderizado WebGL interactivo en navegador mediante Plotly 3D.
===============================================================================
"""

import os
import webbrowser
from typing import Optional, Dict, Any, List
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import matplotlib.pyplot as plt
from mpl_toolkits.mplot3d import Axes3D
from Pynite import FEModel3D


def generar_figura_3d_plotly(modelo: FEModel3D,
                              combo: str = "1.2D + 1.6L",
                              mostrar_deformada: bool = False,
                              escala_deformada: float = 50.0,
                              titulo: str = "Casa 2 Niveles en Ladera - Modelo 3D") -> go.Figure:
    """Construye una figura Plotly 3D interactiva con vista de pendiente y miembros."""
    traces = []
    es_envolvente = "ENV" in combo.upper()
    combo_def = combo if (combo in modelo.load_combos) else (list(modelo.load_combos.keys())[0] if modelo.load_combos else None)

    # 1. Dibujar miembros (Columnas y Vigas)
    for m_name, m in modelo.members.items():
        n1, n2 = m.i_node, m.j_node
        es_columna = m_name.startswith("C")
        x1, y1, z1 = n1.X, n1.Z, n1.Y
        x2, y2, z2 = n2.X, n2.Z, n2.Y

        if mostrar_deformada and combo_def and combo_def in modelo.load_combos:
            try:
                x1 += (n1.DX.get(combo_def, 0.0) or 0.0) * escala_deformada
                y1 += (n1.DZ.get(combo_def, 0.0) or 0.0) * escala_deformada
                z1 += (n1.DY.get(combo_def, 0.0) or 0.0) * escala_deformada
                x2 += (n2.DX.get(combo_def, 0.0) or 0.0) * escala_deformada
                y2 += (n2.DZ.get(combo_def, 0.0) or 0.0) * escala_deformada
                z2 += (n2.DY.get(combo_def, 0.0) or 0.0) * escala_deformada
            except Exception:
                pass

        color = "#3388FF" if es_columna else "#FF9800"
        ancho = 6 if es_columna else 4

        try:
            if not es_envolvente and combo in modelo.load_combos:
                pu = abs(m.max_axial(combo) or 0.0)
                mu = abs(m.max_moment("Mz", combo) or 0.0)
                vu = abs(m.max_shear("Fy", combo) or 0.0)
            else:
                c_all = list(modelo.load_combos.keys())
                pu = max(abs(m.max_axial(c) or 0.0) for c in c_all) if c_all else 0.0
                mu = max(abs(m.max_moment("Mz", c) or 0.0) for c in c_all) if c_all else 0.0
                vu = max(abs(m.max_shear("Fy", c) or 0.0) for c in c_all) if c_all else 0.0
        except Exception:
            pu, mu, vu = 0.0, 0.0, 0.0

        hover_txt = (
            f"<b>{m_name} ({'Columna' if es_columna else 'Viga'})</b><br>"
            f"Longitud: {m.L():.2f} m<br>"
            f"Pu: {pu:.2f} kN | Mu: {mu:.2f} kN·m | Vu: {vu:.2f} kN"
        )

        traces.append(go.Scatter3d(
            x=[x1, x2], y=[y1, y2], z=[z1, z2],
            mode='lines',
            line=dict(color=color, width=ancho),
            name=m_name,
            text=hover_txt,
            hoverinfo='text',
            showlegend=False
        ))

    # 2. Apoyos de cimentación y Nodos
    apoyos_x, apoyos_y, apoyos_z, apoyos_txt = [], [], [], []
    for n_name, n in modelo.nodes.items():
        if any([n.support_DX, n.support_DY, n.support_DZ]):
            apoyos_x.append(n.X)
            apoyos_y.append(n.Z)
            apoyos_z.append(n.Y)
            apoyos_txt.append(f"<b>Apoyo Zapata {n_name}</b><br>Z elevación: {n.Y:.2f} m")

    if apoyos_x:
        traces.append(go.Scatter3d(
            x=apoyos_x, y=apoyos_y, z=apoyos_z,
            mode='markers',
            marker=dict(size=8, color='#FF1744', symbol='diamond'),
            name='Apoyos en Ladera',
            text=apoyos_txt,
            hoverinfo='text'
        ))

    layout = go.Layout(
        title=dict(text=titulo, font=dict(size=18, color="#FFFFFF")),
        paper_bgcolor="#181825",
        scene=dict(
            xaxis=dict(title="X (Ancho m)", backgroundcolor="#11111B", gridcolor="#313244"),
            yaxis=dict(title="Z Global (Largo m)", backgroundcolor="#11111B", gridcolor="#313244"),
            zaxis=dict(title="Elevación Y (m)", backgroundcolor="#11111B", gridcolor="#313244"),
            aspectmode="data"
        ),
        margin=dict(l=0, r=0, b=0, t=40)
    )
    return go.Figure(data=traces, layout=layout)


def exportar_y_abrir_visor_web(modelo: FEModel3D,
                               ruta_html: str = "visor_estructura_3d.html",
                               combo: str = "1.2D + 1.6L"):
    """Exporta y abre en navegador el visor 3D Plotly WebGL."""
    fig = generar_figura_3d_plotly(modelo, combo=combo)
    fig.write_html(ruta_html)
    webbrowser.open("file://" + os.path.abspath(ruta_html))


def dibujar_estructura_matplotlib(ax, modelo: FEModel3D,
                                  combo: str = "1.2D + 1.6L",
                                  mostrar_deformada: bool = False,
                                  escala_deformada: float = 30.0):
    """Renderiza la estructura 3D en un eje Matplotlib embebible en Tkinter."""
    ax.clear()
    ax.set_facecolor("#181825")

    combo_def = combo if (combo in modelo.load_combos) else (list(modelo.load_combos.keys())[0] if modelo.load_combos else None)

    for m_name, m in modelo.members.items():
        n1, n2 = m.i_node, m.j_node
        x1, y1, z1 = n1.X, n1.Z, n1.Y
        x2, y2, z2 = n2.X, n2.Z, n2.Y

        if mostrar_deformada and combo_def and combo_def in modelo.load_combos:
            try:
                x1 += (n1.DX.get(combo_def, 0.0) or 0.0) * escala_deformada
                y1 += (n1.DZ.get(combo_def, 0.0) or 0.0) * escala_deformada
                z1 += (n1.DY.get(combo_def, 0.0) or 0.0) * escala_deformada
                x2 += (n2.DX.get(combo_def, 0.0) or 0.0) * escala_deformada
                y2 += (n2.DZ.get(combo_def, 0.0) or 0.0) * escala_deformada
                z2 += (n2.DY.get(combo_def, 0.0) or 0.0) * escala_deformada
            except Exception:
                pass

        es_col = m_name.startswith("C")
        c = "#4C78A8" if es_col else "#F58518"
        lw = 2.5 if es_col else 1.8
        ax.plot([x1, x2], [y1, y2], [z1, z2], color=c, linewidth=lw)

    # Apoyos
    ap_x, ap_y, ap_z = [], [], []
    for n in modelo.nodes.values():
        if any([n.support_DX, n.support_DY, n.support_DZ]):
            ap_x.append(n.X); ap_y.append(n.Z); ap_z.append(n.Y)

    if ap_x:
        ax.scatter(ap_x, ap_y, ap_z, color="#E45756", s=40, marker="^", label="Apoyos (Zapatas)")

    ax.set_xlabel("X (Ancho m)", color="#CDD6F4", labelpad=8)
    ax.set_ylabel("Z (Largo m)", color="#CDD6F4", labelpad=8)
    ax.set_zlabel("Elevación (m)", color="#CDD6F4", labelpad=8)
    ax.tick_params(colors="#A6ADC8")
    ax.set_title("Modelo 3D: Vivienda en Pendiente", color="#89B4FA", fontsize=12, pad=10)
