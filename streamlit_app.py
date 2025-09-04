import streamlit as st
import pandas as pd
import io
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors

# -----------------------------
# Données de coût énergétique (FCFA)
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

    # Filtrage selon le délai (toujours 10min d’avance = 0.17h)
    df = df[df["Temps (h)"] <= (delai_h - 0.17)]
    return df

# -----------------------------
# Génération de graphiques
# -----------------------------
def generate_charts(df):
    charts = []

    # Coût
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="Motorisation", y="Coût (FCFA)", ax=ax, legend=False)
    ax.set_ylabel("FCFA")
    ax.set_title("Comparaison des coûts")
    buf1 = io.BytesIO()
    plt.savefig(buf1, format="png")
    buf1.seek(0)
    charts.append(buf1)
    plt.close(fig)

    # Émissions
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="Motorisation", y="Émissions (kg)", ax=ax, legend=False, color="green")
    ax.set_ylabel("kg CO₂")
    ax.set_title("Comparaison des émissions")
    buf2 = io.BytesIO()
    plt.savefig(buf2, format="png")
    buf2.seek(0)
    charts.append(buf2)
    plt.close(fig)

    # Temps
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="Motorisation", y="Temps (h)", ax=ax, legend=False, color="orange")
    ax.set_ylabel("Heures")
    ax.set_title("Comparaison des temps de trajet")
    buf3 = io.BytesIO()
    plt.savefig(buf3, format="png")
    buf3.seek(0)
    charts.append(buf3)
    plt.close(fig)

    return charts

# -----------------------------
# Génération du PDF
# -----------------------------
def generate_pdf(df, meilleure_solution):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer)
    styles = getSampleStyleSheet()
    story = []

    # Titre
    story.append(Paragraph("🚚 Rapport logistique optimisé", styles["Title"]))
    story.append(Spacer(1, 20))

    # Tableau des solutions
    story.append(Paragraph("Comparaison des solutions :", styles["Heading2"]))
    story.append(Spacer(1, 12))

    data = [list(df.columns)] + df.values.tolist()
    table = Table(data, colWidths=[100]*len(df.columns))
    table.setStyle(TableStyle([
        ("BACKGROUND", (0,0), (-1,0), colors.HexColor("#4CAF50")),
        ("TEXTCOLOR", (0,0), (-1,0), colors.white),
        ("ALIGN", (0,0), (-1,-1), "CENTER"),
        ("GRID", (0,0), (-1,-1), 1, colors.black)
    ]))
    story.append(table)
    story.append(Spacer(1, 20))

    # Graphiques
    charts = generate_charts(df)
    for chart in charts:
        story.append(Image(chart, width=400, height=250))
        story.append(Spacer(1, 20))

    # Meilleure solution
    story.append(Paragraph("✅ Solution recommandée :", styles["Heading2"]))
    story.append(Spacer(1, 12))
    story.append(Paragraph(
        f"La meilleure option est <b>{meilleure_solution['Motorisation']}</b> "
        f"({meilleure_solution['Scénario']}) avec un coût de "
        f"{meilleure_solution['Coût (FCFA)']} FCFA, un temps de "
        f"{meilleure_solution['Temps (h)']}h et des émissions de "
        f"{meilleure_solution['Émissions (kg)']} kg.",
        styles["Normal"]
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer

# -----------------------------
# Interface Streamlit
# -----------------------------
st.title("🚛 Assistant Intelligent d’Optimisation Logistique")

distance = st.number_input("Distance du trajet (km)", min_value=10, value=100, step=10)
delai = st.number_input("Délai maximum (heures)", min_value=1, value=4, step=1)

if st.button("Calculer les solutions optimales"):
    df = simuler_solutions(distance, delai)

    if not df.empty:
        meilleure_solution = df.sort_values(["Coût (FCFA)", "Émissions (kg)", "Temps (h)"]).iloc[0]

        st.write("### 🔍 Solutions disponibles")
        st.dataframe(df)

        st.write("### ✅ Solution optimale proposée")
        st.success(f"{meilleure_solution['Motorisation']} - {meilleure_solution['Scénario']}")

        pdf_buffer = generate_pdf(df, meilleure_solution)

        st.download_button(
            label="📄 Télécharger le rapport PDF",
            data=pdf_buffer,
            file_name="rapport_logistique.pdf",
            mime="application/pdf"
        )
    else:
        st.error("⚠️ Aucune solution ne respecte le délai (au moins 10 min d’avance exigés).")
