# 🏗️ Suite de Aplicaciones de Ingeniería Civil y Estructural

Suite modular e interactiva desarrollada en Python para análisis estructural, diseño en acero según norma AISC 360-16 / McCormac, y cálculo general de cantidades de obra y concreto.

---

## 🌟 Contenido y Arquitectura del Proyecto

El proyecto está organizado en **3 aplicaciones principales de ingeniería** coordinadas a través de un lanzador central (`main.py`), más una **herramienta multimedia independiente** para estudio de estructuras metálicas (`Videos_Acero.py`):

```
AplicacionesIngenieria/
├── main.py                     # Lanzador principal (GUI y CLI) para elegir y ejecutar las 3 apps
├── requirements.txt            # Dependencias del proyecto
├── .gitignore                   # Protección de temporales y entorno virtual
├── README.md                   # Documentación técnica completa
├── Videos_Acero.py             # Reproductor independiente con GUI y selección de resolución
│
├── app_fuerzas_casa/           # [APP 1] Análisis de Fuerzas en Casa de 2 Niveles en Ladera
│   ├── app_fuerzas.py          # Interfaz gráfica y consola para análisis FEA 3D
│   ├── motor_analisis.py       # Motor PyNite, combinaciones LRFD, sismo NSR-10 y viento
│   ├── exportador_fuerzas.py   # Exporta el paquete de fuerzas críticas para alimentar la App 2
│   ├── visualizador_3d.py      # Visor 3D en Matplotlib embebido y WebGL (Plotly)
│   └── NodosYCargasCopacabana.ods # Geometría, cargas y niveles de ladera
│
├── app_diseno_perfiles/        # [APP 2] Diseñador y Verificador Didáctico de Perfiles HSS
│   ├── app_diseno.py           # Interfaz gráfica y consola didáctica
│   ├── verificador_aisc.py     # Motor AISC 360-16 / McCormac LRFD (tensión, compresión, flexión, cortante, H1)
│   ├── tutor_didactico.py      # Módulo pedagógico: lecciones y explicación paso a paso de cada fórmula
│   ├── puente_fuerzas.py       # Carga directa de solicitaciones calculadas por la App 1
│   ├── catalogo_hss.py         # Catálogo completo de perfiles tubulares cuadrados y rectangulares
│   └── Propiedades Geometricas Perfiles HSS (AISC - Estructuras Metalicas).ods
│
├── app_cantidades_concreto/    # [APP 3] Calculadora General de Cantidades de Concreto y Mortero
│   ├── app_concreto.py         # Interfaz gráfica y consola para dosificaciones de obra
│   ├── concreto_core.py        # Motor de mezclas por volumen y elementos estructurales
│   └── tablas_referencia.py    # Tablas técnicas de varillas (#2 a #11) y dosificaciones
│
└── reproductor_videos/         # Módulo multimedia de apoyo académico
    └── videos_acero.py         # Reproductor MPV / YouTube con calidad configurable
```

---

## 🚀 Aplicaciones Principales

### 🏢 1. Cálculo de Fuerzas en Casa de 2 Niveles en Ladera (`app_fuerzas_casa`)
Diseñada específicamente para viviendas en ladera con dos niveles diferenciados:
- **Nivel 1 (Piso de Nivelación):** Columnas cimentadas sobre la pendiente topográfica con alturas variables (entre 0 y 8 m), experimentando efectos de columna corta y alta rigidez lateral.
- **Nivel 2 (Piso Habitable):** Columnas de altura constante y pórticos principales habitables.
- **Capacidades:**
  - Análisis por elementos finitos 3D en **PyNite** (Solver lineal y P-Delta de segundo orden).
  - Cargas gravitacionales, sismo (NSR-10 Título A por Fuerza Horizontal Equivalente) y viento (NSR-10 Título B).
  - Combinaciones LRFD completas y Envolvente Crítica (`ENV`).
  - **Exportación Automática:** Genera el archivo `solicitaciones_casa_para_diseno.json` con las solicitaciones críticas (Pu, Mux, Muy, Vu, L, K) para que la Aplicación 2 las reciba directamente.

