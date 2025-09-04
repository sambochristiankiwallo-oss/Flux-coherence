import streamlit as st
import pandas as pd
import numpy as np
import io
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4

# =========================
# CONFIG & EN-TÊTE
# =========================
st.set_page_config(page_title="Assistant Logistique Intelligent", page_icon="🚛", layout="wide")
st.title("🚛 Assistant Logistique Intelligent")
st.caption("Optimise le coût, le temps, les émissions et l’adéquation aux marchandises — avec contraintes de capacité et d’autonomie.")

# =========================
# PARAMÈTRES ÉNERGIE & ÉMISSIONS
# =========================
PRIX = {
    "Essence": 695.0,     # FCFA / L
    "Diesel": 720.0,      # FCFA / L
    "Electrique": 109.0,  # FCFA / kWh
}

# Consommations moyennes (par km)
CONSO = {
    "Essence": 0.07,       # L/km (7L/100km)
    "Diesel": 0.055,       # L/km (5.5L/100km)
    "Hybride": 0.045,      # L/km (4.5L/100km) -> carburant essence
    "Electrique": 0.18,    # kWh/km (18kWh/100km)
}

# Facteurs d’émission
EMISSION_FACTEUR = {
    "Essence": 2.31,      # kg CO2 / L
    "Diesel": 2.68,       # kg CO2 / L
    "Hybride": 2.31,      # kg CO2 / L (mix essence, conso réduite)
    "Electrique": 0.10,   # kg CO2 / kWh (mix réseau)
}

# Définition de véhicules types (vitesses, capacités, autonomie, maintenance)
VEHICULES = [
    {
        "Option": "Fourgon Diesel",
        "Motorisation": "Diesel",
        "Vitesse_km_h": 75,
        "Autonomie_km": 900,      # plein
        "Capacite_kg": 1200,
        "Capacite_m3": 12,
        "Maintenance_FCFA_km": 45.0
    },
    {
        "Option": "Utilitaire Hybride",
        "Motorisation": "Hybride",
        "Vitesse_km_h": 70,
        "Autonomie_km": 800,
        "Capacite_kg": 800,
        "Capacite_m3": 7,
        "Maintenance_FCFA_km": 35.0
    },
    {
        "Option": "Fourgonnette Essence",
        "Motorisation": "Essence",
        "Vitesse_km_h": 70,
        "Autonomie_km": 700,
        "Capacite_kg": 700,
        "Capacite_m3": 6,
        "Maintenance_FCFA_km": 40.0
    },
    {
        "Option": "Véhicule Électrique",
        "Motorisation": "Electrique",
        "Vitesse_km_h": 65,
        "Autonomie_km": 320,       # sans recharge en route (simplification)
        "Capacite_kg": 500,
        "Capacite_m3": 4,
        "Maintenance_FCFA_km": 20.0
    },
]

# =========================
# FONCTIONS DE CALCUL
# =========================
def cout_energie(distance_km, motorisation):
    if motorisation == "Hybride":
        # hybride utilise l’essence avec conso réduite
        return CONSO["Hybride"] * distance_km * PRIX["Essence"]
    elif motorisation in ("Essence", "Diesel"):
        return CONSO[motorisation] * distance_km * PRIX[motorisation]
    elif motorisation == "Electrique":
        return CONSO["Electrique"] * distance_km * PRIX["Electrique"]
    return float("inf")

def emissions(distance_km, motorisation):
    if motorisation == "Hybride":
        return CONSO["Hybride"] * distance_km * EMISSION_FACTEUR["Hybride"]
    elif motorisation in ("Essence", "Diesel"):
        return CONSO[motorisation] * distance_km * EMISSION_FACTEUR[motorisation]
    elif motorisation == "Electrique":
        return CONSO["Electrique"] * distance_km * EMISSION_FACTEUR["Electrique"]
    return float("inf")

def temps_trajet(distance_km, vitesse_km_h):
    return distance_km / max(vitesse_km_h, 1)

