import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image
from reportlab.lib.styles import getSampleStyleSheet
from reportlab.lib import colors
from reportlab.lib.pagesizes import A4
import io

st.set_page_config(page_title="Assistant Logistique Intelligent", page_icon="🚚", layout="wide")

# =========================
# Données véhicules (corrigées + enrichies)
# =========================
VEHICULES = {
    # conso thermique = L/100km ; électrique = kWh/km (valeurs réalistes)
    "Moto essence":      {"conso": 3.0,   "energie": "essence", "co2": 0.07, "vitesse": 60, "capacité": 50,   "type": "Moto",      "maintenance_fcfa_km": 15, "fiabilite": 0.85, "autonomie_km": None, "route": {"Urbain":1.0,"Mixte":0.9,"Difficile":0.6}},
    "Moto électrique":   {"conso": 0.07,  "energie": "elec",    "co2": 0.00, "vitesse": 65, "capacité": 60,   "type": "Moto",      "maintenance_fcfa_km": 8,  "fiabilite": 0.9,  "autonomie_km": 120,  "route": {"Urbain":1.0,"Mixte":0.95,"Difficile":0.6}},
    "Tricycle essence":  {"conso": 5.0,   "energie": "essence", "co2": 0.09, "vitesse": 50, "capacité": 200,  "type": "Tricycle",  "maintenance_fcfa_km": 20, "fiabilite": 0.8,  "autonomie_km": None, "route": {"Urbain":0.95,"Mixte":1.0,"Difficile":0.7}},
    "Tricycle électrique":{"conso": 0.18, "energie": "elec",    "co2": 0.00, "vitesse": 45, "capacité": 250,  "type": "Tricycle",  "maintenance_fcfa_km": 10, "fiabilite": 0.85, "autonomie_km": 140,  "route": {"Urbain":0.95,"Mixte":1.0,"Difficile":0.7}},
    "Voiture essence":   {"conso": 7.0,   "energie": "essence", "co2": 0.12, "vitesse": 80, "capacité": 300,  "type": "Voiture",   "maintenance_fcfa_km": 30, "fiabilite": 0.9,  "autonomie_km": None, "route": {"Urbain":0.9,"Mixte":1.0,"Difficile":0.8}},
    "Voiture hybride":   {"conso": 5.0,   "energie": "essence", "co2": 0.05, "vitesse": 85, "capacité": 300,  "type": "Voiture",   "maintenance_fcfa_km": 28, "fiabilite": 0.92, "autonomie_km": None, "route": {"Urbain":0.95,"Mixte":1.0,"Difficile":0.85}},
    "Camion diesel":     {"conso": 25.0,  "energie": "diesel",  "co2": 0.25, "vitesse": 70, "capacité": 5000, "type": "Camion",    "maintenance_fcfa_km": 80, "fiabilite": 0.95, "autonomie_km": None, "route": {"Urbain":0.8,"Mixte":1.0,"Difficile":0.95}},
    "Camion électrique": {"conso": 1.2,   "energie": "elec_km", "co2": 0.00, "vitesse": 65, "capacité": 4000, "type": "Camion",    "maintenance_fcfa_km": 50, "fiabilite": 0.9,  "autonomie_km": 300,  "route": {"Urbain":0.85,"Mixte":1.0,"Difficile":0.9}},
}
# Note: "elec" = kWh/km, "elec_km" idem (pour distinguer des /100km thermiques)

PRIX = {"essence": 695, "diesel": 720, "kWh": 109}  # FCFA
AVANCE_HEURES = 0.25  # 15 minutes

# =========================
# Utilitaires
# =========================
def est_compatible_marchandise(veh, marchandise):
    t = veh["type"]
    if marchandise == "Dangereux":
        return t in {"Camion","Voiture"}  # on évite 2 roues & tricycles
    return True

