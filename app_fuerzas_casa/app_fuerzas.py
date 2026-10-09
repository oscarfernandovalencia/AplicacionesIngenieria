#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_fuerzas.py
===============================================================================
APLICACIÓN 1: ANÁLISIS DE FUERZAS EN VIVIENDA DE 2 NIVELES EN LADERA
- Nivel 1: Nivelación del terreno (columnas en pendiente).
- Nivel 2: Nivel habitable.

Calcula solicitaciones (Pu, Mux, Muy, Vu) y reacciones en zapatas bajo
combinaciones gravitacionales, sismo (NSR-10 Título A) y viento (NSR-10 Título B).
Exporta el paquete de fuerzas para el diseño de perfiles en la App 2.
===============================================================================
"""

import os
import sys
import argparse
import threading
import queue
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk
import pandas as pd
import numpy as np

import matplotlib
matplotlib.use('TkAgg')
import matplotlib.pyplot as plt
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from mpl_toolkits.mplot3d import Axes3D

# Módulos internos
dir_actual = os.path.dirname(os.path.abspath(__file__))
if dir_actual not in sys.path:
    sys.path.insert(0, dir_actual)
try:
    from .motor_analisis import (
        cargar_datos_estructura, construir_modelo_estructural,
        extraer_reacciones_apoyos, extraer_solicitaciones_columnas,
        extraer_solicitaciones_vigas, DEFAULT_LOAD_COMBINATIONS
    )
    from .exportador_fuerzas import (
        generar_paquete_solicitaciones, guardar_paquete_solicitaciones,
        generar_texto_resumen_exportacion
    )
    from .visualizador_3d import dibujar_estructura_matplotlib, exportar_y_abrir_visor_web
except ImportError:
    from motor_analisis import (
        cargar_datos_estructura, construir_modelo_estructural,
        extraer_reacciones_apoyos, extraer_solicitaciones_columnas,
        extraer_solicitaciones_vigas, DEFAULT_LOAD_COMBINATIONS
    )
    from exportador_fuerzas import (
        generar_paquete_solicitaciones, guardar_paquete_solicitaciones,
        generar_texto_resumen_exportacion
    )
    from visualizador_3d import dibujar_estructura_matplotlib, exportar_y_abrir_visor_web


class AppFuerzasGUI(ctk.CTk):
    def __init__(self, ruta_ods: Optional[str] = None):
        super().__init__()
        self.title("🏢 App 1: Análisis de Fuerzas en Casa de 2 Niveles (Nivelación + Habitable)")
        self.geometry("1300x880")
        self.minsize(1050, 700)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        # Buscar archivo base ODS
        if ruta_ods and os.path.exists(ruta_ods):
            self.ruta_archivo = ruta_ods
        else:
            dir_act = os.path.dirname(os.path.abspath(__file__))
            ruta_cand = os.path.join(dir_act, "NodosYCargasCopacabana.ods")
            if os.path.exists(ruta_cand):
                self.ruta_archivo = ruta_cand
            else:
                self.ruta_archivo = "NodosYCargasCopacabana.ods"

        self.tipo_solver = "Lineal"
        self.direccion_lat = "+X"
        self.combo_actual = "ENV (Envolvente Crítica)"

        # Estado del modelo
        self.datos = None
        self.modelo = None
        self.info_modelo = None
        self.df_cols = None
        self.df_vigas = None
        self.df_reacciones = None
        self.paquete_exportado = None

        self._crear_encabezado()
        self._crear_panel_pestañas()

        # Iniciar cálculo en segundo plano
        self.after(200, self.resolver_modelo)

    def _crear_encabezado(self):
        header = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=10)
        header.pack(fill="x", padx=15, pady=(10, 5))

        top_box = ctk.CTkFrame(header, fg_color="transparent")
        top_box.pack(fill="x", padx=15, pady=8)

        lbl_tit = ctk.CTkLabel(
            top_box,
            text="🏢 Análisis de Fuerzas: Casa de 2 Niveles en Ladera",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#89B4FA"
        )
        lbl_tit.pack(side="left")

        self.lbl_estado = ctk.CTkLabel(
            top_box,
            text="⏳ Cargando y resolviendo modelo FEA...",
            font=ctk.CTkFont(size=12, weight="bold"),
            text_color="#F9E2AF"
        )
        self.lbl_estado.pack(side="right")

        # Barra de controles
        ctrl_bar = ctk.CTkFrame(header, fg_color="transparent")
        ctrl_bar.pack(fill="x", padx=15, pady=(0, 8))

        ctk.CTkLabel(ctrl_bar, text="Combinación:").pack(side="left", padx=(0, 5))
        self.combo_combos = ctk.CTkComboBox(
            ctrl_bar,
            values=["ENV (Envolvente Crítica)", "1.2D + 1.6L", "1.4D", "1.2D + 1.0E + 1.0L", "1.2D + 1.6W + 1.0L + 0.5Lr"],
            width=230,
            command=self._cambiar_combo
        )
        self.combo_combos.pack(side="left", padx=5)

        ctk.CTkLabel(ctrl_bar, text="Solver:").pack(side="left", padx=(15, 5))
        self.combo_solver = ctk.CTkComboBox(
            ctrl_bar,
            values=["Lineal (1er Orden)", "P-Delta (2do Orden)"],
            width=160,
            command=self._cambiar_solver
        )
        self.combo_solver.pack(side="left", padx=5)

        ctk.CTkLabel(ctrl_bar, text="Sismo/Viento:").pack(side="left", padx=(15, 5))
        self.combo_dir = ctk.CTkComboBox(
            ctrl_bar,
            values=["+X", "-X", "+Z", "-Z"],
            width=80,
            command=self._cambiar_direccion
        )
        self.combo_dir.pack(side="left", padx=5)

        btn_recalc = ctk.CTkButton(ctrl_bar, text="🔄 Recalcular", width=110, command=self.resolver_modelo)
        btn_recalc.pack(side="left", padx=(15, 5))

        btn_exp = ctk.CTkButton(
            ctrl_bar,
            text="💾 EXPORTAR PARA APP 2",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            command=self._exportar_fuerzas_accion
        )
        btn_exp.pack(side="right", padx=5)

    def _crear_panel_pestañas(self):
        self.tabs = ctk.CTkTabview(self, corner_radius=10)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=8)

        self.tab_3d = self.tabs.add("  🌐 Vista 3D y Terreno  ")
        self.tab_columnas = self.tabs.add("  🏛️ Fuerzas en Columnas  ")
        self.tab_vigas = self.tabs.add("  📐 Fuerzas en Vigas  ")
        self.tab_zapatas = self.tabs.add("  🧱 Reacciones en Zapatas  ")
        self.tab_export = self.tabs.add("  📤 Paquete para Diseño (App 2)  ")

        self._construir_tab_3d()
        self._construir_tab_columnas()
        self._construir_tab_vigas()
        self._construir_tab_zapatas()
        self._construir_tab_export()

    # -------------------------------------------------------------------------
    # TAB 1: VISOR 3D
    # -------------------------------------------------------------------------
    def _construir_tab_3d(self):
        tab = self.tab_3d
        top_ctrl = ctk.CTkFrame(tab, fg_color="transparent")
        top_ctrl.pack(fill="x", padx=10, pady=5)

        self.chk_def_var = ctk.BooleanVar(value=True)
        chk_def = ctk.CTkCheckBox(top_ctrl, text="Mostrar Deformada", variable=self.chk_def_var, command=self._actualizar_canvas_3d)
        chk_def.pack(side="left", padx=10)

        ctk.CTkLabel(top_ctrl, text="Escala Deformada:").pack(side="left", padx=(15, 5))
        self.slider_escala = ctk.CTkSlider(top_ctrl, from_=5.0, to=150.0, number_of_steps=29, command=lambda v: self._actualizar_canvas_3d())
        self.slider_escala.set(40.0)
        self.slider_escala.pack(side="left", padx=5)

        btn_web = ctk.CTkButton(
            top_ctrl,
            text="🌐 Abrir Visor WebGL Interactivo (Plotly)",
            fg_color="#313244",
            hover_color="#45475A",
            command=self._abrir_visor_plotly
        )
        btn_web.pack(side="right", padx=10)

        # Canvas Matplotlib
        self.fig = plt.Figure(figsize=(8, 5.5), facecolor="#181825")
        self.ax_3d = self.fig.add_subplot(111, projection="3d")
        self.canvas_3d = FigureCanvasTkAgg(self.fig, master=tab)
        self.canvas_3d.get_tk_widget().pack(fill="both", expand=True, padx=10, pady=5)

    def _actualizar_canvas_3d(self):
        if not self.modelo:
            return
        esc = self.slider_escala.get()
        mostrar_def = self.chk_def_var.get()
        combo = self.combo_combos.get()
        dibujar_estructura_matplotlib(self.ax_3d, self.modelo, combo=combo, mostrar_deformada=mostrar_def, escala_deformada=esc)
        self.canvas_3d.draw()

    def _abrir_visor_plotly(self):
        if not self.modelo:
            return
        combo = self.combo_combos.get()
        exportar_y_abrir_visor_web(self.modelo, combo=combo)

    # -------------------------------------------------------------------------
    # TAB 2: COLUMNAS
    # -------------------------------------------------------------------------
    def _construir_tab_columnas(self):
        tab = self.tab_columnas

        # Tarjetas de resumen en la parte superior
        cards = ctk.CTkFrame(tab, fg_color="transparent")
        cards.pack(fill="x", padx=10, pady=5)

        self.card_col_n1 = ctk.CTkFrame(cards, fg_color="#181825", corner_radius=8)
        self.card_col_n1.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.lbl_card_n1 = ctk.CTkLabel(self.card_col_n1, text="Cargando...", justify="left", font=ctk.CTkFont(size=12))
        self.lbl_card_n1.pack(padx=10, pady=8)

        self.card_col_n2 = ctk.CTkFrame(cards, fg_color="#181825", corner_radius=8)
        self.card_col_n2.pack(side="left", fill="both", expand=True, padx=5, pady=5)
        self.lbl_card_n2 = ctk.CTkLabel(self.card_col_n2, text="Cargando...", justify="left", font=ctk.CTkFont(size=12))
        self.lbl_card_n2.pack(padx=10, pady=8)

        # Tabla
        self.tree_cols = self._crear_tabla(tab, ["Columna", "Nivel", "Longitud (m)", "Sección", "Pu (kN)", "Tipo", "Mux (kNm)", "Muy (kNm)", "Vu (kN)", "K"])

    # -------------------------------------------------------------------------
    # TAB 3: VIGAS
    # -------------------------------------------------------------------------
    def _construir_tab_vigas(self):
        tab = self.tab_vigas
        self.tree_vigas = self._crear_tabla(tab, ["Viga", "Nivel", "Longitud (m)", "Sección", "Mux_max (kNm)", "Muy (kNm)", "Vu_max (kN)", "Pu (kN)", "Combo Gov"])

    # -------------------------------------------------------------------------
    # TAB 4: ZAPATAS
    # -------------------------------------------------------------------------
    def _construir_tab_zapatas(self):
        tab = self.tab_zapatas
        self.tree_zapatas = self._crear_tabla(tab, ["Zapata / Nodo", "Pu Vertical (kN)", "Vux Cortante (kN)", "Vuz Cortante (kN)", "Mux (kNm)", "Muz (kNm)", "Combo Gov"])

    # -------------------------------------------------------------------------
    # TAB 5: EXPORTACIÓN PARA APP 2
    # -------------------------------------------------------------------------
    def _construir_tab_export(self):
        tab = self.tab_export
        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(
            top,
            text="📦 Solicitaciones Estructurales Gobernantes listas para transferir a la App de Perfiles:",
            font=ctk.CTkFont(size=14, weight="bold")
        ).pack(side="left")

        btn_guardar_json = ctk.CTkButton(
            top,
            text="💾 Guardar Copia JSON...",
            command=self._guardar_json_manual
        )
        btn_guardar_json.pack(side="right", padx=5)

        self.txt_export = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="monospace", size=13))
        self.txt_export.pack(fill="both", expand=True, padx=10, pady=5)

    def _crear_tabla(self, parent, columnas):
        f = ctk.CTkFrame(parent)
        f.pack(fill="both", expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#181825", foreground="#CDD6F4", fieldbackground="#181825", rowheight=24)
        style.configure("Treeview.Heading", background="#313244", foreground="#89B4FA", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#45475A')])

        tree = ttk.Treeview(f, columns=columnas, show="headings", selectmode="browse")
        for col in columnas:
            tree.heading(col, text=col)
            tree.column(col, anchor="center", width=110)

        sb = ttk.Scrollbar(f, orient="vertical", command=tree.yview)
        tree.configure(yscrollcommand=sb.set)
        tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")
        return tree

    # -------------------------------------------------------------------------
    # LÓGICA DE ANÁLISIS FEA Y ACTUALIZACIÓN
    # -------------------------------------------------------------------------
    def resolver_modelo(self):
        self.lbl_estado.configure(text="⏳ Resolviendo modelo FEA...")
        resultado_q = queue.Queue()

        def worker():
            try:
                datos = cargar_datos_estructura(self.ruta_archivo)
                modelo, info = construir_modelo_estructural(
                    datos,
                    direccion_lateral=self.direccion_lat,
                    incluir_sismo_viento=True
                )
                if "P-Delta" in self.tipo_solver:
                    modelo.analyze_PDelta()
                else:
                    modelo.analyze()
                resultado_q.put(("OK", datos, modelo, info))
            except Exception as e:
                resultado_q.put(("ERROR", str(e)))

        threading.Thread(target=worker, daemon=True).start()

        def verificar():
            try:
                item = resultado_q.get_nowait()
                if item[0] == "OK":
                    _, self.datos, self.modelo, self.info_modelo = item
                    self.lbl_estado.configure(
                        text=f"✔ Análisis exitoso ({self.tipo_solver} | {len(self.modelo.nodes)} nodos | {len(self.modelo.members)} miembros)"
                    )
                    self._actualizar_datos_y_tablas()
                    self._actualizar_canvas_3d()
                else:
                    err = item[1]
                    self.lbl_estado.configure(text=f"❌ Error: {err}")
                    messagebox.showerror("Error en Análisis", f"Error en FEA:\n{err}")
            except queue.Empty:
                self.after(100, verificar)

        self.after(100, verificar)

    def _actualizar_datos_y_tablas(self):
        combo = self.combo_combos.get()
        combo_eval = "ENV" if "ENV" in combo else combo

        self.df_reacciones = extraer_reacciones_apoyos(self.modelo, combo_eval, self.info_modelo["nodos_apoyo"])
        self.df_cols = extraer_solicitaciones_columnas(self.modelo, self.datos["Columnas"], self.datos["Nodos"], combo_eval)
        self.df_vigas = extraer_solicitaciones_vigas(self.modelo, self.datos["Vigas"], self.datos["Nodos"], combo_eval)

        # Generar paquete
        self.paquete_exportado = generar_paquete_solicitaciones(self.df_cols, self.df_vigas, self.df_reacciones, combo_origen=combo)
        guardar_paquete_solicitaciones(self.paquete_exportado)

        # 1. Poblar Columnas
        self.tree_cols.delete(*self.tree_cols.get_children())
        for _, r in self.df_cols.iterrows():
            self.tree_cols.insert("", "end", values=[
                r["Columna"], r["Nivel"], f"{r['Longitud_m']:.2f}", r["Seccion"],
                f"{r['Pu_kN']:.2f}", r["Tipo_Axial"], f"{r['Mu_eje_fuerte_kNm']:.2f}",
                f"{r['Mu_eje_debil_kNm']:.2f}", f"{r['Vu_kN']:.2f}", f"{r.get('K_sugerido', 1.0)}"
            ])

        # Actualizar Tarjetas
        c1 = self.paquete_exportado["elementos_criticos"].get("columna_nivel1_nivelacion", {})
        c2 = self.paquete_exportado["elementos_criticos"].get("columna_nivel2_habitable", {})
        self.lbl_card_n1.configure(
            text=f"🏛️ NIVEL 1 (Nivelación en Ladera)\n"
                 f"Columna Crítica: {c1.get('nombre', 'N/A')} (L = {c1.get('L_m', 0):.2f}m)\n"
                 f"Pu: {c1.get('Pu_kN', 0):.2f} kN | Mux: {c1.get('Mux_kNm', 0):.2f} kNm\n"
                 f"Vu: {c1.get('Vu_kN', 0):.2f} kN | K sugerido: {c1.get('K_recomendado', 1.85)}"
        )
        self.lbl_card_n2.configure(
            text=f"🏠 NIVEL 2 (Nivel Habitable Superior)\n"
                 f"Columna Crítica: {c2.get('nombre', 'N/A')} (L = {c2.get('L_m', 0):.2f}m)\n"
                 f"Pu: {c2.get('Pu_kN', 0):.2f} kN | Mux: {c2.get('Mux_kNm', 0):.2f} kNm\n"
                 f"Vu: {c2.get('Vu_kN', 0):.2f} kN | K sugerido: {c2.get('K_recomendado', 1.55)}"
        )

        # 2. Poblar Vigas
        self.tree_vigas.delete(*self.tree_vigas.get_children())
        for _, r in self.df_vigas.iterrows():
            self.tree_vigas.insert("", "end", values=[
                r["Viga"], r["Nivel"], f"{r['Longitud_m']:.2f}", r["Seccion"],
                f"{r['Mu_max_kNm']:.2f}", f"{r['Mu_debil_kNm']:.2f}",
                f"{r['Vu_max_kN']:.2f}", f"{r['Pu_kN']:.2f}", r["Combo_Gov"]
            ])

        # 3. Poblar Zapatas
        self.tree_zapatas.delete(*self.tree_zapatas.get_children())
        for _, r in self.df_reacciones.iterrows():
            self.tree_zapatas.insert("", "end", values=[
                r["Zapata_Nodo"], f"{r['Pu_vertical_kN']:.2f}", f"{r['Vux_kN']:.2f}",
                f"{r['Vuz_kN']:.2f}", f"{r['Mux_kNm']:.2f}", f"{r['Muz_kNm']:.2f}", r["Combo_Gov"]
            ])

        # 4. Texto de exportación
        txt_res = generar_texto_resumen_exportacion(self.paquete_exportado)
        self.txt_export.delete("1.0", "end")
        self.txt_export.insert("1.0", txt_res)

    def _cambiar_combo(self, seleccion):
        self.combo_actual = seleccion
        if self.modelo:
            self._actualizar_datos_y_tablas()
            self._actualizar_canvas_3d()

    def _cambiar_solver(self, seleccion):
        self.tipo_solver = "Lineal" if "Lineal" in seleccion else "P-Delta"
        self.resolver_modelo()

    def _cambiar_direccion(self, seleccion):
        self.direccion_lat = seleccion
        self.resolver_modelo()

    def _exportar_fuerzas_accion(self):
        if not self.paquete_exportado:
            messagebox.showwarning("Aviso", "Primero debe resolver el modelo.")
            return
        rutas = guardar_paquete_solicitaciones(self.paquete_exportado)
        messagebox.showinfo(
            "Exportación Exitosa",
            f"Las solicitaciones de diseño se guardaron exitosamente en:\n"
            + "\n".join(f"• {r}" for r in rutas) + "\n\n"
            "Ya puedes abrir la Aplicación 2 (Diseñador Didáctico de Perfiles HSS) y cargar estos valores con 1 clic."
        )

    def _guardar_json_manual(self):
        if not self.paquete_exportado:
            return
        ruta = filedialog.asksaveasfilename(
            defaultextension=".json",
            filetypes=[("Archivos JSON", "*.json")],
            initialfile="solicitaciones_casa_para_diseno.json"
        )
        if ruta:
            guardar_paquete_solicitaciones(self.paquete_exportado, [ruta])
            messagebox.showinfo("Guardado", f"Archivo guardado en:\n{ruta}")


# =============================================================================
# MODO LÍNEA DE COMANDOS (CLI INTERACTIVO)
# =============================================================================
def modo_consola(ruta_ods: str):
    print("\n" + "=" * 75)
    print("  🏢 ANÁLISIS ESTRUCTURAL 3D DE CASA EN LADERA (PYNITE FEA / NSR-10)")
    print("=" * 75)
    print(f"Cargando archivo: {ruta_ods}")
    datos = cargar_datos_estructura(ruta_ods)
    print("✔ Datos cargados correctamente.")
    print("Construyendo y resolviendo modelo con combinaciones LRFD completas...")
    modelo, info = construir_modelo_estructural(datos, direccion_lateral="+X", incluir_sismo_viento=True)
    modelo.analyze()
    print("✔ Modelo convergido con éxito.")

    df_reac = extraer_reacciones_apoyos(modelo, "ENV", info["nodos_apoyo"])
    df_cols = extraer_solicitaciones_columnas(modelo, datos["Columnas"], datos["Nodos"], "ENV")
    df_vigas = extraer_solicitaciones_vigas(modelo, datos["Vigas"], datos["Nodos"], "ENV")

    paquete = generar_paquete_solicitaciones(df_cols, df_vigas, df_reac, combo_origen="ENV (Envolvente Crítica)")
    rutas = guardar_paquete_solicitaciones(paquete)

    print("\n" + generar_texto_resumen_exportacion(paquete))
    print(f"\n✔ Archivos JSON exportados para diseño en: {rutas}")


def main():
    parser = argparse.ArgumentParser(description="Análisis de Fuerzas de Casa de 2 Niveles")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en modo consola (sin GUI)")
    parser.add_argument("--file", type=str, default="NodosYCargasCopacabana.ods", help="Ruta al archivo ODS")
    args = parser.parse_args()

    dir_act = os.path.dirname(os.path.abspath(__file__))
    ruta_archivo = args.file
    if not os.path.exists(ruta_archivo):
        cand = os.path.join(dir_act, "NodosYCargasCopacabana.ods")
        if os.path.exists(cand):
            ruta_archivo = cand

    if args.cli or not os.environ.get("DISPLAY"):
        modo_consola(ruta_archivo)
    else:
        try:
            app = AppFuerzasGUI(ruta_archivo)
            app.mainloop()
        except Exception as e:
            print(f"Aviso GUI: {e}. Pasando a modo consola.")
            modo_consola(ruta_archivo)

if __name__ == "__main__":
    main()
