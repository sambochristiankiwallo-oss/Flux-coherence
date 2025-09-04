import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# -------------------------------
# Paramètres des motorisations
# -------------------------------
vehicules = {
    "Moto électrique": {"conso_kWh_km": 0.05, "capacité": 50, "vitesse": 50, "type": "électrique"},
    "Tricycle électrique": {"conso_kWh_km": 0.1, "capacité": 1000, "vitesse": 40, "type": "électrique"},
    "Voiture électrique": {"conso_kWh_km": 0.18, "capacité": 3000, "vitesse": 70, "type": "électrique"},
    "Voiture diesel": {"conso_L_km": 0.07, "capacité": 3000, "vitesse": 70, "type": "diesel"},
    "Voiture hybride": {"conso_L_km": 0.05, "conso_kWh_km": 0.05, "capacité": 3000, "vitesse": 70, "type": "hybride"},
    "Camion diesel": {"conso_L_km": 0.3, "capacité": 19000, "vitesse": 60, "type": "diesel"},
    "Camion hybride": {"conso_L_km": 0.2, "conso_kWh_km": 0.15, "capacité": 19000, "vitesse": 60, "type": "hybride"},
    "Camion électrique": {"conso_kWh_km": 1.2, "capacité": 19000, "vitesse": 60, "type": "électrique"},
}

# Coûts en FCFA
prix = {"diesel": 720, "essence": 695, "kWh": 109}

# Émissions CO2 (kg par unité)
emissions = {"diesel": 2.68, "essence": 2.31, "kWh": 0.05}

# -------------------------------
# Fonctions de calcul
# -------------------------------
def calculer_resultats(distance, poids, delai_max):
    resultats = []

    for nom, data in vehicules.items():
        if poids > data["capacité"]:
            continue

        temps_h = distance / data["vitesse"]

        # Vérifier délai avec marge de 10 min
        if temps_h > delai_max - (10/60):
            continue

        cout, co2 = 0, 0
        if data["type"] == "diesel":
            cout = distance * data["conso_L_km"] * prix["diesel"]
            co2 = distance * data["conso_L_km"] * emissions["diesel"]
        elif data["type"] == "électrique":
            cout = distance * data["conso_kWh_km"] * prix["kWh"]
            co2 = distance * data["conso_kWh_km"] * emissions["kWh"]
        elif data["type"] == "hybride":
            cout = distance * (data["conso_L_km"] * prix["essence"] + data["conso_kWh_km"] * prix["kWh"])
            co2 = distance * (data["conso_L_km"] * emissions["essence"] + data["conso_kWh_km"] * emissions["kWh"])

        resultats.append({
            "Véhicule": nom,
            "Coût (FCFA)": round(cout, 2),
            "Temps (h)": round(temps_h, 2),
            "Émissions CO2 (kg)": round(co2, 2),
            "Score global": round(cout*0.5 + co2*0.3 + temps_h*0.2, 2)
        })

    return pd.DataFrame(resultats)

def meilleures_solutions(df):
    meilleures = {}
    if df.empty:
        return meilleures
    meilleures["💰 Moins coûteuse"] = df.loc[df["Coût (FCFA)"].idxmin()]["Véhicule"]
    meilleures["⚡ Plus rapide"] = df.loc[df["Temps (h)"].idxmin()]["Véhicule"]
    meilleures["🌍 Moins polluante"] = df.loc[df["Émissions CO2 (kg)"].idxmin()]["Véhicule"]
    meilleures["⭐ Équilibrée"] = df.loc[df["Score global"].idxmin()]["Véhicule"]
    return meilleures

def generer_pdf(df, distance, poids, delai_max, meilleures):
    fichier_pdf = "rapport_logistique.pdf"
    doc = SimpleDocTemplate(fichier_pdf, pagesize=A4)
    styles = getSampleStyleSheet()
    story = []

    story.append(Paragraph("📦 Rapport Logistique Intelligent", styles['Title']))
    story.append(Spacer(1, 12))
    story.append(Paragraph(f"Distance : {distance} km", styles['Normal']))
    story.append(Paragraph(f"Poids : {poids} kg", styles['Normal']))
    story.append(Paragraph(f"Délai max : {delai_max} h", styles['Normal']))
    story.append(Spacer(1, 12))

    # Tableau
    data_table = [list(df.columns)] + df.values.tolist()
    table = Table(data_table)
    table.setStyle(TableStyle([("BACKGROUND", (0,0), (-1,0), colors.grey),
                               ("TEXTCOLOR", (0,0), (-1,0), colors.whitesmoke),
                               ("ALIGN", (0,0), (-1,-1), "CENTER"),
                               ("GRID", (0,0), (-1,-1), 1, colors.black)]))
    story.append(table)
    story.append(Spacer(1, 12))

    # Graphiques
    for col, titre in [("Coût (FCFA)", "Comparaison des coûts"),
                       ("Temps (h)", "Comparaison des temps"),
                       ("Émissions CO2 (kg)", "Comparaison des émissions")]:
        plt.figure()
        df.plot(x="Véhicule", y=col, kind="bar", legend=False)
        plt.ylabel(col)
        plt.title(titre)
        plt.tight_layout()
        img_path = f"{col}.png"
        plt.savefig(img_path)
        plt.close()
        story.append(Image(img_path, width=400, height=200))
        story.append(Spacer(1, 12))

    # Meilleures solutions
    story.append(Paragraph("🏆 Meilleures solutions :", styles['Heading2']))
    for critere, vehicule in meilleures.items():
        story.append(Paragraph(f"{critere} : {vehicule}", styles['Normal']))

    doc.build(story)
    return fichier_pdf

# -------------------------------
# Interface Streamlit
# -------------------------------
st.title("🚚 Assistant Logistique Intelligent")

distance = st.number_input("Distance (km)", min_value=1, value=100)
poids = st.number_input("Poids de la marchandise (kg)", min_value=1, value=500)
delai_max = st.number_input("Délai maximum (heures)", min_value=1, value=5)

if st.button("Calculer"):
    df = calculer_resultats(distance, poids, delai_max)

    if df.empty:
        st.error("⚠️ Aucune solution possible avec ces contraintes.")
    else:
        st.subheader("📊 Résultats comparatifs")
        st.dataframe(df)

        meilleures = meilleures_solutions(df)
        st.subheader("🏆 Meilleures solutions")
        for critere, vehicule in meilleures.items():
            st.write(f"{critere} → {vehicule}")

        # Graphiques interactifs
        for col in ["Coût (FCFA)", "Temps (h)", "Émissions CO2 (kg)"]:
            st.bar_chart(df.set_index("Véhicule")[col])

        # Export PDF
        fichier_pdf = generer_pdf(df, distance, poids, delai_max, meilleures)
        with open(fichier_pdf, "rb") as f:
            st.download_button("📄 Télécharger le rapport PDF", f, file_name="rapport_logistique.pdf", mime="application/pdf")