def cout_energie(distance_km, veh):
    e = veh["energie"]
    if e == "elec" or e == "elec_km":
        # conso en kWh/km
        return distance_km * veh["conso"] * PRIX["kWh"]
    elif e == "diesel":
        return (distance_km / 100.0) * veh["conso"] * PRIX["diesel"]
    else:  # essence (et hybride ici modélisée essence)
        return (distance_km / 100.0) * veh["conso"] * PRIX["essence"]

def emissions(distance_km, veh):
    return distance_km * veh["co2"]  # kg CO2

def temps_trajet(distance_km, veh, trafic):
    v = veh["vitesse"]
    if trafic == "Élevé":
        v *= 0.7
    elif trafic == "Moyen":
        v *= 0.85
    return distance_km / max(v, 1e-6)

def adequation_route(veh, route_type):
    # score 0..1 selon profil route déclaré dans la fiche
    return veh["route"].get(route_type, 1.0)

def autonomie_ok(distance_km, veh):
    if veh["autonomie_km"] is None:
        return True
    return distance_km <= veh["autonomie_km"]

def normaliser_serie(s):
    if len(s) == 0:
        return s
    mn, mx = float(s.min()), float(s.max())
    if mx - mn < 1e-9:
        return pd.Series([0.5]*len(s), index=s.index)  # tous identiques
    return (s - mn) / (mx - mn)

# =========================
# Simulation
# =========================
def simuler(distance, delai_h, poids, marchandise, trafic, route_type,
            w_cout, w_co2, w_temps, w_maint, w_fiabilite, w_route):
    lignes = []
    for nom, v in VEHICULES.items():

        # Contraintes dures : capacité, compatibilité marchandise, autonomie
        if poids > v["capacité"]:
            continue
        if not est_compatible_marchandise(v, marchandise):
            continue
        if not autonomie_ok(distance, v):
            continue

        # Calculs
        t = temps_trajet(distance, v, trafic)
        faisable = t <= max(delai_h - AVANCE_HEURES, 0)

        cout_energy = cout_energie(distance, v)
        cout_maint = distance * v["maintenance_fcfa_km"]
        co2 = emissions(distance, v)
        adequation = adequation_route(v, route_type)

        lignes.append({
            "Mode": nom,
            "Type": v["type"],
            "Temps (h)": round(t, 2),
            "Coût énergie (FCFA)": round(cout_energy, 0),
            "Coût maintenance (FCFA)": round(cout_maint, 0),
            "Coût total (FCFA)": round(cout_energy + cout_maint, 0),
            "Émissions (kg CO2)": round(co2, 2),
            "Fiabilité": v["fiabilite"],
            "Adéquation route": adequation,
            "Faisable": faisable
        })

    df = pd.DataFrame(lignes)
    if df.empty:
        return df, None

    # Score pondéré (minimiser coût, CO2, temps, maintenance ; maximiser fiabilité, adéquation)
    # Normalisation 0..1
    df["n_cout"] = normaliser_serie(df["Coût total (FCFA)"])
    df["n_co2"] = normaliser_serie(df["Émissions (kg CO2)"])
    df["n_temps"] = normaliser_serie(df["Temps (h)"])
    df["n_maint"] = normaliser_serie(df["Coût maintenance (FCFA)"])
    df["n_fiab"] = normaliser_serie(df["Fiabilité"])            # plus = mieux
    df["n_route"] = normaliser_serie(df["Adéquation route"])    # plus = mieux

    df["Score"] = (
        -(w_cout * df["n_cout"]) +
        -(w_co2  * df["n_co2"]) +
        -(w_temps* df["n_temps"]) +
        -(w_maint* df["n_maint"]) +
         (w_fiabilite * df["n_fiab"]) +
         (w_route     * df["n_route"])
    )

    return df, df[df["Faisable"]].sort_values("Score", ascending=False)

