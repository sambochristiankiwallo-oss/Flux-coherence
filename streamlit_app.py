import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import io
from fpdf import FPDF

# ----------------------
# Génération PDF
# ----------------------
def generer_pdf(df, resume, meilleures, figures):
    pdf = FPDF()
    pdf.add_page()

    pdf.add_font("DejaVu", "", "fonts/DejaVuSans.ttf", uni=True)
    pdf.set_font("DejaVu", size=16)
    pdf.cell(200, 10, "🚚 Rapport Logistique Intelligent", ln=True, align="C")
    pdf.ln(10)

    pdf.set_font("DejaVu", size=12)
    pdf.multi_cell(0, 10,
        f"Résumé des données saisies :\n"
        f"- Distance : {resume['distance']} km\n"
        f"- Poids : {resume['poids']} kg\n"
        f"- Marchandise : {resume['marchandise']}\n"
        f"- Route : {resume['route']}\n"
        f"- Délai maximum : {resume['delai']} h"
    )
    pdf.ln(5)

    # Tableau comparatif
    pdf.cell(0, 10, "📊 Comparatif des solutions :", ln=True)

    col_widths = [45, 35, 35, 45, 40]
    headers = ["Motorisation", "Coût (FCFA)", "Temps (h)", "Émissions (kgCO2)", "Validité"]

    for h, w in zip(headers, col_widths):
        pdf.cell(w, 10, h, 1, 0, "C")
    pdf.ln()

    for _, row in df.iterrows():
        pdf.cell(col_widths[0], 10, str(row["Motorisation"]), 1)
        pdf.cell(col_widths[1], 10, str(row["Coût (FCFA)"]), 1)
        pdf.cell(col_widths[2], 10, str(row["Temps (h)"]), 1)
        pdf.cell(col_widths[3], 10, str(row["Émissions (kg CO2)"]), 1)
        pdf.cell(col_widths[4], 10, str(row["Validité"]), 1)
        pdf.ln()

    pdf.ln(5)

    pdf.multi_cell(0, 10,
        f"🏆 Meilleures solutions :\n"
        f"- 💰 Moins coûteuse : {meilleures.get('moins_cher','Aucune valide')}\n"
        f"- ⏱️ Plus rapide : {meilleures.get('plus_rapide','Aucune valide')}\n"
        f"- 🌍 Moins polluante : {meilleures.get('moins_polluant','Aucune valide')}\n"
        f"- ⚖️ Meilleure globale : {meilleures.get('meilleur_score','Aucune valide')}"
    )

    pdf.ln(10)

    # Graphiques
    pdf.cell(0, 10, "📈 Illustrations graphiques :", ln=True)
    pdf.ln(5)

    for titre, fig in figures.items():
        buf = io.BytesIO()
        fig.savefig(buf, format="PNG")
        buf.seek(0)
        pdf.image(buf, w=150)
        pdf.ln(10)

    pdf.output("rapport_logistique.pdf")

# ----------------------
# Application principale
# ----------------------
st.title("🚛 Assistant Intelligent d’Optimisation Logistique")
st.write("Comparez coût 💰, délai ⏱️, émissions 🌍 et obtenez un rapport PDF complet.")

# Entrées utilisateur
distance = st.number_input("Distance (km)", min_value=1, value=100)
poids = st.number_input("Poids total (kg)", min_value=1, value=500)
marchandise = st.selectbox("Type de marchandise", ["Générale", "Périssable", "Fragile", "Dangereuse"])
route = st.selectbox("Type de route", ["Autoroute", "Nationale", "Urbaine", "Rurale"])
delai_max = st.number_input("⏱️ Délai maximum (h)", min_value=1.0, value=4.0)

# Données motorisations
motorisations = {
    "Diesel": {"conso": 0.07, "prix": 720, "emission": 2.68, "vitesse": 70},
    "Hybride": {"conso": 0.05, "prix": 695, "emission": 1.5, "vitesse": 65},
    "Électrique": {"conso": 0.20, "prix": 109, "emission": 0.05, "vitesse": 60},
    "Moto électrique": {"conso": 0.06, "prix": 109, "emission": 0.02, "vitesse": 50},
    "Tricycle électrique": {"conso": 0.10, "prix": 109, "emission": 0.03, "vitesse": 40},
    "Camion électrique": {"conso": 1.2, "prix": 109, "emission": 0.1, "vitesse": 55},
}

