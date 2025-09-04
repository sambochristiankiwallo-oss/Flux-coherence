import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet
import io

# ------------------------
# Config Streamlit
# ------------------------
st.set_page_config(
    page_title="Assistant Logistique Intelligent",
    page_icon="🚛",
    layout="wide"
)

st.image("logo.png", width=120)
st.title("🚚 Assistant Logistique Intelligent")
st.write("Optimisation des coûts, délais et émissions pour vos livraisons.")

# ------------------------
# Fonctions de calcul
# ------------------------
def calculer_cout(distance_km, motorisation):
    if motorisation == "Essence":
        consommation = 0.07 * distance_km  # L
        cout = consommation * 695
    elif motorisation == "Diesel":
        consommation = 0.055 * distance_km  # L
        cout = consommation * 720
    elif motorisation == "Hybride":
        consommation = 0.045 * distance_km  # L
        cout = consommation * 695
    elif motorisation == "Électrique":
        consommation = 0.18 * distance_km  # kWh
        cout = consommation * 109
    else:
        cout = float("inf")
    return round(cout, 2)

def calculer_emissions(distance_km, motorisation):
    if motorisation == "Essence":
        consommation = 0.07 * distance_km  # L
        emissions = consommation * 2.31
    elif motorisation == "Diesel":
        consommation = 0.055 * distance_km  # L
        emissions = consommation * 2.68
    elif motorisation == "Hybride":
        consommation = 0.045 * distance_km  # L
        emissions = consommation * 2.31
    elif motorisation == "Électrique":
        consommation = 0.18 * distance_km  # kWh
        emissions = consommation * 0.1
    else:
        emissions = float("inf")
    return round(emissions, 2)

def calculer_temps(distance_km, vitesse_moy=60):
    return round(distance_km / vitesse_moy, 2)

# ------------------------
# Génération des graphiques
# ------------------------
def generate_charts(df):
    charts = []

    # Coût
    fig, ax = plt.subplots()
    df.plot(kind="bar", x="Motorisation", y="Coût (FCFA)", ax=ax, legend=False, color="blue")
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

# ------------------------
# Génération du PDF
# ------------------------
def generate_pdf(df, meilleure_solution):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
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

# ------------------------
# Interface Streamlit
# ------------------------
distance = st.number_input("Entrez la distance (km)", min_value=1, value=100)
delai_max = st.number_input("Entrez le délai maximum (heures)", min_value=1, value=4)

if st.button("Calculer les solutions"):
    data = []
    for motorisation in ["Essence", "Diesel", "Hybride", "Électrique"]:
        cout = calculer_cout(distance, motorisation)
        emissions = calculer_emissions(distance, motorisation)
        temps = calculer_temps(distance)

        # On accepte seulement si le temps respecte le délai - 10 minutes
        if temps <= delai_max - (10/60):
            data.append({
                "Motorisation": motorisation,
                "Scénario": "Livraison directe",
                "Coût (FCFA)": cout,
                "Émissions (kg)": emissions,
                "Temps (h)": temps
            })

    df = pd.DataFrame(data)

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
        st.error("Aucune solution ne respecte le délai imposé.")