# =========================
# PDF
# =========================
def generate_pdf(df, bests, final_choice):
    buf = io.BytesIO()
    doc = SimpleDocTemplate(buf, pagesize=A4)
    styles = getSampleStyleSheet()
    el = []

    el.append(Paragraph("📊 Rapport d'optimisation logistique", styles["Title"]))
    el.append(Spacer(1, 12))

    # Tableau
    cols = ["Mode","Type","Temps (h)","Coût énergie (FCFA)","Coût maintenance (FCFA)","Coût total (FCFA)","Émissions (kg CO2)","Fiabilité","Adéquation route","Faisable","Score"]
    df_show = df[cols].copy()
    data = [cols] + df_show.values.tolist()
    table = Table(data, repeatRows=1)
    table.setStyle(TableStyle([
        ("BACKGROUND",(0,0),(-1,0),colors.lightblue),
        ("ALIGN",(0,0),(-1,-1),"CENTER"),
        ("GRID",(0,0),(-1,-1),0.5,colors.black)
    ]))
    el.append(table)
    el.append(Spacer(1, 12))

    el.append(Paragraph("🏆 Meilleures solutions par critère", styles["Heading2"]))
    for label, row in bests.items():
        el.append(Paragraph(f"✔️ {label} : {row['Mode']} ({row['Type']}) — "
                            f"Coût {row['Coût total (FCFA)']} FCFA, "
                            f"Temps {row['Temps (h)']} h, "
                            f"CO₂ {row['Émissions (kg CO2)']} kg", styles["Normal"]))
    el.append(Spacer(1, 12))

    if final_choice is not None:
        el.append(Paragraph("🥇 Verdict final", styles["Heading2"]))
        el.append(Paragraph(f"Solution globale : <b>{final_choice['Mode']}</b> ({final_choice['Type']}) — "
                            f"{final_choice['Coût total (FCFA)']} FCFA, "
                            f"{final_choice['Temps (h)']} h, "
                            f"{final_choice['Émissions (kg CO2)']} kg CO₂.", styles["Normal"]))
        el.append(Spacer(1, 12))

    # Graphique (barres multi-métriques)
    fig, ax = plt.subplots()
    df_plot = df.set_index("Mode")[["Coût total (FCFA)","Temps (h)","Émissions (kg CO2)"]]
    df_plot.plot(kind="bar", ax=ax)
    ax.set_title("Comparaison des solutions")
    ax.set_ylabel("Valeurs")
    plt.xticks(rotation=45, ha="right")
    img_buf = io.BytesIO()
    plt.tight_layout()
    plt.savefig(img_buf, format="png", dpi=150)
    plt.close(fig)
    img_buf.seek(0)
    el.append(Image(img_buf, width=480, height=280))

    doc.build(el)
    buf.seek(0)
    return buf

# =========================
# UI
# =========================
st.title("🚚 Assistant Logistique Intelligent — optimisation multi-critères")

with st.sidebar:
    st.header("⚙️ Paramètres")
    distance = st.number_input("Distance (km)", min_value=1, value=200, step=10)
    delai = st.number_input("Délai maximal (heures)", min_value=1.0, value=6.0, step=0.25)
    trafic = st.selectbox("Trafic", ["Faible","Moyen","Élevé"])
    route_type = st.selectbox("Type de route", ["Urbain","Mixte","Difficile"])
    marchandise = st.selectbox("Type de marchandise", ["Standard","Périssable","Dangereux"])
    poids = st.number_input("Poids (kg)", min_value=1, value=500, step=10)

    st.markdown("---")
    st.subheader("🎛️ Pondérations du score")
    w_cout = st.slider("Poids coût", 0.0, 1.0, 0.40, 0.05)
    w_co2 = st.slider("Poids CO₂", 0.0, 1.0, 0.20, 0.05)
    w_temps = st.slider("Poids temps", 0.0, 1.0, 0.25, 0.05)
    w_maint = st.slider("Poids maintenance", 0.0, 1.0, 0.10, 0.05)
    w_fiabilite = st.slider("Poids fiabilité (+)", 0.0, 1.0, 0.30, 0.05)
    w_route = st.slider("Poids adéquation route (+)", 0.0, 1.0, 0.25, 0.05)

