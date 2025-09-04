import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from fpdf import FPDF

# ---------------------------
# Paramètres énergétiques et coûts
# ---------------------------
COUTS = {
    "Diesel": 720,             # FCFA/L
    "Essence": 695,            # FCFA/L
    "Hybride": 710,            # moyenne
    "Électrique": 109,         # FCFA/kWh
    "Camion Électrique": 109,
    "Moto Électrique": 109,
    "Tricycle Électrique": 109,
}

CONSO = {
    "Diesel": 0.08,             # L/km
    "Essence": 0.09,
    "Hybride": 0.05,
    "Électrique": 0.20,         # kWh/km
    "Camion Électrique": 1.2,
    "Moto Électrique": 0.05,
    "Tricycle Électrique": 0.15,
}

EMISSIONS = {
    "Diesel": 2.68,             # kg CO₂/L
    "Essence": 2.31,
    "Hybride": 1.5,
    "Électrique": 0.1,          # kg CO₂/kWh (mix réseau)
    "Camion Électrique": 0.1,
    "Moto Électrique": 0.1,
    "Tricycle Électrique": 0.1,
}

VITESSES = {
    "Diesel": 90,
    "Essence": 90,
    "Hybride": 100,
    "Électrique": 100,
    "Camion Électrique": 80,
    "Moto Électrique": 70,
    "Tricycle Électrique": 50,
}

CAPACITES = {
    "Diesel": 2000,
    "Essence": 1500,
    "Hybride": 1000,
    "Électrique": 1200,
    "Camion Électrique": 8000,
    "Moto Électrique": 200,
    "Tricycle Électrique": 500,
}

# ---------------------------
# Fonctions de calcul
# ---------------------------
def calculer_solution(motorisation, distance, delai, marchandise, poids):
    vitesse = VITESSES[motorisation]
    temps = distance / vitesse
    cout = distance * CONSO[motorisation] * COUTS[motorisation]
    emissions = distance * CONSO[motorisation] * EMISSIONS[motorisation]

    respect_delai = temps <= (delai - 0.1667)   # au moins 10 min d’avance
    respect_poids = poids <= CAPACITES[motorisation]

    return {
        "Motorisation": motorisation,
        "Temps (h)": round(temps, 2),
        "Coût (FCFA)": round(cout, 2),
        "Émissions (kg CO₂)": round(emissions, 2),
        "Respect délai": respect_delai,
        "Respect poids": respect_poids,
        "Marchandise": marchandise
    }

def trouver_meilleures_solutions(df):
    resultats = {}
    df_valides = df[(df["Respect délai"]) & (df["Respect poids"])]
    if df_valides.empty:
        return {"message": "⚠️ Aucune solution ne respecte toutes les contraintes."}

    resultats["Moins coûteuse"] = df_valides.loc[df_valides["Coût (FCFA)"].idxmin()]
    resultats["Moins polluante"] = df_valides.loc[df_valides["Émissions (kg CO₂)"].idxmin()]
    resultats["Plus rapide"] = df_valides.loc[df_valides["Temps (h)"].idxmin()]

    # Score mixte pondéré (40% coût, 30% temps, 30% émissions)
    df_valides["Score"] = (
        0.4 * (df_valides["Coût (FCFA)"] / df_valides["Coût (FCFA)"].max()) +
        0.3 * (df_valides["Temps (h)"] / df_valides["Temps (h)"].max()) +
        0.3 * (df_valides["Émissions (kg CO₂)"] / df_valides["Émissions (kg CO₂)"].max())
    )
    resultats["Mixte équilibrée"] = df_valides.loc[df_valides["Score"].idxmin()]

    return resultats

# ---------------------------
# Interface utilisateur Streamlit
# ---------------------------
st.title("🚛 Assistant Intelligent d’Optimisation Logistique")
st.write("Compare **coût 💰**, **temps ⏱️**, **émissions 🌍** et propose la meilleure solution logistique.")

# Entrées utilisateur
distance = st.number_input("📏 Distance (km)", min_value=1, value=150)
delai = st.number_input("⏱️ Délai maximal (heures)", min_value=1, value=4)
marchandise = st.selectbox("📦 Type de marchandise", ["Alimentaire", "Fragile", "Lourd", "Standard"])
poids = st.number_input("⚖️ Poids de la marchandise (kg)", min_value=1, value=500)

if st.button("🚀 Lancer la simulation"):
    resultats = []
    for motorisation in COUTS.keys():
        res = calculer_solution(motorisation, distance, delai, marchandise, poids)
        resultats.append(res)

    df = pd.DataFrame(resultats)
    st.subheader("📊 Résultats des simulations")
    st.dataframe(df)

    meilleures = trouver_meilleures_solutions(df)

    if "message" in meilleures:
        st.warning(meilleures["message"])
    else:
        st.subheader("🏆 Meilleures solutions")
        for critere, sol in meilleures.items():
            st.markdown(f"**{critere}** → {sol['Motorisation']} | ⏱️ {sol['Temps (h)']} h | 💰 {sol['Coût (FCFA)']} | 🌍 {sol['Émissions (kg CO₂)']} kg")

        # Graphiques
        fig, axes = plt.subplots(1, 3, figsize=(15, 5))
        df.plot(x="Motorisation", y="Coût (FCFA)", kind="bar", ax=axes[0], color="green", legend=False)
        axes[0].set_title("Coût")
        df.plot(x="Motorisation", y="Temps (h)", kind="bar", ax=axes[1], color="blue", legend=False)
        axes[1].set_title("Temps")
        df.plot(x="Motorisation", y="Émissions (kg CO₂)", kind="bar", ax=axes[2], color="red", legend=False)
        axes[2].set_title("Émissions")
        st.pyplot(fig)

        # Export PDF
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("Arial", "B", 16)
        pdf.cell(200, 10, "Rapport d’Optimisation Logistique", ln=True, align="C")

        pdf.set_font("Arial", "", 12)
        pdf.cell(200, 10, f"Distance : {distance} km | Délai : {delai} h | Poids : {poids} kg", ln=True)

        # Tableau PDF
        pdf.set_font("Arial", "B", 10)
        col_width = pdf.w / 5
        pdf.cell(col_width, 10, "Motorisation", 1)
        pdf.cell(col_width, 10, "Temps (h)", 1)
        pdf.cell(col_width, 10, "Coût (FCFA)", 1)
        pdf.cell(col_width, 10, "Émissions (kg CO₂)", 1)
        pdf.cell(col_width, 10, "OK", 1)
        pdf.ln()

        pdf.set_font("Arial", "", 10)
        for _, row in df.iterrows():
            pdf.cell(col_width, 10, row["Motorisation"], 1)
            pdf.cell(col_width, 10, str(row["Temps (h)"]), 1)
            pdf.cell(col_width, 10, str(row["Coût (FCFA)"]), 1)
            pdf.cell(col_width, 10, str(row["Émissions (kg CO₂)"]), 1)
            pdf.cell(col_width, 10, "✔" if row["Respect délai"] and row["Respect poids"] else "❌", 1)
            pdf.ln()

        pdf.output("rapport_logistique.pdf")
        st.success("📄 Rapport PDF généré : `rapport_logistique.pdf`")
