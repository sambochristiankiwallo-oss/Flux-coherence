# 🚚 Assistant Intelligent d’Optimisation Logistique

## 📌 Description
Cette application aide les entreprises de transport et de logistique à **planifier efficacement leurs livraisons** en tenant compte de :
- ⏱️ Délais de livraison (avec obligation d’être 15 minutes en avance)  
- 💰 Coûts réels (FCFA, basé sur consommation et carburant/électricité)  
- 🌱 Impact environnemental (CO₂ émis ou zéro émission pour véhicules électriques)  
- 📦 Nature des marchandises (périssables, dangereux, standard)  
- ⚡ Autonomie et capacité de chaque véhicule  
- 🚦 Conditions de route et trafic  

L’application compare plusieurs motorisations (**essence, diesel, hybride, électrique, moto, tricycle, camion**) et propose :  
- La **solution la moins coûteuse** 💰  
- La **solution la moins polluante** 🌱  
- La **solution la plus rapide** ⏱️  
- La **solution globale optimale** (pondération coût/CO₂/temps)  

Enfin, un **rapport PDF détaillé** est généré, avec :  
- Un résumé des meilleures solutions  
- Une liste détaillée par véhicule (coût, CO₂, temps, score)  
- Un graphique comparatif 📊  

---

## 🚀 Fonctionnalités principales
- Entrée manuelle de la distance **ou** calcul automatique via coordonnées GPS (Haversine)  
- Saisie du poids, type de marchandise, type de route, trafic  
- Pondération personnalisée des critères (coût, CO₂, temps)  
- Graphiques interactifs et tableau comparatif  
- Génération d’un PDF exportable avec résultats + graphiques  

---

## ⚙️ Installation

1. Clonez le dépôt :
```bash
git clone https://github.com/ton-compte/ton-repo.git
cd ton-repo
