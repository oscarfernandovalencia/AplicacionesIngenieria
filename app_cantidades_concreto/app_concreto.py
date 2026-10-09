#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_concreto.py
===============================================================================
APLICACIÓN DE CÁLCULO DE CANTIDADES DE CONCRETO Y MORTERO (GENERAL)
Diseñada para obras civiles y de edificación.
Incluye Interfaz Gráfica (CustomTkinter) y Modo Consola Interactivo (CLI).
===============================================================================
"""

import os
import sys
import argparse
from datetime import datetime
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

dir_actual = os.path.dirname(os.path.abspath(__file__))
if dir_actual not in sys.path:
    sys.path.insert(0, dir_actual)

try:
    from .concreto_core import (
        calcular_concreto, calcular_mortero, calcular_acero_refuerzo,
        volumen_losa, volumen_columna_rectangular, volumen_columna_circular,
        volumen_viga, volumen_zapata, volumen_muro,
        DOSIFICACIONES_CONCRETO_REF, DOSIFICACIONES_MORTERO_REF, TABLA_VARILLAS_ACERO
    )
    from .tablas_referencia import texto_tabla_varillas, texto_tabla_dosificaciones
except ImportError:
    from concreto_core import (
        calcular_concreto, calcular_mortero, calcular_acero_refuerzo,
        volumen_losa, volumen_columna_rectangular, volumen_columna_circular,
        volumen_viga, volumen_zapata, volumen_muro,
        DOSIFICACIONES_CONCRETO_REF, DOSIFICACIONES_MORTERO_REF, TABLA_VARILLAS_ACERO
    )
    from tablas_referencia import texto_tabla_varillas, texto_tabla_dosificaciones


# =============================================================================
# INTERFAZ GRÁFICA (GUI CUSTOMTKINTER)
# =============================================================================
class AppConcretoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🧱 Calculadora General de Cantidades de Concreto y Mortero")
        self.geometry("1100x750")
        self.minsize(950, 650)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.ultimo_reporte = ""

        # Encabezado
        self._crear_encabezado()

        # Panel de Pestañas
        self.tabs = ctk.CTkTabview(self, corner_radius=10)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=10)

        self.tab_concreto = self.tabs.add("  🧱 Concreto Estructural  ")
        self.tab_mortero = self.tabs.add("  🏗️ Mortero de Pega / Revoque  ")
        self.tab_acero = self.tabs.add("  🔩 Acero de Refuerzo  ")
        self.tab_tablas = self.tabs.add("  📚 Tablas de Referencia  ")

        self._construir_tab_concreto()
        self._construir_tab_mortero()
        self._construir_tab_acero()
        self._construir_tab_tablas()

    def _crear_encabezado(self):
        header = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=8)
        header.pack(fill="x", padx=15, pady=(10, 5))

        lbl_t = ctk.CTkLabel(
            header,
            text="🧱 Calculadora General de Concreto, Mortero y Materiales",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#89B4FA"
        )
        lbl_t.pack(side="left", padx=15, pady=8)

        lbl_sub = ctk.CTkLabel(
            header,
            text="Dosificación por m³ o elementos (Losas, Columnas, Vigas, Zapatas)",
            font=ctk.CTkFont(size=12),
            text_color="#BAC2DE"
        )
        lbl_sub.pack(side="right", padx=15, pady=8)

    # -------------------------------------------------------------------------
    # PESTAÑA: CONCRETO
    # -------------------------------------------------------------------------
    def _construir_tab_concreto(self):
        tab = self.tab_concreto

        # Panel izquierdo: Parámetros
        left = ctk.CTkScrollableFrame(tab, width=420)
        left.pack(side="left", fill="both", expand=False, padx=10, pady=10)

        # Método de entrada
        ctk.CTkLabel(left, text="1. Forma de Definir el Concreto:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 3))
        self.combo_metodo_concreto = ctk.CTkComboBox(
            left,
            values=[
                "Volumen Total Directo (m³)",
                "Losa / Piso (Largo x Ancho x Espesor)",
                "Columna Rectangular (Lado A x Lado B x Altura)",
                "Columna Circular (Diámetro x Altura)",
                "Viga (Base x Altura x Longitud)",
                "Zapata / Dado (Largo x Ancho x Peralte)",
                "Muro (Longitud x Altura x Espesor)"
            ],
            command=self._cambiar_metodo_concreto,
            width=380
        )
        self.combo_metodo_concreto.pack(anchor="w", pady=5)
        self.combo_metodo_concreto.set("Volumen Total Directo (m³)")

        # Contenedor dinámico de entradas geométricas
        self.frame_dims_concreto = ctk.CTkFrame(left, fg_color="transparent")
        self.frame_dims_concreto.pack(fill="x", pady=5)
        self._dibujar_entradas_concreto_directo()

        # Proporción
        ctk.CTkLabel(left, text="2. Proporción de Mezcla (C:A:G):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 3))
        self.combo_prop_concreto = ctk.CTkComboBox(
            left,
            values=[
                "1:2:2 (~28 MPa / 4000 psi - Columnas y vigas)",
                "1:2:3 (~21 MPa / 3000 psi - Estándar losas y zapatas)",
                "1:2:4 (~17.5 MPa / 2500 psi - Andenes y pisos)",
                "1:3:5 (~14 MPa / 2000 psi - Solados y ciclópeo)",
                "Personalizada (C:A:G)"
            ],
            width=380,
            command=self._cambiar_prop_concreto
        )
        self.combo_prop_concreto.pack(anchor="w", pady=5)
        self.combo_prop_concreto.set("1:2:3 (~21 MPa / 3000 psi - Estándar losas y zapatas)")

        # Entrada para proporción personalizada (oculta inicialmente)
        self.entry_prop_custom_c = ctk.CTkEntry(left, placeholder_text="Ej: 1:2.5:3.5", width=380)

        # Desperdicio
        ctk.CTkLabel(left, text="3. Desperdicio Estimado (%):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 2))
        self.entry_desp_concreto = ctk.CTkEntry(left, width=150)
        self.entry_desp_concreto.pack(anchor="w", pady=2)
        self.entry_desp_concreto.insert(0, "5.0")

        # Botón Calcular
        btn_calc = ctk.CTkButton(
            left,
            text="⚡ CALCULAR MATERIALES DE CONCRETO",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            height=40,
            command=self._calcular_concreto_gui
        )
        btn_calc.pack(fill="x", pady=(20, 10))

        # Panel derecho: Resultados
        right = ctk.CTkFrame(tab)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(right, text="📋 Resultados del Cálculo:", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=10, pady=5)
        self.txt_res_concreto = ctk.CTkTextbox(right, font=ctk.CTkFont(family="monospace", size=13))
        self.txt_res_concreto.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_guardar = ctk.CTkButton(
            right,
            text="💾 Guardar Reporte en TXT",
            command=lambda: self._guardar_reporte(self.txt_res_concreto.get("1.0", "end-1c"))
        )
        btn_guardar.pack(anchor="e", padx=10, pady=5)

    def _cambiar_metodo_concreto(self, seleccion):
        for widget in self.frame_dims_concreto.winfo_children():
            widget.destroy()

        if "Volumen Total" in seleccion:
            self._dibujar_entradas_concreto_directo()
        elif "Losa" in seleccion:
            self._crear_campo_dim(self.frame_dims_concreto, "Largo (m):", "largo", "6.0")
            self._crear_campo_dim(self.frame_dims_concreto, "Ancho (m):", "ancho", "3.0")
            self._crear_campo_dim(self.frame_dims_concreto, "Espesor (m):", "espesor", "0.15")
            self._crear_campo_dim(self.frame_dims_concreto, "Cantidad:", "cantidad", "1")
        elif "Columna Rectangular" in seleccion:
            self._crear_campo_dim(self.frame_dims_concreto, "Lado A (m):", "lado_a", "0.30")
            self._crear_campo_dim(self.frame_dims_concreto, "Lado B (m):", "lado_b", "0.30")
            self._crear_campo_dim(self.frame_dims_concreto, "Altura (m):", "altura", "2.70")
            self._crear_campo_dim(self.frame_dims_concreto, "Cantidad de Columnas:", "cantidad", "4")
        elif "Columna Circular" in seleccion:
            self._crear_campo_dim(self.frame_dims_concreto, "Diámetro (m):", "diametro", "0.30")
            self._crear_campo_dim(self.frame_dims_concreto, "Altura (m):", "altura", "2.70")
            self._crear_campo_dim(self.frame_dims_concreto, "Cantidad de Columnas:", "cantidad", "4")
        elif "Viga" in seleccion:
            self._crear_campo_dim(self.frame_dims_concreto, "Base (m):", "base", "0.25")
            self._crear_campo_dim(self.frame_dims_concreto, "Altura (m):", "altura", "0.35")
            self._crear_campo_dim(self.frame_dims_concreto, "Longitud (m):", "longitud", "6.0")
            self._crear_campo_dim(self.frame_dims_concreto, "Cantidad de Vigas:", "cantidad", "2")
        elif "Zapata" in seleccion:
            self._crear_campo_dim(self.frame_dims_concreto, "Largo (m):", "largo", "1.20")
            self._crear_campo_dim(self.frame_dims_concreto, "Ancho (m):", "ancho", "1.20")
            self._crear_campo_dim(self.frame_dims_concreto, "Peralte / Altura (m):", "peralte", "0.35")
            self._crear_campo_dim(self.frame_dims_concreto, "Cantidad de Zapatas:", "cantidad", "4")
        elif "Muro" in seleccion:
            self._crear_campo_dim(self.frame_dims_concreto, "Longitud (m):", "longitud", "10.0")
            self._crear_campo_dim(self.frame_dims_concreto, "Altura (m):", "altura", "2.50")
            self._crear_campo_dim(self.frame_dims_concreto, "Espesor (m):", "espesor", "0.20")
            self._crear_campo_dim(self.frame_dims_concreto, "Cantidad:", "cantidad", "1")

    def _dibujar_entradas_concreto_directo(self):
        ctk.CTkLabel(self.frame_dims_concreto, text="Volumen Requerido (m³):").pack(anchor="w", pady=(5, 2))
        self.entry_vol_concreto = ctk.CTkEntry(self.frame_dims_concreto, width=180)
        self.entry_vol_concreto.pack(anchor="w", pady=2)
        self.entry_vol_concreto.insert(0, "1.0")

    def _crear_campo_dim(self, parent, label_text, var_attr, val_default):
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", pady=(4, 1))
        e = ctk.CTkEntry(parent, width=180)
        e.pack(anchor="w", pady=1)
        e.insert(0, val_default)
        setattr(self, f"entry_{var_attr}", e)

    def _cambiar_prop_concreto(self, seleccion):
        if "Personalizada" in seleccion:
            self.entry_prop_custom_c.pack(anchor="w", pady=5)
        else:
            self.entry_prop_custom_c.pack_forget()

    def _calcular_concreto_gui(self):
        try:
            metodo = self.combo_metodo_concreto.get()
            desp = float(self.entry_desp_concreto.get().replace(",", "."))

            # Determinar volumen base
            if "Volumen Total" in metodo:
                vol = float(self.entry_vol_concreto.get().replace(",", "."))
                titulo = f"Volumen Directo {vol} m³"
            elif "Losa" in metodo:
                l = float(self.entry_largo.get().replace(",", "."))
                w = float(self.entry_ancho.get().replace(",", "."))
                t = float(self.entry_espesor.get().replace(",", "."))
                cant = int(self.entry_cantidad.get())
                vol = volumen_losa(l, w, t, cant)
                titulo = f"Losa ({l}x{w}x{t}m, {cant} unid)"
            elif "Columna Rectangular" in metodo:
                a = float(self.entry_lado_a.get().replace(",", "."))
                b = float(self.entry_lado_b.get().replace(",", "."))
                h = float(self.entry_altura.get().replace(",", "."))
                cant = int(self.entry_cantidad.get())
                vol = volumen_columna_rectangular(a, b, h, cant)
                titulo = f"Columnas Rectangulares ({a}x{b}x{h}m, {cant} unid)"
            elif "Columna Circular" in metodo:
                d = float(self.entry_diametro.get().replace(",", "."))
                h = float(self.entry_altura.get().replace(",", "."))
                cant = int(self.entry_cantidad.get())
                vol = volumen_columna_circular(d, h, cant)
                titulo = f"Columnas Circulares (Ø{d}m x {h}m, {cant} unid)"
            elif "Viga" in metodo:
                b = float(self.entry_base.get().replace(",", "."))
                h = float(self.entry_altura.get().replace(",", "."))
                l = float(self.entry_longitud.get().replace(",", "."))
                cant = int(self.entry_cantidad.get())
                vol = volumen_viga(b, h, l, cant)
                titulo = f"Vigas ({b}x{h}x{l}m, {cant} unid)"
            elif "Zapata" in metodo:
                l = float(self.entry_largo.get().replace(",", "."))
                w = float(self.entry_ancho.get().replace(",", "."))
                p = float(self.entry_peralte.get().replace(",", "."))
                cant = int(self.entry_cantidad.get())
                vol = volumen_zapata(l, w, p, cant)
                titulo = f"Zapatas ({l}x{w}x{p}m, {cant} unid)"
            elif "Muro" in metodo:
                l = float(self.entry_longitud.get().replace(",", "."))
                h = float(self.entry_altura.get().replace(",", "."))
                e = float(self.entry_espesor.get().replace(",", "."))
                cant = int(self.entry_cantidad.get())
                vol = volumen_muro(l, h, e, cant)
                titulo = f"Muros ({l}x{h}x{e}m, {cant} unid)"
            else:
                vol = 1.0
                titulo = "Concreto General"

            # Proporción
            sel_prop = self.combo_prop_concreto.get()
            if "1:2:2" in sel_prop:
                prop = (1.0, 2.0, 2.0)
            elif "1:2:3" in sel_prop:
                prop = (1.0, 2.0, 3.0)
            elif "1:2:4" in sel_prop:
                prop = (1.0, 2.0, 4.0)
            elif "1:3:5" in sel_prop:
                prop = (1.0, 3.0, 5.0)
            else:
                partes = [float(p.strip()) for p in self.entry_prop_custom_c.get().split(":")]
                if len(partes) != 3:
                    raise ValueError("Formato de proporción inválido. Debe ser C:A:G (ej. 1:2:3)")
                prop = tuple(partes)

            res = calcular_concreto(vol, proporcion=prop, desperdicio_pct=desp)
            reporte = res.generar_reporte_texto(titulo=titulo)
            self.txt_res_concreto.delete("1.0", "end")
            self.txt_res_concreto.insert("1.0", reporte)
            self.ultimo_reporte = reporte

        except Exception as e:
            messagebox.showerror("Error en Cálculo", f"Error al calcular concreto:\n{e}")

    # -------------------------------------------------------------------------
    # PESTAÑA: MORTERO
    # -------------------------------------------------------------------------
    def _construir_tab_mortero(self):
        tab = self.tab_mortero

        left = ctk.CTkScrollableFrame(tab, width=420)
        left.pack(side="left", fill="both", expand=False, padx=10, pady=10)

        ctk.CTkLabel(left, text="1. Definición del Volumen de Mortero:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 3))
        self.combo_metodo_mortero = ctk.CTkComboBox(
            left,
            values=[
                "Volumen Total Directo (m³)",
                "Área de Pañete / Revoque (Área m² x Espesor m)",
                "Pega de Ladrillo (Área de muro m² x Espesor junta)"
            ],
            command=self._cambiar_metodo_mortero,
            width=380
        )
        self.combo_metodo_mortero.pack(anchor="w", pady=5)
        self.combo_metodo_mortero.set("Volumen Total Directo (m³)")

        self.frame_dims_mortero = ctk.CTkFrame(left, fg_color="transparent")
        self.frame_dims_mortero.pack(fill="x", pady=5)
        self._dibujar_entradas_mortero_directo()

        ctk.CTkLabel(left, text="2. Proporción Cemento : Arena (C:A):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 3))
        self.combo_prop_mortero = ctk.CTkComboBox(
            left,
            values=[
                "1:3 (~12.5 MPa - Revoques impermeables / tanques)",
                "1:4 (~9.0 MPa - Revoques exteriores / pega estructural)",
                "1:5 (~6.0 MPa - Revoques interiores / pañete común)",
                "1:6 (~4.0 MPa - Mampostería no estructural / rellenos)",
                "Personalizada (C:A)"
            ],
            width=380,
            command=self._cambiar_prop_mortero
        )
        self.combo_prop_mortero.pack(anchor="w", pady=5)
        self.combo_prop_mortero.set("1:4 (~9.0 MPa - Revoques exteriores / pega estructural)")

        self.entry_prop_custom_m = ctk.CTkEntry(left, placeholder_text="Ej: 1:3.5", width=380)

        ctk.CTkLabel(left, text="3. Desperdicio Estimado (%):", font=ctk.CTkFont(size=13, weight="bold")).pack(anchor="w", pady=(10, 2))
        self.entry_desp_mortero = ctk.CTkEntry(left, width=150)
        self.entry_desp_mortero.pack(anchor="w", pady=2)
        self.entry_desp_mortero.insert(0, "5.0")

        btn_calc_m = ctk.CTkButton(
            left,
            text="⚡ CALCULAR MATERIALES DE MORTERO",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1",
            height=40,
            command=self._calcular_mortero_gui
        )
        btn_calc_m.pack(fill="x", pady=(20, 10))

        right = ctk.CTkFrame(tab)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(right, text="📋 Resultados de Mortero:", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=10, pady=5)
        self.txt_res_mortero = ctk.CTkTextbox(right, font=ctk.CTkFont(family="monospace", size=13))
        self.txt_res_mortero.pack(fill="both", expand=True, padx=10, pady=(0, 10))

        btn_guardar_m = ctk.CTkButton(
            right,
            text="💾 Guardar Reporte en TXT",
            command=lambda: self._guardar_reporte(self.txt_res_mortero.get("1.0", "end-1c"))
        )
        btn_guardar_m.pack(anchor="e", padx=10, pady=5)

    def _dibujar_entradas_mortero_directo(self):
        ctk.CTkLabel(self.frame_dims_mortero, text="Volumen Requerido (m³):").pack(anchor="w", pady=(5, 2))
        self.entry_vol_mortero = ctk.CTkEntry(self.frame_dims_mortero, width=180)
        self.entry_vol_mortero.pack(anchor="w", pady=2)
        self.entry_vol_mortero.insert(0, "0.5")

    def _cambiar_metodo_mortero(self, seleccion):
        for w in self.frame_dims_mortero.winfo_children():
            w.destroy()

        if "Volumen Total" in seleccion:
            self._dibujar_entradas_mortero_directo()
        elif "Pañete" in seleccion:
            self._crear_campo_dim(self.frame_dims_mortero, "Área de Pared (m²):", "area_mortero", "25.0")
            self._crear_campo_dim(self.frame_dims_mortero, "Espesor del Revoque (m):", "espesor_mortero", "0.015")
        elif "Pega" in seleccion:
            self._crear_campo_dim(self.frame_dims_mortero, "Área del Muro (m²):", "area_muro_pega", "30.0")
            self._crear_campo_dim(self.frame_dims_mortero, "Consumo estimado de mortero (m³/m²):", "consumo_mortero_m2", "0.025")

    def _cambiar_prop_mortero(self, seleccion):
        if "Personalizada" in seleccion:
            self.entry_prop_custom_m.pack(anchor="w", pady=5)
        else:
            self.entry_prop_custom_m.pack_forget()

    def _calcular_mortero_gui(self):
        try:
            metodo = self.combo_metodo_mortero.get()
            desp = float(self.entry_desp_mortero.get().replace(",", "."))

            if "Volumen Total" in metodo:
                vol = float(self.entry_vol_mortero.get().replace(",", "."))
                titulo = f"Mortero por Volumen {vol} m³"
            elif "Pañete" in metodo:
                area = float(self.entry_area_mortero.get().replace(",", "."))
                esp = float(self.entry_espesor_mortero.get().replace(",", "."))
                vol = area * esp
                titulo = f"Pañete / Revoque ({area} m² x {esp*100:.1f} cm)"
            elif "Pega" in metodo:
                area = float(self.entry_area_muro_pega.get().replace(",", "."))
                cons = float(self.entry_consumo_mortero_m2.get().replace(",", "."))
                vol = area * cons
                titulo = f"Pega de Mampostería ({area} m²)"
            else:
                vol = 0.5
                titulo = "Mortero General"

            sel_prop = self.combo_prop_mortero.get()
            if "1:3" in sel_prop:
                prop = (1.0, 3.0)
            elif "1:4" in sel_prop:
                prop = (1.0, 4.0)
            elif "1:5" in sel_prop:
                prop = (1.0, 5.0)
            elif "1:6" in sel_prop:
                prop = (1.0, 6.0)
            else:
                partes = [float(p.strip()) for p in self.entry_prop_custom_m.get().split(":")]
                if len(partes) != 2:
                    raise ValueError("Formato de proporción inválido. Debe ser C:A (ej. 1:4)")
                prop = tuple(partes)

            res = calcular_mortero(vol, proporcion=prop, desperdicio_pct=desp)
            reporte = res.generar_reporte_texto(titulo=titulo)
            self.txt_res_mortero.delete("1.0", "end")
            self.txt_res_mortero.insert("1.0", reporte)
            self.ultimo_reporte = reporte

        except Exception as e:
            messagebox.showerror("Error en Cálculo", f"Error al calcular mortero:\n{e}")

    # -------------------------------------------------------------------------
    # PESTAÑA: ACERO DE REFUERZO
    # -------------------------------------------------------------------------
    def _construir_tab_acero(self):
        tab = self.tab_acero

        left = ctk.CTkFrame(tab, width=420)
        left.pack(side="left", fill="both", expand=False, padx=10, pady=10)

        ctk.CTkLabel(left, text="🔩 Calculadora de Varillas y Peso de Acero:", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=15, pady=(15, 10))

        ctk.CTkLabel(left, text="Número de Varilla ASTM:").pack(anchor="w", padx=15, pady=(5, 2))
        opciones_varillas = [f"#{n} ({d['pulgadas']} - {d['diam_mm']} mm)" for n, d in TABLA_VARILLAS_ACERO.items()]
        self.combo_varilla = ctk.CTkComboBox(left, values=opciones_varillas, width=350)
        self.combo_varilla.pack(anchor="w", padx=15, pady=5)
        self.combo_varilla.set(opciones_varillas[2])  # #4 (1/2")

        ctk.CTkLabel(left, text="Longitud Total Requerida en Metros:").pack(anchor="w", padx=15, pady=(10, 2))
        self.entry_long_acero = ctk.CTkEntry(left, width=200)
        self.entry_long_acero.pack(anchor="w", padx=15, pady=5)
        self.entry_long_acero.insert(0, "60.0")

        btn_calc_a = ctk.CTkButton(
            left,
            text="⚡ CALCULAR PESO Y BARRAS",
            font=ctk.CTkFont(size=14, weight="bold"),
            fg_color="#D84315",
            hover_color="#BF360C",
            height=40,
            command=self._calcular_acero_gui
        )
        btn_calc_a.pack(fill="x", padx=15, pady=(25, 15))

        right = ctk.CTkFrame(tab)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        ctk.CTkLabel(right, text="📋 Ficha Técnica y Cantidades de Acero:", font=ctk.CTkFont(size=15, weight="bold")).pack(anchor="w", padx=10, pady=5)
        self.txt_res_acero = ctk.CTkTextbox(right, font=ctk.CTkFont(family="monospace", size=13))
        self.txt_res_acero.pack(fill="both", expand=True, padx=10, pady=(0, 10))

    def _calcular_acero_gui(self):
        try:
            texto_var = self.combo_varilla.get()
            num_v = int(texto_var.split()[0].replace("#", ""))
            long_m = float(self.entry_long_acero.get().replace(",", "."))

            res = calcular_acero_refuerzo(num_v, long_m)

            rep = [
                "=" * 65,
                f"  🔩 RESUMEN DE ACERO DE REFUERZO - VARILLA #{num_v} ({res['pulgadas']})",
                "=" * 65,
                f"• Diámetro Nominal:        {res['diam_mm']} mm ({res['pulgadas']})",
                f"• Área Transversal:        {res['area_cm2']} cm²",
                f"• Masa Nominal por Metro:  {res['masa_kg_m']} kg/m",
                "-" * 65,
                f"• Longitud Total de Obra:  {res['longitud_total_m']} metros",
                f"• Peso Total Estimado:     {res['peso_total_kg']} kg ({res['peso_total_ton']:.3f} Toneladas)",
                f"• Barras Comerciales (6m): {res['barras_comerciales_6m']} varillas",
                f"• Barras Comerciales (12m):{res['barras_comerciales_12m']} varillas",
                "=" * 65
            ]
            salida = "\n".join(rep)
            self.txt_res_acero.delete("1.0", "end")
            self.txt_res_acero.insert("1.0", salida)

        except Exception as e:
            messagebox.showerror("Error en Cálculo", f"Error calculando acero:\n{e}")

    # -------------------------------------------------------------------------
    # PESTAÑA: TABLAS TÉCNICAS
    # -------------------------------------------------------------------------
    def _construir_tab_tablas(self):
        tab = self.tab_tablas
        txt = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="monospace", size=12))
        txt.pack(fill="both", expand=True, padx=15, pady=15)

        contenido = (
            texto_tabla_dosificaciones() +
            "\n\n" +
            texto_tabla_varillas() +
            "\n\n" +
            "=" * 78 + "\n"
            "  NOTAS TÉCNICAS GENERALES DE CONSTRUCCIÓN:\n"
            "=" * 78 + "\n"
            "• Factores de esponjamiento/contracción:\n"
            "  - Concreto: Factor 1.57 (se requieren 1.57 m³ de materiales secos sueltos para 1.0 m³ de concreto vibrado).\n"
            "  - Mortero:  Factor 1.52 (se requieren 1.52 m³ de materiales secos para 1.0 m³ de mortero húmedo).\n"
            "• Medidas estándar en obra:\n"
            "  - 1 Lata de construcción = 5 galones US = 18.93 litros = 0.0189 m³.\n"
            "  - Densidad aparente del cemento suelto = 1440 kg/m³.\n"
            "  - 1 Bulto de cemento estándar en Colombia y Latinoamérica = 50 kg (~2.64 latas).\n"
            "  - 1 Viaje comercial de volqueta sencilla = 6 m³.\n"
        )
        txt.insert("1.0", contenido)

    def _guardar_reporte(self, contenido):
        if not contenido.strip():
            messagebox.showwarning("Aviso", "No hay resultados para guardar.")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt")],
            title="Guardar Reporte de Materiales"
        )
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(contenido)
                messagebox.showinfo("Guardado", f"Reporte guardado con éxito en:\n{ruta}")
            except Exception as e:
                messagebox.showerror("Error", f"No se pudo guardar el archivo:\n{e}")


# =============================================================================
# MODO LÍNEA DE COMANDOS (CLI INTERACTIVO)
# =============================================================================
def modo_consola_interactivo():
    while True:
        print("\n" + "=" * 68)
        print("   🧱 CALCULADORA GENERAL DE CANTIDADES DE CONCRETO Y MORTERO")
        print("=" * 68)
        print(" 1. 🧱 Concreto por Volumen Total (m³)")
        print(" 2. 🏠 Concreto por Dimensiones de Elemento (Losa, Columna, Viga, Zapata)")
        print(" 3. 🏗️ Mortero para Revoques, Pañetes o Pega")
        print(" 4. 🔩 Consulta y Cálculo de Varillas de Acero (#2 a #11)")
        print(" 5. 📚 Ver Tablas de Dosificaciones y Barras Comerciales")
        print(" 6. 🚪 Volver / Salir")
        print("=" * 68)
        opc = input("Seleccione una opción [1-6]: ").strip()

        if opc == "1":
            try:
                vol = float(input("\nIngrese el volumen de concreto en m³: ").replace(",", "."))
                desp = float(input("Ingrese porcentaje de desperdicio [%, por defecto 5]: ") or "5.0")
                print("\nDosificaciones recomendadas:")
                print(" 1. 1:2:2 (Alta resistencia ~280 kg/cm²)")
                print(" 2. 1:2:3 (Estructural estándar ~210 kg/cm²)")
                print(" 3. 1:2:4 (Pisos / andenes ~175 kg/cm²)")
                print(" 4. 1:3:5 (Concreto simple ~140 kg/cm²)")
                print(" 5. Personalizada (C:A:G)")
                d_opc = input("Opción [1-5, por defecto 2]: ").strip() or "2"
                mapa_props = {"1": (1, 2, 2), "2": (1, 2, 3), "3": (1, 2, 4), "4": (1, 3, 5)}
                if d_opc in mapa_props:
                    prop = mapa_props[d_opc]
                else:
                    prop_str = input("Ingrese proporción (ej. 1:2:3): ")
                    prop = tuple(float(x.strip()) for x in prop_str.split(":"))

                res = calcular_concreto(vol, proporcion=prop, desperdicio_pct=desp)
                print("\n" + res.generar_reporte_texto(titulo=f"{vol} m³ de Concreto"))
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "2":
            try:
                print("\nTipo de elemento:")
                print(" 1. Losa / Piso")
                print(" 2. Columna Rectangular / Cuadrada")
                print(" 3. Columna Cilíndrica")
                print(" 4. Viga")
                print(" 5. Zapata / Dado")
                print(" 6. Muro de concreto")
                t_elem = input("Opción [1-6]: ").strip()

                if t_elem == "1":
                    l = float(input("Largo [m]: ").replace(",", "."))
                    w = float(input("Ancho [m]: ").replace(",", "."))
                    e = float(input("Espesor [m]: ").replace(",", "."))
                    cant = int(input("Cantidad [por defecto 1]: ") or "1")
                    vol = volumen_losa(l, w, e, cant)
                    tit = f"Losa {l}x{w}x{e}m ({cant} unid)"
                elif t_elem == "2":
                    a = float(input("Lado A [m]: ").replace(",", "."))
                    b = float(input("Lado B [m]: ").replace(",", "."))
                    h = float(input("Altura [m]: ").replace(",", "."))
                    cant = int(input("Cantidad [por defecto 1]: ") or "1")
                    vol = volumen_columna_rectangular(a, b, h, cant)
                    tit = f"Columnas {a}x{b}x{h}m ({cant} unid)"
                elif t_elem == "3":
                    d = float(input("Diámetro [m]: ").replace(",", "."))
                    h = float(input("Altura [m]: ").replace(",", "."))
                    cant = int(input("Cantidad [por defecto 1]: ") or "1")
                    vol = volumen_columna_circular(d, h, cant)
                    tit = f"Columnas circulares Ø{d}m x {h}m ({cant} unid)"
                elif t_elem == "4":
                    b = float(input("Base [m]: ").replace(",", "."))
                    h = float(input("Altura [m]: ").replace(",", "."))
                    l = float(input("Longitud [m]: ").replace(",", "."))
                    cant = int(input("Cantidad [por defecto 1]: ") or "1")
                    vol = volumen_viga(b, h, l, cant)
                    tit = f"Vigas {b}x{h}x{l}m ({cant} unid)"
                elif t_elem == "5":
                    l = float(input("Largo [m]: ").replace(",", "."))
                    w = float(input("Ancho [m]: ").replace(",", "."))
                    p = float(input("Peralte [m]: ").replace(",", "."))
                    cant = int(input("Cantidad [por defecto 1]: ") or "1")
                    vol = volumen_zapata(l, w, p, cant)
                    tit = f"Zapatas {l}x{w}x{p}m ({cant} unid)"
                elif t_elem == "6":
                    l = float(input("Longitud [m]: ").replace(",", "."))
                    h = float(input("Altura [m]: ").replace(",", "."))
                    e = float(input("Espesor [m]: ").replace(",", "."))
                    cant = int(input("Cantidad [por defecto 1]: ") or "1")
                    vol = volumen_muro(l, h, e, cant)
                    tit = f"Muros {l}x{h}x{e}m ({cant} unid)"
                else:
                    print("Opción inválida.")
                    continue

                desp = float(input("Desperdicio [%, defecto 5]: ") or "5.0")
                res = calcular_concreto(vol, proporcion=(1, 2, 3), desperdicio_pct=desp)
                print("\n" + res.generar_reporte_texto(titulo=tit))
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "3":
            try:
                vol = float(input("\nIngrese volumen de mortero en m³: ").replace(",", "."))
                desp = float(input("Desperdicio [%, defecto 5]: ") or "5.0")
                print("Proporciones de mortero:")
                print(" 1. 1:3 (Impermeabilizaciones / tanques)")
                print(" 2. 1:4 (Revoques exteriores / pega estructural)")
                print(" 3. 1:5 (Revoques interiores comunes)")
                print(" 4. 1:6 (Pega no estructural / rellenos)")
                m_opc = input("Opción [1-4, defecto 2]: ").strip() or "2"
                mapa_m = {"1": (1, 3), "2": (1, 4), "3": (1, 5), "4": (1, 6)}
                prop = mapa_m.get(m_opc, (1, 4))
                res = calcular_mortero(vol, proporcion=prop, desperdicio_pct=desp)
                print("\n" + res.generar_reporte_texto(titulo=f"{vol} m³ de Mortero ({prop[0]}:{prop[1]})"))
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "4":
            try:
                print("\n" + texto_tabla_varillas())
                num_v = int(input("Ingrese el número de varilla (#2 al #11): ").replace("#", ""))
                long_m = float(input("Ingrese los metros lineales totales: ").replace(",", "."))
                res = calcular_acero_refuerzo(num_v, long_m)
                print("\n" + "=" * 60)
                print(f"  VARILLA #{num_v} ({res['pulgadas']} - {res['diam_mm']} mm)")
                print(f"  • Metros requeridos:      {res['longitud_total_m']} m")
                print(f"  • Peso total:             {res['peso_total_kg']} kg ({res['peso_total_ton']} ton)")
                print(f"  • Barras de 6m necesarias:{res['barras_comerciales_6m']}")
                print(f"  • Barras de 12m necesarias:{res['barras_comerciales_12m']}")
                print("=" * 60)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "5":
            print("\n" + texto_tabla_dosificaciones())
            print("\n" + texto_tabla_varillas())

        elif opc == "6":
            print("\nVolviendo al menú principal...")
            break
        else:
            print("Opción no válida.")


# =============================================================================
# ENTRADA PRINCIPAL
# =============================================================================
def main():
    parser = argparse.ArgumentParser(description="Calculadora General de Concreto y Mortero")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en modo consola interactiva (sin GUI)")
    args = parser.parse_args()

    # Si se pide CLI o no hay entorno gráfico
    if args.cli or not os.environ.get("DISPLAY"):
        modo_consola_interactivo()
    else:
        try:
            app = AppConcretoGUI()
            app.mainloop()
        except Exception as e:
            print(f"Aviso: No se pudo abrir la interfaz gráfica ({e}). Cambiando a modo consola.")
            modo_consola_interactivo()

if __name__ == "__main__":
    main()