col1, col2 = st.columns([1,1])
with col1:
    lancer = st.button("🚀 Lancer la simulation")
with col2:
    st.caption(f"Règle délai : arrivée ≤ délai − 15 min ({AVANCE_HEURES*60:.0f} min d'avance obligatoire).")

if lancer:
    df, df_feasible_sorted = simuler(
        distance, delai, poids, marchandise, trafic, route_type,
        w_cout, w_co2, w_temps, w_maint, w_fiabilite, w_route
    )

    if df.empty:
        st.error("Aucune solution ne respecte les contraintes (capacité, autonomie, marchandise ou délais).")
    else:
        st.subheader("📊 Résultats détaillés")
        st.dataframe(df.sort_values(["Faisable","Score"], ascending=[False, False]), use_container_width=True)

        # Meilleures par critère (sur faisables)
        if df_feasible_sorted is not None and not df_feasible_sorted.empty:
            dfF = df[df["Faisable"]].copy()
            least_cost = dfF.loc[dfF["Coût total (FCFA)"].idxmin()]
            least_polluting = dfF.loc[dfF["Émissions (kg CO2)"].idxmin()]
            fastest = dfF.loc[dfF["Temps (h)"].idxmin()]
            balanced = df_feasible_sorted.iloc[0]

            # Marchandise : heuristique simple
            if marchandise == "Périssable":
                best_goods = fastest
            elif marchandise == "Dangereux":
                # prioriser Camion / Voiture avec bonne adéquation route
                cand = dfF[dfF["Type"].isin(["Camion","Voiture"])].copy()
                best_goods = cand.sort_values(["Adéquation route","Fiabilité","Coût total (FCFA)"], ascending=[False,False,True]).iloc[0] if not cand.empty else balanced
            else:
                best_goods = least_cost

            # Route : max adéquation, puis score
            best_route = dfF.sort_values(["Adéquation route","Score"], ascending=[False,False]).iloc[0]

            st.subheader("🏆 Meilleures solutions")
            st.success(f"💰 Moins coûteuse : {least_cost['Mode']} ({least_cost['Type']}) — {least_cost['Coût total (FCFA)']} FCFA")
            st.success(f"🌱 Moins polluante : {least_polluting['Mode']} ({least_polluting['Type']}) — {least_polluting['Émissions (kg CO2)']} kg CO₂")
            st.success(f"⚡ Plus rapide : {fastest['Mode']} ({fastest['Type']}) — {fastest['Temps (h)']} h")
            st.success(f"⚖️ Équilibrée (score) : {balanced['Mode']} ({balanced['Type']}) — Score {round(balanced['Score'],3)}")
            st.success(f"📦 Adaptée marchandise : {best_goods['Mode']} ({best_goods['Type']})")
            st.success(f"🛣️ Adaptée route : {best_route['Mode']} ({best_route['Type']})")

            final_choice = balanced  # déjà la meilleure faisable au score

            # Graphique
            st.subheader("📈 Comparaison (coût, temps, CO₂)")
            chart_df = df.set_index("Mode")[["Coût total (FCFA)","Temps (h)","Émissions (kg CO2)"]]
            st.bar_chart(chart_df)

            # PDF
            bests = {
                "Moins coûteuse": least_cost,
                "Moins polluante": least_polluting,
                "Plus rapide": fastest,
                "Équilibrée (score)": balanced,
                "Adaptée marchandise": best_goods,
                "Adaptée route": best_route
            }
            pdf_buf = generate_pdf(df, bests, final_choice)
            st.download_button("📥 Télécharger le rapport PDF", data=pdf_buf, file_name="rapport_logistique.pdf", mime="application/pdf")
        else:
            st.warning("Aucune option faisable ne respecte l'avance de 15 minutes sur le délai.")
