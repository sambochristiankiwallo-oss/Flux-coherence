import streamlit as st
import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

st.set_page_config(page_title="Algorithme du Flux", page_icon="🌊")

st.title("🌊 Algorithme du Flux - Recherche de Cohérence")
st.write("Cette application illustre ton **algorithme du flux de cohérence**.")

# === Entrée utilisateur ===
st.header("📝 Entrez vos données")
n_rows = st.number_input("Nombre de lignes :", min_value=2, max_value=20, value=5, step=1)
n_cols = st.number_input("Nombre de colonnes :", min_value=2, max_value=20, value=3, step=1)

if st.button("🎲 Générer des données aléatoires"):
    # Génération de données aléatoires
    data = np.random.rand(n_rows, n_cols)
    df = pd.DataFrame(data, columns=[f"Col {i+1}" for i in range(n_cols)])
    
    st.subheader("📊 Données générées")
    st.dataframe(df.style.background_gradient(cmap="Blues"))

    # === Calcul du score de cohérence ===
    row_var = df.var(axis=1).mean()
    col_var = df.var(axis=0).mean()
    global_var = (row_var + col_var) / 2
    score = max(0, 100 - global_var * 100)

    st.subheader("📈 Score de cohérence global")
    st.metric(label="Score global de cohérence", value=f"{score:.2f} / 100")

    # === Recherche de la sous-matrice la plus cohérente ===
    best_var = float("inf")
    best_coords = None
    window_size = 2  # taille minimale de la sous-matrice (2x2)

    for i in range(n_rows - window_size + 1):
        for j in range(n_cols - window_size + 1):
            submatrix = df.iloc[i:i+window_size, j:j+window_size]
            var = submatrix.var().mean()
            if var < best_var:
                best_var = var
                best_coords = (i, j)

    st.subheader("🟩 Zone la plus cohérente")
    if best_coords:
        i, j = best_coords
        st.write(f"La zone la plus cohérente est autour de **lignes {i+1}-{i+window_size}** et **colonnes {j+1}-{j+window_size}**.")
        st.write(f"Variance locale : `{best_var:.4f}`")

        # === Heatmap avec surlignage ===
        fig, ax = plt.subplots()
        sns.heatmap(df, annot=True, fmt=".2f", cmap="coolwarm", ax=ax, cbar=True)

        # Ajouter un rectangle vert autour de la meilleure sous-matrice
        rect = plt.Rectangle((j, i), window_size, window_size, fill=False, color="green", lw=3)
        ax.add_patch(rect)

        st.pyplot(fig)
