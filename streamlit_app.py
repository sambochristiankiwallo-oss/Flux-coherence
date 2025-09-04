# app.py
import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

import os

# =========================
# Paramètres véhicules
# =========================
vehicules = {
    # Deux/trois roues
    "Moto électrique":      {"type": "electrique", "conso_kWh_km": 0.05, "vitesse": 50, "capacite": 50},
    "Tricycle électrique":  {"type": "electrique", "conso_kWh_km": 0.10, "vitesse": 40, "capacite": 1000},

    # Voitures
    "Voiture électrique":   {"type": "electrique", "conso_kWh_km": 0.18, "vitesse": 70, "capacite": 3000},
    "Voiture hybride":      {"type": "hybride",    "conso_L_km": 0.05, "conso_kWh_km": 0.05, "vitesse": 70, "capacite": 3000},
    "Voiture diesel":       {"type": "diesel",     "conso_L_km": 0.07, "vitesse": 70, "capacite": 3000},

    # Camions
    "Camion électrique":    {"type": "electrique", "conso_kWh_km": 1.20, "vitesse": 60, "capacite": 19000},
    "Camion hybride":       {"type": "hybride",    "conso_L_km": 0.20, "conso_kWh_km": 0.15, "vitesse": 60, "capacite": 19000},
    "Camion diesel":        {"type": "diesel",     "conso_L_km": 0.30, "vitesse": 60, "capacite": 19000},
}

# Coûts (FCFA / unité)
prix = {"diesel": 720, "essence": 695, "kWh": 109}

# Émissions (kg CO2 / unité)
emissions = {"diesel": 2.68, "essence": 2.31, "kWh": 0.05}

# =========================
# Pondérations dynamiques
# =========================
def pondérations(marchandise: str):
    """
    Renvoie (w_cout, w_co2, w_temps) selon le type de marchandise.
    """
    if marchandise == "Périssable":
        return 0.20, 0.20, 0.60   # priorité rapidité
    if marchandise == "Fragile":
        return 0.20, 0.60, 0.20   # priorité faible CO2/souplesse
    if marchandise == "Alimentaire":
        return 0.30, 0.40, 0.30   # équilibre éco + rapidité
    return 0.50, 0.30, 0.20       # Général : coût prioritaire

def texte_pondérations(marchandise: str):
    if marchandise == "Périssable":
        return "Priorité à la rapidité (60%), coût (20%), émissions (20%)."
    if marchandise == "Fragile":
        return "Priorité à la réduction des émissions (60%), coût (20%), rapidité (20%)."
    if marchandise == "Alimentaire":
        return "Équilibre entre émissions (40%), coût (30%) et rapidité (30%)."
    return "Équilibre standard : coût (50%), émissions (30%), rapidité (20%)."

# =========================
# Calculs
# =========================
def est_compatible_marchandise(nom: str, marchandise: str) -> bool:
    # Règles simples (tu peux les affiner plus tard)
    if marchandise in ["Fragile", "Périssable"] and "Moto" in nom:
        return False
    if marchandise == "Fragile" and "Tricycle" in nom:
        return False
    if marchandise in ["Alimentaire", "Périssable"] and "Camion" in nom:
        # on évite camions (plus lents) pour denrées sensibles
        return False
    return True

def calculer_solutions(distance_km: float, poids_kg: float, delai_h: float, marchandise: str) -> pd.DataFrame:
    w_cout, w_co2, w_temps = pondérations(marchandise)
    lignes = []

    for nom, v in vehicules.items():
        # Capacité
        if poids_kg > v["capacite"]:
            continue

        # Compatibilité marchandise
        if not est_compatible_marchandise(nom, marchandise):
            continue

        # Temps et contrainte délai (au moins 10 minutes d'avance)
        temps_h = distance_km / v["vitesse"]
        if temps_h >= delai_h - (10/60):
            continue

        # Coût et CO2 selon type
        if v["type"] == "diesel":
            cout = distance_km * v["conso_L_km"] * prix["diesel"]
            co2  = distance_km * v["conso_L_km"] * emissions["diesel"]
        elif v["type"] == "electrique":
            cout = distance_km * v["conso_kWh_km"] * prix["kWh"]
            co2  = distance_km * v["conso_kWh_km"] * emissions["kWh"]
        else:  # hybride
            cout = distance_km * (v["conso_L_km"] * prix["essence"] + v["conso_kWh_km"] * prix["kWh"])
            co2  = distance_km * (v["conso_L_km"] * emissions["essence"] + v["conso_kWh_km"] * emissions["kWh"])

        score = w_cout*cout + w_co2*co2 + w_temps*temps_h

        lignes.append({
            "Véhicule": nom,
            "Coût (FCFA)": round(cout, 2),
            "Temps (h)": round(temps_h, 2),
            "Émissions CO2 (kg)": round(co2, 2),
            "Score global": round(score, 4)
        })

    df = pd.DataFrame(lignes)
    return df.sort_values("Score global", ascending=True).reset_index(drop=True)

def meilleures_solutions(df: pd.DataFrame):
    if df.empty:
        return {}
    return {
        "💰 Moins coûteuse": df.loc[df["Coût (FCFA)"].idxmin(), "Véhicule"],
        "⚡ Plus rapide": df.loc[df["Temps (h)"].idxmin(), "Véhicule"],
        "🌍 Moins polluante": df.loc[df["Émissions CO2 (kg)"].idxmin(), "Véhicule"],
        "⭐ Meilleure globale (pondérée)": df.loc[df["Score global"].idxmin(), "Véhicule"],
    }

