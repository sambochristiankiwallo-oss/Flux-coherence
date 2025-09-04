import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import os

# --------------------------
# Données véhicules
# --------------------------
vehicules = {
    "Moto électrique": {"conso": 0.05, "type": "electrique", "capacite": 50},
    "Tricycle électrique": {"conso": 0.08, "type": "electrique", "capacite": 1000},
    "Voiture électrique": {"conso": 0.18, "type": "electrique", "capacite": 3000},
    "Camion électrique": {"conso": 1.2, "type": "electrique", "capacite": 19000},
    "Voiture diesel": {"conso": 0.07, "type": "diesel", "capacite": 3000},
    "Camion diesel": {"conso": 0.35, "type": "diesel", "capacite": 19000},
    "Voiture hybride": {"conso": 0.05, "type": "hybride", "capacite": 3000},
    "Camion hybride": {"conso": 0.28, "type": "hybride", "capacite": 19000},
}

prix = {"diesel": 720, "essence": 695, "electrique": 109}
emissions = {"diesel": 2.68, "essence": 2.31, "electrique": 0.1}

vitesses = {
    "Moto électrique": 50,
    "Tricycle électrique": 40,
    "Voiture électrique": 70,
    "Camion électrique": 60,
    "Voiture diesel": 80,
    "Camion diesel": 70,
    "Voiture hybride": 75,
    "Camion hybride": 65,
}

# --------------------------
# Calculs logistiques
# --------------------------
def calculer_solutions(distance, poids, delai_max):
    resultats = []

    for nom, data in vehicules.items():
        if poids > data["capacite"]:
            continue

        conso = data["conso"] * distance
        if data["type"] == "diesel":
            cout = conso * prix["diesel"]
            emission = conso * emissions["diesel"]
        elif data["type"] == "hybride":
            cout = conso * ((prix["diesel"] + prix["essence"]) / 2)
            emission = conso * ((emissions["diesel"] + emissions["essence"]) / 2)
        else:  # électrique
            cout = conso * prix["electrique"]
            emission = conso * emissions["electrique"]

        temps = distance / vitesses[nom]

        # Vérification délai (toujours 10 min d’avance)
        if temps >= delai_max - 0.25:  # 0.25h = 15min
            continue

        resultats.append({
            "Motorisation": nom,
            "Coût (FCFA)": round(cout, 2),
            "Temps (h)": round(temps, 2),
            "Émissions (kg CO2)": round(emission, 2),
        })

    df = pd.DataFrame(resultats)

    meilleures = {}
    if not df.empty:
        meilleures["Moins coûteuse"] = df.loc[df["Coût (FCFA)"].idxmin(), "Motorisation"]
        meilleures["Plus rapide"] = df.loc[df["Temps (h)"].idxmin(), "Motorisation"]
        meilleures["Moins polluante"] = df.loc[df["Émissions (kg CO2)"].idxmin(), "Motorisation"]

    return df, meilleures

# --------------------------
# Génération PDF
# --------------------------
def generer_pdf(df, distance, poids, delai_max, meilleures):
    doc = SimpleDocTemplate("rapport_logistique.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    elements.append(Paragraph("Rapport d’Optimisation Logistique", styles['Title']))
    elements.append(Spacer(1, 12))

    resume = f"Distance : {distance} km<br/>Poids : {poids} kg<br/>Délai maximum : {delai_max} h"
    elements.append(Paragraph(resume, styles['Normal']))
    elements.append(Spacer(1, 12))

    if not df.empty:
        tableau_data = [df.columns.tolist()] + df.fillna("").values.tolist()
        table = Table(tableau_data)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), colors.grey),
            ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('GRID', (0,0), (-1,-1), 1, colors.black),
        ]))
        elements.append(table)
        elements.append(Spacer(1, 12))

        for col in ["Coût (FCFA)", "Temps (h)", "Émissions (kg CO2)"]:
            if df[col].notnull().any():
                plt.figure()
                df[df[col].notnull()].plot(x="Motorisation", y=col, kind="bar", legend=False)
                plt.title(col)
                plt.ylabel(col)
                plt.tight_layout()
                filename = f"temp_{col}.png"
                plt.savefig(filename)
                plt.close()
                elements.append(Image(filename, width=400, height=200))
                elements.append(Spacer(1, 12))
                os.remove(filename)

        elements.append(Paragraph("🏆 Meilleures solutions :", styles['Heading2']))
        for critere, valeur in meilleures.items():
            elements.append(Paragraph(f"{critere} : {valeur}", styles['Normal']))

    doc.build(elements)
    return "rapport_logistique.pdf"

# --------------------------
# Application Streamlit
# --------------------------
st.title("🚚 Assistant Logistique Intelligent")
st.write("Optimisation des solutions de transport selon le coût, le temps et les émissions.")

distance = st.number_input("Distance (km)", min_value=1, value=100)
poids = st.number_input("Poids de la marchandise (kg)", min_value=1, value=500)
delai_max = st.number_input("Délai maximum (heures)", min_value=1.0, value=5.0, step=0.25)

if st.button("🔍 Calculer les solutions"):
    df, meilleures = calculer_solutions(distance, poids, delai_max)

    if df.empty:
        st.error("❌ Aucune solution ne respecte les contraintes.")
    else:
        st.subheader("📊 Tableau comparatif")
        st.dataframe(df)

        st.subheader("📈 Graphiques comparatifs")
        for col in ["Coût (FCFA)", "Temps (h)", "Émissions (kg CO2)"]:
            fig, ax = plt.subplots()
            df.plot(x="Motorisation", y=col, kind="bar", ax=ax, legend=False)
            ax.set_title(col)
            ax.set_ylabel(col)
            st.pyplot(fig)

        st.subheader("🏆 Meilleures solutions")
        for critere, valeur in meilleures.items():
            st.write(f"**{critere}** : {valeur}")

        if st.button("📄 Exporter le rapport PDF"):
            fichier_pdf = generer_pdf(df, distance, poids, delai_max, meilleures)
            with open(fichier_pdf, "rb") as f:
                st.download_button("Télécharger le PDF", f, file_name="rapport_logistique.pdf")