def suitability_goods(goods_type, motorisation):
    """
    Score d’adéquation aux marchandises (0 = très adapté, 1 = peu adapté).
    """
    # Par défaut neutre
    score = 0.5

    if goods_type == "Léger / Colis":
        # Urbain, silencieux, faible coût
        if motorisation in ("Electrique", "Hybride"):
            score = 0.0
        elif motorisation == "Essence":
            score = 0.5
        else:  # Diesel
            score = 0.7

    elif goods_type == "Lourd / Palettes":
        if motorisation == "Diesel":
            score = 0.0
        elif motorisation == "Hybride":
            score = 0.4
        elif motorisation == "Essence":
            score = 0.7
        else:  # Electrique
            score = 0.9

    elif goods_type == "Frais / Sensibles":
        # priorité ponctualité + fiabilité/autonomie
        if motorisation in ("Hybride", "Diesel"):
            score = 0.1
        elif motorisation == "Essence":
            score = 0.4
        else:  # Electrique (autonomie/temps recharge)
            score = 0.6

    elif goods_type == "Éco-responsable":
        if motorisation == "Electrique":
            score = 0.0
        elif motorisation == "Hybride":
            score = 0.3
        elif motorisation == "Essence":
            score = 0.7
        else:  # Diesel
            score = 0.9

    return score

def normaliser(col):
    # Min-max avec garde-fous
    cmin, cmax = np.min(col), np.max(col)
    if np.isclose(cmin, cmax):
        return np.zeros_like(col)
    return (col - cmin) / (cmax - cmin)

# =========================
# BARRE LATÉRALE — ENTRÉES
# =========================
with st.sidebar:
    st.header("⚙️ Paramètres")
    distance = st.number_input("Distance (km)", min_value=10, value=300, step=10)
    delai_max_h = st.number_input("Délai max (heures)", min_value=1.0, value=4.0, step=0.5)
    st.markdown("*La solution doit arriver **au moins 10 minutes** avant le délai.*")

    st.divider()
    st.subheader("📦 Marchandises")
    goods_type = st.selectbox(
        "Type de marchandise",
        ["Léger / Colis", "Lourd / Palettes", "Frais / Sensibles", "Éco-responsable"]
    )
    poids_kg = st.number_input("Poids total (kg)", min_value=1, value=400, step=10)
    volume_m3 = st.number_input("Volume total (m³)", min_value=1, value=3, step=1)

    st.divider()
    st.subheader("🎯 Stratégie d’optimisation")
    preset = st.selectbox("Choix rapide", ["Équilibre", "Économique", "Ponctualité", "Écologique", "Personnalisée"])

    if preset == "Équilibre":
        w_cost, w_time, w_emis, w_goods = 0.4, 0.3, 0.2, 0.1
    elif preset == "Économique":
        w_cost, w_time, w_emis, w_goods = 0.6, 0.2, 0.15, 0.05
    elif preset == "Ponctualité":
        w_cost, w_time, w_emis, w_goods = 0.2, 0.6, 0.1, 0.1
    elif preset == "Écologique":
        w_cost, w_time, w_emis, w_goods = 0.25, 0.15, 0.5, 0.1
    else:
        w_cost = st.slider("Poids coût", 0.0, 1.0, 0.4, 0.05)
        w_time = st.slider("Poids temps", 0.0, 1.0, 0.3, 0.05)
        w_emis = st.slider("Poids émissions", 0.0, 1.0, 0.2, 0.05)
        w_goods = st.slider("Poids adéquation marchandise", 0.0, 1.0, 0.1, 0.05)
        # normaliser la somme à 1
        s = w_cost + w_time + w_emis + w_goods
        if s > 0:
            w_cost, w_time, w_emis, w_goods = [x/s for x in (w_cost, w_time, w_emis, w_goods)]

    st.caption(f"Poids utilisés → Coût: {w_cost:.2f} | Temps: {w_time:.2f} | CO₂: {w_emis:.2f} | Marchandises: {w_goods:.2f}")

