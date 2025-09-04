import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
import io

# -------------------------------
# Données de base
# -------------------------------
VEHICULES = {
    "Moto essence": {"conso": 3, "co2": 0.07, "vitesse": 60, "capacité": 50, "type": "Moto"},
    "Voiture essence": {"conso": 7, "co2": 0.12, "vitesse": 80, "capacité": 300, "type": "Voiture"},
    "Camion diesel": {"conso": 25, "co2": 0.25, "vitesse": 70, "capacité": 5000, "type": "Camion"},
    "Tricycle essence": {"conso": 5, "co2": 0.09, "vitesse": 50, "capacité": 200, "type": "Tricycle"},
    "Voiture hybride": {"conso": 5, "co2": 0.05, "vitesse": 85, "capacité": 300, "type": "Voiture"},
    "Camion électrique": {"conso": 1.2, "co2": 0.0, "vitesse": 65, "capacité": 4000, "type": "Camion"},
}

COUTS = {
    "essence": 695,  # FCFA / litre
    "diesel": 720,   # FCFA / litre
    "kwh": 109       # FCFA / kWh
}

# -------------------------------
# Fonction de simulation
# -------------------------------
def run_simulation(distance, deadline, weight, goods, traffic):
    results = []

    for mode, data in VEHICULES.items():
        if weight > data["capacité"]:
            continue

        speed = data["vitesse"]
        if traffic == "Élevé":
            speed *= 0.7
        elif traffic == "Moyen":
            speed *= 0.85

        temps = round(distance / speed, 2)

        if "électrique" in mode.lower():
            consommation = (distance / 100) * data["conso"] * COUTS["kwh"]
            emission = (distance / 100) * data["co2"]
        elif "diesel" in mode.lower():
            consommation = (distance / 100) * data["conso"] * COUTS["diesel"]
            emission = (distance / 100) * data["co2"]
        else:
            consommation = (distance / 100) * data["conso"] * COUTS["essence"]
            emission = (distance / 100) * data["co2"]

        faisable = temps <= (deadline - 0.25)
        score = -consommation*0.4 - emission*0.3 - temps*0.3

        results.append({
            "Mode": mode,
            "Type": data["type"],
            "Temps (h)": temps,
            "Coût total (FCFA)": round(consommation, 0),
            "Émissions (kg CO2)": round(emission, 2),
            "Faisable": faisable,
            "Score": score
        })

    return pd.DataFrame(results)

# -------------------------------
# Fonction PDF
# -------------------------------
def generate_pdf(df, best_solutions, final_choice):
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)

    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("📊 Rapport d'optimisation logistique", styles['Title']))
    elements.append(Spacer(1, 12))

    table_data = [list(df.columns)] + df.values.tolist()
    table = Table(table_data)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0,0), (-1,0), colors.lightblue),
        ('ALIGN',(0,0),(-1,-1),'CENTER'),
        ('GRID', (0,0), (-1,-1), 1, colors.black),
    ]))
    elements.append(table)
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("🏆 Meilleures solutions par critère", styles['Heading2']))
    for crit, sol in best_solutions.items():
        elements.append(Paragraph(f"✔️ {crit} : {sol['Mode']} "
                                  f"(Coût: {sol['Coût total (FCFA)']} FCFA, "
                                  f"Temps: {sol['Temps (h)']} h, "
                                  f"CO₂: {sol['Émissions (kg CO2)']} kg)", styles['Normal']))
    elements.append(Spacer(1, 12))

    elements.append(Paragraph("🥇 Verdict final", styles['Heading2']))
    elements.append(Paragraph(
        f"La meilleure solution est <b>{final_choice['Mode']}</b> "
        f"(Coût: {final_choice['Coût total (FCFA)']} FCFA, "
        f"Temps: {final_choice['Temps (h)']} h, "
        f"CO₂: {final_choice['Émissions (kg CO2)']} kg).", styles['Normal']
    ))

    fig, ax = plt.subplots()
    df.set_index("Mode")[["Coût total (FCFA)", "Temps (h)", "Émissions (kg CO2)"]].plot(kind="bar", ax=ax)
    ax.set_ylabel("Valeurs")
    ax.set_title("Comparaison des solutions logistiques")
    plt.xticks(rotation=45)

    img_buffer = io.BytesIO()
    plt.savefig(img_buffer, format="png")
    plt.close(fig)
    img_buffer.seek(0)
    elements.append(Image(img_buffer, width=400, height=250))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# -------------------------------
