#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
tutor_didactico.py
===============================================================================
MÓDULO PEDAGÓGICO DE DISEÑO ESTRUCTURAL EN ACERO (AISC 360-16 / McCORMAC)
Explica paso a paso, de forma didáctica y comprensible para ingenieros y estudiantes:
- Qué significa cada función y variable en el diseño.
- Cómo diseñar columnas a compresión y pandeo.
- Cómo diseñar vigas a flexión y cortante.
- Por qué y cómo interactúan las fuerzas combinadas (flexo-compresión H1-1a / H1-1b).
- Por qué se elige el perfil de menor peso y cómo interpretar el DCR.
===============================================================================
"""

from typing import Dict, Any
try:
    from .verificador_aisc import DesignResult
except ImportError:
    from verificador_aisc import DesignResult


LECCIONES_DIDACTICAS: Dict[str, Dict[str, str]] = {
    "filosofia_lrfd": {
        "titulo": "1. Filosofía de Diseño LRFD (AISC / McCormac Cap. 1-2)",
        "contenido": """
================================================================================
  📘 LECCIÓN 1: ¿CÓMO FUNCIONA EL MÉTODO LRFD? (McCormac Cap. 1-2)
================================================================================
El método LRFD (Load and Resistance Factor Design / Diseño por Factores de Carga
y Resistencia) es el estándar moderno mundial y de la norma sismorresistente NSR-10.

• Principio fundamental de seguridad:
    DEMANDA MAYORADA (Ru) <= RESISTENCIA DE DISEÑO (phi * Rn)

1. FACTORES DE CARGA (gamma > 1.0):
   Mayoramos las cargas aplicadas para considerar incertidumbres:
   - Carga Muerta (D): 1.2D (o 1.4D pura)
   - Carga Viva de uso (L): 1.6L
   - Carga Sísmica (E): 1.0E
   - Carga de Viento (W): 1.6W (o 0.8W)
   Ejemplo de combinación crítica: Pu = 1.2D + 1.6L

2. FACTORES DE RESISTENCIA (phi < 1.0):
   Reducen la capacidad nominal calculada para proteger la vida ante variaciones del material:
   - Fluencia en Tensión: phi_t = 0.90
   - Ruptura neta:        phi_t = 0.75
   - Compresión Axial:    phi_c = 0.90
   - Flexión en Vigas:    phi_b = 0.90
   - Cortante en Almas:   phi_v = 0.90
   - Aplastamiento conc.: phi_c = 0.65

3. RATIO DEMANDA / CAPACIDAD (DCR):
   DCR = Demanda / Resistencia_de_Diseño
   - Si DCR <= 0.70: Perfil muy sobrado (seguro pero antieconómico).
   - Si 0.70 < DCR <= 0.95: Rango óptimo y eficiente de diseño.
   - Si 0.95 < DCR <= 1.00: Límite estricto de capacidad.
   - Si DCR > 1.00: FALLA ESTRUCTURAL (el perfil no resiste la carga).
"""
    },

    "compresion_euler": {
        "titulo": "2. Columnas a Compresión y Pandeo (AISC Cap. E / McCormac Cap. 5-7)",
        "contenido": """
================================================================================
  📘 LECCIÓN 2: ¿CÓMO SE DISEÑA UNA COLUMNA A COMPRESIÓN? (McCormac Cap. 5-7)
================================================================================
A diferencia de los miembros a tensión, una columna casi nunca falla por aplastamiento
del acero, sino por INESTABILIDAD (PANDEO). Antes de alcanzar el límite de fluencia (Fy),
la columna se dobla lateralmente de forma súbita.

PASO A: FACTOR DE LONGITUD EFECTIVA (K) Y ESBELTEZ GLOBAL (KL/r)
• K (Factor de longitud efectiva): Depende de las restricciones en los extremos.
  - K = 1.0: Apoyos articulados en ambos extremos.
  - K = 0.65 - 0.80: Extremos empotrados con arriostramiento lateral.
  - K = 1.50 - 1.85: Columnas de pórticos sin arriostrar (como en laderas y casas abiertas).
• r (Radio de giro) = sqrt(I / A): Representa la distribución del área respecto al eje.
  - A mayor radio de giro 'r', mayor resistencia al pandeo.
  - Los tubos HSS son ideales porque tienen un radio de giro 'r' casi idéntico en ambos ejes.
• Límite reglamentario: (KL/r) <= 200 para compresión.

PASO B: ESFUERZO CRÍTICO DE EULER (Fe)
Es la carga teórica ideal elástica a la cual la columna pierde estabilidad:
    Fe = (pi^2 * E) / (KL/r)^2
• E = 200,000 MPa (29,000 ksi) es el módulo de elasticidad del acero.
• Si la columna es muy larga (KL/r alto), Fe se vuelve muy pequeño.

