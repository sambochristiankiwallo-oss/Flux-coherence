import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# --------------------------
# Données des motorisations
# --------------------------
motorisations = {
    # Voitures
    "Voiture Diesel": {"conso": 0.07, "prix": 720, "emission": 2.68, "vitesse": 70, "capacite": 3000},
    "Voiture Hybride": {"conso": 0.05, "prix": 695, "emission": 1.5, "vitesse": 65, "capacite": 3000},
    "Voiture Électrique": {"conso": 0.20, "prix": 109, "emission": 0.05, "vitesse": 60, "capacite": 3000},

    # Camions
    "Camion Diesel": {"conso": 0.30, "prix": 720, "emission": 2.68, "vitesse": 70, "capacite": 19000},
    "Camion Hybride": {"conso": 0.22, "prix": 695, "emission": 1.5, "vitesse": 65, "capacite": 19000},
    "Camion Électrique": {"conso": 1.2, "prix": 109, "emission": 0.1, "vitesse": 55, "capacite": 19000},

    # Deux-roues et tricycle
    "Moto électrique": {"conso": 0.06, "prix": 109, "emission": 0.02, "vitesse": 50, "capacite": 50},
    "Tricycle électrique": {"conso": 0.10, "prix": 109, "emission": 0.03, "vitesse": 40, "capacite": 1000},
}

# --------------------------
# Fonction d'évaluation
# --------------------------
def evaluer_solutions(distance, poids, delai_max):
    resultats = []
    for nom, data in motorisations.items():
        # Vérification capacité max
        if poids > data["capacite"]:
            resultats.append({
                "Motorisation": nom,
                "Coût (FCFA)": None,
                "Temps (h)": None,
                "Émissions (kg CO2)": None,
                "Score Global": None,
                "Statut": f"❌ Non valide (poids > {data['capacite']}kg)"
            })
            continue

        # Calculs
        cout = distance * data["conso"] * data["prix"]
        temps = distance / data["vitesse"]
        emissions = distance * data["conso"] * data["emission"]

        # Vérification délai
        if temps > (delai_max - 0.17):  # 0.17h ≈ 10 minutes
            statut = "❌ Non valide (délai dépassé)"
        else:
            statut = "✅ Valide"

        score = (cout / 1000) + temps + emissions if statut == "✅ Valide" else None

        resultats.append({
            "Motorisation": nom,
            "Coût (FCFA)": round(cout, 2),
            "Temps (h)": round(temps, 2),
            "Émissions (kg CO2)": round(emissions, 2),
            "Score Global": round(score, 2) if score else None,
            "Statut": statut
        })

    return pd.DataFrame(resultats)

# --------------------------
# Fonction génération PDF
# --------------------------
def generer_pdf(df, distance, poids, delai_max, meilleures):
    doc = SimpleDocTemplate("rapport_logistique.pdf", pagesize=A4)
    styles = getSampleStyleSheet()
    elements = []

    # Titre
    elements.append(Paragraph("Rapport d’Optimisation Logistique", styles['Title']))
    elements.append(Spacer(1, 12))

    # Résumé
    resume = f"Distance : {distance} km<br/>Poids : {poids} kg<br/>Délai maximum : {delai_max} h"
    elements.append(Paragraph(resume, styles['Normal']))
    elements.append(Spacer(1, 12))

    # Tableau comparatif
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

    # Graphiques
    for col in ["Coût (FCFA)", "Temps (h)", "Émissions (kg CO2)"]:
        if df[col].notnull().any():
            plt.figure()
            df[df[col].notnull()].plot(x="Motorisation", y=col, kind="bar", legend=False)
            plt.title(col)
            plt.ylabel(col)
            plt.tight_layout()
            plt.savefig("temp.png")
            elements.append(Image("temp.png", width=400, height=200))
            elements.append(Spacer(1, 12))

    # Meilleures solutions
    elements.append(Paragraph("🏆 Meilleures solutions :", styles['Heading2']))
    for critere, valeur in meilleures.items():
        elements.append(Paragraph(f"{critere} : {valeur}", styles['Normal']))

    doc.build(elements)
    return "rapport_logistique.pdf"

# --------------------------
# Application Streamlit
# --------------------------
st.title("🚚 Assistant Logistique Intelligent")

distance = st.number_input("Distance (km)", min_value=1, value=100)
poids = st.number_input("Poids (kg)", min_value=1, value=500)
delai_max = st.number_input("Délai maximum (heures)", min_value=1, value=5)

if st.button("Évaluer les solutions"):
    df = evaluer_solutions(distance, poids, delai_max)
    st.dataframe(df)

    # Identifier les meilleures solutions
    valides = df[df["Statut"] == "✅ Valide"]
    meilleures = {}
    if not valides.empty:
        meilleures["💰 Moins coûteuse"] = valides.loc[valides["Coût (FCFA)"].idxmin(), "Motorisation"]
        meilleures["⚡ Plus rapide"] = valides.loc[valides["Temps (h)"].idxmin(), "Motorisation"]
        meilleures["🌱 Moins polluante"] = valides.loc[valides["Émissions (kg CO2)"].idxmin(), "Motorisation"]
        meilleures["📊 Score global"] = valides.loc[valides["Score Global"].idxmin(), "Motorisation"]

        st.subheader("🏆 Meilleures solutions")
        for critere, valeur in meilleures.items():
            st.write(f"{critere} : {valeur}")

        # Export PDF
        if st.button("📄 Exporter le rapport PDF"):
            fichier_pdf = generer_pdf(df, distance, poids, delai_max, meilleures)
            with open(fichier_pdf, "rb") as f:
                st.download_button("Télécharger le PDF", f, file_name="rapport_logistique.pdf")
