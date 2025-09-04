# app.py
import io
import math
from dataclasses import dataclass
from typing import Dict, List, Tuple

import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt

# --- PDF (optionnel) ----------------------------------------------------------
REPORTLAB_AVAILABLE = True
try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
except Exception:
    REPORTLAB_AVAILABLE = False

# ------------------- Paramètres globaux & hypothèses --------------------------
FUEL_PRICE_GASOLINE = 695.0   # FCFA / litre (essence)
FUEL_PRICE_DIESEL   = 720.0   # FCFA / litre
ELECT_PRICE_KWH     = 109.0   # FCFA / kWh

# Facteurs d'émission
CO2_PER_L_GASOLINE = 2.31   # kgCO2/litre
CO2_PER_L_DIESEL   = 2.68   # kgCO2/litre
CO2_PER_KWH_GRID   = 0.12   # kgCO2/kWh (moyenne réseau)

# Fenêtre de délai : entre 10 et 15 minutes d'avance (inclus)
AHEAD_MIN_MIN = 10
AHEAD_MAX_MIN = 15

# Cartographie des marchandises → recommandations
CARGO_MAP = {
    "Fragile":        {"avoid": ["Moto électrique", "Tricycle électrique"], "prefer": ["Électrique", "Hybride", "Diesel", "Camion électrique"]},
    "Périssable":     {"avoid": [], "prefer": ["Électrique", "Hybride", "Diesel"]},  # priorité à la vitesse/disponibilité
    "Dangereux":      {"avoid": ["Moto électrique", "Tricycle électrique"], "prefer": ["Diesel", "Camion électrique"]},
    "Standard":       {"avoid": [], "prefer": []},
    "Volumineux":     {"avoid": ["Moto électrique", "Tricycle électrique", "Électrique"], "prefer": ["Camion électrique", "Diesel"]},
    "Léger/urgent":   {"avoid": ["Camion électrique"], "prefer": ["Moto électrique", "Électrique", "Hybride", "Tricycle électrique"]},
}

@dataclass
class Vehicle:
    name: str
    kind: str                # type: "moto", "voiture", "camion", "tricycle"
    motor: str               # "Essence", "Diesel", "Électrique", "Hybride"
    capacity_kg: float
    volume_m3: float
    autonomy_km: float
    speed_urban: float       # km/h
    speed_highway: float     # km/h
    maint_fcfa_km: float
    # conso
    l_per_100km: float = 0.0
    kwh_per_km: float = 0.0

def catalog() -> Dict[str, Vehicle]:
    return {
        # Thermiques / hybrides (voiture)
        "Diesel": Vehicle(
            name="Diesel", kind="voiture", motor="Diesel",
            capacity_kg=800, volume_m3=3.0, autonomy_km=800,
            speed_urban=35, speed_highway=100, maint_fcfa_km=45,
            l_per_100km=6.5
        ),
        "Hybride": Vehicle(
            name="Hybride", kind="voiture", motor="Essence/Électrique",
            capacity_kg=700, volume_m3=3.0, autonomy_km=900,
            speed_urban=40, speed_highway=105, maint_fcfa_km=40,
            l_per_100km=4.0
        ),
        # Voiture électrique
        "Électrique": Vehicle(
            name="Électrique", kind="voiture", motor="Électrique",
            capacity_kg=600, volume_m3=2.5, autonomy_km=350,
            speed_urban=38, speed_highway=110, maint_fcfa_km=25,
            kwh_per_km=0.18
        ),
        # Camion diesel (référence pour lourds)
        "Diesel camion": Vehicle(
            name="Diesel camion", kind="camion", motor="Diesel",
            capacity_kg=8000, volume_m3=35, autonomy_km=1000,
            speed_urban=30, speed_highway=85, maint_fcfa_km=120,
            l_per_100km=28.0
        ),
        # Camion électrique
        "Camion électrique": Vehicle(
            name="Camion électrique", kind="camion", motor="Électrique",
            capacity_kg=6000, volume_m3=30, autonomy_km=300,
            speed_urban=28, speed_highway=80, maint_fcfa_km=80,
            kwh_per_km=1.2
        ),
        # Moto & tricycle électriques (léger/last-mile)
        "Moto électrique": Vehicle(
            name="Moto électrique", kind="moto", motor="Électrique",
            capacity_kg=80, volume_m3=0.2, autonomy_km=120,
            speed_urban=45, speed_highway=70, maint_fcfa_km=10,
            kwh_per_km=0.04
        ),
        "Tricycle électrique": Vehicle(
            name="Tricycle électrique", kind="tricycle", motor="Électrique",
            capacity_kg=300, volume_m3=2.0, autonomy_km=140,
            speed_urban=35, speed_highway=60, maint_fcfa_km=18,
            kwh_per_km=0.08
        ),
    }