PASO C: RÉGIMEN INELÁSTICO VS ELÁSTICO (Fcr)
AISC define la esbeltez límite de transición:
    Limite = 4.71 * sqrt(E / Fy)   (~113 para acero de 345 MPa)

1. Si KL/r <= 4.71 * sqrt(E / Fy)  --> PANDEO INELÁSTICO:
   La columna tiene imperfecciones y plastificación parcial antes de pandear:
       Fcr = [0.658^(Fy / Fe)] * Fy

2. Si KL/r > 4.71 * sqrt(E / Fy)   --> PANDEO ELÁSTICO (Euler):
   La columna es muy esbelta y pandea puramente en rango elástico:
       Fcr = 0.877 * Fe

PASO D: RESISTENCIA DE DISEÑO
    phi_c * Pn = 0.90 * Fcr * Ag
"""
    },

    "pandeo_local": {
        "titulo": "3. Pandeo Local en Perfiles Tubulares HSS (AISC Tabla B4.1a / McCormac Cap. 5)",
        "contenido": """
================================================================================
  📘 LECCIÓN 3: ¿QUÉ ES EL PANDEO LOCAL Y CÓMO AFECTA A LOS TUBOS HSS?
================================================================================
¿Alguna vez has pisado una lata de refresco vacía por los lados? Las paredes delgadas
se arrugan localmente antes de que la lata colapse verticalmente.
Eso mismo es el PANDEO LOCAL en un perfil estructural tubular.

• RELACIONES ANCHO / ESPESOR:
  - Patín comprimido: b/t  (ancho exterior menos radios de esquina dividido por el espesor)
  - Alma comprimida:  h/t  (altura exterior menos radios dividido por el espesor)

• LÍMITE DE ESBELTEZ LOCAL (AISC 360-16 Tabla B4.1a):
    lambda_r = 1.40 * sqrt(E / Fy)
    Para acero de 345 MPa (50 ksi): lambda_r = 1.40 * sqrt(200000 / 345) = 33.7

1. SECCIÓN NO ESBELTA (b/t <= 33.7):
   Las paredes son lo suficientemente gruesas. No habrá pandeo local prematuro.
   Factor de reducción: Q = 1.0 (aprovecha el 100% de la capacidad de la sección).

2. SECCIÓN ESBELTA (b/t > 33.7):
   Las paredes del tubo son muy delgadas. Se arrugan antes de alcanzar el pandeo global.
   AISC exige calcular un factor de reducción Q < 1.0 (Ecuaciones Cap. E7)
   reduciendo el área efectiva que realmente trabaja a compresión.
"""
    },

    "flexion_vigas": {
        "titulo": "4. Vigas a Flexión y Cortante (AISC Cap. F7 & G4 / McCormac Cap. 8-10)",
        "contenido": """
================================================================================
  📘 LECCIÓN 4: ¿CÓMO SE DISEÑA UNA VIGA METÁLICA HSS? (McCormac Cap. 8-10)
================================================================================
Las vigas soportan cargas perpendiculares a su eje longitudinal, lo que genera
MOMENTO FLECTOR (Mu) y FUERZA CORTANTE (Vu).

1. MÓDULO ELÁSTICO (S) VS MÓDULO PLÁSTICO (Z):
   - Módulo elástico S = I / c: Límite cuando la primera fibra exterior alcanza Fy.
   - Módulo plástico Z: Capacidad cuando TODA la sección rectangular se plastifica.
   - En perfiles tubulares, Z es entre un 15% y un 25% mayor que S.
   - Momento Plástico Nominal: Mp = Fy * Z

2. ¿QUÉ PASA CON EL PANDEO LATERAL-TORSIONAL (LTB)?
   En vigas en I (perfiles W), cuando el patín superior se comprime, tiende a doblarse
   hacia los lados y retorcer la viga (LTB).
   ¡GRAN VENTAJA DE LOS TUBOS HSS!:
   - En tubos cuadrados (SHS), su constante torsional 'J' es cientos de veces mayor
     que la de una viga en I. Por tanto, ¡NO SUFREN PANDEO LATERAL TORSIONAL!
     Mn = Mp siempre (mientras el patín sea compacto).
   - En tubos rectangulares (RHS), el LTB solo ocurre si la longitud no arriostrada Lb
     supera la longitud límite Lp = 0.13 * E * ry * sqrt(J*A) / Mp.

3. RESISTENCIA A CORTANTE (AISC Cap. G4):
   En una viga tubular hueca rectangular, existen DOS almas verticales paralelas:
       Área de cortante: Av = 2 * H * t_diseño
       Cortante nominal: Vn = 0.60 * Fy * Av
       Diseño LRFD:      phi_v * Vn = 0.90 * Vn
