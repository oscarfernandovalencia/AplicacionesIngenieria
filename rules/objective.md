# Project Objective — `AplicacionesIngenieria`

> **Source of Truth**: Mirror of [`rules/objetivo.md`](file:///home/v1rr3eor/IAs/projects/AplicacionesIngenieria/rules/objetivo.md) (Spanish).

## 1. Strategic Purpose
This repository maintains a structured, modular suite of desktop and CLI engineering applications developed in Python to support structural analysis, member design, and construction material takeoffs.

## 2. Core Applications in Suite (`main.py`)
1. **App 1 (`app_fuerzas_casa/app_fuerzas.py`)**: 3D Finite Element Analysis (`PyNiteFEA`) of a 2-story hillside house (Level 1 topographic leveling columns $0\text{–}8\text{ m}$, Level 2 habitable story) under NSR-10 Title A seismic forces, wind loads, and LRFD combinations. Exports critical member demands ($P_u, M_{ux}, M_{uy}, V_u$).
2. **App 2 (`app_diseno_perfiles/app_diseno.py`)**: Didactic Structural Steel HSS Designer per AISC 360-16 / McCormac (Euler buckling $F_e$, local buckling $b/t$, $Q$, flexure $M_p = F_y Z$, shear, combined H1 interaction, and minimum weight optimizer).
3. **App 3 (`app_cantidades_concreto/app_concreto.py`)**: General Concrete, Mortar, and Structural Rebar (#2 to #11) Takeoff Calculator by volume or structural element (slabs, columns, beams, footings).

## 3. Operational Rules for AI Agents
- Preserve dual execution modes (CustomTkinter GUI + `--cli` interactive console mode).
- Use the shared virtual environment at `/home/v1rr3eor/IAs/projects/AplicacionesIngenieria/venv`.
- Enforce strict unit consistency and NSR-10 / AISC 360-16 mathematical transparency.