def avg_speed(v: Vehicle, road_type: str) -> float:
    if road_type == "Urbain":
        return v.speed_urban
    if road_type == "Autoroute":
        return v.speed_highway
    # Mixte
    return 0.5 * (v.speed_urban + v.speed_highway)

def fuel_cost_emissions(v: Vehicle, distance_km: float) -> Tuple[float, float]:
    """Retourne (coût_fcfa, emissions_kgCO2) hors maintenance."""
    if v.kwh_per_km > 0:
        kwh = v.kwh_per_km * distance_km
        return kwh * ELECT_PRICE_KWH, kwh * CO2_PER_KWH_GRID
    else:
        liters = (v.l_per_100km / 100.0) * distance_km
        if v.motor == "Diesel":
            return liters * FUEL_PRICE_DIESEL, liters * CO2_PER_L_DIESEL
        else:
            # Essence (hybride consomme surtout essence côté thermique)
            return liters * FUEL_PRICE_GASOLINE, liters * CO2_PER_L_GASOLINE

def autonomy_ok(v: Vehicle, distance_km: float, allow_refuel: bool, stop_minutes: float) -> Tuple[bool, float]:
    """Vérifie l'autonomie. Si recharges/refuels autorisés, ajoute du temps par arrêt."""
    if distance_km <= v.autonomy_km:
        return True, 0.0
    if not allow_refuel:
        return False, 0.0
    # nb d'arrêts nécessaires (arrondi haut)
    n_stops = math.ceil(distance_km / v.autonomy_km) - 1
    extra_h = max(0, n_stops) * (stop_minutes / 60.0)
    return True, extra_h

def within_deadline(time_h: float, deadline_h: float) -> bool:
    # doit être entre (deadline-15) et (deadline-10) minutes
    ahead_min_h = AHEAD_MIN_MIN / 60.0
    ahead_max_h = AHEAD_MAX_MIN / 60.0
    return (deadline_h - ahead_max_h) <= time_h <= (deadline_h - ahead_min_h)

def suitability_note(vname: str, cargo_type: str) -> str:
    pref = CARGO_MAP.get(cargo_type, {"avoid": [], "prefer": []})
    if vname in pref.get("avoid", []):
        return "⚠️ moins adapté"
    if pref.get("prefer") and vname in pref.get("prefer"):
        return "✅ adapté"
    return "—"

# ----------------------------- UI ---------------------------------------------
st.set_page_config(page_title="Assistant Logistique Intelligent", page_icon="🚚", layout="wide")
st.title("🚚 Assistant Intelligent d’Optimisation Logistique")
st.write("Compare **coût (FCFA)**, **délai**, **émissions**, contraintes **capacité** et **autonomie**, puis propose la meilleure solution. Export PDF inclus.")

with st.expander("🔧 Paramètres & pondérations (facultatif)"):
    colw1, colw2, colw3 = st.columns(3)
    with colw1:
        w_cost  = st.slider("Poids Coût", 0.0, 1.0, 0.40, 0.05)
    with colw2:
        w_time  = st.slider("Poids Temps", 0.0, 1.0, 0.35, 0.05)
    with colw3:
        w_emiss = st.slider("Poids Émissions", 0.0, 1.0, 0.25, 0.05)
    # normalisation simple
    s = w_cost + w_time + w_emiss
    if s == 0: w_cost, w_time, w_emiss = 0.34, 0.33, 0.33
    else: w_cost, w_time, w_emiss = w_cost/s, w_time/s, w_emiss/s