### 📐 2. Diseñador y Verificador Didáctico de Perfiles HSS (`app_diseno_perfiles`)
Diseñado para que cualquier usuario entienda paso a paso **cómo se diseña una estructura de acero** según la norma **AISC 360-16** y el texto guía de Jack C. McCormac:
- **Flujo conectado:** Carga con un solo clic los valores calculados por la Aplicación 1 (`Columna Nivel 1`, `Columna Nivel 2`, `Viga Nivel 1`, `Viga Nivel 2`), o permite ingreso manual.
- **Enfoque Pedagógico:**
  - Explica qué es el esfuerzo de Euler ($F_e$), el régimen inelástico vs elástico ($F_{cr}$) y la esbeltez $KL/r$.
  - Evalúa el pandeo local ($b/t$, $h/t$) y el factor de reducción $Q$.
  - Explica la flexión plástica ($M_p = F_y \cdot Z$) y por qué los tubos HSS resisten torsión sin sufrir pandeo lateral-torsional (LTB).
  - Analiza la interacción flexo-compresión (Ecuaciones H1-1a y H1-1b) y traduce el ratio DCR a un porcentaje comprensible.
- **Optimizador Automático:** Encuentra entre todos los perfiles del catálogo aquellos que cumplen, clasificándolos por menor peso propio (kg/m) para máximo ahorro de acero.
- **Placas Base:** Predimensiona el área de apoyo contra el aplastamiento en concreto y el espesor comercial de la placa base metálica.

### 🧱 3. Calculadora General de Cantidades de Concreto y Mortero (`app_cantidades_concreto`)
Calculadora versátil para cualquier usuario u obra de construcción general (libre de particularidades regionales de vías):
- **Cálculo por Volumen Directo o Elementos Constructivos:** Losas de entrepiso, columnas rectangulares/cuadradas, columnas cilíndricas, vigas, zapatas aisladas y muros.
- **Dosificaciones Típicas:** 1:2:2 (alta resistencia ~28 MPa), 1:2:3 (estándar estructural ~21 MPa), 1:2:4 (pisos/andenes), 1:3:5 (solados y ciclópeo) o personalizada.
- **Unidades Prácticas de Obra:** Cemento (kg, bultos de 50 kg y 42.5 kg, latas), Arena y Grava (m³, latas de 5 galones, viajes de volqueta de 6 m³), Agua (litros, latas).
- **Morteros:** Proporciones 1:3, 1:4, 1:5, 1:6 para pañetes, revoques y pegas.
- **Acero de Refuerzo:** Consulta de varillas comerciales (#2 a #11) y estimación de kilos totales y número de barras de 6 m o 12 m.

---

## 🎬 Herramienta Independiente: Videos_Acero (`Videos_Acero.py`)
Script multimedia independiente para repasar clases audiovisuales de diseño estructural en acero:
- **Interfaz Gráfica Moderna:** Permite listar, filtrar y agregar nuevos videos de YouTube.
- **Selector de Calidad de Reproducción:** Permite elegir la resolución antes de abrir el video en `mpv`:
  - 1080p (Full HD)
  - 720p (HD)
  - 480p (SD)
  - 360p (Ahorro de datos)
  - Máxima calidad disponible
  - Solo audio (modo escucha/podcast)
- Se ejecuta directamente con:
  ```bash
  python Videos_Acero.py
  ```

---

## ⚙️ Instalación y Entorno Virtual

1. **Requisitos del Sistema:**
   - Linux (Arch Linux, Ubuntu, Debian, etc.) o cualquier sistema operativo con Python 3.10+.
   - `mpv` y `yt-dlp` instalados para la reproducción de video (`sudo pacman -S mpv yt-dlp` en Arch Linux).

2. **Crear Entorno Virtual e Instalar Dependencias:**
   ```bash
   # Crear entorno virtual local en esta carpeta
   python3 -m venv venv

   # Activar el entorno virtual
   source venv/bin/activate

   # Instalar dependencias requeridas
   pip install -r requirements.txt
   ```

---

## 🖥️ Modos de Ejecución

### Lanzador Principal (Recomendado)
Abre la interfaz gráfica central con las 3 aplicaciones:
```bash
./venv/bin/python main.py
```
*(O si no dispones de pantalla gráfica, puedes ejecutarlo en modo consola con `./venv/bin/python main.py --cli`).*

### Ejecución Directa de Cada Aplicación

- **App 1 (Fuerzas en Casa):**
  ```bash
  ./venv/bin/python app_fuerzas_casa/app_fuerzas.py
  ```
- **App 2 (Diseño Didáctico de Perfiles):**
  ```bash
  ./venv/bin/python app_diseno_perfiles/app_diseno.py
  ```
- **App 3 (Cantidades de Concreto):**
  ```bash
  ./venv/bin/python app_cantidades_concreto/app_concreto.py
  ```
- **Reproductor de Videos:**
  ```bash
  ./venv/bin/python Videos_Acero.py
  ```
