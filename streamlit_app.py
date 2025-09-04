import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# -----------------------------
# Paramètres des options
# -----------------------------
PRIX_ESSENCE = 695   # FCFA / L
PRIX_DIESEL = 720    # FCFA / L
PRIX_KWH = 109       # FCFA / kWh

# Consommations
CONS_ESSENCE = 7 / 100    # L/km
CONS_DIESEL = 7 / 100     # L/km
CONS_HYBRIDE_ESS = 4 / 100   # L/km
CONS_HYBRIDE_KWH = 0.1       # kWh/km
CONS_ELEC = 0.2              # kWh/km

# Emissions (kg CO₂ par km)
CO2_ESSENCE = 0.26
CO2_DIESEL = 0.23
CO2_HYBRIDE = 0.15
CO2_ELEC = 0.05

# -----------------------------
# Interface utilisateur
# -----------------------------
st.title("🚚 Optimisation logistique intelligente")
st.write("Comparatif des coûts (FCFA), temps, et émissions CO₂ pour différents scénarios")

distance = st.number_input("Distance à parcourir (km)", min_value=10, value=100)
delai_max = st.number_input("Délai maximum (heures)", min_value=1, value=4)

# -----------------------------
# Calculs
# -----------------------------
resultats = []

# Thermique Essence
cout_ess = distance * CONS_ESSENCE * PRIX_ESSENCE
temps_ess = distance / 60
resultats.append({
    "Option": "Thermique Essence",
    "Coût (FCFA)": round(cout_ess, 2),
    "Temps (h)": round(temps_ess, 2),
    "Émissions CO₂ (kg)": round(distance * CO2_ESSENCE, 2)
})

# Thermique Diesel
cout_diesel = distance * CONS_DIESEL * PRIX_DIESEL
temps_diesel = distance / 60
resultats.append({
    "Option": "Thermique Diesel",
    "Coût (FCFA)": round(cout_diesel, 2),
    "Temps (h)": round(temps_diesel, 2),
    "Émissions CO₂ (kg)": round(distance * CO2_DIESEL, 2)
})

# Hybride
cout_hybride = (distance * CONS_HYBRIDE_ESS * PRIX_ESSENCE) + (distance * CONS_HYBRIDE_KWH * PRIX_KWH)
temps_hybride = distance / 55
resultats.append({
    "Option": "Hybride",
    "Coût (FCFA)": round(cout_hybride, 2),
    "Temps (h)": round(temps_hybride, 2),
    "Émissions CO₂ (kg)": round(distance * CO2_HYBRIDE, 2)
})

# Électrique
cout_elec = distance * CONS_ELEC * PRIX_KWH
temps_elec = distance / 50
resultats.append({
    "Option": "Électrique",
    "Coût (FCFA)": round(cout_elec, 2),
    "Temps (h)": round(temps_elec, 2),
    "Émissions CO₂ (kg)": round(distance * CO2_ELEC, 2)
})

# -----------------------------
# Comparatif tableau
# -----------------------------
df = pd.DataFrame(resultats)
df["Valide ?"] = df["Temps (h)"] <= (delai_max - 0.16)

st.subheader("📊 Résultats comparatifs")
st.dataframe(df)

# -----------------------------
# Graphiques
# -----------------------------
st.subheader("📈 Comparaison des coûts")
fig, ax = plt.subplots()
ax.bar(df["Option"], df["Coût (FCFA)"], color="orange")
ax.set_ylabel("Coût (FCFA)")
plt.xticks(rotation=30)
st.pyplot(fig)

st.subheader("🌍 Comparaison des émissions CO₂")
fig2, ax2 = plt.subplots()
ax2.bar(df["Option"], df["Émissions CO₂ (kg)"], color="green")
ax2.set_ylabel("Émissions CO₂ (kg)")
plt.xticks(rotation=30)
st.pyplot(fig2)

# -----------------------------
# Recommandations
# -----------------------------
solutions_valides = df[df["Valide ?"] == True]

