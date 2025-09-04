import streamlit as st
import pandas as pd
import io
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# -----------------------------
# Données de coût énergétique
# -----------------------------
COUTS = {
    "Diesel": 720,      # FCFA / L
    "Essence": 695,     # FCFA / L
    "Hybride": 710,     # mix estimatif FCFA / L
    "Electrique": 109   # FCFA / kWh
}

# -----------------------------
# Fonction de simulation
# -----------------------------
def simuler_solutions(distance_km, delai_h):
    solutions = []

    scenarios = [
        ("Diesel", "Rapide", 80, 0.22, 18),
        ("Hybride", "Normal", 75, 0.18, 10),
        ("Electrique", "Éco", 70, 0.15, 0.03)
    ]

    for motorisation, scenario, vitesse, conso, emissions_unit in scenarios:
        temps_h = distance_km / vitesse
        cout = conso * distance_km * COUTS[motorisation if motorisation != "Electrique" else "Electrique"]
        emissions = emissions_unit * distance_km

        solutions.append({
            "Motorisation": motorisation,
            "Scénario": scenario,
            "Temps (h)": round(temps_h, 2),
            "Coût (FCFA)": round(cout, 2),
            "Émissions (kg)": round(emissions, 2)
        })

    df = pd.DataFrame(solutions)

    # Filtrage selon le délai
    df = df[df["Temps (h)"] <= (delai_h - 0.17)]  # toujours 10min d’avance
    return df

# -----------------------------
# Fonction PDF
# -----------------------------
def generate_pdf(solution):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)

    styles = getSampleStyleSheet()
    story = []

    # Titre
    story.append(Paragraph("🚚 Rapport Logistique Optimisé", styles['Title']))
    story.append(Spacer(1, 20))

    # Résumé
    story.append(Paragraph("Résumé de la solution optimale :", styles['Heading2']))
    story.append(Spacer(1, 12))

    data = [
        ["Paramètre", "Valeur"],
        ["Motorisation", solution["Motorisation"]],
        ["Scénario", solution["Scénario"]],
        ["Temps total (h)", f"{solution['Temps (h)']:.2f}"],
        ["Coût total (FCFA)", f"{solution['Coût (FCFA)']:.2f}"],
        ["Émissions (kg)", f"{solution['Émissions (kg)']:.2f}"]
    ]

    table = Table(data, colWidths=[150, 250])
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#4CAF50")),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
        ('BACKGROUND', (0, 1), (-1, -1), colors.whitesmoke),
        ('GRID', (0, 0), (-1, -1), 1, colors.black),
    ]))

    story.append(table)
    story.append(Spacer(1, 20))

    # Conclusion
    story.append(Paragraph("👉 Recommandation : privilégier la motorisation électrique pour réduire les coûts et minimiser l’impact écologique.", styles['Normal']))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Interface Streamlit
# -----------------------------
st.title("🔍 Optimisation Logistique")

distance = st.number_input("📏 Distance du trajet (km)", min_value=50, max_value=2000, value=300)
delai = st.number_input("⏰ Délai maximum (h)", min_value=1.0, max_value=24.0, value=4.0)

if st.button("Lancer la simulation 🚀"):
    df = simuler_solutions(distance, delai)

    if df.empty:
        st.error("⚠️ Aucune solution ne respecte le délai imposé.")
    else:
        st.subheader("📊 Comparatif des solutions")
        st.dataframe(df)

        # Meilleure solution (optimisation multicritères : coût + pollution + temps)
        meilleure = df.sort_values(by=["Coût (FCFA)", "Émissions (kg)", "Temps (h)"]).iloc[0]

        st.success(f"✅ Solution optimale : {meilleure['Motorisation']} - {meilleure['Scénario']}")
        st.write(f"⏱️ Temps : {meilleure['Temps (h)']} h")
        st.write(f"💰 Coût : {meilleure['Coût (FCFA)']} FCFA")
        st.write(f"🌱 Émissions : {meilleure['Émissions (kg)']} kg")

        # PDF
        pdf_buffer = generate_pdf(meilleure)
        st.download_button(
            label="📄 Télécharger le rapport PDF",
            data=pdf_buffer,
            file_name="rapport_logistique.pdf",
            mime="application/pdf"
        )
