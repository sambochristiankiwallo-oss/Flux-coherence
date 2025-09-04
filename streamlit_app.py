import streamlit as st
import matplotlib.pyplot as plt
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

# ------------------------
# 1. Titre et description
# ------------------------
st.set_page_config(page_title="Assistant Logistique Intelligent", page_icon="🚚", layout="centered")

st.title("🚚 Assistant Intelligent d’Optimisation Logistique")
st.write("Entrez vos propres données pour comparer les solutions de transport et obtenir la meilleure option.")

# ------------------------
# 2. Champs de saisie
# ------------------------
distance = st.number_input("Distance à parcourir (km)", min_value=1, step=1)
delai = st.number_input("Délai maximum (heures)", min_value=1, step=1)
marchandises = st.text_input("Type de marchandises (optionnel)")

# ------------------------
# 3. Calcul des résultats
# ------------------------
if distance > 0 and delai > 0:
    st.subheader("📊 Résultats d’optimisation")

    # Hypothèses de vitesses moyennes
    vitesses = {
        "Thermique": 60,    # km/h
        "Hybride": 65,      # km/h
        "Électrique": 70    # km/h
    }

    resultats = {}
    for mode, vitesse in vitesses.items():
        temps = distance / vitesse
        resultats[mode] = temps

    # ------------------------
    # 4. Affichage textuel
    # ------------------------
    meilleur_mode = None
    meilleur_temps = float("inf")

    for mode, temps in resultats.items():
        if temps <= delai - 0.25:  # Marge de 15 minutes
            st.success(f"{mode} : {temps:.2f} h ✅ (respecte le délai)")
            if temps < meilleur_temps:
                meilleur_temps = temps
                meilleur_mode = mode
        else:
            st.warning(f"{mode} : {temps:.2f} h ❌ (dépasse le délai)")

    if meilleur_mode:
        st.info(f"👉 Meilleure option : **{meilleur_mode}** ({meilleur_temps:.2f} h)")
    else:
        st.error("⚠️ Aucune solution ne respecte le délai avec la marge de 15 minutes.")

    # ------------------------
    # 5. Graphique comparatif
    # ------------------------
    st.subheader("📈 Comparaison graphique")
    fig, ax = plt.subplots()
    ax.bar(resultats.keys(), resultats.values(), color=["#FF7043", "#66BB6A", "#42A5F5"])
    ax.axhline(y=delai, color="r", linestyle="--", label="Délai max")
    ax.axhline(y=delai - 0.25, color="g", linestyle="--", label="Délai - 15 min")
    ax.set_ylabel("Temps (heures)")
    ax.set_title("Comparaison des temps de trajet")
    ax.legend()
    st.pyplot(fig)

    # ------------------------
    # 6. Rapport PDF
    # ------------------------
    st.subheader("📄 Télécharger un rapport PDF")
    if st.button("Générer le rapport"):
        file_name = "rapport_logistique.pdf"
        c = canvas.Canvas(file_name, pagesize=letter)
        c.setFont("Helvetica", 12)
        c.drawString(100, 750, "Rapport d’optimisation logistique")
        c.drawString(100, 730, f"Distance : {distance} km")
        c.drawString(100, 710, f"Délai maximum : {delai} h")
        if marchandises:
            c.drawString(100, 690, f"Marchandises : {marchandises}")

        y = 660
        for mode, temps in resultats.items():
            c.drawString(100, y, f"{mode} : {temps:.2f} h")
            y -= 20

        if meilleur_mode:
            c.drawString(100, y - 10, f"✅ Meilleure option : {meilleur_mode} ({meilleur_temps:.2f} h)")
        else:
            c.drawString(100, y - 10, "⚠️ Aucune solution valide dans le délai.")

        c.save()

        with open(file_name, "rb") as f:
            st.download_button("⬇️ Télécharger le rapport", f, file_name, mime="application/pdf")
