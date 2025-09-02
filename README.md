# 🌊 Algorithme du Flux - Recherche de Cohérence

Cette application illustre un **algorithme du flux de cohérence** permettant d’analyser et de visualiser les relations entre différentes variables d’un jeu de données.  
Elle est déployée avec **Streamlit Cloud** et accessible en ligne.

👉 [Accéder à l’application](https://TON-LIEN-STREAMLIT.streamlit.app)

---

## 🚀 Fonctionnalités

- 🔢 Génération aléatoire de données (pour tester rapidement l’algorithme).  
- 📂 Import de fichiers CSV (utiliser vos propres données).  
- 📈 Analyse des corrélations entre variables.  
- 🎨 Visualisation côte à côte :
  - Heatmap statique (Seaborn)  
  - Heatmap interactive (Plotly)  
- 💾 Exportation de la matrice en **CSV**.  

---

## 🛠️ Exemple d’utilisation

### 📦 Logistique (supply chain)  
Une entreprise analyse ses données de livraison :  
- Distance parcourue  
- Temps de transport  
- Coût du carburant  
- Taux de retard  

Grâce à l’application :  
- Elle identifie les variables **fortement corrélées** (ex. distance ↔️ carburant).  
- Elle visualise rapidement les **facteurs critiques**.  
- Elle optimise la **planification des livraisons**.

---

## 📊 Exemple chiffré

### Jeu de données (simplifié)
| Livraison | Distance (km) | Temps (h) | Carburant (€) | Retards (%) |
|-----------|---------------|-----------|---------------|-------------|
| 1         | 120           | 2.0       | 18            | 5           |
| 2         | 300           | 5.1       | 45            | 12          |
| 3         | 150           | 2.6       | 22            | 7           |
| 4         | 400           | 6.8       | 60            | 15          |
| 5         | 250           | 4.4       | 38            | 10          |

### Matrice de corrélation (calculée)
| Variable     | Distance | Temps  | Carburant | Retards |
|--------------|----------|--------|-----------|---------|
| **Distance** | 1.00     | 0.98   | 0.99      | 0.95    |
| **Temps**    | 0.98     | 1.00   | 0.97      | 0.93    |
| **Carburant**| 0.99     | 0.97   | 1.00      | 0.96    |
| **Retards**  | 0.95     | 0.93   | 0.96      | 1.00    |

### 🔥 Exemple visuel
![Matrice de corrélation](matrice_correlation_exemple.png)

**Interprétation :**  
- Plus la distance est grande, plus le temps, le carburant et les retards augmentent.  
- Réduire les distances peut améliorer les coûts et la ponctualité.  

---

## ⚙️ Installation locale (optionnel)

```bash
git clone https://github.com/TON-UTILISATEUR/flux-coherence.git
cd flux-coherence
pip install -r requirements.txt
streamlit run streamlit_app.py
