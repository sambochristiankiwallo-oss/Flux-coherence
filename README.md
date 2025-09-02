# 🚚 Algorithme du Flux - Optimisation Logistique

Cette application **Streamlit** aide à trouver la meilleure solution logistique en comparant **temps de livraison, coût et émissions**.  
Elle prend en compte plusieurs scénarios : **Diesel, Hybride, Électrique**, avec différentes stratégies (Rapide, Normal, Éco).  

---

## ✨ Fonctionnalités
- Entrée des paramètres logistiques (distance, délai, etc.)
- Calcul automatique des temps, coûts et émissions
- Comparaison de plusieurs solutions logistiques
- Sélection de la **meilleure option optimisée**
- Visualisation avec graphiques interactifs

---

## 🔧 Installation locale (optionnel)

```bash
# Cloner le projet
git clone https://github.com/TON-REPO/optimisation-logistique.git
cd optimisation-logistique

# Créer un environnement virtuel
python -m venv venv
source venv/bin/activate   # sous Linux/Mac
venv\Scripts\activate      # sous Windows

# Installer les dépendances
pip install -r requirements.txt

# Lancer l'application
streamlit run streamlit_app.py
