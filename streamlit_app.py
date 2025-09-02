import streamlit as st
import pandas as pd
import numpy as np

# -------------------------------
# Paramètres de simulation
# -------------------------------
scenarios = {
    "Éco": {"w_fuel": 0.6, "w_time": 0.2, "w_emiss": 0.2},
    "À l’heure": {"w_fuel": 0.3, "w_time": 0.5, "w_emiss": 0.2},
    "Express": {"w_fuel": 0.2, "w_time": 0.6, "w_emiss": 0.2},
}

motorisations = {
    "Thermique": {"conso_L100": 6.5, "emiss_CO2": 2.3},   # kg CO₂ par litre
    "Hybride": {"conso_L100": 4.5, "emiss_CO2": 1.5},
    "Électrique": {"conso_L100": 18/100, "emiss_CO2": 0.05}  # kWh/km
}

# -------------------------------
# Fonction d’optimisation
# -------------------------------
def optimize_speeds(distance_km, fuel_price, driver_cost_h,
                    v_min, v_max, w_fuel, w_time, w_emiss,
                    motor, carbon_price, deadline_h):

    speeds = np.linspace(v_min, v_max, 20)
    best = None

    for v in speeds:
        # Temps (heures)
        time_h = distance_km / v

        # Conso carburant ou énergie
        conso_L100 = motorisations[motor]["conso_L100"]
        fuel_used = conso_L100 * distance_km / 100

        # Coût carburant
        cost_fuel = fuel_used * fuel_price

        # Coût temps conducteur
        cost_time = time_h * driver_cost_h

        # Émissions CO₂
        emissions = fuel_used * motorisations[motor]["emiss_CO2"]

        # Coût CO₂
        cost_co2 = emissions * carbon_price

        # Coût total pondéré
        cost_total = w_fuel * cost_fuel + w_time * cost_time + w_emiss * cost_co2

        if best is None or cost_total < best["Coût total (€)"]:
            best = {
                "Vitesse optimale (km/h)": v,
                "Temps total (h)": time_h,
                "Coût total (€)": cost_total,
                "Émissions CO₂ (kg)": emissions,
            }

    return best

# -------------------------------
# Application Streamlit
# -------------------------------
st.title("🚚 Assistant Intelligent d’Optimisation Logistique")

st.sidebar.header("Paramètres")
distance = st.sidebar.number_input("Distance du trajet (km)", 10, 1000, 300)
fuel_price = st.sidebar.number_input("Prix carburant/énergie (€/L ou €/kWh)", 0.5, 3.0, 1.8, 0.1)
driver_cost_h = st.sidebar.number_input("Coût horaire conducteur (€)", 10, 100, 25, 1)
deadline_h = st.sidebar.number_input("Délai max (heures)", 1, 24, 4, 1)
carbon_price = st.sidebar.number_input("Prix du CO₂ (€/kg)", 0.0, 1.0, 0.1, 0.01)

v_min = st.sidebar.slider("Vitesse min (km/h)", 30, 60, 50)
v_max = st.sidebar.slider("Vitesse max (km/h)", 80, 140, 120)

margin_h = 10 / 60  # 10 minutes

st.subheader("🔎 Recherche de la meilleure solution logistique")

best_solution = None

for mot in motorisations.keys():
    for scen_name, weights in scenarios.items():
        result = optimize_speeds(
            distance, fuel_price, driver_cost_h,
            v_min=v_min, v_max=v_max,
            w_fuel=weights["w_fuel"], w_time=weights["w_time"], w_emiss=weights["w_emiss"],
            motor=mot, carbon_price=carbon_price,
            deadline_h=deadline_h
        )

        # Vérification stricte : toujours 10 minutes d'avance
        if result["Temps total (h)"] <= deadline_h - margin_h:
            result["Motorisation"] = mot
            result["Scénario"] = scen_name

            if best_solution is None or result["Coût total (€)"] < best_solution["Coût total (€)"]:
                best_solution = result

# -------------------------------
# Résultat final
# -------------------------------
if best_solution:
    st.success(f"✅ Solution optimale trouvée :")
    st.write(f"- Motorisation : **{best_solution['Motorisation']}**")
    st.write(f"- Scénario : **{best_solution['Scénario']}**")
    st.write(f"- Vitesse optimale : **{best_solution['Vitesse optimale (km/h)']:.1f} km/h**")
    st.write(f"- Temps total : **{best_solution['Temps total (h)']:.2f} h**")
    st.write(f"- Coût total : **{best_solution['Coût total (€)']:.2f} €**")
    st.write(f"- Émissions : **{best_solution['Émissions CO₂ (kg)']:.2f} kg**")
else:
    st.error("⚠️ Aucune solution ne respecte le délai avec 10 minutes d'avance obligatoire.")
