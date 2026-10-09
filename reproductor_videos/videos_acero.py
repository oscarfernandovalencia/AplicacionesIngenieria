#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
videos_acero.py
===============================================================================
REPRODUCTOR EDUCATIVO DE CLASES DE DISEÑO EN ACERO (MPV / YOUTUBE)
Con Interfaz Gráfica (GUI), selección de resolución/calidad y soporte CLI.
===============================================================================
"""

import os
import sys
import json
import subprocess
import threading
import tkinter as tk
from tkinter import ttk, messagebox
import customtkinter as ctk

RUTA_PREFERIDA_JSON = os.path.expanduser("~/scripts/videos_links_youtube.json")
RUTA_LOCAL_JSON = os.path.join(os.path.dirname(os.path.abspath(__file__)), "videos_links_youtube.json")

VIDEOS_INICIALES = [
    {
        "id": 1,
        "tema": "Fundamentos y Filosofías de Diseño",
        "titulo": "Diseño Estructural: ¿ASD vs LRFD?",
        "url": "http://www.youtube.com/watch?v=LZSi7QjktSI"
    },
    {
        "id": 2,
        "tema": "Columnas a Compresión",
        "titulo": "¿Cómo diseño una columna de acero en Compresión?",
        "url": "http://www.youtube.com/watch?v=_NzvuDjRLzo"
    },
    {
        "id": 3,
        "tema": "Compresión, Pandeo Local y Euler",
        "titulo": "Diseño de elementos a compresión - flexo compresión, Euler, pandeo local",
        "url": "http://www.youtube.com/watch?v=FyzB10b5JbY"
    },
    {
        "id": 4,
        "tema": "Vigas a Flexión y Cortante",
        "titulo": "Diseño de Viga de Acero a Flexión y Cortante",
        "url": "http://www.youtube.com/watch?v=rI4T0fT7vq0"
    },
    {
        "id": 5,
        "tema": "Vigas Metálicas Paso a Paso",
        "titulo": "Diseño de vigas metálicas a flexión, cortante y deflexión",
        "url": "http://www.youtube.com/watch?v=x5pSufgOK_o"
    },
    {
        "id": 6,
        "tema": "Conexiones y Uniones",
        "titulo": "Tensión: ¿Conexión Atornillada o Soldada?",
        "url": "http://www.youtube.com/watch?v=z0YUOLoAoXY"
    }
]

OPCIONES_CALIDAD = {
    "1080p (Full HD)": "bestvideo[height<=1080]+bestaudio/best[height<=1080]",
    "720p (HD)": "bestvideo[height<=720]+bestaudio/best[height<=720]",
    "480p (Estándar SD)": "bestvideo[height<=480]+bestaudio/best[height<=480]",
    "360p (Baja - Ahorro de Datos)": "bestvideo[height<=360]+bestaudio/best[height<=360]",
    "Máxima Calidad (Best)": "bestvideo+bestaudio/best",
    "Solo Audio (Podcast/Escucha)": "audio_only"
}


def obtener_ruta_json() -> str:
    if os.path.exists(RUTA_PREFERIDA_JSON):
        return RUTA_PREFERIDA_JSON
    if os.path.exists(RUTA_LOCAL_JSON):
        return RUTA_LOCAL_JSON
    return RUTA_PREFERIDA_JSON


def cargar_videos() -> list:
    ruta = obtener_ruta_json()
    if os.path.exists(ruta):
        try:
            with open(ruta, "r", encoding="utf-8") as f:
                return json.load(f)
        except Exception as e:
            print(f"Error al leer {ruta}: {e}")
    # Guardar lista inicial por defecto si no existía
    guardar_videos(VIDEOS_INICIALES, ruta)
    return VIDEOS_INICIALES


def guardar_videos(videos: list, ruta: str = None) -> bool:
    if not ruta:
        ruta = obtener_ruta_json()
    try:
        os.makedirs(os.path.dirname(ruta), exist_ok=True)
        with open(ruta, "w", encoding="utf-8") as f:
            json.dump(videos, f, indent=2, ensure_ascii=False)
        return True
    except Exception as e:
        # Fallback a local si no tiene permiso en ~/scripts
        try:
            with open(RUTA_LOCAL_JSON, "w", encoding="utf-8") as f:
                json.dump(videos, f, indent=2, ensure_ascii=False)
            return True
        except Exception as err:
            print(f"Error al guardar videos: {err}")
            return False


def reproducir_video(url: str, calidad_str: str = "720p (HD)"):
    formato = OPCIONES_CALIDAD.get(calidad_str, "bestvideo[height<=720]+bestaudio/best[height<=720]")
    cmd = ["mpv"]
    if formato == "audio_only":
        cmd.extend(["--no-video", url])
    else:
        cmd.extend([f"--ytdl-format={formato}", url])

    try:
        subprocess.run(cmd, check=False)
    except FileNotFoundError:
        print("Error: 'mpv' no está instalado en el sistema.")


# =============================================================================
# INTERFAZ GRÁFICA (CUSTOMTKINTER)
# =============================================================================
class VideosAceroGUI(ctk.CTk):
    def __init__(self):
        super().__init__()
        self.title("🎬 Videos de Estudio: Diseño de Estructuras de Acero")
        self.geometry("980x680")
        self.minsize(850, 550)
        ctk.set_appearance_mode("Dark")
        ctk.set_default_color_theme("blue")

        self.videos = cargar_videos()

        self._crear_encabezado()
        self._crear_cuerpo()
        self._poblar_tabla()

    def _crear_encabezado(self):
        header = ctk.CTkFrame(self, fg_color="#1E1E2E", corner_radius=10)
        header.pack(fill="x", padx=15, pady=(10, 5))

        top = ctk.CTkFrame(header, fg_color="transparent")
        top.pack(fill="x", padx=15, pady=8)

        ctk.CTkLabel(
            top,
            text="🎬 Reproductor de Clases: Estructuras Metálicas (MPV / YouTube)",
            font=ctk.CTkFont(size=18, weight="bold"),
            text_color="#89B4FA"
        ).pack(side="left")

        # Selector de calidad en encabezado
        ctrl = ctk.CTkFrame(header, fg_color="#181825", corner_radius=8)
        ctrl.pack(fill="x", padx=15, pady=(0, 10))

        ctk.CTkLabel(ctrl, text="📺 Calidad de Reproducción:", font=ctk.CTkFont(weight="bold"), text_color="#A6E3A1").pack(side="left", padx=10, pady=6)
        self.combo_calidad = ctk.CTkComboBox(
            ctrl,
            values=list(OPCIONES_CALIDAD.keys()),
            width=260
        )
        self.combo_calidad.pack(side="left", padx=5, pady=6)
        self.combo_calidad.set("720p (HD)")

        btn_play = ctk.CTkButton(
            ctrl,
            text="▶ REPRODUCIR VIDEO SELECCIONADO",
            font=ctk.CTkFont(weight="bold"),
            fg_color="#D84315",
            hover_color="#BF360C",
            command=self._reproducir_seleccionado
        )
        btn_play.pack(side="right", padx=10, pady=6)

    def _crear_cuerpo(self):
        body = ctk.CTkFrame(self)
        body.pack(fill="both", expand=True, padx=15, pady=8)

        # Barra de búsqueda y agregar
        bar_top = ctk.CTkFrame(body, fg_color="transparent")
        bar_top.pack(fill="x", padx=10, pady=5)

        ctk.CTkLabel(bar_top, text="Buscar:").pack(side="left", padx=5)
        self.entry_busqueda = ctk.CTkEntry(bar_top, placeholder_text="Filtrar por título o tema...", width=320)
        self.entry_busqueda.pack(side="left", padx=5)
        self.entry_busqueda.bind("<KeyRelease>", lambda e: self._filtrar_videos())

        btn_add = ctk.CTkButton(
            bar_top,
            text="➕ Agregar Nuevo Video",
            command=self._ventana_agregar_video
        )
        btn_add.pack(side="right", padx=5)

        # Tabla de videos
        cols = ["#", "Tema / Módulo", "Título del Video", "Enlace de YouTube"]
        f_tree = ctk.CTkFrame(body)
        f_tree.pack(fill="both", expand=True, padx=10, pady=5)

        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview", background="#181825", foreground="#CDD6F4", fieldbackground="#181825", rowheight=26)
        style.configure("Treeview.Heading", background="#313244", foreground="#89B4FA", font=("Arial", 10, "bold"))
        style.map("Treeview", background=[('selected', '#45475A')])

        self.tree = ttk.Treeview(f_tree, columns=cols, show="headings", selectmode="browse")
        self.tree.heading("#", text="#"); self.tree.column("#", width=40, anchor="center")
        self.tree.heading("Tema / Módulo", text="Tema / Módulo"); self.tree.column("Tema / Módulo", width=220, anchor="w")
        self.tree.heading("Título del Video", text="Título del Video"); self.tree.column("Título del Video", width=420, anchor="w")
        self.tree.heading("Enlace de YouTube", text="Enlace de YouTube"); self.tree.column("Enlace de YouTube", width=240, anchor="w")

        sb = ttk.Scrollbar(f_tree, orient="vertical", command=self.tree.yview)
        self.tree.configure(yscrollcommand=sb.set)
        self.tree.pack(side="left", fill="both", expand=True)
        sb.pack(side="right", fill="y")

        self.tree.bind("<Double-1>", lambda e: self._reproducir_seleccionado())

        # Pie con controles rápidos
        footer = ctk.CTkFrame(body, fg_color="#181825", corner_radius=6)
        footer.pack(fill="x", padx=10, pady=5)
        lbl_info = ctk.CTkLabel(
            footer,
            text="💡 Controles de MPV durante reproducción: [Espacio] Pausa | [q] Salir | [9 / 0] Volumen | [← / →] Retroceder/Avanzar 5 seg",
            font=ctk.CTkFont(size=11),
            text_color="#BAC2DE"
        )
        lbl_info.pack(padx=10, pady=5)

    def _poblar_tabla(self, lista_a_mostrar=None):
        self.tree.delete(*self.tree.get_children())
        items = lista_a_mostrar if lista_a_mostrar is not None else self.videos
        for v in items:
            self.tree.insert("", "end", values=[v.get("id", ""), v.get("tema", ""), v.get("titulo", ""), v.get("url", "")])

    def _filtrar_videos(self):
        q = self.entry_busqueda.get().strip().lower()
        if not q:
            self._poblar_tabla()
            return
        filtrados = [
            v for v in self.videos
            if q in v.get("titulo", "").lower() or q in v.get("tema", "").lower()
        ]
        self._poblar_tabla(filtrados)

    def _reproducir_seleccionado(self):
        sel = self.tree.selection()
        if not sel:
            messagebox.showwarning("Selección", "Por favor selecciona un video de la lista.")
            return
        valores = self.tree.item(sel[0], "values")
        url = valores[3]
        calidad = self.combo_calidad.get()

        # Ejecutar MPV en hilo secundario para no congelar la GUI
        threading.Thread(target=reproducir_video, args=(url, calidad), daemon=True).start()

    def _ventana_agregar_video(self):
        win = ctk.CTkToplevel(self)
        win.title("Agregar Video de YouTube")
        win.geometry("500x320")
        win.grab_set()

        ctk.CTkLabel(win, text="Título del Video:").pack(anchor="w", padx=20, pady=(15, 2))
        e_tit = ctk.CTkEntry(win, width=440)
        e_tit.pack(padx=20, pady=2)

        ctk.CTkLabel(win, text="Enlace de YouTube:").pack(anchor="w", padx=20, pady=(10, 2))
        e_url = ctk.CTkEntry(win, width=440)
        e_url.pack(padx=20, pady=2)

        ctk.CTkLabel(win, text="Tema o Módulo (Opcional):").pack(anchor="w", padx=20, pady=(10, 2))
        e_tem = ctk.CTkEntry(win, width=440)
        e_tem.pack(padx=20, pady=2)

        def guardar():
            url = e_url.get().strip()
            tit = e_tit.get().strip()
            tem = e_tem.get().strip() or "General"
            if not url:
                messagebox.showerror("Error", "El enlace no puede estar vacío.", parent=win)
                return
            nid = max([v.get("id", 0) for v in self.videos], default=0) + 1
            nuevo = {"id": nid, "tema": tem, "titulo": tit or "Sin título", "url": url}
            self.videos.append(nuevo)
            guardar_videos(self.videos)
            self._poblar_tabla()
            win.destroy()
            messagebox.showinfo("Guardado", "Video agregado exitosamente.")

        btn_save = ctk.CTkButton(win, text="💾 Guardar Video", fg_color="#2E7D32", hover_color="#1B5E20", command=guardar)
        btn_save.pack(pady=20)


# =============================================================================
# MODO CONSOLA
# =============================================================================
def modo_consola():
    videos = cargar_videos()
    while True:
        print("\n" + "=" * 70)
        print("   🎬 REPRODUCTOR DE CLASES: ESTRUCTURAS METÁLICAS (MPV / YOUTUBE)")
        print("=" * 70)
        for i, item in enumerate(videos, start=1):
            print(f" [{i}] [{item.get('tema', '')}] {item.get('titulo', 'Sin título')}")
        print("-" * 70)
        print(" [A] Agregar nuevo video | [S] Salir")
        print("-" * 70)
        opc = input("Selecciona un número de video o acción: ").strip().lower()

        if opc == "s":
            break
        elif opc == "a":
            tit = input("Título: ").strip()
            url = input("Link YouTube: ").strip()
            tem = input("Tema: ").strip() or "General"
            if url:
                nid = max([v.get("id", 0) for v in videos], default=0) + 1
                videos.append({"id": nid, "tema": tem, "titulo": tit, "url": url})
                guardar_videos(videos)
        else:
            try:
                num = int(opc)
                if 1 <= num <= len(videos):
                    v = videos[num - 1]
                    print("\nElija calidad:")
                    print(" 1. 1080p | 2. 720p (Defecto) | 3. 480p | 4. 360p | 5. Máxima | 6. Solo Audio")
                    c_opc = input("Opción [1-6, defecto 2]: ").strip() or "2"
                    m_cal = {
                        "1": "1080p (Full HD)", "2": "720p (HD)", "3": "480p (Estándar SD)",
                        "4": "360p (Baja - Ahorro de Datos)", "5": "Máxima Calidad (Best)", "6": "Solo Audio (Podcast/Escucha)"
                    }
                    cal = m_cal.get(c_opc, "720p (HD)")
                    print(f"Iniciando reproducción en {cal}...")
                    reproducir_video(v["url"], cal)
            except ValueError:
                print("Opción inválida.")


def main():
    import argparse
    parser = argparse.ArgumentParser(description="Reproductor de Videos de Diseño de Estructuras de Acero")
    parser.add_argument("--cli", action="store_true", help="Ejecutar en modo consola interactiva (sin GUI)")
    args = parser.parse_args()

    if args.cli or not os.environ.get("DISPLAY"):
        modo_consola()
    else:
        try:
            app = VideosAceroGUI()
            app.mainloop()
        except Exception as e:
            print(f"Aviso GUI: {e}. Pasando a consola.")
            modo_consola()

if __name__ == "__main__":
    main()
