#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
verificador_aisc.py
===============================================================================
Motor de diseño y verificación de perfiles tubulares estructurales HSS
(cuadrados SHS y rectangulares RHS) según AISC 360-16 y el texto guía de Jack C. McCormac
("Diseño de Estructuras de Acero").

Módulos de verificación técnica:
1. Tracción Axial (AISC 360 Cap. D / McCormac Cap. 3-4)
2. Compresión Axial y Pandeo Global/Local (AISC 360 Cap. E y Tabla B4.1a / McCormac Cap. 5-7)
3. Flexión en Ambos Ejes y Pandeo Lateral-Torsional LTB (AISC 360 Cap. F7 / McCormac Cap. 8-10)
4. Cortante en Ambos Ejes (AISC 360 Cap. G4 / McCormac Cap. 10)
5. Flexo-compresión / Fuerzas Combinadas (AISC 360 Cap. H1 - Ecs. H1-1a y H1-1b)
6. Prediseño de Placa Base sobre Pedestal de Concreto (AISC Design Guide 1 / McCormac Cap. 15)
7. Selección Automática de Perfiles Óptimos por Peso Mínimo
===============================================================================
"""

import math
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple, Any

try:
    from .catalogo_hss import HSSProfile, get_profile, list_all_profiles
except ImportError:
    from catalogo_hss import HSSProfile, get_profile, list_all_profiles


@dataclass
class DesignResult:
    profile: HSSProfile
    is_adequate: bool
    dcr_max: float          # Demanda / Capacidad máxima (<= 1.0 CUMPLE, > 1.0 FALLA)
    governing_mode: str     # Modo gobernante de falla
    details: Dict[str, Any]


class AISCHSSDesigner:
    """
    Diseñador estructural para secciones tubulares HSS según AISC 360-16 / McCormac.
    Opera en Sistema Internacional (kN, kN·m, m, MPa) o Imperial (kips, kip·in, in, ksi).
    """

    def __init__(self, Fy: float = 345.0, E: float = 200000.0, system: str = "si"):
        """
        :param Fy: Límite de fluencia del acero (MPa para SI, ksi para Imperial)
        :param E: Módulo de elasticidad del acero (MPa para SI, ksi para Imperial)
        :param system: "si" (métrico) o "imperial"
        """
        self.system = system.lower()
        if self.system in ["si", "metric", "internacional", "2"]:
            self.is_metric = True
            # Normalizar internamente a Imperial para emplear las fórmulas estándar AISC 360
            if Fy > 100:  # Viene en MPa (ej. 345 MPa para A500 Gr B/C, 250 MPa para A36)
                self.Fy_ksi = Fy / 6.89476
                self.E_ksi = E / 6.89476 if E > 50000 else 29000.0
            else:         # Viene en kN/cm²
                self.Fy_ksi = Fy * 1.45038
                self.E_ksi = E * 1.45038 if E > 5000 else 29000.0
        else:
            self.is_metric = False
            self.Fy_ksi = Fy
            self.E_ksi = E

        # Factores de resistencia LRFD según AISC 360
        self.phi_t_yield = 0.90   # Tensión fluencia bruta
        self.phi_t_rupt = 0.75    # Tensión ruptura neta
        self.phi_c = 0.90         # Compresión
        self.phi_b = 0.90         # Flexión
        self.phi_v = 0.90         # Cortante

    # =========================================================================
    # 1. TENSIÓN AXIAL (AISC 360 CAP. D)
    # =========================================================================
    def check_tension(self, profile: HSSProfile, Pu_kips: float, L_in: float, U: float = 0.85) -> Dict[str, Any]:
        """Verifica miembro a tensión axial considerando fluencia en área bruta y ruptura en área neta."""
        Pn_yield = self.Fy_ksi * profile.A_in2
        phi_Pn_yield = self.phi_t_yield * Pn_yield

        Fu_ksi = 1.30 * self.Fy_ksi
        Ae = profile.A_in2 * U
        Pn_rupt = Fu_ksi * Ae
        phi_Pn_rupt = self.phi_t_rupt * Pn_rupt

        phi_Pn = min(phi_Pn_yield, phi_Pn_rupt)
        r_min = min(profile.rx_in, profile.ry_in)
        slenderness = L_in / r_min if r_min > 0 else 0

        dcr = abs(Pu_kips) / phi_Pn if phi_Pn > 0 else 999.0
        return {
            "phi_Pn_kips": phi_Pn,
            "phi_Pn_kN": round(phi_Pn * 4.44822, 2),
            "dcr_tension": round(dcr, 4),
            "slenderness": round(slenderness, 2),
            "slenderness_limit": 300.0,
            "slenderness_ok": slenderness <= 300.0
        }

    # =========================================================================
    # 2. COMPRESIÓN AXIAL Y PANDEO (AISC 360 CAP. E / McCORMAC CAP. 5-7)
    # =========================================================================
    def check_compression(self, profile: HSSProfile, Pu_kips: float,
                          Lx_in: float, Ly_in: float,
                          Kx: float = 1.0, Ky: float = 1.0) -> Dict[str, Any]:
        """
        Verifica miembro a compresión axial considerando:
        - Esbeltez global KL/r
        - Esbeltez local b/t y h/t (Tabla B4.1a) y factor de reducción Q (AISC E7)
        - Esfuerzo de Euler Fe y Esfuerzo Crítico Fcr (inelástico vs elástico)
        """
        KL_rx = (Kx * Lx_in) / profile.rx_in if profile.rx_in > 0 else 0
        KL_ry = (Ky * Ly_in) / profile.ry_in if profile.ry_in > 0 else 0
        KL_r = max(KL_rx, KL_ry)

        # Límite de esbeltez local para paredes de tubo cuadrado/rectangular (Tabla B4.1a)
        limit_local = 1.40 * math.sqrt(self.E_ksi / self.Fy_ksi)
        is_flange_slender = profile.b_t > limit_local
        is_web_slender = profile.h_t > limit_local
        is_locally_slender = is_flange_slender or is_web_slender

        Q = 1.0
        if is_locally_slender:
            b_eff = min(1.0, limit_local / max(profile.b_t, 0.001))
            h_eff = min(1.0, limit_local / max(profile.h_t, 0.001))
            Q = min(b_eff, h_eff)

        # Esfuerzo de Euler Fe
        Fe = (math.pi ** 2 * self.E_ksi) / (KL_r ** 2) if KL_r > 0 else 1e6

        # Límite de transición elástica/inelástica: 4.71 * sqrt(E / (Q*Fy))
        limit_inelastic = 4.71 * math.sqrt(self.E_ksi / (Q * self.Fy_ksi))
        relacion_esfuerzos = (Q * self.Fy_ksi) / Fe

        if KL_r <= limit_inelastic and relacion_esfuerzos <= 2.25:
            Fcr = Q * (0.658 ** relacion_esfuerzos) * self.Fy_ksi
            regime = "Inelástico (Pandeo con Plastificación Parcial)"
        else:
            Fcr = 0.877 * Fe
            regime = "Elástico (Pandeo Global de Euler)"

        Pn = Fcr * profile.A_in2
        phi_Pn = self.phi_c * Pn
        dcr = abs(Pu_kips) / phi_Pn if phi_Pn > 0 else 999.0

        return {
            "KL_r": round(KL_r, 2),
            "KL_rx": round(KL_rx, 2),
            "KL_ry": round(KL_ry, 2),
            "Fe_ksi": round(Fe, 2),
            "Fe_MPa": round(Fe * 6.89476, 1),
            "Fcr_ksi": round(Fcr, 2),
            "Fcr_MPa": round(Fcr * 6.89476, 1),
            "regime": regime,
            "Q": round(Q, 3),
            "limit_local": round(limit_local, 2),
            "is_locally_slender": is_locally_slender,
            "Pn_kips": round(Pn, 2),
            "phi_Pn_kips": round(phi_Pn, 2),
            "phi_Pn_kN": round(phi_Pn * 4.44822, 2),
            "dcr_compression": round(dcr, 4),
            "slenderness_ok": KL_r <= 200.0
        }

    # =========================================================================
    # 3. FLEXIÓN Y PANDEO LATERAL-TORSIONAL LTB (AISC 360 CAP. F7)
    # =========================================================================
    def check_flexure(self, profile: HSSProfile, Mux_kip_in: float, Muy_kip_in: float = 0.0,
                      Lb_in: float = 0.0, Cb: float = 1.0) -> Dict[str, Any]:
        """
        Verifica capacidad a flexión según AISC 360 Sección F7 para HSS rectangulares y cuadrados.
        Evalúa Momento Plástico Mp, Pandeo Local del Patín (FLB) y Pandeo Lateral-Torsional (LTB).
        """
        Mpx = self.Fy_ksi * profile.Zx_in3
        Myx = self.Fy_ksi * profile.Sx_in3

        lambda_b = profile.b_t
        lambda_p = 1.12 * math.sqrt(self.E_ksi / self.Fy_ksi)
        lambda_r = 1.40 * math.sqrt(self.E_ksi / self.Fy_ksi)

        if lambda_b <= lambda_p:
            Mn_flb_x = Mpx
            estado_patin = "Compacto (Alcanza Mp)"
        elif lambda_b <= lambda_r:
            Mn_flb_x = Mpx - (Mpx - Myx) * ((lambda_b - lambda_p) / (lambda_r - lambda_p))
            estado_patin = "No Compacto (Inelástico)"
        else:
            be = 1.92 * profile.t_des * math.sqrt(self.E_ksi / self.Fy_ksi) * (1.0 - 0.38 / lambda_b * math.sqrt(self.E_ksi / self.Fy_ksi))
            Mn_flb_x = self.Fy_ksi * profile.Sx_in3 * (be / max(profile.B - 3 * profile.t_des, 0.1))
            estado_patin = "Esbelto (Pandeo Local Previo)"

        # Pandeo lateral-torsional (LTB): no aplica en cuadrados SHS
        is_sq = profile.is_square
        if is_sq:
            Mn_ltb_x = Mpx
            Lp, Lr = 1e6, 1e6
            ltb_status = "No aplica LTB (Tubo Cuadrado de Alta Rigidez Torsional)"
        else:
            sqrt_JA = math.sqrt(profile.J_in4 * profile.A_in2)
            Lp = 0.13 * self.E_ksi * profile.ry_in * (sqrt_JA / Mpx) if Mpx > 0 else 1e6
            Lr = 2.0 * self.E_ksi * profile.ry_in * (sqrt_JA / (0.7 * self.Fy_ksi * profile.Sx_in3)) if profile.Sx_in3 > 0 else 1e6

            if Lb_in <= Lp:
                Mn_ltb_x = Mpx
                ltb_status = f"Lb <= Lp ({Lb_in:.1f} <= {Lp:.1f} in) -> Sin LTB"
            elif Lb_in <= Lr:
                Mn_ltb_x = Cb * (Mpx - (Mpx - 0.7 * self.Fy_ksi * profile.Sx_in3) * ((Lb_in - Lp) / (Lr - Lp)))
                ltb_status = f"Lp < Lb <= Lr -> LTB Inelástico"
            else:
                Mn_ltb_x = 2.0 * self.E_ksi * Cb * (sqrt_JA / (Lb_in / profile.ry_in))
                ltb_status = f"Lb > Lr -> LTB Elástico"

        Mnx = min(Mpx, Mn_flb_x, Mn_ltb_x)
        phi_Mnx = self.phi_b * Mnx

        # Eje Débil
        Mpy = self.Fy_ksi * profile.Zy_in3
        phi_Mny = self.phi_b * Mpy

        dcr_x = abs(Mux_kip_in) / phi_Mnx if phi_Mnx > 0 else 999.0
        dcr_y = abs(Muy_kip_in) / phi_Mny if phi_Mny > 0 else 0.0

        return {
            "Mpx_kip_in": round(Mpx, 2),
            "Mnx_kip_in": round(Mnx, 2),
            "phi_Mnx_kip_in": round(phi_Mnx, 2),
            "phi_Mnx_kNm": round(phi_Mnx * 0.1129848, 2),
            "Mpy_kip_in": round(Mpy, 2),
            "phi_Mny_kip_in": round(phi_Mny, 2),
            "phi_Mny_kNm": round(phi_Mny * 0.1129848, 2),
            "estado_patin": estado_patin,
            "ltb_status": ltb_status,
            "Lp_in": round(Lp, 2),
            "Lr_in": round(Lr, 2),
            "dcr_flexure_x": round(dcr_x, 4),
            "dcr_flexure_y": round(dcr_y, 4)
        }

    # =========================================================================
    # 4. CORTANTE NOMINAL (AISC 360 CAP. G4)
    # =========================================================================
    def check_shear(self, profile: HSSProfile, Vux_kips: float = 0.0, Vuy_kips: float = 0.0) -> Dict[str, Any]:
        """Verifica resistencia a cortante en ambas direcciones considerando las dos almas del perfil HSS."""
        Avy = 2.0 * profile.H * profile.t_des
        Vny = 0.6 * self.Fy_ksi * Avy
        phi_Vny = self.phi_v * Vny

        Avx = 2.0 * profile.B * profile.t_des
        Vnx = 0.6 * self.Fy_ksi * Avx
        phi_Vnx = self.phi_v * Vnx

        dcr_vy = abs(Vuy_kips) / phi_Vny if phi_Vny > 0 else 0.0
        dcr_vx = abs(Vux_kips) / phi_Vnx if phi_Vnx > 0 else 0.0

        return {
            "phi_Vny_kips": round(phi_Vny, 2),
            "phi_Vny_kN": round(phi_Vny * 4.44822, 2),
            "phi_Vnx_kips": round(phi_Vnx, 2),
            "phi_Vnx_kN": round(phi_Vnx * 4.44822, 2),
            "dcr_shear_y": round(dcr_vy, 4),
            "dcr_shear_x": round(dcr_vx, 4),
            "dcr_shear_max": round(max(dcr_vy, dcr_vx), 4)
        }

    # =========================================================================
    # 5. FLEXO-COMPRESIÓN / INTERACCIÓN COMBINADA (AISC 360 CAP. H1)
    # =========================================================================
    def check_combined(self, profile: HSSProfile,
                       Pu_kips: float, Mux_kip_in: float, Muy_kip_in: float,
                       Vux_kips: float, Vuy_kips: float,
                       Lx_in: float, Ly_in: float,
                       Kx: float = 1.0, Ky: float = 1.0,
                       Lb_in: Optional[float] = None,
                       Cb: float = 1.0) -> DesignResult:
        """Evaluación rigurosa de interacción P-M bajo ecuaciones H1-1a y H1-1b de AISC."""
        if Lb_in is None:
            Lb_in = max(Lx_in, Ly_in)

        is_compression = Pu_kips >= 0
        if is_compression:
            comp_res = self.check_compression(profile, Pu_kips, Lx_in, Ly_in, Kx, Ky)
            Pc = comp_res["phi_Pn_kips"]
            slenderness_ok = comp_res["slenderness_ok"]
        else:
            tens_res = self.check_tension(profile, Pu_kips, max(Lx_in, Ly_in))
            Pc = tens_res["phi_Pn_kips"]
            slenderness_ok = tens_res["slenderness_ok"]
            comp_res = {}

        flex_res = self.check_flexure(profile, Mux_kip_in, Muy_kip_in, Lb_in, Cb)
        Mcx = flex_res["phi_Mnx_kip_in"]
        Mcy = flex_res["phi_Mny_kip_in"]

        shear_res = self.check_shear(profile, Vux_kips, Vuy_kips)

        Pr = abs(Pu_kips)
        Mrx = abs(Mux_kip_in)
        Mry = abs(Muy_kip_in)

        ratio_axial = Pr / Pc if Pc > 0 else 999.0
        ratio_mx = Mrx / Mcx if Mcx > 0 else 0.0
        ratio_my = Mry / Mcy if Mcy > 0 else 0.0

        if ratio_axial >= 0.2:
            dcr_pm = ratio_axial + (8.0 / 9.0) * (ratio_mx + ratio_my)
            formula_used = "H1-1a (Pr/Pc >= 0.20)"
            explicacion_formula = "Pr/Pc >= 0.2 -> Carga axial dominante. Se usa Pr/Pc + (8/9)*(Mrx/Mcx + Mry/Mcy) <= 1.0"
        else:
            dcr_pm = (ratio_axial / 2.0) + (ratio_mx + ratio_my)
            formula_used = "H1-1b (Pr/Pc < 0.20)"
            explicacion_formula = "Pr/Pc < 0.2 -> Momento flector dominante. Se reduce la penalización axial a la mitad: Pr/(2Pc) + (Mrx/Mcx + Mry/Mcy) <= 1.0"

        dcr_shear = shear_res["dcr_shear_max"]
        dcr_max = max(dcr_pm, dcr_shear)

        if dcr_shear > dcr_pm:
            gov_mode = "Cortante (Shear)"
        elif ratio_axial > 0.6 and (ratio_mx + ratio_my) < 0.2:
            gov_mode = "Compresión Axial Pura"
        elif (ratio_mx + ratio_my) > 0.6 and ratio_axial < 0.2:
            gov_mode = "Flexión Pura Dominante"
        else:
            gov_mode = f"Flexo-Compresión Combinada [{formula_used}]"

        is_adequate = (dcr_max <= 1.0) and slenderness_ok

        details = {
            "axial": comp_res if is_compression else tens_res,
            "flexure": flex_res,
            "shear": shear_res,
            "ratio_axial": round(ratio_axial, 4),
            "ratio_mx": round(ratio_mx, 4),
            "ratio_my": round(ratio_my, 4),
            "dcr_pm": round(dcr_pm, 4),
            "dcr_shear": round(dcr_shear, 4),
            "formula_used": formula_used,
            "explicacion_formula": explicacion_formula,
            "slenderness_ok": slenderness_ok
        }

        return DesignResult(
            profile=profile,
            is_adequate=is_adequate,
            dcr_max=round(dcr_max, 4),
            governing_mode=gov_mode,
            details=details
        )

    # =========================================================================
    # 6. ENTRADA EN SISTEMA INTERNACIONAL (MÉTRICO: kN, kNm, m, MPa)
    # =========================================================================
    def check_combined_si(self, profile: HSSProfile,
                          Pu_kN: float, Mux_kNm: float = 0.0, Muy_kNm: float = 0.0,
                          Vux_kN: float = 0.0, Vuy_kN: float = 0.0,
                          L_m: float = 3.0, Kx: float = 1.0, Ky: float = 1.0,
                          Lb_m: Optional[float] = None, Cb: float = 1.0) -> DesignResult:
        """Verificación AISC 360-16 / McCormac recibiendo variables en Sistema Internacional."""
        KN_TO_KIP = 0.22480894
        KNM_TO_KIPIN = 8.8507458
        M_TO_IN = 39.370079

        res = self.check_combined(
            profile=profile,
            Pu_kips=Pu_kN * KN_TO_KIP,
            Mux_kip_in=Mux_kNm * KNM_TO_KIPIN,
            Muy_kip_in=Muy_kNm * KNM_TO_KIPIN,
            Vux_kips=Vux_kN * KN_TO_KIP,
            Vuy_kips=Vuy_kN * KN_TO_KIP,
            Lx_in=L_m * M_TO_IN,
            Ly_in=L_m * M_TO_IN,
            Kx=Kx,
            Ky=Ky,
            Lb_in=(Lb_m * M_TO_IN) if Lb_m else (L_m * M_TO_IN),
            Cb=Cb
        )
        return res

    # =========================================================================
    # 7. OPTIMIZACIÓN Y BÚSQUEDA DEL PERFIL MÁS LIVIANO
    # =========================================================================
    def find_optimal_profiles_si(self,
                                 Pu_kN: float, Mux_kNm: float = 0.0, Muy_kNm: float = 0.0,
                                 Vux_kN: float = 0.0, Vuy_kN: float = 0.0,
                                 L_m: float = 3.0, Kx: float = 1.0, Ky: float = 1.0,
                                 Lb_m: Optional[float] = None,
                                 profile_type: str = "all",
                                 max_dcr: float = 0.95) -> List[DesignResult]:
        """
        Encuentra y clasifica todos los perfiles que soportan la carga, ordenados por menor peso propio (kg/m).
        """
        results: List[DesignResult] = []
        todos = list_all_profiles(sort_by_weight=True)

        for p in todos:
            is_sq = p.is_square
            if profile_type == "square" and not is_sq: continue
            if profile_type == "rectangular" and is_sq: continue

            res = self.check_combined_si(
                profile=p, Pu_kN=Pu_kN, Mux_kNm=Mux_kNm, Muy_kNm=Muy_kNm,
                Vux_kN=Vux_kN, Vuy_kN=Vuy_kN, L_m=L_m, Kx=Kx, Ky=Ky, Lb_m=Lb_m
            )
            if res.is_adequate and res.dcr_max <= max_dcr:
                results.append(res)

        results.sort(key=lambda r: (r.profile.weight_kg_m, r.dcr_max))
        return results

    # =========================================================================
    # 8. PREDISEÑO DE PLACA BASE SOBRE CONCRETO (McCORMAC CAP. 15)
    # =========================================================================
    def check_base_plate(self, Pu_kN: float, profile: HSSProfile,
                         fc_MPa: float = 21.0, Fy_plate_MPa: float = 250.0) -> Dict[str, Any]:
        """Calcula dimensiones (B x N) y espesor tp de la placa base según AISC Design Guide 1."""
        Pu_N = abs(Pu_kN) * 1000.0
        phi_c = 0.65
        phi_b = 0.90

        Fp_max = phi_c * 0.85 * fc_MPa
        A_req_mm2 = Pu_N / Fp_max if Fp_max > 0 else 0

        H_col_mm = profile.H_mm
        B_col_mm = profile.B_mm

        N_min_mm = H_col_mm + 100.0
        B_min_mm = B_col_mm + 100.0

        side = math.sqrt(max(A_req_mm2, N_min_mm * B_min_mm))
        N_mm = math.ceil(max(N_min_mm, side) / 25.0) * 25.0
        B_mm = math.ceil(max(B_min_mm, side) / 25.0) * 25.0
        A_final_mm2 = N_mm * B_mm

        fp = Pu_N / A_final_mm2 if A_final_mm2 > 0 else 0
        m = (N_mm - 0.95 * H_col_mm) / 2.0
        n = (B_mm - 0.95 * B_col_mm) / 2.0
        l_crit = max(m, n)

        tp_mm = l_crit * math.sqrt((2.0 * fp) / (phi_b * Fy_plate_MPa)) if fp > 0 else 6.35
        tp_comercial_mm = max(9.5, math.ceil(tp_mm / 3.175) * 3.175)

        return {
            "Pu_kN": Pu_kN,
            "B_mm": B_mm,
            "N_mm": N_mm,
            "Area_cm2": round(A_final_mm2 / 100.0, 1),
            "fp_MPa": round(fp, 2),
            "Fp_max_MPa": round(Fp_max, 2),
            "tp_calculado_mm": round(tp_mm, 2),
            "tp_comercial_mm": round(tp_comercial_mm, 2),
            "espesor_pulgadas": f"{round(tp_comercial_mm / 25.4 * 16)}/16\""
        }