if not solutions_valides.empty:
    meilleur_cout = solutions_valides.loc[solutions_valides["Coût (FCFA)"].idxmin()]
    plus_rapide = solutions_valides.loc[solutions_valides["Temps (h)"].idxmin()]
    moins_polluante = solutions_valides.loc[solutions_valides["Émissions CO₂ (kg)"].idxmin()]

    df_equilibre = solutions_valides.copy()
    df_equilibre["Score"] = (df_equilibre["Coût (FCFA)"]/df_equilibre["Coût (FCFA)"].max())*0.6 + \
                            (df_equilibre["Émissions CO₂ (kg)"]/df_equilibre["Émissions CO₂ (kg)"].max())*0.4
    meilleur_equilibre = df_equilibre.loc[df_equilibre["Score"].idxmin()]

    st.success(f"✅ Meilleure solution économique : **{meilleur_cout['Option']}**")
    st.info(f"⏱️ Option la plus rapide : **{plus_rapide['Option']}**")
    st.warning(f"🌍 Option la moins polluante : **{moins_polluante['Option']}**")
    st.success(f"⚖️ Option la plus équilibrée (rentable + écologique) : **{meilleur_equilibre['Option']}**")

    # -----------------------------
    # Rapport automatique
    # -----------------------------
    st.subheader("📑 Rapport automatique")
    rapport = f"""
    Pour un trajet de **{distance} km** avec un délai maximum de **{delai_max} h** :

    - L'option **{plus_rapide['Option']}** est la plus rapide ({plus_rapide['Temps (h)']} h).
    - L'option **{meilleur_cout['Option']}** est la moins chère ({meilleur_cout['Coût (FCFA)']} FCFA).
    - L'option **{moins_polluante['Option']}** émet le moins de CO₂ ({moins_polluante['Émissions CO₂ (kg)']} kg).
    - Enfin, l'option **{meilleur_equilibre['Option']}** offre le meilleur équilibre entre coût et écologie.

    👉 Recommandation finale : privilégier **{meilleur_equilibre['Option']}** pour concilier coûts maîtrisés et impact environnemental réduit.
    """
    st.write(rapport)

else:
    st.error("❌ Aucune option ne respecte la contrainte de délai.")
    from reportlab.lib.pagesizes import A4
from reportlab.platypus import Table, TableStyle, Paragraph, SimpleDocTemplate, Spacer, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO

if not solutions_valides.empty:
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    styles = getSampleStyleSheet()
    title_style = styles["Title"]
    normal_style = styles["Normal"]

    # 🔹 Logo en haut (si disponible)
    try:
        logo = Image("logo.png", width=100, height=60)  # adapte la taille si besoin
        elements.append(logo)
    except:
        elements.append(Paragraph("🚚 [Pas de logo trouvé]", normal_style))

    elements.append(Spacer(1, 15))

    # 🔹 Titre
    elements.append(Paragraph("Rapport d’optimisation logistique", title_style))
    elements.append(Spacer(1, 20))

    # 🔹 Informations de base
    elements.append(Paragraph(f"📏 Distance : {distance} km", normal_style))
    elements.append(Paragraph(f"⏱️ Délai maximum : {delai_max} h", normal_style))
    elements.append(Spacer(1, 15))

    # 🔹 Tableau comparatif
    data = [["Option", "Coût (FCFA)", "Temps (h)", "Émissions CO₂ (kg)"]]
    for _, row in df.iterrows():
        data.append([row["Option"], row["Coût (FCFA)"], row["Temps (h)"], row["Émissions CO₂ (kg)"]])

    table = Table(data, colWidths=[150, 100, 100, 120])
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#264653")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 1, colors.black),
        ("FONTNAME", (0,0), (-1,0), "Helvetica-Bold"),
        ("FONTSIZE", (0,0), (-1,-1), 10),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # 🔹 Recommandations
    recommendation = f"""
    ✅ Meilleure solution économique : {meilleur_cout['Option']} ({meilleur_cout['Coût (FCFA)']} FCFA)  
    ⏱️ Plus rapide : {plus_rapide['Option']} ({plus_rapide['Temps (h)']} h)  
    🌍 Moins polluante : {moins_polluante['Option']} ({moins_polluante['Émissions CO₂ (kg)']} kg CO₂)  
    ⚖️ Meilleur équilibre : {meilleur_equilibre['Option']}
    """

    elements.append(Paragraph("📑 Recommandations :", styles["Heading2"]))
    elements.append(Paragraph(recommendation, normal_style))

    doc.build(elements)

    st.download_button(
        label="📥 Télécharger le rapport PDF avec logo",
        data=buffer.getvalue(),
        file_name="rapport_logistique.pdf",
        mime="application/pdf"
    )