# Ajustements en fonction du type de route
facteur_route = {
    "Autoroute": 1.0,
    "Nationale": 1.1,
    "Urbaine": 1.3,
    "Rurale": 1.5
}

facteur_marchandise = {
    "Générale": 1.0,
    "Périssable": 0.9,
    "Fragile": 0.95,
    "Dangereuse": 1.2
}

# Résultats
resultats = []
for m, data in motorisations.items():
    cout = distance * data["conso"] * data["prix"] * facteur_route[route]
    temps = (distance / data["vitesse"]) * facteur_route[route]
    emissions = distance * data["conso"] * data["emission"] * facteur_route[route]

    cout *= facteur_marchandise[marchandise]
    emissions *= facteur_marchandise[marchandise]

    validite = "✅ Valide" if temps <= (delai_max - 0.17) else "❌ Non valide"

    score = cout * 0.4 + temps * 0.3 + emissions * 0.3 if validite == "✅ Valide" else float("inf")

    resultats.append({
        "Motorisation": m,
        "Coût (FCFA)": round(cout, 2),
        "Temps (h)": round(temps, 2),
        "Émissions (kg CO2)": round(emissions, 2),
        "Score global": round(score, 2) if validite == "✅ Valide" else "N/A",
        "Validité": validite
    })

df = pd.DataFrame(resultats)

# Affichage tableau
st.subheader("📊 Résultats comparatifs")
st.dataframe(df)

# Graphiques
df_valides = df[df["Validité"] == "✅ Valide"]

fig1, ax1 = plt.subplots()
df_valides.plot(x="Motorisation", y="Coût (FCFA)", kind="bar", ax=ax1)
plt.title("Comparatif des coûts (solutions valides)")

fig2, ax2 = plt.subplots()
df_valides.plot(x="Motorisation", y="Temps (h)", kind="bar", ax=ax2, color="blue")
plt.title("Comparatif des temps (solutions valides)")

fig3, ax3 = plt.subplots()
df_valides.plot(x="Motorisation", y="Émissions (kg CO2)", kind="bar", ax=ax3, color="red")
plt.title("Comparatif des émissions (solutions valides)")

st.pyplot(fig1)
st.pyplot(fig2)
st.pyplot(fig3)

# Meilleures solutions
meilleures = {}
if not df_valides.empty:
    meilleures["moins_cher"] = df_valides.loc[df_valides["Coût (FCFA)"].idxmin()]["Motorisation"]
    meilleures["plus_rapide"] = df_valides.loc[df_valides["Temps (h)"].idxmin()]["Motorisation"]
    meilleures["moins_polluant"] = df_valides.loc[df_valides["Émissions (kg CO2)"].idxmin()]["Motorisation"]
    meilleures["meilleur_score"] = df_valides.loc[df_valides["Score global"].idxmin()]["Motorisation"]

st.subheader("🏆 Meilleures solutions")
if meilleures:
    st.write(f"💰 Moins coûteuse : **{meilleures['moins_cher']}**")
    st.write(f"⏱️ Plus rapide : **{meilleures['plus_rapide']}**")
    st.write(f"🌍 Moins polluante : **{meilleures['moins_polluant']}**")
    st.write(f"⚖️ Meilleure globale : **{meilleures['meilleur_score']}**")
else:
    st.warning("⚠️ Aucune solution valide ne respecte le délai.")

# Génération PDF
if st.button("📥 Exporter le rapport PDF"):
    resume = {"distance": distance, "poids": poids, "marchandise": marchandise, "route": route, "delai": delai_max}
    figures = {"Coût": fig1, "Temps": fig2, "Émissions": fig3}

    generer_pdf(df, resume, meilleures, figures)
    st.success("✅ Rapport PDF généré : rapport_logistique.pdf")