# =========================
# CALCUL DES SCÉNARIOS
# =========================
def calculer_scenarios():
    lignes = []
    marge_h = 10/60  # 10 minutes d'avance

    for v in VEHICULES:
        opt = v["Option"]; mot = v["Motorisation"]
        speed = v["Vitesse_km_h"]; autonomie = v["Autonomie_km"]
        cap_kg = v["Capacite_kg"]; cap_m3 = v["Capacite_m3"]; maint = v["Maintenance_FCFA_km"]

        # Contraintes de capacité
        if poids_kg > cap_kg or volume_m3 > cap_m3:
            continue

        # Autonomie : on exclut les VE si distance > autonomie (simplification)
        if mot == "Electrique" and distance > autonomie:
            continue

        t = temps_trajet(distance, speed)
        if t > max(delai_max_h - marge_h, 0):
            continue

        # Coûts & émissions
        c_energy = cout_energie(distance, mot)
        c_maint = maint * distance
        c_total = c_energy + c_maint
        co2 = emissions(distance, mot)

        # Adéquation marchandises
        goods_score = suitability_goods(goods_type, mot)

        lignes.append({
            "Option": opt,
            "Motorisation": mot,
            "Vitesse (km/h)": speed,
            "Temps (h)": round(t, 2),
            "Coût énergie (FCFA)": round(c_energy, 0),
            "Coût maintenance (FCFA)": round(c_maint, 0),
            "Coût total (FCFA)": round(c_total, 0),
            "Émissions CO₂ (kg)": round(co2, 2),
            "Capacité restante (kg)": cap_kg - poids_kg,
            "Volume restant (m³)": cap_m3 - volume_m3,
            "Score marchandises": goods_score
        })

    return pd.DataFrame(lignes)

df = calculer_scenarios()

# =========================
# AFFICHAGE TABLE + KPI
# =========================
if df.empty:
    st.error("Aucune option ne respecte en même temps les contraintes (délai -10min, capacité, autonomie). Essayez d’ajuster les paramètres.")
