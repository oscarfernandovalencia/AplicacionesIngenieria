"""
Módulo didáctico de diseño y verificación de perfiles tubulares HSS (AISC 360-16 / McCormac).
"""
from .catalogo_hss import HSSProfile, get_profile, list_all_profiles
from .verificador_aisc import AISCHSSDesigner, DesignResult
from .tutor_didactico import LECCIONES_DIDACTICAS, obtener_texto_leccion, explicar_resultado_paso_a_paso
from .puente_fuerzas import obtener_elementos_disponibles, cargar_paquete_solicitaciones