# =========================
# PDF
# =========================
def tracer_et_sauver_bar(df, col, titre, fname):
    plt.figure()
    df.plot(x="Véhicule", y=col, kind="bar", legend=False)
    plt.ylabel(col)
    plt.title(titre)
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    plt.savefig(fname)
    plt.close()

def generer_pdf(df, distance, poids, delai_max, marchandise, meilleures, texte_poids):
    pdf_path = "rapport_logistique.pdf"
    styles = getSampleStyleSheet()
    doc = SimpleDocTemplate(pdf_path, pagesize=A4)
    story = []

    # En-tête
    story.append(Paragraph("📦 Rapport d’Optimisation Logistique", styles["Title"]))
    story.append(Spacer(1, 8))
    story.append(Paragraph(f"<b>Distance :</b> {distance} km", styles["Normal"]))
    story.append(Paragraph(f"<b>Poids :</b> {poids} kg {texte_poids}", styles["Normal"]))
    story.append(Paragraph(f"<b>Délai maximal :</b> {delai_max} h (arrivée exigée ≥ 10 min avant)", styles["Normal"]))
    story.append(Paragraph(f"<b>Type de marchandise :</b> {marchandise}", styles["Normal"]))
    story.append(Paragraph(f"<b>Pondérations appliquées :</b> {texte_pondérations(marchandise)}", styles["Italic"]))
    story.append(Spacer(1, 12))

    if df.empty:
        story.append(Paragraph("⚠️ Aucune solution valide n’a été trouvée pour ces contraintes.", styles["Normal"]))
        doc.build(story)
        return pdf_path

    # Tableau
    data = [list(df.columns)] + df.values.tolist()
    table = Table(data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.grey),
        ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
    ]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Graphiques -> fichiers temporaires
    imgs = []
    plots = [
        ("Coût (FCFA)", "Comparaison des coûts", "plot_cout.png"),
        ("Temps (h)", "Comparaison des temps", "plot_temps.png"),
        ("Émissions CO2 (kg)", "Comparaison des émissions", "plot_co2.png"),
    ]
    for col, titre, fname in plots:
        tracer_et_sauver_bar(df, col, titre, fname)
        imgs.append(fname)
        story.append(Image(fname, width=430, height=230))
        story.append(Spacer(1, 10))

    # Meilleures solutions
    story.append(Paragraph("🏆 Meilleures solutions", styles["Heading2"]))
    for k, v in meilleures.items():
        story.append(Paragraph(f"{k} : {v}", styles["Normal"]))

    doc.build(story)

    # Nettoyage
    for f in imgs:
        try:
            os.remove(f)
        except Exception:
            pass

    return pdf_path

# =========================
# UI Streamlit
# =========================
st.title("🚚 Assistant Logistique Intelligent")
st.caption("Compare les options de transport selon le coût (FCFA), le temps (h) et les émissions de CO₂ (kg). "
           "Respect du délai avec au moins 10 minutes d’avance.")

col1, col2 = st.columns(2)
with col1:
    distance = st.number_input("Distance (km)", min_value=1, value=100)
    delai_max = st.number_input("Délai maximum (heures)", min_value=1.0, value=5.0, step=0.25)
with col2:
    poids = st.number_input("Poids de la marchandise (kg)", min_value=1, value=500)
    marchandise = st.selectbox("Type de marchandise", ["Général", "Alimentaire", "Fragile", "Périssable"])

texte_poids = ""
if poids <= 50:
    texte_poids = "(compatible avec Moto, etc.)"
elif poids <= 1000:
    texte_poids = "(compatible dès Tricycle et au-dessus)"
elif poids <= 3000:
    texte_poids = "(compatible dès Voiture et au-dessus)"
elif poids <= 19000:
    texte_poids = "(compatible Camion uniquement)"
else:
    texte_poids = "(❌ Au-delà de 19 t : aucune option disponible)"

if st.button("🔍 Calculer les solutions"):
    df = calculer_solutions(distance, poids, delai_max, marchandise)

    if df.empty:
        st.error("❌ Aucune solution ne respecte les contraintes (poids/capacité, compatibilité marchandise, délai avec 10 min d’avance).")
    else:
        st.subheader("📊 Tableau comparatif")
        st.dataframe(df, use_container_width=True)

        # Graphiques (matplotlib)
        st.subheader("📈 Graphiques comparatifs")
        for col, titre in [("Coût (FCFA)", "Comparaison des coûts"),
                           ("Temps (h)", "Comparaison des temps"),
                           ("Émissions CO2 (kg)", "Comparaison des émissions")]:
            fig, ax = plt.subplots()
            df.plot(x="Véhicule", y=col, kind="bar", legend=False, ax=ax)
            ax.set_title(titre)
            ax.set_ylabel(col)
            ax.tick_params(axis='x', rotation=30)
            st.pyplot(fig, clear_figure=True)

        # Meilleures solutions
        best = meilleures_solutions(df)
        st.subheader("🏆 Meilleures solutions")
        for k, v in best.items():
            st.write(f"**{k}** : {v}")

        # Recommandation finale
        reco = best.get("⭐ Meilleure globale (pondérée)", None)
        if reco:
            st.success(f"✅ **Solution recommandée** (pondérée selon '{marchandise}') : **{reco}**")

        # Export PDF : bouton direct
        pdf_file = generer_pdf(df, distance, poids, delai_max, marchandise, best, texte_poids)
        with open(pdf_file, "rb") as f:
            st.download_button(
                label="📄 Télécharger le rapport PDF",
                data=f,
                file_name="rapport_logistique.pdf",
                mime="application/pdf"
            )
