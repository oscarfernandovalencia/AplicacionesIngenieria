#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Videos_Acero.py
Script independiente para ver videos educativos de diseño de estructuras de acero
con Interfaz Gráfica (GUI) y selección de calidad de video (1080p, 720p, 480p, etc.).
"""

import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from reproductor_videos.videos_acero import main

if __name__ == "__main__":
    main()
