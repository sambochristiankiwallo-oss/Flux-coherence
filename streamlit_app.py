import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
import plotly.express as px

# Configuration de la page
st.set_page_config(page_title="Algorithme du Flux", page_icon="🌊", layout="wide")

st.title("🌊 Algorithme du Flux - Recherche de Cohérence")
st.write("Cette application illustre un **algorithme du flux de cohérence**. "
         "👉 Tu peux soit entrer des données aléatoires, soit importer ton propre fichier CSV.")

# ================================
# 1. Choix de la source des données
# ================================
option = st.radio("📌 Choisissez la source des données :", ["🔢 Générer aléatoirement", "📂 Importer un fichier CSV"])

if option == "🔢 Générer aléatoirement":
    st.subheader("🔢 Génération aléatoire")
    n_rows = st.number_input("Nombre de lignes :", min_value=2, max_value=50, value=5)
    n_cols = st.number_input("Nombre de colonnes :", min_value=2, max_value=10, value=3)

    if st.button("🎲 Générer des données aléatoires"):
        data = np.random.randn(n_rows, n_cols)
        df = pd.DataFrame(data, columns=[f"Col_{i+1}" for i in range(n_cols)])
        st.write("📊 Données générées :", df)

elif option == "📂 Importer un fichier CSV":
    uploaded_file = st.file_uploader("📂 Importer un fichier CSV", type="csv")
    if uploaded_file is not None:
        df = pd.read_csv(uploaded_file)
        st.write("📊 Données importées :", df)

# =================================
# 2. Analyse de cohérence (corrélations)
# =================================
if 'df' in locals():
    st.subheader("📈 Analyse de cohérence")
    corr = df.corr()
    st.write("Matrice de corrélation :", corr)

    # Deux colonnes côte à côte
    col1, col2 = st.columns(2)

    with col1:
        st.subheader("🎨 Heatmap statique (Seaborn)")
        fig, ax = plt.subplots()
        sns.heatmap(corr, annot=True, cmap="coolwarm", ax=ax)
        st.pyplot(fig)

    with col2:
        st.subheader("🌀 Heatmap interactive (Plotly)")
        fig_plotly = px.imshow(corr,
                               text_auto=True,
                               color_continuous_scale="RdBu_r",
                               title="Matrice Interactive")
        st.plotly_chart(fig_plotly, use_container_width=True)

    # Télécharger la matrice
    csv = corr.to_csv().encode("utf-8")
    st.download_button("💾 Télécharger la matrice en CSV", data=csv, file_name="coherence.csv", mime="text/csv")
