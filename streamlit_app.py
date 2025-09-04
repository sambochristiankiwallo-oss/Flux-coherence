import streamlit as st
import pandas as pd
import numpy as np
import math
import matplotlib.pyplot as plt
from io import BytesIO

# PDF (reportlab - platypus)
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image as RLImage, PageBreak
)

# -------------------------------
# Haversine (distance entre 2 lat/lon en km)
# -------------------------------
def haversine(lat1, lon1, lat2, lon2):
    R = 6371.0
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    dphi = math.radians(lat2 - lat1)
    dlambda = math.radians(lon2 - lon1)
    a = math.sin(dphi/2)**2 + math.cos(phi1)*math.cos(phi2)*math.sin(dlambda/2)**2
    c = 2*math.atan2(math.sqrt(a), math.sqrt(1-a))
    return R*c

# -------------------------------
# Paramètres véhicules (coûts en FCFA, conso : essence/diesel en L/km, élec en kWh/km)
# -------------------------------
vehicles = {
    "Moto essence":        {"energie": "essence", "conso": 0.035, "co2": 0.08, "autonomie": 300, "capacite": 50,   "vitesse": 60, "prix": 695},
    "Moto électrique":     {"energie": "elec",    "conso": 0.025, "co2": 0.02, "autonomie": 120, "capacite": 40,   "vitesse": 65, "prix": 109},
    "Tricycle essence":    {"energie": "essence", "conso": 0.050, "co2": 0.12, "autonomie": 200, "capacite": 200,  "vitesse": 50, "prix": 695},
    "Tricycle électrique": {"energie": "elec",    "conso": 0.040, "co2": 0.03, "autonomie": 140, "capacite": 150,  "vitesse": 45, "prix": 109},
    "Voiture essence":     {"energie": "essence", "conso": 0.070, "co2": 0.18, "autonomie": 600, "capacite": 500,  "vitesse": 80, "prix": 695},
    "Voiture diesel":      {"energie": "diesel",  "conso": 0.060, "co2": 0.15, "autonomie": 800, "capacite": 600,  "vitesse": 80, "prix": 720},
    "Voiture hybride":     {"energie": "essence", "conso": 0.045, "co2": 0.09, "autonomie": 700, "capacite": 550,  "vitesse": 85, "prix": 695},
    "Voiture électrique":  {"energie": "elec",    "conso": 0.180, "co2": 0.05, "autonomie": 400, "capacite": 500,  "vitesse": 75, "prix": 109},
    "Camion diesel":       {"energie": "diesel",  "conso": 0.250, "co2": 0.70, "autonomie":1000, "capacite":10000, "vitesse": 70, "prix": 720},
    "Camion électrique":   {"energie": "elec",    "conso": 1.200, "co2": 0.20, "autonomie": 400, "capacite": 8000, "vitesse": 65, "prix": 109},
}

ADVANCE_HOURS = 0.25  # 15 minutes d'avance obligatoire

# -------------------------------
# UI
# -------------------------------
st.set_page_config(page_title="Assistant Logistique Intelligent", page_icon="🚚", layout="wide")
st.title("🚚 Assistant Intelligent d’Optimisation Logistique")
st.caption("Compare coût 💰, délai ⏱️, émissions 🌍 et génère un rapport PDF complet.")

with st.sidebar:
    st.header("⚙️ Paramètres")
    use_gps = st.checkbox("📍 Calculer la distance avec coordonnées (Haversine)")
    if use_gps:
        lat1 = st.number_input("Latitude départ", -90.0, 90.0, 5.354, format="%.6f")
        lon1 = st.number_input("Longitude départ", -180.0, 180.0, -4.001, format="%.6f")
        lat2 = st.number_input("Latitude arrivée", -90.0, 90.0, 5.400, format="%.6f")
        lon2 = st.number_input("Longitude arrivée", -180.0, 180.0, -3.980, format="%.6f")
        distance = haversine(lat1, lon1, lat2, lon2)
        st.info(f"🌍 Distance calculée : **{distance:.2f} km**")
    else:
        distance = st.number_input("Distance (km)", min_value=1.0, value=200.0, step=10.0)

    deadline = st.number_input("⏱️ Délai maximal (heures)", min_value=1.0, value=6.0, step=0.25)
    trafic = st.selectbox("🚦 Trafic", ["Faible", "Moyen", "Élevé"])
    route = st.selectbox("🛣️ Route", ["Urbain", "Mixte", "Difficile"])
    marchandise = st.selectbox("📦 Marchandise", ["Standard", "Périssable", "Dangereux"])
    poids = st.number_input("⚖️ Poids (kg)", min_value=1, value=500, step=10)

    st.subheader("🎛️ Pondérations (score global à minimiser)")
    w_cost = st.slider("Poids Coût", 0.0, 1.0, 0.40, 0.05)
    w_co2  = st.slider("Poids CO₂", 0.0, 1.0, 0.30, 0.05)
    w_time = st.slider("Poids Temps",0.0, 1.0, 0.30, 0.05)

    st.subheader("🚗 Véhicules à comparer")
    vehicle_filter = st.multiselect("Sélection", list(vehicles.keys()), default=list(vehicles.keys()))