else:
    st.subheader("📊 Scénarios faisables")
    st.dataframe(df, use_container_width=True)

    # Sélections par critère
    idx_cost = df["Coût total (FCFA)"].idxmin()
    idx_time = df["Temps (h)"].idxmin()
    idx_emis = df["Émissions CO₂ (kg)"].idxmin()
    idx_goods = df["Score marchandises"].idxmin()

    best_cost = df.loc[idx_cost]
    best_time = df.loc[idx_time]
    best_emis = df.loc[idx_emis]
    best_goods = df.loc[idx_goods]

    # Score global (normalisation)
    df_scores = df.copy()
    df_scores["C_norm"] = normaliser(df_scores["Coût total (FCFA)"].to_numpy(dtype=float))
    df_scores["T_norm"] = normaliser(df_scores["Temps (h)"].to_numpy(dtype=float))
    df_scores["E_norm"] = normaliser(df_scores["Émissions CO₂ (kg)"].to_numpy(dtype=float))
    df_scores["G_norm"] = normaliser(df_scores["Score marchandises"].to_numpy(dtype=float))
    df_scores["Score global"] = (
        w_cost * df_scores["C_norm"] +
        w_time * df_scores["T_norm"] +
        w_emis * df_scores["E_norm"] +
        w_goods * df_scores["G_norm"]
    )
    idx_global = df_scores["Score global"].idxmin()
    best_global = df_scores.loc[idx_global]

    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("💰 Moins coûteuse", best_cost["Option"], f"{int(best_cost['Coût total (FCFA)'])} FCFA")
    c2.metric("⏱️ Plus rapide", best_time["Option"], f"{best_time['Temps (h)']} h")
    c3.metric("🌱 Moins polluante", best_emis["Option"], f"{best_emis['Émissions CO₂ (kg)']} kg")
    c4.metric("📦 Mieux adaptée", best_goods["Option"], goods_type)
    c5.metric("🏆 Recommandée", best_global["Option"], "Score global min")

    st.success(
        f"**Solution recommandée** : {best_global['Option']} "
        f"({best_global['Motorisation']}) — Coût: {int(best_global['Coût total (FCFA)'])} FCFA | "
        f"Temps: {best_global['Temps (h)']} h | "
        f"CO₂: {best_global['Émissions CO₂ (kg)']} kg"
    )

    # =========================
    # GRAPHIQUES (pour l’app & le PDF)
    # =========================
    def build_charts(dataframe):
        charts = []

        def save_fig(fig):
            buf = io.BytesIO()
            fig.savefig(buf, format="png", bbox_inches="tight")
            buf.seek(0)
            plt.close(fig)
            return buf

        # Coûts
        fig1, ax1 = plt.subplots()
        dataframe.plot(kind="bar", x="Option", y="Coût total (FCFA)", ax=ax1, legend=False)
        ax1.set_ylabel("FCFA"); ax1.set_title("Comparaison des coûts totaux")
        charts.append(save_fig(fig1))

        # Émissions
        fig2, ax2 = plt.subplots()
        dataframe.plot(kind="bar", x="Option", y="Émissions CO₂ (kg)", ax=ax2, legend=False)
        ax2.set_ylabel("kg CO₂"); ax2.set_title("Comparaison des émissions")
        charts.append(save_fig(fig2))

        # Temps
        fig3, ax3 = plt.subplots()
        dataframe.plot(kind="bar", x="Option", y="Temps (h)", ax=ax3, legend=False)
        ax3.set_ylabel("heures"); ax3.set_title("Comparaison des temps de trajet")
        charts.append(save_fig(fig3))

        # Score global
        fig4, ax4 = plt.subplots()
        dataframe2 = dataframe.merge(df_scores[["Option","Score global"]], on="Option")
        dataframe2.plot(kind="bar", x="Option", y="Score global", ax=ax4, legend=False)
        ax4.set_ylabel("Score (0 = meilleur)"); ax4.set_title("Score global pondéré")
        charts.append(save_fig(fig4))

        return charts

    st.divider()
    st.subheader("📈 Diagrammes comparatifs")
    charts_for_pdf = build_charts(df)

    # Affichage dans l’app
    for ch in charts_for_pdf:
        st.image(ch)

    # =========================
    # PDF AVEC TABLEAU + DIAGRAMMES
    # =========================
    def generate_pdf(dataframe, best_rows):
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=A4)
        styles = getSampleStyleSheet()
        story = []

        story.append(Paragraph("🚚 Rapport d’optimisation logistique", styles["Title"]))
        story.append(Spacer(1, 12))
        story.append(Paragraph(
            f"Distance : {distance} km — Délai maximum : {delai_max_h} h (marge d’arrivée de 10 min). "
            f"Marchandises : {goods_type} — Poids : {poids_kg} kg — Volume : {volume_m3} m³.",
            styles["Normal"]
        ))
        story.append(Spacer(1, 16))

        # Tableau comparatif
        headers = ["Option","Motorisation","Temps (h)","Coût total (FCFA)","Émissions CO₂ (kg)","Capacité restante (kg)","Volume restant (m³)"]
        table_data = [headers] + dataframe[headers].values.tolist()
        table = Table(table_data, colWidths=[120,80,70,90,90,90,90])
        table.setStyle(TableStyle([
            ("BACKGROUND",(0,0),(-1,0), colors.HexColor("#264653")),
            ("TEXTCOLOR",(0,0),(-1,0), colors.white),
            ("ALIGN",(0,0),(-1,-1), "CENTER"),
            ("GRID",(0,0),(-1,-1), 0.5, colors.grey),
            ("FONTSIZE",(0,0),(-1,-1), 8),
            ("BOTTOMPADDING",(0,0),(-1,0), 6),
        ]))
        story.append(table)
        story.append(Spacer(1, 16))

        # Graphiques
        story.append(Paragraph("Diagrammes comparatifs", styles["Heading2"]))
        story.append(Spacer(1, 8))
        for ch in charts_for_pdf:
            story.append(Image(ch, width=430, height=260))
            story.append(Spacer(1, 12))

        # Résumés
        story.append(Paragraph("Synthèse des meilleures options", styles["Heading2"]))
        story.append(Spacer(1, 8))
        br = best_rows
        synth = f"""
        <b>💰 Moins coûteuse :</b> {br['cost']['Option']} ({int(br['cost']['Coût total (FCFA)'])} FCFA)<br/>
        <b>⏱️ Plus rapide :</b> {br['time']['Option']} ({br['time']['Temps (h)']} h)<br/>
        <b>🌱 Moins polluante :</b> {br['emis']['Option']} ({br['emis']['Émissions CO₂ (kg)']} kg CO₂)<br/>
        <b>📦 Mieux adaptée :</b> {br['goods']['Option']} (type : {goods_type})<br/>
        <b>🏆 Recommandée :</b> {br['global']['Option']} (score global minimal)
        """
        story.append(Paragraph(synth, styles["Normal"]))

        doc.build(story)
        buffer.seek(0)
        return buffer

    best_rows = {
        "cost": best_cost,
        "time": best_time,
        "emis": best_emis,
        "goods": best_goods,
        "global": best_global
    }
    pdf_bytes = generate_pdf(df, best_rows)

    st.download_button(
        "📄 Télécharger le rapport PDF",
        data=pdf_bytes,
        file_name="rapport_logistique.pdf",
        mime="application/pdf"
    )
