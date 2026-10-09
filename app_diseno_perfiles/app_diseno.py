#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
app_diseno.py
===============================================================================
APLICACIÓN 2: DISEÑADOR DIDÁCTICO DE PERFILES METÁLICOS HSS (AISC 360 / McCORMAC)
- Permite verificar si un perfil específico resiste o no las cargas aplicadas.
- Explica didácticamente cada paso, fórmula, límite y concepto de ingeniería.
- Permite cargar directamente las solicitaciones calculadas por la App 1 (Casa de 2 Niveles).
- Incluye optimizador automático por peso propio mínimo para ahorro de acero.
- Incluye prediseño de placas base sobre pedestales de concreto.
===============================================================================
"""

import os
import sys
import argparse
import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import customtkinter as ctk

# Módulos internos
dir_actual = os.path.dirname(os.path.abspath(__file__))
if dir_actual not in sys.path:
    sys.path.insert(0, dir_actual)
try:
    from .catalogo_hss import get_profile, list_all_profiles, HSSProfile
    from .verificador_aisc import AISCHSSDesigner, DesignResult
    from .tutor_didactico import LECCIONES_DIDACTICAS, obtener_texto_leccion, explicar_resultado_paso_a_paso
    from .puente_fuerzas import obtener_elementos_disponibles, cargar_paquete_solicitaciones
except ImportError:
    from catalogo_hss import get_profile, list_all_profiles, HSSProfile
    from verificador_aisc import AISCHSSDesigner, DesignResult
    from tutor_didactico import LECCIONES_DIDACTICAS, obtener_texto_leccion, explicar_resultado_paso_a_paso
    from puente_fuerzas import obtener_elementos_disponibles, cargar_paquete_solicitaciones


class AppDisenoGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("📐 App 2: Diseñador Didáctico de Perfiles HSS (AISC 360-16 / McCormac)")
        self.geometry("1300x880")
        self.minsize(1050, 700)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.elementos_casa = obtener_elementos_disponibles()
        self.designer = AISCHSSDesigner(Fy=345.0, E=200000.0, system="si")
        self.ultimo_resultado = None

        self._crear_encabezado()
        self._crear_panel_pestañas()

    def _crear_encabezado(self):
        header = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=10)
        header.pack(fill="x", padx=15, pady=(10, 5))

        top_box = ctk.CTkFrame(header, fg_color="transparent")
        top_box.pack(fill="x", padx=15, pady=8)

        lbl_t = ctk.CTkLabel(
            top_box,
            text="⚡ Diseñador y Verificador Didáctico de Perfiles HSS",
            font=ctk.CTkFont(size=20, weight="bold"),
            text_color="#89B4FA"
        )
        lbl_t.pack(side="left")

        lbl_sub = ctk.CTkLabel(
            top_box,
            text="Norma AISC 360-16 / McCormac (Método LRFD)",
            font=ctk.CTkFont(size=12),
            text_color="#BAC2DE"
        )
        lbl_sub.pack(side="right")

        # Barra de Carga Rápida desde la Casa
        bar = ctk.CTkFrame(header, fg_color="#181825", corner_radius=8)
        bar.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(
            bar,
            text="📂 Cargar Fuerzas de la Casa (App 1):",
            font=ctk.CTkFont(size=13, weight="bold"),
            text_color="#A6E3A1"
        ).pack(side="left", padx=10, pady=6)

        nombres_elems = list(self.elementos_casa.keys())
        self.combo_elementos_casa = ctk.CTkComboBox(
            bar,
            values=nombres_elems,
            width=420,
            command=self._cargar_fuerzas_elemento_casa
        )
        self.combo_elementos_casa.pack(side="left", padx=5, pady=6)
        if nombres_elems:
            self.combo_elementos_casa.set(nombres_elems[0])

        btn_aplicar = ctk.CTkButton(
            bar,
            text="✔ Cargar Solicitaciones",
            width=150,
            command=lambda: self._cargar_fuerzas_elemento_casa(self.combo_elementos_casa.get())
        )
        btn_aplicar.pack(side="left", padx=10, pady=6)

    def _crear_panel_pestañas(self):
        self.tabs = ctk.CTkTabview(self, corner_radius=10)
        self.tabs.pack(fill="both", expand=True, padx=15, pady=8)

        self.tab_verif = self.tabs.add("  📋 Verificación Paso a Paso  ")
        self.tab_opt = self.tabs.add("  🚀 Selector Óptimo por Peso Mínimo  ")
        self.tab_teoria = self.tabs.add("  📖 Manual Didáctico de Fórmulas  ")

        self._construir_tab_verificacion()
        self._construir_tab_optimizacion()
        self._construir_tab_teoria()

    # -------------------------------------------------------------------------
    # TAB 1: VERIFICACIÓN PASO A PASO
    # -------------------------------------------------------------------------
    def _construir_tab_verificacion(self):
        tab = self.tab_verif

        # Columna Izquierda: Parámetros y Cargas
        left = ctk.CTkScrollableFrame(tab, width=440)
        left.pack(side="left", fill="both", expand=False, padx=10, pady=10)

        # 1. Perfil a Verificar
        ctk.CTkLabel(left, text="1. Selección de Perfil HSS:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 3))
        profs = [p.name for p in list_all_profiles(sort_by_weight=True)]
        self.combo_perfil = ctk.CTkComboBox(left, values=profs, width=380, command=self._actualizar_info_perfil_preview)
        self.combo_perfil.pack(anchor="w", pady=3)
        self.combo_perfil.set("HSS6x6x3/16")

        self.lbl_perfil_props = ctk.CTkLabel(left, text="", justify="left", font=ctk.CTkFont(size=11), text_color="#A6ADC8")
        self.lbl_perfil_props.pack(anchor="w", pady=(2, 10))

        # 2. Cargas Solicitantes
        ctk.CTkLabel(left, text="2. Cargas Últimas de Diseño (LRFD):", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(5, 3))

        self.entry_pu = self._crear_campo_input(left, "Carga Axial Pu [kN, (+) compresión]:", "161.67")
        self.entry_mux = self._crear_campo_input(left, "Momento Eje Fuerte Mux [kN·m]:", "10.11")
        self.entry_muy = self._crear_campo_input(left, "Momento Eje Débil Muy [kN·m]:", "0.85")
        self.entry_vu = self._crear_campo_input(left, "Cortante Último Vu [kN]:", "6.69")

        # 3. Geometría y Longitud
        ctk.CTkLabel(left, text="3. Longitud y Factores de Pandeo:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 3))
        self.entry_l = self._crear_campo_input(left, "Longitud No Arriostrada L [m]:", "3.02")
        self.entry_k = self._crear_campo_input(left, "Factor Longitud Efectiva K (ej. 1.85 ladera, 1.0 simple):", "1.85")

        # 4. Material
        ctk.CTkLabel(left, text="4. Resistencia del Acero:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", pady=(10, 3))
        self.combo_fy = ctk.CTkComboBox(
            left,
            values=["345 MPa (ASTM A500 Gr. B/C)", "355 MPa (ASTM A1085)", "250 MPa (ASTM A36)"],
            width=380
        )
        self.combo_fy.pack(anchor="w", pady=3)
        self.combo_fy.set("345 MPa (ASTM A500 Gr. B/C)")

        # Botón Verificar
        btn_verif = ctk.CTkButton(
            left,
            text="⚡ VERIFICAR CAPACIDAD AISC PASO A PASO",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            height=42,
            command=self._verificar_perfil_accion
        )
        btn_verif.pack(fill="x", pady=(20, 10))

        # Columna Derecha: Resultados y Explicación Didáctica
        right = ctk.CTkFrame(tab)
        right.pack(side="right", fill="both", expand=True, padx=10, pady=10)

        # Barra de estado superior de resultado
        self.card_status = ctk.CTkFrame(right, fg_color="#313244", corner_radius=8)
        self.card_status.pack(fill="x", padx=10, pady=8)

        self.lbl_status_resultado = ctk.CTkLabel(
            self.card_status,
            text="Presione 'VERIFICAR' para evaluar el perfil",
            font=ctk.CTkFont(size=15, weight="bold"),
            text_color="#89B4FA"
        )
        self.lbl_status_resultado.pack(padx=15, pady=10)

        ctk.CTkLabel(right, text="📖 Desglose y Explicación Didáctica Paso a Paso:", font=ctk.CTkFont(size=14, weight="bold")).pack(anchor="w", padx=10, pady=(5, 3))

        self.txt_explicacion = ctk.CTkTextbox(right, font=ctk.CTkFont(family="monospace", size=13))
        self.txt_explicacion.pack(fill="both", expand=True, padx=10, pady=5)

        btn_guardar_informe = ctk.CTkButton(
            right,
            text="💾 Guardar Informe de Diseño en TXT",
            command=self._guardar_informe_txt
        )
        btn_guardar_informe.pack(anchor="e", padx=10, pady=5)

        self._actualizar_info_perfil_preview("HSS6x6x3/16")

    def _crear_campo_input(self, parent, label_text, default_val):
        ctk.CTkLabel(parent, text=label_text).pack(anchor="w", pady=(3, 1))
        e = ctk.CTkEntry(parent, width=200)
        e.pack(anchor="w", pady=(1, 4))
        e.insert(0, default_val)
        return e

    def _actualizar_info_perfil_preview(self, nombre_perfil):
        p = get_profile(nombre_perfil)
        if not p:
            self.lbl_perfil_props.configure(text="")
            return
        info = (
            f"• H: {p.H_mm:.1f} mm | B: {p.B_mm:.1f} mm | t: {p.t_mm:.2f} mm\n"
            f"• Área: {p.A_cm2:.1f} cm² | Peso: {p.weight_kg_m:.2f} kg/m ({p.weight_lb_ft:.2f} lb/ft)\n"
            f"• Inercias: Ix = {p.Ix_cm4:.1f} cm⁴ | Iy = {p.Iy_cm4:.1f} cm⁴\n"
            f"• Módulos Plásticos: Zx = {p.Zx_cm3:.1f} cm³ | Zy = {p.Zy_cm3:.1f} cm³\n"
            f"• Radios de Giro: rx = {p.rx_cm:.2f} cm | ry = {p.ry_cm:.2f} cm"
        )
        self.lbl_perfil_props.configure(text=info)

    def _cargar_fuerzas_elemento_casa(self, seleccion):
        if not seleccion or seleccion not in self.elementos_casa:
            return
        item = self.elementos_casa[seleccion]

        self.entry_pu.delete(0, "end"); self.entry_pu.insert(0, str(item.get("Pu_kN", 0.0)))
        self.entry_mux.delete(0, "end"); self.entry_mux.insert(0, str(item.get("Mux_kNm", 0.0)))
        self.entry_muy.delete(0, "end"); self.entry_muy.insert(0, str(item.get("Muy_kNm", 0.0)))
        self.entry_vu.delete(0, "end"); self.entry_vu.insert(0, str(item.get("Vu_kN", 0.0)))
        self.entry_l.delete(0, "end"); self.entry_l.insert(0, str(item.get("L_m", 3.0)))
        self.entry_k.delete(0, "end"); self.entry_k.insert(0, str(item.get("K_recomendado", 1.85)))

        sec_act = item.get("seccion_actual", "")
        # Normalizar nombres como A1085-6x6x3-16 a HSS6x6x3/16
        if "6x6x3-16" in sec_act: self.combo_perfil.set("HSS6x6x3/16")
        elif "10x6x3-16" in sec_act: self.combo_perfil.set("HSS10x6x3/16")
        elif "4x4x3-16" in sec_act: self.combo_perfil.set("HSS4x4x3/16")
        elif "4x2x3-16" in sec_act: self.combo_perfil.set("HSS4x2x3/16")

        self._actualizar_info_perfil_preview(self.combo_perfil.get())
        messagebox.showinfo(
            "Cargas Cargadas",
            f"Se cargaron las solicitaciones de:\n{seleccion}\n\n"
            f"• Pu = {item.get('Pu_kN')} kN\n"
            f"• Mux = {item.get('Mux_kNm')} kN·m\n"
            f"• Vu = {item.get('Vu_kN')} kN\n"
            f"• Longitud = {item.get('L_m')} m (K = {item.get('K_recomendado')})"
        )

    def _verificar_perfil_accion(self):
        try:
            nom_p = self.combo_perfil.get().strip()
            p = get_profile(nom_p)
            if not p:
                messagebox.showerror("Error", f"Perfil '{nom_p}' no encontrado en el catálogo.")
                return

            pu = float(self.entry_pu.get().replace(",", "."))
            mux = float(self.entry_mux.get().replace(",", "."))
            muy = float(self.entry_muy.get().replace(",", "."))
            vu = float(self.entry_vu.get().replace(",", "."))
            l_m = float(self.entry_l.get().replace(",", "."))
            k_val = float(self.entry_k.get().replace(",", "."))

            # Fluencia
            sel_fy = self.combo_fy.get()
            fy_val = float(sel_fy.split()[0])
            self.designer = AISCHSSDesigner(Fy=fy_val, E=200000.0, system="si")

            res = self.designer.check_combined_si(
                profile=p, Pu_kN=pu, Mux_kNm=mux, Muy_kNm=muy,
                Vux_kN=0.0, Vuy_kN=vu, L_m=l_m, Kx=k_val, Ky=k_val
            )
            self.ultimo_resultado = res

            # Actualizar tarjeta de estado
            dcr = res.dcr_max
            pct = dcr * 100.0
            if res.is_adequate:
                color_bg = "#1B5E20" if dcr <= 0.95 else "#F57F17"
                txt_st = f"✔ CUMPLE - PERFIL ADECUADO | DCR = {dcr:.4f} ({pct:.1f}% de capacidad) | Modo: {res.governing_mode}"
            else:
                color_bg = "#B71C1C"
                txt_st = f"❌ FALLA - SOBREESFORZADO | DCR = {dcr:.4f} ({pct:.1f}% de capacidad) | Modo: {res.governing_mode}"

            self.card_status.configure(fg_color=color_bg)
            self.lbl_status_resultado.configure(text=txt_st, text_color="#FFFFFF")

            # Cálculo de placa base para pedestal
            res_placa = self.designer.check_base_plate(pu, p, fc_MPa=21.0, Fy_plate_MPa=250.0)

            # Generar explicación didáctica paso a paso
            narrativa = explicar_resultado_paso_a_paso(res, sistema="si")
            narrativa += (
                "\n\n" +
                "=" * 78 + "\n"
                "  🧱 PREDISEÑO DE PLACA BASE SOBRE PEDESTAL DE CONCRETO (McCormac Cap. 15)\n"
                "=" * 78 + "\n"
                f"• Carga Axial a Cimentación: {res_placa['Pu_kN']:.2f} kN\n"
                f"• Dimensiones Recomendadas:   {res_placa['B_mm']:.0f} mm x {res_placa['N_mm']:.0f} mm (Área: {res_placa['Area_cm2']} cm²)\n"
                f"• Presión de Contacto fp:    {res_placa['fp_MPa']} MPa vs Máx Admisible Fp = {res_placa['Fp_max_MPa']} MPa (f'c = 21 MPa)\n"
                f"• Espesor Teórico de Placa:  {res_placa['tp_calculado_mm']} mm\n"
                f"• Espesor Comercial Mínimo:  {res_placa['tp_comercial_mm']} mm ({res_placa['espesor_pulgadas']})\n"
                "=" * 78
            )

            self.txt_explicacion.delete("1.0", "end")
            self.txt_explicacion.insert("1.0", narrativa)

        except Exception as e:
            messagebox.showerror("Error", f"Error durante la verificación:\n{e}")

    # -------------------------------------------------------------------------
    # TAB 2: SELECTOR ÓPTIMO POR PESO MÍNIMO
    # -------------------------------------------------------------------------
    def _construir_tab_optimizacion(self):
        tab = self.tab_opt

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(top, text="Tipo de Tubo:").pack(side="left", padx=5)
        self.combo_tipo_tubo = ctk.CTkComboBox(top, values=["Todos los HSS", "Solo Cuadrados (SHS)", "Solo Rectangulares (RHS)"], width=200)
        self.combo_tipo_tubo.pack(side="left", padx=5)
        self.combo_tipo_tubo.set("Todos los HSS")

        ctk.CTkLabel(top, text="DCR Máximo Admisible:").pack(side="left", padx=(15, 5))
        self.slider_max_dcr = ctk.CTkSlider(top, from_=0.50, to=1.00, number_of_steps=10)
        self.slider_max_dcr.set(0.95)
        self.slider_max_dcr.pack(side="left", padx=5)

        btn_buscar = ctk.CTkButton(
            top,
            text="🔍 BUSCAR PERFILES MÁS ECONÓMICOS",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1",
            command=self._buscar_optimos_accion
        )
        btn_buscar.pack(side="right", padx=10)

        # Tabla de clasificación
        cols = ["Rank", "Perfil HSS", "Peso (kg/m)", "Peso (lb/ft)", "DCR Máx", "Utilización", "Modo Gobernante", "Calificación"]
        f_tree = ctk.CTkFrame(tab)
        f_tree.pack(fill="both", expand=True, padx=10, pady=5)

        self.tree_opt = ttk.Treeview(f_tree, columns=cols, show="headings", selectmode="browse")
        for c in cols:
            self.tree_opt.heading(c, text=c)
            self.tree_opt.column(c, anchor="center", width=120)

        sb = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree_opt.yview)
        self.tree_opt.configure(yscrollcommand=sb.set)
        self.tree_opt.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

    def _buscar_optimos_accion(self):
        try:
            pu = float(self.entry_pu.get().replace(",", "."))
            mux = float(self.entry_mux.get().replace(",", "."))
            muy = float(self.entry_muy.get().replace(",", "."))
            vu = float(self.entry_vu.get().replace(",", "."))
            l_m = float(self.entry_l.get().replace(",", "."))
            k_val = float(self.entry_k.get().replace(",", "."))
            max_dcr = self.slider_max_dcr.get()

            sel_tipo = self.combo_tipo_tubo.get()
            t_filtro = "square" if "Cuadrados" in sel_tipo else ("rectangular" if "Rectangulares" in sel_tipo else "all")

            fy_val = float(self.combo_fy.get().split()[0])
            self.designer = AISCHSSDesigner(Fy=fy_val, E=200000.0, system="si")

            res_lista = self.designer.find_optimal_profiles_si(
                Pu_kN=pu, Mux_kNm=mux, Muy_kNm=muy, Vux_kN=0.0, Vuy_kN=vu,
                L_m=l_m, Kx=k_val, Ky=k_val, profile_type=t_filtro, max_dcr=max_dcr
            )

            self.tree_opt.delete(*self.tree_opt.get_children())
            if not res_lista:
                messagebox.showwarning("Sin resultados", "No se encontraron perfiles en el catálogo que resistan las cargas con el DCR solicitado.")
                return

            for i, r in enumerate(res_lista, start=1):
                p = r.profile
                calif = "⭐ MÁS ECONÓMICO (ÓPTIMO)" if i == 1 else ("Muy Eficiente" if i <= 3 else "Seguro")
                self.tree_opt.insert("", "end", values=[
                    i, p.name, f"{p.weight_kg_m:.2f}", f"{p.weight_lb_ft:.2f}",
                    f"{r.dcr_max:.4f}", f"{r.dcr_max*100:.1f}%", r.governing_mode, calif
                ])

            messagebox.showinfo(
                "Búsqueda Exitosa",
                f"Se encontraron {len(res_lista)} perfiles adecuados.\n"
                f"La opción óptima más ligera y económica es: {res_lista[0].profile.name} ({res_lista[0].profile.weight_kg_m:.2f} kg/m, DCR = {res_lista[0].dcr_max:.3f})."
            )

        except Exception as e:
            messagebox.showerror("Error", f"Error en búsqueda: {e}")

    # -------------------------------------------------------------------------
    # TAB 3: MANUAL DIDÁCTICO
    # -------------------------------------------------------------------------
    def _construir_tab_teoria(self):
        tab = self.tab_teoria

        top = ctk.CTkFrame(tab, fg_color="transparent")
        top.pack(fill="x", padx=10, pady=8)

        ctk.CTkLabel(top, text="Seleccione el tema a estudiar:", font=ctk.CTkFont(size=14, weight="bold")).pack(side="left", padx=5)

        opciones_lecciones = [
            ("filosofia_lrfd", "1. Filosofía de Diseño LRFD (AISC / McCormac)"),
            ("compresion_euler", "2. Columnas a Compresión y Pandeo de Euler"),
            ("pandeo_local", "3. Pandeo Local en Paredes de Tubos HSS (b/t, h/t)"),
            ("flexion_vigas", "4. Vigas a Flexión, Momento Plástico Mp y Cortante"),
            ("interaccion_flexocompresion", "5. Interacción Flexo-Compresión (H1-1a / H1-1b)"),
            ("placa_base", "6. Prediseño de Placas Base sobre Concreto")
        ]
        self.mapa_lecciones = {nom: k for k, nom in opciones_lecciones}

        self.combo_lecciones = ctk.CTkComboBox(
            top,
            values=[nom for _, nom in opciones_lecciones],
            width=450,
            command=self._cambiar_leccion_didactica
        )
        self.combo_lecciones.pack(side="left", padx=10)
        self.combo_lecciones.set(opciones_lecciones[0][1])

        self.txt_teoria = ctk.CTkTextbox(tab, font=ctk.CTkFont(family="monospace", size=13))
        self.txt_teoria.pack(fill="both", expand=True, padx=10, pady=10)

        self._cambiar_leccion_didactica(opciones_lecciones[0][1])

    def _cambiar_leccion_didactica(self, seleccion):
        clave = self.mapa_lecciones.get(seleccion, "filosofia_lrfd")
        txt = obtener_texto_leccion(clave)
        self.txt_teoria.delete("1.0", "end")
        self.txt_teoria.insert("1.0", txt)

    def _guardar_informe_txt(self):
        contenido = self.txt_explicacion.get("1.0", "end-1c")
        if not contenido.strip():
            messagebox.showwarning("Aviso", "Primero realiza una verificación.")
            return

        ruta = filedialog.asksaveasfilename(
            defaultextension=".txt",
            filetypes=[("Archivos de texto", "*.txt")],
            initialfile="informe_diseno_perfil_hss.txt"
        )
        if ruta:
            try:
                with open(ruta, "w", encoding="utf-8") as f:
                    f.write(contenido)
                messagebox.showinfo("Guardado", f"Informe guardado en:\n{ruta}")
            except Exception as e:
                messagebox.showerror("Error", f"Error al guardar: {e}")


# =============================================================================
# MODO LÍNEA DE COMANDOS (CLI INTERACTIVO)
# =============================================================================
def modo_consola_interactivo():
    from .puente_fuerzas import obtener_elementos_disponibles
    from .catalogo_hss import get_profile, list_all_profiles
    from .verificador_aisc import AISCHSSDesigner
    from .tutor_didactico import LECCIONES_DIDACTICAS, explicar_resultado_paso_a_paso

    designer = AISCHSSDesigner(Fy=345.0, E=200000.0, system="si")
    elementos = obtener_elementos_disponibles()

    while True:
        print("\n" + "=" * 75)
        print("   📐 DISEÑADOR DIDÁCTICO DE PERFILES HSS (AISC 360-16 / McCORMAC)")
        print("=" * 75)
        print(" 1. 📂 Cargar solicitaciones calculadas por la Casa de 2 Niveles (App 1)")
        print(" 2. ✏️ Ingresar solicitaciones manualmente (Pu, Mux, Muy, Vu, L, K)")
        print(" 3. 🔍 Buscar automáticamente el perfil óptimo por peso mínimo")
        print(" 4. 📖 Leer lecciones didácticas sobre cómo diseñar estructuras de acero")
        print(" 5. 🚪 Volver / Salir")
        print("=" * 75)
        opc = input("Seleccione una opción [1-5]: ").strip()

        if opc == "1":
            print("\nElementos disponibles de la Casa:")
            noms = list(elementos.keys())
            for i, n in enumerate(noms, start=1):
                it = elementos[n]
                print(f" [{i}] {n}: Pu={it.get('Pu_kN')} kN | Mux={it.get('Mux_kNm')} kNm | Vu={it.get('Vu_kN')} kN | L={it.get('L_m')}m")
            sel_i = input(f"Elija un elemento [1-{len(noms)}]: ").strip()
            try:
                idx = int(sel_i) - 1
                item = elementos[noms[idx]]
                pu = float(item.get("Pu_kN", 0.0))
                mux = float(item.get("Mux_kNm", 0.0))
                muy = float(item.get("Muy_kNm", 0.0))
                vu = float(item.get("Vu_kN", 0.0))
                l_m = float(item.get("L_m", 3.0))
                k_val = float(item.get("K_recomendado", 1.85))
                p_sug = item.get("seccion_actual", "HSS6x6x3/16")

                print(f"\nSección actual del modelo: {p_sug}")
                nom_p = input(f"Ingrese perfil a evaluar [Enter para {p_sug}]: ").strip() or p_sug
                if "6x6x3-16" in nom_p: nom_p = "HSS6x6x3/16"
                elif "10x6x3-16" in nom_p: nom_p = "HSS10x6x3/16"
                elif "4x4x3-16" in nom_p: nom_p = "HSS4x4x3/16"
                elif "4x2x3-16" in nom_p: nom_p = "HSS4x2x3/16"

                p = get_profile(nom_p)
                if not p:
                    print(f"❌ Perfil {nom_p} no encontrado.")
                    continue

                res = designer.check_combined_si(
                    profile=p, Pu_kN=pu, Mux_kNm=mux, Muy_kNm=muy,
                    Vux_kN=0.0, Vuy_kN=vu, L_m=l_m, Kx=k_val, Ky=k_val
                )
                print("\n" + explicar_resultado_paso_a_paso(res, sistema="si"))

            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "2":
            try:
                nom_p = input("\nIngrese nombre del perfil (ej. HSS6x6x3/16, HSS10x6x1/4): ").strip()
                p = get_profile(nom_p)
                if not p:
                    print(f"❌ Perfil '{nom_p}' no encontrado.")
                    continue

                pu = float(input("Carga Axial Pu [kN, (+) compresión]: ").replace(",", "."))
                mux = float(input("Momento Eje Fuerte Mux [kN·m]: ").replace(",", "."))
                muy = float(input("Momento Eje Débil Muy [kN·m]: ").replace(",", "."))
                vu = float(input("Cortante Vu [kN]: ").replace(",", "."))
                l_m = float(input("Longitud L [m]: ").replace(",", "."))
                k_val = float(input("Factor K [ej. 1.0 simple, 1.85 no arriostrado]: ") or "1.0")

                res = designer.check_combined_si(
                    profile=p, Pu_kN=pu, Mux_kNm=mux, Muy_kNm=muy,
                    Vux_kN=0.0, Vuy_kN=vu, L_m=l_m, Kx=k_val, Ky=k_val
                )
                print("\n" + explicar_resultado_paso_a_paso(res, sistema="si"))
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "3":
            try:
                pu = float(input("\nCarga Axial Pu [kN]: ").replace(",", "."))
                mux = float(input("Momento Mux [kN·m]: ").replace(",", "."))
                muy = float(input("Momento Muy [kN·m]: ").replace(",", "."))
                vu = float(input("Cortante Vu [kN]: ").replace(",", "."))
                l_m = float(input("Longitud L [m]: ").replace(",", "."))
                k_val = float(input("Factor K [por defecto 1.5]: ") or "1.5")

                optimos = designer.find_optimal_profiles_si(
                    Pu_kN=pu, Mux_kNm=mux, Muy_kNm=muy, Vux_kN=0.0, Vuy_kN=vu,
                    L_m=l_m, Kx=k_val, Ky=k_val, max_dcr=0.95
                )
                if not optimos:
                    print("❌ No se encontraron perfiles que soporten las cargas.")
                    continue

                print("\n" + "=" * 80)
                print(f"{'RANK':<5} | {'PERFIL HSS':<16} | {'PESO (kg/m)':<12} | {'DCR':<8} | {'UTILIZACIÓN':<12} | {'MODO GOBERNANTE'}")
                print("=" * 80)
                for i, r in enumerate(optimos[:10], start=1):
                    marca = " ⭐ [ÓPTIMO]" if i == 1 else ""
                    print(f"{i:<5} | {r.profile.name:<16} | {r.profile.weight_kg_m:<12.2f} | {r.dcr_max:<8.3f} | {r.dcr_max*100:<11.1f}% | {r.governing_mode}{marca}")
                print("=" * 80)
            except Exception as e:
                print(f"❌ Error: {e}")

        elif opc == "4":
            print("\nTemas pedagógicos:")
            for i, (k, inf) in enumerate(LECCIONES_DIDACTICAS.items(), start=1):
                print(f" [{i}] {inf['titulo']}")
            t_sel = input("Seleccione el tema [1-6]: ").strip()
            claves = list(LECCIONES_DIDACTICAS.keys())
            try:
                c_idx = int(t_sel) - 1
                print(LECCIONES_DIDACTICAS[claves[c_idx]]["contenido"])
            except Exception:
                print("Opción inválida.")

        elif opc == "5":
            break


def main():
    parser = argparse.ArgumentParser(description="Diseñador Didáctico de Perfiles HSS")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en modo consola interactiva (sin GUI)")
    args = parser.parse_args()

    if args.cli or not os.environ.get("DISPLAY"):
        modo_consola_interactivo()
    else:
        try:
            app = AppDisenoGUI()
            app.mainloop()
        except Exception as e:
            print(f"Aviso GUI: {e}. Pasando a modo consola.")
            modo_consola_interactivo()

if __name__ == "__main__":
    main()