"""
    },

    "interaccion_flexocompresion": {
        "titulo": "5. Interacción Flexo-Compresión (AISC Cap. H1 / McCormac Cap. 11)",
        "contenido": """
================================================================================
  📘 LECCIÓN 5: INTERACCIÓN FLEXO-COMPRESIÓN (ECUACIONES H1-1a Y H1-1b)
================================================================================
En la vida real (y en especial en viviendas en ladera con sismo y viento), una columna
RARA VEZ trabaja a compresión pura.
Las cargas de sismo, viento y la excentricidad de las vigas generan MOMENTOS (Mux y Muy).

• EL EFECTO P-DELTA (AMPLIFICACIÓN):
  Cuando una columna tiene carga axial P y se deforma un delta por flexión, la carga P
  multiplica la deformación (P * delta), aumentando drásticamente el momento flector.
  Por eso no se pueden verificar el axial y el momento por separado.

• FÓRMULAS DE INTERACCIÓN DE AISC 360-16 (Capítulo H1):

CASO A: CARGA AXIAL ALTA (Pr / Pc >= 0.20) --> ECUACIÓN H1-1a
  Si la carga axial representa el 20% o más de la capacidad de la columna:
      [ Pr / Pc ] + (8/9) * [ (Mrx / Mcx) + (Mry / Mcy) ] <= 1.00

CASO B: CARGA AXIAL BAJA (Pr / Pc < 0.20) --> ECUACIÓN H1-1b
  Si los momentos son los que dominan y el axial es menor al 20%:
      [ Pr / (2 * Pc) ] + [ (Mrx / Mcx) + (Mry / Mcy) ] <= 1.00

Donde:
- Pr = Pu (Carga axial solicitante) | Pc = phi_c * Pn (Capacidad axial de diseño)
- Mrx, Mry = Momentos solicitantes  | Mcx, Mcy = phi_b * Mnx, phi_b * Mny (Capacidades a flexión)
"""
    },

    "placa_base": {
        "titulo": "6. Prediseño de Placa Base sobre Pedestal (McCormac Cap. 15)",
        "contenido": """
================================================================================
  📘 LECCIÓN 6: CÓMO SE DIMENSIONA LA PLACA BASE DE COLUMNA (McCormac Cap. 15)
================================================================================
La columna de acero transmite cargas concentradas de cientos de kilonewtons.
Si apoyáramos el tubo directamente sobre el pedestal de concreto, el concreto se
desmoronaría por aplastamiento (el acero resiste 345 MPa, pero el concreto solo ~21 MPa).

La PLACA BASE de acero cumple dos funciones:
1. Distribuir la carga vertical en una superficie mayor (Área B x N) para no aplastar el concreto.
2. Anclar la columna al pedestal mediante pernos de anclaje para resistir cortante y tracción.

PASO 1: ÁREA REQUERIDA DE LA PLACA
• Resistencia máxima del concreto al aplastamiento: Fp = 0.65 * 0.85 * f'c
• Área mínima: A_req = Pu / Fp

PASO 2: DIMENSIONES EN PLANTA (B x N)
Se colocan márgenes comerciales de 50 mm (2 pulgadas) por lado respecto a las caras del tubo
para poder alojar los pernos de anclaje y realizar la soldadura perimetral.

PASO 3: ESPESOR REQUERIDO DE LA PLACA (tp)
El voladizo de la placa entre la cara de la columna y el borde libre trabaja como
una viga en voladizo soportando la presión ascendente del concreto (fp):
    m = (N - 0.95*H) / 2
    n = (B - 0.95*B) / 2
    l_crit = max(m, n)
    tp = l_crit * sqrt( [2 * fp] / [0.90 * Fy_placa] )
