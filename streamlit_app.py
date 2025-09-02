import streamlit as st
import numpy as np

st.set_page_config(page_title="Optimisation Trajet", page_icon="🚚")

st.title("🚚 Optimisation Trajet - Temps, Carburant et Retards")

st.write("Cette application simule un trajet et propose des recommandations pour optimiser le **temps** et le **carburant**.")

# === Entrée utilisateur ===
distance = st.number_input("Distance (km)", min_value=10, max_value=2000, value=200)
vitesse = st.slider("Vitesse moyenne (km/h)", min_value=30, max_value=150, value=90)
conso = st.number_input("Consommation (L/100km)", min_value=3.0, max_value=20.0, value=6.5)
prix = st.number_input("Prix carburant (€ / L)", min_value=1.0, max_value=3.0, value=1.8)

# === Calculs ===
temps = distance / vitesse
carburant = distance * conso / 100
cout = carburant * prix

# Retard estimé si vitesse < 60
retard = max(0, (60 - vitesse) * 0.05 * distance)

# === Résultats ===
st.subheader("📊 Résultats du trajet")
st.write(f"⏱️ Temps estimé : **{temps:.2f} heures**")
st.write(f"⛽ Carburant consommé : **{carburant:.1f} L**")
st.write(f"💰 Coût total : **{cout:.2f} €**")
st.write(f"🐌 Retard estimé : **{retard:.1f} minutes**")

# === Recommandations ===
st.subheader("💡 Recommandations")
if cout > 150:
    st.warning("⚠️ Le coût est élevé. Réduis la vitesse pour consommer moins de carburant.")
if retard > 0:
    st.error("🚦 Attention, vitesse trop faible : risque de retard important.")
if cout < 100 and retard == 0:
    st.success("✅ Ton trajet est optimisé : bon équilibre entre temps et coût.")

# Graphique comparatif
import matplotlib.pyplot as plt

vitesses = np.arange(40, 130, 10)
temps_list = distance / vitesses
carburant_list = distance * conso / 100
cout_list = carburant_list * prix

fig, ax = plt.subplots()
ax.plot(vitesses, temps_list, label="Temps (h)")
ax.plot(vitesses, cout_list, label="Coût (€)")
ax.set_xlabel("Vitesse (km/h)")
ax.legend()
st.pyplot(fig)
