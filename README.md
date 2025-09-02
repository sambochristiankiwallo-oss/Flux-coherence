# 🚚 Assistant Intelligent d’Optimisation Logistique

Cette application **Streamlit** est un assistant d’aide à la décision logistique.  
Elle optimise automatiquement les trajets de livraison en comparant plusieurs **motorisations** (Thermique, Hybride, Électrique) et différents **scénarios de conduite** (Éco, À l’heure, Express).  

L’algorithme recherche la **solution la moins coûteuse** qui respecte les délais tout en imposant une contrainte stricte :  
> ✅ Chaque livraison doit arriver **au moins 10 minutes avant le délai maximal fixé**.  

---

## ⚡ Fonctionnalités

- Simulation de trajets logistiques avec paramètres ajustables :  
  - Distance du trajet  
  - Prix carburant / énergie (€)  
  - Coût horaire du conducteur (€)  
  - Prix du CO₂ (€ / kg)  
  - Délai maximum (avec 10 minutes d’avance obligatoire)  

- Comparaison automatique de :  
  - **Motorisations** : Thermique, Hybride, Électrique  
  - **Scénarios logistiques** : Éco, À l’heure, Express  

- Résultats clairs et détaillés :  
  - Vitesse optimale  
  - Temps total (h)  
  - Coût total (€)  
  - Émissions CO₂ (kg)  
  - Motorisation & scénario retenus  

- Sélection automatique de la **meilleure solution logistique**.  

---

## 📊 Exemple de Résultat