"""
    }
}


def obtener_texto_leccion(clave: str) -> str:
    """Devuelve el texto explicativo de una lección pedagógica."""
    if clave in LECCIONES_DIDACTICAS:
        return LECCIONES_DIDACTICAS[clave]["contenido"]
    return "Lección no encontrada."


def explicar_resultado_paso_a_paso(res: DesignResult, sistema: str = "si") -> str:
    """
    Toma el resultado de un análisis de perfil y construye una narrativa didáctica
    paso a paso que explica al usuario por qué cumple o por qué falla.
    """
    p = res.profile
    det = res.details
    ax = det.get("axial", {})
    flx = det.get("flexure", {})
    shr = det.get("shear", {})

    dcr = res.dcr_max
    porcentaje = dcr * 100.0

    lineas = [
        "=" * 78,
        f"  📋 EXPLICACIÓN PASO A PASO DEL DISEÑO: {p.name}",
        "=" * 78,
        f"• Estado General: {'✔ PERFIL ADECUADO (CUMPLE)' if res.is_adequate else '❌ PERFIL SOBREESFORZADO (FALLA)'}",
        f"• Ratio DCR Máximo: {dcr:.4f} (Utilización del {porcentaje:.1f}% de la capacidad)",
        f"• Modo de Falla Gobernante: {res.governing_mode}",
        "-" * 78,
        "PASO 1: REVISIÓN DE GEOMETRÍA Y ESBELTEZ LOCAL (Tabla B4.1a):",
        f"  - Dimensiones del tubo: {p.H:.1f}\" x {p.B:.1f}\" x espesor {p.t_nom:.3f}\" (t_des = {p.t_des:.3f}\")",
        f"  - Relación patín b/t = {p.b_t:.1f} vs Límite = {ax.get('limit_local', 33.7):.1f}",
        f"  - Factor de reducción local Q = {ax.get('Q', 1.0)}",
        f"  -> Conclusión local: {'Sección compacta/no esbelta (sin pandeo local prematuro)' if not ax.get('is_locally_slender') else 'Sección esbelta: las paredes delgadas se arrugan (factor Q menor a 1.0)'}",
        "",
        "PASO 2: REVISIÓN DE COMPRESIÓN AXIAL Y PANDEO (Cap. E):",
        f"  - Esbeltez global calculada KL/r = {ax.get('KL_r', 0.0):.2f} (Límite normativo <= 200)",
        f"  - Esfuerzo de Euler Fe = {ax.get('Fe_MPa' if sistema=='si' else 'Fe_ksi', 0.0)} {'MPa' if sistema=='si' else 'ksi'}",
        f"  - Esfuerzo Crítico Fcr = {ax.get('Fcr_MPa' if sistema=='si' else 'Fcr_ksi', 0.0)} {'MPa' if sistema=='si' else 'ksi'}",
        f"  - Régimen de Pandeo: {ax.get('regime', 'N/A')}",
        f"  - Resistencia de Diseño Axial phi_c * Pn = {ax.get('phi_Pn_kN' if sistema=='si' else 'phi_Pn_kips', 0.0)} {'kN' if sistema=='si' else 'kips'}",
        f"  - Ratio Axial Pr/Pc = {det.get('ratio_axial', 0.0):.3f}",
        "",
        "PASO 3: REVISIÓN DE FLEXIÓN EN VIGAS / COLUMNAS (Cap. F7):",
        f"  - Momento nominal eje fuerte Mnx = {flx.get('phi_Mnx_kNm' if sistema=='si' else 'phi_Mnx_kip_in', 0.0)} {'kN·m' if sistema=='si' else 'kip·in'}",
        f"  - Estado de patín: {flx.get('estado_patin', 'Compacto')}",
        f"  - Estado LTB: {flx.get('ltb_status', 'No aplica')}",
        f"  - Ratio Momento Mrx/Mcx = {det.get('ratio_mx', 0.0):.3f}",
        "",
        "PASO 4: REVISIÓN DE CORTANTE EN LAS DOS ALMAS (Cap. G4):",
        f"  - Resistencia de Diseño a Cortante phi_v * Vn = {shr.get('phi_Vny_kN' if sistema=='si' else 'phi_Vny_kips', 0.0)} {'kN' if sistema=='si' else 'kips'}",
        f"  - Ratio Cortante = {shr.get('dcr_shear_max', 0.0):.3f}",
        "",
        "PASO 5: EVALUACIÓN DE INTERACCIÓN FLEXO-COMPRESIÓN (Cap. H1):",
        f"  - Fórmula aplicada: {det.get('formula_used', '')}",
        f"  - {det.get('explicacion_formula', '')}",
        f"  - DCR Combinado P-M = {det.get('dcr_pm', 0.0):.4f}",
        "-" * 78,
        "💡 DIAGNÓSTICO DIDÁCTICO Y RECOMENDACIÓN:"
    ]

    if res.is_adequate:
        if dcr < 0.65:
            lineas.append(
                f"  ✔ El perfil {p.name} resiste holgadamente (utilizado solo al {porcentaje:.1f}%). "
                f"Para ahorrar costos y peso de acero, podrías probar un perfil con menor espesor o menor área."
            )
        else:
            lineas.append(
                f"  ✔ ¡EXCELENTE SELECCIÓN! El perfil {p.name} trabaja en un rango óptimo de eficiencia ({porcentaje:.1f}%). "
                f"Aprovecha el material con seguridad sin sobredimensionar la estructura."
            )
    else:
        lineas.append(
            f"  ❌ El perfil {p.name} NO soporta las solicitaciones (sobrepasado al {porcentaje:.1f}%). "
            f"Modo causante: {res.governing_mode}. "
            f"Recomendación: selecciona un perfil con mayor momento de inercia o mayor espesor de pared (ej. 1/4\" o 5/16\")."
        )

    lineas.append("=" * 78)
    return "\n".join(lineas)