lancer = st.button("🚀 Lancer la simulation")

# -------------------------------
# Helpers
# -------------------------------
def vitesse_effective(base, trafic):
    if trafic == "Faible": return base
    if trafic == "Moyen":  return base * 0.85
    return base * 0.70

def constraints_ok(row):
    # délai avec 15 min d'avance
    if row["Temps (h)"] > max(0.0, deadline - ADVANCE_HOURS):
        return False
    # périssable -> préférence temps court (exemple : <= 3h si possible)
    if marchandise == "Périssable" and row["Temps (h)"] > 3.0:
        return False
    # dangereux -> pas de moto/tricycle
    if marchandise == "Dangereux" and ("Moto" in row["Véhicule"] or "Tricycle" in row["Véhicule"]):
        return False
    return True

# -------------------------------
# Simulation
# -------------------------------
if lancer:
    results = []
    for name, v in vehicles.items():
        if name not in vehicle_filter:
            continue
        # capacité
        if poids > v["capacite"]:
            continue
        # autonomie (si définie)
        if v["autonomie"] is not None and distance > v["autonomie"]:
            continue

        # coût énergie
        conso = distance * v["conso"]         # L ou kWh
        cout = conso * v["prix"]              # FCFA
        co2  = conso * v["co2"]               # kg CO2 (facteur simplifié)
        # temps
        v_eff = max(5.0, vitesse_effective(v["vitesse"], trafic))
        temps = distance / v_eff

        results.append({
            "Véhicule": name,
            "Coût (FCFA)": round(cout, 2),
            "CO₂ (kg)": round(co2, 3),
            "Temps (h)": round(temps, 2),
        })

    if not results:
        st.warning("Aucune option ne satisfait les contraintes initiales (capacité/autonomie/filtre).")
    else:
        df = pd.DataFrame(results)

        # Appliquer contraintes « fines »
        df["Faisable"] = df.apply(constraints_ok, axis=1)
        dfF = df[df["Faisable"]].copy()

        st.subheader("📊 Résultats")
        st.dataframe(df.sort_values(["Faisable","Coût (FCFA)"], ascending=[False, True]), use_container_width=True)

        if dfF.empty:
            st.error("Aucune solution ne respecte le délai (avec 15 min d’avance) et les contraintes marchandise.")
        else:
            # Score global (à minimiser)
            # normalisation min-max par colonne pour comparabilité
            def norm(s):
                mn, mx = s.min(), s.max()
                if mx - mn < 1e-9: return pd.Series([0.5]*len(s), index=s.index)
                return (s - mn) / (mx - mn)

            dfF["_n_cost"] = norm(dfF["Coût (FCFA)"])
            dfF["_n_co2"]  = norm(dfF["CO₂ (kg)"])
            dfF["_n_time"] = norm(dfF["Temps (h)"])
            dfF["Score global"] = (w_cost*dfF["_n_cost"] + w_co2*dfF["_n_co2"] + w_time*dfF["_n_time"])

            # Meilleures solutions
            best_cost  = dfF.loc[dfF["Coût (FCFA)"].idxmin()]
            best_co2   = dfF.loc[dfF["CO₂ (kg)"].idxmin()]
            best_time  = dfF.loc[dfF["Temps (h)"].idxmin()]
            best_score = dfF.loc[dfF["Score global"].idxmin()]

            st.subheader("🏆 Meilleures solutions")
            st.success(f"💰 Moins coûteuse : **{best_cost['Véhicule']}** — {best_cost['Coût (FCFA)']} FCFA")
            st.success(f"🌱 Moins polluante : **{best_co2['Véhicule']}** — {best_co2['CO₂ (kg)']} kg CO₂")
            st.success(f"⚡ Plus rapide : **{best_time['Véhicule']}** — {best_time['Temps (h)']} h")
            st.success(f"🤖 Meilleure au global : **{best_score['Véhicule']}** — score {round(best_score['Score global'],3)}")

            # Graphique comparatif
            st.subheader("📈 Comparaison (Coût / CO₂ / Temps)")
            fig, ax = plt.subplots()
            df_plot = dfF.set_index("Véhicule")[["Coût (FCFA)","CO₂ (kg)","Temps (h)"]]
            df_plot.plot(kind="bar", ax=ax)
            ax.set_title("Comparaison des critères")
            ax.set_ylabel("Valeurs")
            ax.tick_params(axis='x', labelrotation=45)
            st.pyplot(fig)

            # -----------------------------------------
            # PDF : résumé + tableau best + graphique + liste détaillée
            # -----------------------------------------
            def build_pdf(dataframe, bests, chart_fig):
                buf = BytesIO()
                doc = SimpleDocTemplate(buf, pagesize=A4, leftMargin=1.5*cm, rightMargin=1.5*cm, topMargin=1.5*cm, bottomMargin=1.5*cm)
                styles = getSampleStyleSheet()
                title = styles["Title"]
                h2 = styles["Heading2"]
                p = styles["BodyText"]
                bullet = ParagraphStyle('bullet', parent=p, bulletIndent=0, leftIndent=12)

                elems = []
                elems.append(Paragraph("Rapport d’Optimisation Logistique", title))
                elems.append(Spacer(1, 6))
                elems.append(Paragraph(f"Distance : {distance:.2f} km — Délai max : {deadline:.2f} h (avance requise : 15 min)",
                                       styles["Italic"]))
                elems.append(Paragraph(f"Trafic : {trafic} — Route : {route} — Marchandise : {marchandise} — Poids : {poids} kg", styles["Italic"]))
                elems.append(Spacer(1, 8))

                # Tableau récapitulatif des meilleures solutions
                elems.append(Paragraph("Meilleures solutions par critère", h2))
                best_table_data = [
                    ["Critère", "Véhicule", "Coût (FCFA)", "CO₂ (kg)", "Temps (h)"]
                ]
                for label, row in bests.items():
                    best_table_data.append([
                        label, row["Véhicule"], f"{row['Coût (FCFA)']}", f"{row['CO₂ (kg)']}", f"{row['Temps (h)']}"
                    ])
                tbl = Table(best_table_data, repeatRows=1)
                tbl.setStyle(TableStyle([
                    ("BACKGROUND", (0,0), (-1,0), colors.lightblue),
                    ("TEXTCOLOR", (0,0), (-1,0), colors.black),
                    ("GRID", (0,0), (-1,-1), 0.4, colors.grey),
                    ("ALIGN", (2,1), (-1,-1), "CENTER"),
                    ("VALIGN", (0,0), (-1,-1), "MIDDLE"),
                ]))
                elems.append(tbl)
                elems.append(Spacer(1, 10))

                # Graphique
                elems.append(Paragraph("Illustration graphique", h2))
                chart_buf = BytesIO()
                chart_fig.tight_layout()
                chart_fig.savefig(chart_buf, format="png", dpi=180)
                chart_buf.seek(0)
                elems.append(RLImage(chart_buf, width=16*cm, height=8*cm))
                elems.append(PageBreak())

                # Liste détaillée par véhicule
                elems.append(Paragraph("Détails par véhicule", h2))
                df_list = dataframe.sort_values("Coût (FCFA)").reset_index(drop=True)
                for _, r in df_list.iterrows():
                    elems.append(Paragraph(f"• <b>{r['Véhicule']}</b>", p))
                    elems.append(Paragraph(f"&nbsp;&nbsp;&nbsp;Coût total : {r['Coût (FCFA)']} FCFA", bullet))
                    elems.append(Paragraph(f"&nbsp;&nbsp;&nbsp;Émissions CO₂ : {r['CO₂ (kg)']} kg", bullet))
                    elems.append(Paragraph(f"&nbsp;&nbsp;&nbsp;Temps estimé : {r['Temps (h)']} h", bullet))
                    elems.append(Spacer(1, 4))

                doc.build(elems)
                buf.seek(0)
                return buf

            bests = {
                "💰 Moins coûteuse": best_cost,
                "🌱 Moins polluante": best_co2,
                "⚡ Plus rapide": best_time,
                "🤖 Meilleure globale": best_score
            }
            pdf_buffer = build_pdf(dfF[["Véhicule","Coût (FCFA)","CO₂ (kg)","Temps (h)"]], bests, fig)

            st.download_button(
                "📥 Télécharger le rapport PDF",
                data=pdf_buffer,
                file_name="rapport_logistique.pdf",
                mime="application/pdf"
            )
