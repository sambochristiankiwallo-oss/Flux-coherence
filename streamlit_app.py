import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# ---------------- CONFIG ----------------
st.set_page_config(page_title="Assistant Logistique Intelligent", page_icon="🚚")

st.title("🚚 Assistant Intelligent d’Optimisation Logistique")
st.write("Cette application compare différentes solutions logistiques "
         "et propose automatiquement **la meilleure option** en tenant compte "
         "du **temps, du coût et des émissions**.")

# ---------------- DONNÉES ----------------
data = pd.DataFrame({
    "Motorisation": ["Diesel", "Hybride", "Électrique"],
    "Scénario": ["Rapide", "Normal", "Éco"],
    "Temps (h)": [2.8, 2.7, 2.5],
    "Coût (€)": [18.5, 15.2, 13.1],
    "Émissions (kg)": [12.0, 6.5, 0.03]
})

# ---------------- AFFICHAGE ----------------
st.subheader("📊 Comparatif des solutions")
st.dataframe(data)

# Graphique Temps
fig1, ax1 = plt.subplots()
ax1.bar(data["Motorisation"], data["Temps (h)"], color="skyblue")
ax1.set_ylabel("Temps (h)")
ax1.set_title("⏱️ Temps par motorisation")
st.pyplot(fig1)

# Graphique Coût
fig2, ax2 = plt.subplots()
ax2.bar(data["Motorisation"], data["Coût (€)"], color="lightgreen")
ax2.set_ylabel("Coût (€)")
ax2.set_title("💰 Coût par motorisation")
st.pyplot(fig2)

# Graphique Émissions
fig3, ax3 = plt.subplots()
ax3.bar(data["Motorisation"], data["Émissions (kg)"], color="salmon")
ax3.set_ylabel("Émissions (kg)")
ax3.set_title("🌱 Émissions par motorisation")
st.pyplot(fig3)

# ---------------- ANALYSE AUTOMATIQUE ----------------
best_solution = data.loc[data["Coût (€)"].idxmin()]

st.subheader("✅ Solution optimale recommandée")
st.success(
    f"**{best_solution['Motorisation']} - {best_solution['Scénario']}**\n\n"
    f"⏱️ Temps : {best_solution['Temps (h)']} h\n"
    f"💰 Coût : {best_solution['Coût (€)']} €\n"
    f"🌱 Émissions : {best_solution['Émissions (kg)']} kg"
)

# ---------------- RAPPORT PDF ----------------
def generate_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4

    c.setFont("Helvetica-Bold", 16)
    c.drawString(50, height - 50, "Rapport Logistique - Optimisation")

    c.setFont("Helvetica", 12)
    c.drawString(50, height - 100, "Comparatif des solutions :")

    y = height - 130
    for i, row in data.iterrows():
        text = (f"- {row['Motorisation']} ({row['Scénario']}): "
                f"{row['Temps (h)']} h, {row['Coût (€)']} €, {row['Émissions (kg)']} kg CO2")
        c.drawString(60, y, text)
        y -= 20

    c.setFont("Helvetica-Bold", 12)
    c.drawString(50, y - 20, "✅ Solution optimale :")
    c.setFont("Helvetica", 12)
    c.drawString(70, y - 40, 
                 f"{best_solution['Motorisation']} - {best_solution['Scénario']} "
                 f"({best_solution['Temps (h)']} h, "
                 f"{best_solution['Coût (€)']} €, "
                 f"{best_solution['Émissions (kg)']} kg CO2)")

    c.save()
    buffer.seek(0)
    return buffer

st.subheader("📥 Exporter le rapport")
pdf_file = generate_pdf()
st.download_button(
    label="Télécharger le rapport PDF",
    data=pdf_file,
    file_name="rapport_logistique.pdf",
    mime="application/pdf"
)
