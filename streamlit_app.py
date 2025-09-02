import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt

# Exemple de données (remplace par tes calculs réels)
solutions = [
    {"Motorisation": "Diesel", "Scénario": "Rapide", "Temps": 2.8, "Coût": 18.5, "Émissions": 12.0},
    {"Motorisation": "Hybride", "Scénario": "Normal", "Temps": 2.7, "Coût": 15.2, "Émissions": 6.5},
    {"Motorisation": "Électrique", "Scénario": "Éco", "Temps": 2.5, "Coût": 13.1, "Émissions": 0.03},
]

df = pd.DataFrame(solutions)

st.subheader("📊 Comparatif des solutions")
st.dataframe(df)

# --- Graphique comparatif ---
fig, ax = plt.subplots(1, 3, figsize=(12, 4))

# Temps
ax[0].bar(df["Motorisation"], df["Temps"], color="skyblue")
ax[0].set_title("⏱ Temps (h)")

# Coût
ax[1].bar(df["Motorisation"], df["Coût"], color="lightgreen")
ax[1].set_title("💰 Coût (€)")

# Émissions
ax[2].bar(df["Motorisation"], df["Émissions"], color="salmon")
ax[2].set_title("🌱 Émissions (kg)")

st.pyplot(fig)

# --- Recommandation finale ---
best_solution = df.sort_values(by=["Coût", "Émissions"]).iloc[0]

st.success(f"✅ Solution optimale recommandée : **{best_solution['Motorisation']} - {best_solution['Scénario']}**\n\n"
           f"⏱ Temps : {best_solution['Temps']} h\n"
           f"💰 Coût : {best_solution['Coût']} €\n"
           f"🌱 Émissions : {best_solution['Émissions']} kg")
