import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from io import BytesIO
from reportlab.lib.pagesizes import A4
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet

# -------------------------------
# PARAMÈTRES DES MODES DE TRANSPORT
# -------------------------------
vehicles = {
    "Diesel": {"conso": 0.07, "fuel_cost": 720, "emission": 2.68, "maintenance": 0.05, "speed": 70},
    "Essence": {"conso": 0.08, "fuel_cost": 695, "emission": 2.31, "maintenance": 0.04, "speed": 65},
    "Hybride": {"conso": 0.05, "fuel_cost": 695, "emission": 1.2, "maintenance": 0.06, "speed": 60},
    "Électrique": {"conso": 0.18, "fuel_cost": 109, "emission": 0.5, "maintenance": 0.03, "speed": 55},
}

# -------------------------------
# FONCTION D’ANALYSE
# -------------------------------
def run_simulation(distance, deadline, weight, goods, traffic, weights):
    results = []

    # Facteur trafic
    traffic_factor = {"Faible": 1.0, "Moyen": 1.2, "Élevé": 1.5}[traffic]

    for mode, params in vehicles.items():
        # Temps ajusté au trafic
        time = (distance / params["speed"]) * traffic_factor

        # Consommation
        consumption = params["conso"] * distance

        # Coût carburant
        cost = consumption * params["fuel_cost"]

        # Entretien
        maintenance_cost = params["maintenance"] * distance

        # Émissions CO2
        emission = consumption * params["emission"]

        # Contraintes
        penalty = 1.0
        if goods == "Périssable" and time > deadline * 0.9:
            penalty *= 0.8
        if goods == "Dangereux" and mode == "Électrique":
            penalty *= 0.7
        if weight > 3000 and mode in ["Hybride", "Électrique"]:
            penalty *= 0.6

        # Faisabilité : doit arriver au moins 10 min avant
        feasible = (time <= deadline - 0.166)

        # Score pondéré
        w_time, w_cost, w_emission, w_other = weights
        score = (
            (1 / time if time > 0 else 0) * w_time +
            (1 / (cost + maintenance_cost) if cost + maintenance_cost > 0 else 0) * w_cost +
            (1 / emission if emission > 0 else 0) * w_emission +
            penalty * w_other
        ) * 1000

        results.append({
            "Mode": mode,
            "Temps (h)": round(time, 2),
            "Coût total (FCFA)": round(cost + maintenance_cost, 0),
            "Émissions (kg CO2)": round(emission, 2),
            "Score": round(score, 2),
            "Faisable": feasible
        })

    return pd.DataFrame(results)

# -------------------------------
# FONCTION EXPORT PDF
# -------------------------------
def export_pdf(df, filename="rapport.pdf", titre="Rapport logistique"):
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph(titre, styles["Title"]))
    elements.append(Spacer(1, 20))

    # Tableau comparatif
    table_data = [df.columns.tolist()] + df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.grey),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.whitesmoke),
        ("ALIGN", (0, 0), (-1, -1), "CENTER"),
        ("GRID", (0, 0), (-1, -1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 20))

    # Graphique barres
    fig, ax = plt.subplots(figsize=(6, 4))
    df.set_index("Mode")[["Coût total (FCFA)", "Émissions (kg CO2)"]].plot(kind="bar", ax=ax)
    plt.ylabel("Valeurs")
    plt.title("Comparaison des coûts et émissions")
    buf = BytesIO()
    plt.savefig(buf, format="PNG")
    plt.close(fig)
    buf.seek(0)
    elements.append(Image(buf, width=400, height=300))
    elements.append(Spacer(1, 20))

    # Diagramme radar
    categories = ["Temps (h)", "Coût total (FCFA)", "Émissions (kg CO2)", "Score"]
    N = len(categories)
    angles = np.linspace(0, 2 * np.pi, N, endpoint=False).tolist()
    angles += angles[:1]

    fig = plt.figure(figsize=(6, 6))
    ax = plt.subplot(111, polar=True)
    for _, row in df.iterrows():
        values = [row[c] for c in categories]
        values[0] = 1 / values[0] if values[0] > 0 else 0
        values[1] = 1 / values[1] if values[1] > 0 else 0
        values[2] = 1 / values[2] if values[2] > 0 else 0
        values += values[:1]
        ax.plot(angles, values, label=row["Mode"])
        ax.fill(angles, values, alpha=0.1)
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(categories)
    ax.set_title("Radar multi-critères", size=14, y=1.1)
    ax.legend(loc="upper right", bbox_to_anchor=(1.3, 1.1))
    buf2 = BytesIO()
    plt.savefig(buf2, format="PNG")
    plt.close(fig)
    buf2.seek(0)
    elements.append(Image(buf2, width=400, height=400))

    doc.build(elements)
    with open(filename, "wb") as f:
        f.write(buffer.getvalue())
    return filename

# -------------------------------
# INTERFACE STREAMLIT
# -------------------------------
st.title("🚚 Assistant intelligent d’optimisation logistique")

# Pondération des critères
st.subheader("⚖️ Pondération des critères")
w_time = st.slider("Poids du temps", 0.0, 1.0, 0.25, 0.05)
w_cost = st.slider("Poids du coût", 0.0, 1.0, 0.25, 0.05)
w_emission = st.slider("Poids des émissions", 0.0, 1.0, 0.25, 0.05)
w_other = st.slider("Poids des contraintes", 0.0, 1.0, 0.25, 0.05)

# Normalisation
total_weight = w_time + w_cost + w_emission + w_other
if total_weight == 0:
    w_time = w_cost = w_emission = w_other = 0.25
    total_weight = 1
weights = (w_time / total_weight, w_cost / total_weight, w_emission / total_weight, w_other / total_weight)

# Entrées utilisateur
st.subheader("⚙️ Simulation")
distance = st.number_input("Distance (km)", 10, 2000, 200)
deadline = st.number_input("Délai de livraison (h)", 1, 48, 6)
weight = st.number_input("Poids marchandise (kg)", 1, 5000, 500)
goods = st.selectbox("Type de marchandise", ["Standard", "Périssable", "Dangereux"])
traffic = st.selectbox("Trafic", ["Faible", "Moyen", "Élevé"])

if st.button("🚀 Lancer la simulation"):
    df = run_simulation(distance, deadline, weight, goods, traffic, weights)
    st.write("### Résultats de la simulation")
    st.dataframe(df)

    st.bar_chart(df.set_index("Mode")[["Coût total (FCFA)", "Temps (h)", "Émissions (kg CO2)"]])

    feasible = df[df["Faisable"] == True]
    if not feasible.empty:
        best_solution = feasible.loc[feasible["Score"].idxmax()]
        st.success(f"✅ Solution optimale : {best_solution['Mode']} "
                   f"(Temps : {best_solution['Temps (h)']}h, "
                   f"Coût : {best_solution['Coût total (FCFA)']} FCFA, "
                   f"Émissions : {best_solution['Émissions (kg CO2)']} kg CO2)")
    else:
        st.error("⚠️ Aucune solution ne respecte le délai imposé.")

    pdf_file = export_pdf(df, filename="rapport_logistique.pdf", titre="Rapport d'optimisation logistique")
    with open(pdf_file, "rb") as f:
        st.download_button(
            label="📄 Télécharger le rapport PDF",
            data=f,
            file_name="rapport_logistique.pdf",
            mime="application/pdf"
        )
