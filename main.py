#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
main.py
===============================================================================
SUITE DE APLICACIONES DE INGENIERÍA ESTRUCTURAL Y CONSTRUCCIÓN
Lanzador principal que permite seleccionar y ejecutar las 3 aplicaciones clave:

1. 🏢 Aplicación 1: Análisis de Fuerzas en Casa de 2 Niveles en Ladera
   - Nivel 1: Nivelación del terreno en pendiente.
   - Nivel 2: Nivel habitable.
   - Análisis FEA 3D (PyNite), combinaciones LRFD, sismo NSR-10 y viento.
   - Genera y exporta el paquete de fuerzas críticas para el diseño de perfiles.

2. 📐 Aplicación 2: Diseñador Didáctico de Perfiles Metálicos HSS
   - Norma AISC 360-16 / Libro guía de McCormac.
   - Importa directamente las solicitaciones calculadas por la Aplicación 1.
   - Explicación didáctica paso a paso de cada fórmula (Euler, Pandeo Local, DCR).
   - Optimizador automático por peso propio mínimo.

3. 🧱 Aplicación 3: Calculadora General de Cantidades de Concreto y Mortero
   - Dosificación por volumen o por elementos constructivos (losas, columnas, vigas, zapatas).
   - Mezclas de concreto (1:2:2, 1:2:3, 1:2:4, 1:3:5) y morteros (1:3, 1:4, 1:5, 1:6).
   - Materiales en kg, bultos, latas, m³ y viajes.
   - Consulta de varillas de acero estructural (#2 a #11).
===============================================================================
"""

import os
import sys
import subprocess
import argparse
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

# Ruta base del proyecto
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
VENV_PYTHON = os.path.join(BASE_DIR, "venv", "bin", "python")
PYTHON_BIN = VENV_PYTHON if os.path.exists(VENV_PYTHON) else sys.executable


def ejecutar_subaplicacion(script_rel: str):
    """Lanza una aplicación en un proceso independiente utilizando el intérprete de Python del entorno."""
    ruta_script = os.path.join(BASE_DIR, script_rel)
    if not os.path.exists(ruta_script):
        print(f"Error: no se encontró el script en {ruta_script}")
        return

    cmd = [PYTHON_BIN, ruta_script]
    try:
        subprocess.Popen(cmd, cwd=BASE_DIR)
    except Exception as e:
        print(f"Error al iniciar aplicación {script_rel}: {e}")


# =============================================================================
# INTERFAZ GRÁFICA DEL LANZADOR (CUSTOMTKINTER)
# =============================================================================
class LauncherSuiteGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🏗️ Suite de Aplicaciones de Ingeniería Estructural y Construcción")
        self.geometry("980x720")
        self.minsize(850, 600)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self._crear_encabezado()
        self._crear_tarjetas_aplicaciones()
        self._crear_pie()

    def _crear_encabezado(self):
        header = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=12)
        header.pack(fill="x", padx=20, pady=(20, 10))

        lbl_tit = ctk.CTkLabel(
            header,
            text="🏗️ SUITE PRINCIPAL DE APLICACIONES DE INGENIERÍA",
            font=ctk.CTkFont(size=22, weight="bold"),
            text_color="#89B4FA"
        )
        lbl_tit.pack(pady=(15, 4))

        lbl_sub = ctk.CTkLabel(
            header,
            text="Selecciona una de las 3 aplicaciones especializadas para ejecutarla:",
            font=ctk.CTkFont(size=13),
            text_color="#BAC2DE"
        )
        lbl_sub.pack(pady=(0, 15))

    def _crear_tarjetas_aplicaciones(self):
        contenedor = ctk.CTkScrollableFrame(self, fg_color="transparent")
        contenedor.pack(fill="both", expand=True, padx=20, pady=5)

        # ---------------------------------------------------------------------
        # TARJETA 1: CASA 2 NIVELES (ANÁLISIS DE FUERZAS)
        # ---------------------------------------------------------------------
        card1 = ctk.CTkFrame(contenedor, fg_color="#181825", corner_radius=12, border_width=1, border_color="#313244")
        card1.pack(fill="x", pady=10)

        c1_top = ctk.CTkFrame(card1, fg_color="transparent")
        c1_top.pack(fill="x", padx=20, pady=(15, 5))

        lbl_c1_t = ctk.CTkLabel(
            c1_top,
            text="🏢 1. Cálculo de Fuerzas en Casa de 2 Niveles en Ladera",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#F9E2AF"
        )
        lbl_c1_t.pack(side="left")

        btn_run1 = ctk.CTkButton(
            c1_top,
            text="🚀 EJECUTAR APP 1",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#D84315",
            hover_color="#BF360C",
            width=160,
            height=36,
            command=lambda: ejecutar_subaplicacion("app_fuerzas_casa/app_fuerzas.py")
        )
        btn_run1.pack(side="right")

        desc1 = (
            "• Nivel 1: Nivelación topográfica del terreno en pendiente (columnas con longitudes entre 0 y 8 m).\n"
            "• Nivel 2: Nivel habitable superior con altura constante.\n"
            "• Análisis de elementos finitos 3D (PyNite FEA) con combinaciones LRFD, sismo NSR-10 Título A y viento.\n"
            "• Genera y exporta automáticamente las solicitaciones críticas (Pu, Mux, Muy, Vu) para alimentar la App 2."
        )
        ctk.CTkLabel(card1, text=desc1, justify="left", font=ctk.CTkFont(size=12), text_color="#CDD6F4").pack(anchor="w", padx=20, pady=(0, 15))

        # ---------------------------------------------------------------------
        # TARJETA 2: DISEÑO DIDÁCTICO DE PERFILES HSS
        # ---------------------------------------------------------------------
        card2 = ctk.CTkFrame(contenedor, fg_color="#181825", corner_radius=12, border_width=1, border_color="#313244")
        card2.pack(fill="x", pady=10)

        c2_top = ctk.CTkFrame(card2, fg_color="transparent")
        c2_top.pack(fill="x", padx=20, pady=(15, 5))

        lbl_c2_t = ctk.CTkLabel(
            c2_top,
            text="📐 2. Diseñador Didáctico de Perfiles HSS (AISC 360 / McCormac)",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#A6E3A1"
        )
        lbl_c2_t.pack(side="left")

        btn_run2 = ctk.CTkButton(
            c2_top,
            text="🚀 EJECUTAR APP 2",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#2E7D32",
            hover_color="#1B5E20",
            width=160,
            height=36,
            command=lambda: ejecutar_subaplicacion("app_diseno_perfiles/app_diseno.py")
        )
        btn_run2.pack(side="right")

        desc2 = (
            "• Carga con un solo clic los valores calculados por la Aplicación 1 o permite ingreso manual.\n"
            "• Enfoque 100% pedagógico: explica qué es cada función, fórmula y límite paso a paso.\n"
            "• Verificación de compresión, Euler (Fe), pandeo local (b/t, Q), flexión (Mp=Fy*Z), cortante y flexo-compresión (H1).\n"
            "• Buscador automático del perfil más liviano (kg/m) para optimizar costos y prediseño de placas base."
        )
        ctk.CTkLabel(card2, text=desc2, justify="left", font=ctk.CTkFont(size=12), text_color="#CDD6F4").pack(anchor="w", padx=20, pady=(0, 15))

        # ---------------------------------------------------------------------
        # TARJETA 3: CANTIDADES DE CONCRETO Y MORTERO
        # ---------------------------------------------------------------------
        card3 = ctk.CTkFrame(contenedor, fg_color="#181825", corner_radius=12, border_width=1, border_color="#313244")
        card3.pack(fill="x", pady=10)

        c3_top = ctk.CTkFrame(card3, fg_color="transparent")
        c3_top.pack(fill="x", padx=20, pady=(15, 5))

        lbl_c3_t = ctk.CTkLabel(
            c3_top,
            text="🧱 3. Calculadora General de Cantidades de Concreto y Mortero",
            font=ctk.CTkFont(size=17, weight="bold"),
            text_color="#89B4FA"
        )
        lbl_c3_t.pack(side="left")

        btn_run3 = ctk.CTkButton(
            c3_top,
            text="🚀 EJECUTAR APP 3",
            font=ctk.CTkFont(size=13, weight="bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1",
            width=160,
            height=36,
            command=lambda: ejecutar_subaplicacion("app_cantidades_concreto/app_concreto.py")
        )
        btn_run3.pack(side="right")

        desc3 = (
            "• Cálculo generalizado sin restricciones regionales de placa huella ni vías específicas.\n"
            "• Dosificación por volumen directo (m³) o por elementos: Losas, Columnas (rectangulares/circulares), Vigas y Zapatas.\n"
            "• Resultados en kg, bultos (50 y 42.5 kg), latas de 5 galones, m³ y viajes de volqueta de 6 m³.\n"
            "• Mezclas de mortero para revoques y mampostería, más tabla y cálculo de varillas de acero (#2 a #11)."
        )
        ctk.CTkLabel(card3, text=desc3, justify="left", font=ctk.CTkFont(size=12), text_color="#CDD6F4").pack(anchor="w", padx=20, pady=(0, 15))

    def _crear_pie(self):
        footer = ctk.CTkFrame(self, fg_color="#181825", corner_radius=8)
        footer.pack(fill="x", padx=20, pady=(5, 15))

        lbl_pie = ctk.CTkLabel(
            footer,
            text="💡 Tip de flujo de trabajo: Ejecuta la App 1 para obtener las solicitaciones de la casa -> Luego ejecuta la App 2 para diseñar y optimizar los perfiles.",
            font=ctk.CTkFont(size=11),
            text_color="#BAC2DE"
        )
        lbl_pie.pack(padx=15, pady=8)


# =============================================================================
# MODO CONSOLA INTERACTIVO (CLI)
# =============================================================================
def menu_consola():
    while True:
        print("\n" + "=" * 75)
        print("   🏗️  SUITE PRINCIPAL DE APLICACIONES DE INGENIERÍA")
        print("=" * 75)
        print(" 1. 🏢 Aplicación 1: Cálculo de Fuerzas en Casa de 2 Niveles (PyNite FEA)")
        print(" 2. 📐 Aplicación 2: Diseñador Didáctico de Perfiles HSS (AISC 360 / McCormac)")
        print(" 3. 🧱 Aplicación 3: Calculadora General de Concreto, Mortero y Materiales")
        print(" 4. 🚪 Salir")
        print("=" * 75)
        opc = input("Seleccione la aplicación a ejecutar [1-4]: ").strip()

        if opc == "1":
            print("\nIniciando Aplicación 1...")
            subprocess.run([PYTHON_BIN, os.path.join(BASE_DIR, "app_fuerzas_casa/app_fuerzas.py"), "--cli"])
        elif opc == "2":
            print("\nIniciando Aplicación 2...")
            subprocess.run([PYTHON_BIN, os.path.join(BASE_DIR, "app_diseno_perfiles/app_diseno.py"), "--cli"])
        elif opc == "3":
            print("\nIniciando Aplicación 3...")
            subprocess.run([PYTHON_BIN, os.path.join(BASE_DIR, "app_cantidades_concreto/app_concreto.py"), "--cli"])
        elif opc == "4":
            print("\n¡Éxitos en tus proyectos de ingeniería! Hasta pronto.")
            break
        else:
            print("Opción inválida. Intente de nuevo.")


def main():
    parser = argparse.ArgumentParser(description="Lanzador de Suite de Aplicaciones de Ingeniería")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en modo menú consola (sin GUI)")
    args = parser.parse_args()

    if args.cli or not os.environ.get("DISPLAY"):
        menu_consola()
    else:
        try:
            app = LauncherSuiteGUI()
            app.mainloop()
        except Exception as e:
            print(f"Aviso GUI: {e}. Iniciando en modo consola.")
            menu_consola()

if __name__ == "__main__":
    main()