st.subheader("🧾 Données de la course")
c1, c2, c3 = st.columns(3)
with c1:
    distance_km = st.number_input("Distance (km)", min_value=1.0, value=120.0, step=1.0)
    cargo_weight = st.number_input("Poids marchandises (kg)", min_value=1.0, value=250.0, step=1.0)
with c2:
    cargo_volume = st.number_input("Volume marchandises (m³)", min_value=0.01, value=2.0, step=0.1, format="%.2f")
    cargo_type = st.selectbox("Nature des marchandises", list(CARGO_MAP.keys()), index=0)
with c3:
    road_type = st.selectbox("Type de route", ["Urbain", "Mixte", "Autoroute"], index=1)
    deadline_h = st.number_input("Délai max (heures, ex 4.0 = 4h)", min_value=0.5, value=4.0, step=0.25)

st.subheader("⛽ Recharges / Ravitaillages (si autonomie insuffisante)")
c4, c5 = st.columns(2)
with c4:
    allow_refuel = st.checkbox("Autoriser recharges / ravitaillements", value=True)
with c5:
    stop_minutes = st.slider("Durée par arrêt (minutes)", 5, 90, 30, 5)

st.subheader("🛠️ Maintenance (facultatif)")
maint_extra = st.number_input("Surcoût maintenance (+ FCFA/km)", min_value=0.0, value=0.0, step=1.0)

st.markdown("---")
run = st.button("🚀 Lancer la simulation")