# Interface Streamlit
# -------------------------------
st.title("🚚 Assistant intelligent d'optimisation logistique")

st.subheader("⚙️ Paramètres de simulation")
distance = st.number_input("Distance à parcourir (km)", 10, 2000, 200)
deadline = st.number_input("Délai de livraison (h)", 1, 48, 6)
weight = st.number_input("Poids de la marchandise (kg)", 1, 5000, 500)
goods = st.selectbox("Type de marchandise", ["Standard", "Périssable", "Dangereux"])
traffic = st.selectbox("Conditions de circulation", ["Faible", "Moyen", "Élevé"])

if st.button("🚀 Lancer la simulation"):
    df = run_simulation(distance, deadline, weight, goods, traffic)

    if df.empty:
        st.error("⚠️ Aucune solution disponible pour ce scénario (poids ou contraintes trop élevées).")
    else:
        st.write("### 📊 Résultats")
        st.dataframe(df)

        st.bar_chart(df.set_index("Mode")[["Coût total (FCFA)", "Temps (h)", "Émissions (kg CO2)"]])

        st.subheader("🏆 Meilleures solutions par critère")
        least_cost = df.loc[df["Coût total (FCFA)"].idxmin()]
        st.success(f"💰 Moins coûteuse : {least_cost['Mode']} ({least_cost['Coût total (FCFA)']} FCFA)")
        least_polluting = df.loc[df["Émissions (kg CO2)"].idxmin()]
        st.success(f"🌱 Moins polluante : {least_polluting['Mode']} ({least_polluting['Émissions (kg CO2)']} kg CO2)")
        fastest = df.loc[df["Temps (h)"].idxmin()]
        st.success(f"⚡ Plus rapide : {fastest['Mode']} ({fastest['Temps (h)']} h)")
        mixed_solution = df.loc[df["Score"].idxmax()]
        st.success(f"⚖️ Solution équilibrée : {mixed_solution['Mode']} (Score {round(mixed_solution['Score'],2)})")

        if weight > 1000:
            best_goods = df[df["Type"] == "Camion"].iloc[0]
        elif goods == "Périssable":
            best_goods = fastest
        else:
            best_goods = least_cost
        st.success(f"📦 Adaptée à la marchandise : {best_goods['Mode']}")

        best_vehicle_type = df.groupby("Type").apply(lambda g: g.loc[g["Score"].idxmax()]).reset_index(drop=True)
        for _, row in best_vehicle_type.iterrows():
            st.info(f"🚙 Meilleure {row['Type']} : {row['Mode']} (Score {round(row['Score'],2)})")

        if traffic == "Élevé":
            best_route = least_polluting
        elif traffic == "Moyen":
            best_route = mixed_solution
        else:
            best_route = fastest
        st.success(f"🛣️ Adaptée à la route : {best_route['Mode']}")

        st.subheader("🥇 Verdict final")
        final_choice = df[df["Faisable"]].sort_values("Score", ascending=False).iloc[0]
        st.success(
            f"✅ La meilleure solution globale est **{final_choice['Mode']}** "
            f"avec un coût de {final_choice['Coût total (FCFA)']} FCFA, "
            f"{final_choice['Émissions (kg CO2)']} kg CO2 et un temps de {final_choice['Temps (h)']} h."
        )

        best_solutions = {
            "Moins coûteuse": least_cost,
            "Moins polluante": least_polluting,
            "Plus rapide": fastest,
            "Solution mixte": mixed_solution,
            "Marchandise": best_goods,
            "Route": best_route,
        }

        pdf_file = generate_pdf(df, best_solutions, final_choice)
        st.download_button(
            label="📥 Télécharger le rapport PDF",
            data=pdf_file,
            file_name="rapport_logistique.pdf",
            mime="application/pdf"
        )
