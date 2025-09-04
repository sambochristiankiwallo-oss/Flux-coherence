# 🚚 Flux Logistique Intelligent  

## 🇫🇷 Description (Français)  
Cette application est un **assistant intelligent d’optimisation logistique** développé avec **Streamlit**.  
Elle permet de comparer plusieurs scénarios de livraison en fonction de :  
- ⛽ **Coût du carburant** (essence, diesel, hybride, électrique)  
- ⏱️ **Temps de trajet** et respect des délais  
- 🌍 **Pollution (émissions de CO₂)**  
- 📦 **Adaptation aux types de marchandises**  
- 🛠️ **Maintenance et autonomie des véhicules**  

### ✅ Fonctionnalités principales  
1. Analyse comparative de plusieurs solutions :  
   - La **moins chère**  
   - La **plus rapide**  
   - La **moins polluante**  
   - La **mieux adaptée aux marchandises**  
2. Génération d’un **score logistique global** prenant en compte coûts, délais, pollution et capacité.  
3. Export des résultats sous forme de **PDF avec graphiques et tableaux**.  

### 🚀 Lancer l’application localement  
```bash
pip install -r requirements.txt
streamlit run app.py