if run:
    vehs = catalog()
    rows = []
    infeasible_reasons = {}

    for vname, v in vehs.items():
        # Capacité / volume
        if cargo_weight > v.capacity_kg or cargo_volume > v.volume_m3:
            infeasible_reasons[vname] = "Capacité/volume insuffisant"
            continue

        spd = avg_speed(v, road_type)
        base_time_h = distance_km / max(spd, 1e-6)

        # Autonomie
        ok_aut, extra_h = autonomy_ok(v, distance_km, allow_refuel, stop_minutes)
        if not ok_aut:
            infeasible_reasons[vname] = "Autonomie insuffisante"
            continue

        trip_time_h = base_time_h + extra_h

        # Délai
        if not within_deadline(trip_time_h, deadline_h):
            infeasible_reasons[vname] = "Hors fenêtre (doit arriver 10–15 min en avance)"
            continue

        # Coûts & émissions
        fuel_cost, emissions = fuel_cost_emissions(v, distance_km)
        maint_cost = (v.maint_fcfa_km + maint_extra) * distance_km
        total_cost = fuel_cost + maint_cost

        rows.append({
            "Motorisation": vname,
            "Type": v.kind,
            "Temps (h)": round(trip_time_h, 3),
            "Coût (FCFA)": round(total_cost, 2),
            "Émissions (kg)": round(emissions, 3),
            "Capacité ok": "Oui",
            "Autonomie ok": "Oui" if extra_h == 0 else f"Oui (+{stop_minutes} min x {int(math.ceil(distance_km/v.autonomy_km)-1)})",
            "Adéquation marchandise": suitability_note(vname, cargo_type),
        })

    if not rows:
        st.error("Aucune option ne respecte **en même temps** les contraintes (délai 10–15 min d’avance, capacité, autonomie).")
        if infeasible_reasons:
            st.write("**Raisons rencontrées :**")
            st.write(pd.DataFrame([{"Motorisation": k, "Problème": v} for k, v in infeasible_reasons.items()]))
        st.stop()

    df = pd.DataFrame(rows)

    # Résumés
    best_cost = df.loc[df["Coût (FCFA)"].idxmin()]
    best_time = df.loc[df["Temps (h)"].idxmin()]
    best_emis = df.loc[df["Émissions (kg)"].idxmin()]

    # Score global (min-max norm)
    norm_cost = (df["Coût (FCFA)"] - df["Coût (FCFA)"].min()) / (df["Coût (FCFA)"].ptp() + 1e-9)
    norm_time = (df["Temps (h)"] - df["Temps (h)"].min()) / (df["Temps (h)"].ptp() + 1e-9)
    norm_emis = (df["Émissions (kg)"] - df["Émissions (kg)"].min()) / (df["Émissions (kg)"].ptp() + 1e-9)
    df["Score global"] = (w_cost*norm_cost + w_time*norm_time + w_emiss*norm_emis)
    best_global = df.loc[df["Score global"].idxmin()]  # plus petit = meilleur

    # Meilleure "adaptée marchandise" : on favorise les "✅ adapté", sinon meilleur global
    adapted_df = df.copy()
    adapted_df["adapt_score"] = adapted_df["Adéquation marchandise"].map(
        {"✅ adapté": 0, "—": 1, "⚠️ moins adapté": 2}
    )
    best_adapted = adapted_df.sort_values(["adapt_score", "Score global"]).iloc[0]

    st.subheader("📊 Résultats comparatifs")
    st.dataframe(df.set_index("Motorisation"))

    # Graphiques
    fig1, ax1 = plt.subplots(figsize=(6,3))
    ax1.bar(df["Motorisation"], df["Coût (FCFA)"])
    ax1.set_ylabel("Coût (FCFA)")
    ax1.set_title("Coût par motorisation")
    plt.xticks(rotation=20)
    st.pyplot(fig1)

    fig2, ax2 = plt.subplots(figsize=(6,3))
    ax2.bar(df["Motorisation"], df["Temps (h)"])
    ax2.set_ylabel("Heures")
    ax2.set_title("Temps de trajet")
    plt.xticks(rotation=20)
    st.pyplot(fig2)

    fig3, ax3 = plt.subplots(figsize=(6,3))
    ax3.bar(df["Motorisation"], df["Émissions (kg)"])
    ax3.set_ylabel("kg CO₂")
    ax3.set_title("Émissions")
    plt.xticks(rotation=20)
    st.pyplot(fig3)

    st.subheader("🏆 Recommandations")
    cA, cB = st.columns(2)
    with cA:
        st.success(f"**Moins coûteuse** : {best_cost['Motorisation']} — {best_cost['Coût (FCFA)']:.0f} FCFA, {best_cost['Temps (h)']:.2f} h, {best_cost['Émissions (kg)']:.2f} kg CO₂.")
        st.info(f"**Plus rapide** : {best_time['Motorisation']} — {best_time['Temps (h)']:.2f} h, {best_time['Coût (FCFA)']:.0f} FCFA, {best_time['Émissions (kg)']:.2f} kg CO₂.")
        st.warning(f"**Moins polluante** : {best_emis['Motorisation']} — {best_emis['Émissions (kg)']:.2f} kg CO₂, {best_emis['Temps (h)']:.2f} h, {best_emis['Coût (FCFA)']:.0f} FCFA.")
    with cB:
        st.success(f"**Meilleure globale (pondérée)** : {best_global['Motorisation']} — score {best_global['Score global']:.3f}")
        st.info(f"**Plus adaptée aux marchandises** : {best_adapted['Motorisation']} — {best_adapted['Adéquation marchandise']}")

    # ------------------ Export PDF -------------------------------------------
    st.markdown("---")
    st.subheader("📄 Exporter un rapport PDF")

    if REPORTLAB_AVAILABLE:
        if st.button("🖨️ Générer le PDF"):
            # Sauvegarder graphiques en mémoire
            def fig_to_buf(fig):
                buf = io.BytesIO()
                fig.savefig(buf, format="png", bbox_inches="tight", dpi=200)
                buf.seek(0)
                return buf

            buf1 = fig_to_buf(fig1)
            buf2 = fig_to_buf(fig2)
            buf3 = fig_to_buf(fig3)

            pdf_bytes = io.BytesIO()
            doc = SimpleDocTemplate(pdf_bytes, pagesize=A4)
            styles = getSampleStyleSheet()
            styles.add(ParagraphStyle(name="H1", fontSize=16, leading=18, spaceAfter=8))
            styles.add(ParagraphStyle(name="H2", fontSize=13, leading=16, spaceAfter=6))
            flow: List = []

            flow.append(Paragraph("Assistant Logistique Intelligent – Rapport", styles["H1"]))
            flow.append(Paragraph(
                f"Distance : {distance_km:.1f} km — Route : {road_type} — Délai : {deadline_h:.2f} h (arrivée 10–15 min avant).",
                styles["Normal"]))
            flow.append(Paragraph(
                f"Marchandises : {cargo_type}, Poids {cargo_weight:.0f} kg, Volume {cargo_volume:.2f} m³.",
                styles["Normal"]))
            flow.append(Spacer(1, 8))

            # Tableau des résultats
            tbl_df = df[["Motorisation","Type","Temps (h)","Coût (FCFA)","Émissions (kg)","Adéquation marchandise"]]
            data = [tbl_df.columns.tolist()] + tbl_df.values.tolist()
            table = Table(data, hAlign="LEFT")
            table.setStyle(TableStyle([
                ("BACKGROUND",(0,0),(-1,0), colors.lightgrey),
                ("GRID",(0,0),(-1,-1), 0.25, colors.grey),
                ("ALIGN",(2,1),(-1,-1),"RIGHT"),
            ]))
            flow.append(Paragraph("Tableau comparatif", styles["H2"]))
            flow.append(table)
            flow.append(Spacer(1, 8))

            # Graphiques
            flow.append(Paragraph("Graphiques", styles["H2"]))
            flow.append(RLImage(buf1, width=450, height=220))
            flow.append(RLImage(buf2, width=450, height=220))
            flow.append(RLImage(buf3, width=450, height=220))
            flow.append(Spacer(1, 8))

            # Recommandations
            flow.append(Paragraph("Recommandations", styles["H2"]))
            rec_lines = [
                f"Moins coûteuse : {best_cost['Motorisation']} ({best_cost['Coût (FCFA)']:.0f} FCFA).",
                f"Plus rapide : {best_time['Motorisation']} ({best_time['Temps (h)']:.2f} h).",
                f"Moins polluante : {best_emis['Motorisation']} ({best_emis['Émissions (kg)']:.2f} kg CO₂).",
                f"Meilleure globale : {best_global['Motorisation']} (score {best_global['Score global']:.3f}).",
                f"Adaptée aux marchandises : {best_adapted['Motorisation']} ({best_adapted['Adéquation marchandise']}).",
            ]
            for line in rec_lines:
                flow.append(Paragraph(line, styles["Normal"]))

            doc.build(flow)
            pdf_bytes.seek(0)
            st.download_button(
                "📥 Télécharger le PDF",
                data=pdf_bytes.read(),
                file_name="rapport_logistique.pdf",
                mime="application/pdf"
            )
    else:
        st.info("Pour activer l’export PDF, ajoute **reportlab** dans `requirements.txt`, puis redeploie.")

    # ------------------ Notes & explications ---------------------------------
    with st.expander("ℹ️ Hypothèses & formules"):
        st.markdown("""
- **Prix énergie** : Essence 695 FCFA/L, Diesel 720 FCFA/L, Électricité 109 FCFA/kWh.  
- **Conso** (réglables dans le code) :  
  - Voiture Diesel 6.5 L/100km — Hybride 4.0 L/100km  
  - Voiture Électrique 0.18 kWh/km  
  - Camion Diesel 28 L/100km — Camion Électrique 1.2 kWh/km  
  - Moto Électrique 0.04 kWh/km — Tricycle Électrique 0.08 kWh/km  
- **Émissions** : 2.31 kgCO₂/L (essence), 2.68 kgCO₂/L (diesel), 0.12 kgCO₂/kWh (réseau).  
- **Délai** : l’arrivée doit être **entre 10 et 15 minutes avant** le délai saisi (4h ⇒ accepté si 3h45–3h50).  
- **Autonomie** : si activé, on ajoute **`stop_minutes`** par recharge/ravitaillement nécessaire.
- **Score global** : combinaison pondérée (min–max) de **coût**, **temps**, **émissions** (poids réglables).  
- **Adéquation marchandise** : pénalités/bonus selon la nature (fragile, périssable, etc.).
""")
