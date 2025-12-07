import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# --- FUNKTIONER FÖR BERÄKNINGAR OCH VISUALISERING ---

def create_cashflow_chart(initial_cost, net_annual_flow, title):
    """Genererar den ackumulerade kassaflödesgrafen."""
    years = list(range(1, 11))
    cashflow = []
    current_balance = -initial_cost

    for year in years:
        current_balance += net_annual_flow
        cashflow.append(current_balance)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=cashflow,
        name="Ackumulerat Resultat",
        marker_color=['#ef553b' if x < 0 else '#00cc96' for x in cashflow]
    ))
    fig.update_layout(title=title, xaxis_title="År", yaxis_title="SEK", template="plotly_white")
    return fig, cashflow

def display_kpis(initial, netto, payback):
    """Visar de tre nyckeltalen."""
    col1_kpi, col2_kpi, col3_kpi = st.columns(3)
    col1_kpi.metric("Total Investering", f"{initial:,.0f} kr".replace(",", " "))
    col2_kpi.metric("Årlig Nettobesparing", f"{netto:,.0f} kr".replace(",", " "), delta_color="normal")
    col3_kpi.metric("Payback-tid", f"{payback:.1f} år")

# --- HUVUDAPPLIKATION ---

st.set_page_config(page_title="IoT ROI Kalkylator", layout="wide")

st.title("💰 ROI Kalkylator: Fastighets-IoT")
st.markdown("---")


# --- URL-PARAMETER STYRNING FÖR AKTIV FLIK ---
# Vi använder URL-parametern för att styra vilken flik som är aktiv. Default är 'temp'.
query_params = st.query_params
active_tab_name = query_params.get("tab", ["temp"])[0].lower() 
tab_names = ["temp", "imd", "skada"]
try:
    default_tab_index = tab_names.index(active_tab_name)
except ValueError:
    default_tab_index = 0 

# FLIKAR
tab1, tab2, tab3 = st.tabs(["🌡️ Temperatur & Energi", "💧 IMD: Vattenförbrukning", "🚨 Vattenskadeskydd"], default_index=default_tab_index)


# --- SIDEBAR FÖR GEMENSAMMA INDATA (LORA/PLATTFORM) ---
with st.sidebar:
    st.header("⚙️ Gemensamma Driftskostnader")
    # Initialisera Session State för alla inputs om de saknas
    if 'antal_lgh_main' not in st.session_state: st.session_state.antal_lgh_main = 1000
    antal_lgh = st.number_input("Antal lägenheter i fastigheten", value=st.session_state.antal_lgh_main, step=10, key='antal_lgh_main')

    st.subheader("Årliga Kostnader per Sensor/Lgh")
    if 'uh_per_sensor' not in st.session_state: st.session_state.uh_per_sensor = 100
    underhall_per_sensor = st.number_input("Underhåll/batteri per sensor/år (kr)", value=st.session_state.uh_per_sensor, key='uh_per_sensor')

    if 'lora_cost' not in st.session_state: st.session_state.lora_cost = 75
    lora_kostnad = st.number_input("LoRaWAN anslutning per sensor/år (kr)", value=st.session_state.lora_cost, key='lora_cost')

    if 'web_cost' not in st.session_state: st.session_state.web_cost = 50
    webiot_kostnad = st.number_input("Plattformskostnad per sensor/år (kr)", value=st.session_state.web_cost, key='web_cost')
    
    st.subheader("Fast Årlig Avgfit")
    if 'app_cost' not in st.session_state: st.session_state.app_cost = 5000
    applikation_kostnad = st.number_input("Applikationskostnad (fast avgift/år)", value=st.session_state.app_cost, key='app_cost')
    
    # Total årlig drift (Används i alla kalkyler)
    total_drift_ar_per_sensor = underhall_per_sensor + lora_kostnad + webiot_kostnad
    total_drift_ar = (antal_lgh * total_drift_ar_per_sensor) + applikation_kostnad


# --- FLIK 1: TEMPERATUR & ENERGI ---
with tab1:
    st.header("Temperatur- och Energikalkyl")
    st.markdown("Fokus: Justerad värmedistribution, minskat underhåll, optimerad energi.")
    st.markdown("---")

    # --- FUNKTIONER FÖR SPARA/LADDA SCENARIO ---
    st.subheader("Spara/Ladda Scenario")
    col_save, col_load = st.columns([1, 2])
    
    # 1. Ladda Scenario
    with col_load:
        uploaded_file = st.file_uploader("Ladda Scenario (.json)", type="json", key='scenario_uploader')
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                # Uppdatera Streamlit Session State för ALLA inputs. Måste matcha nycklarna i koden.
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("Scenario laddat! Kalkylen har uppdaterats.")
            except Exception as e:
                st.error(f"Kunde inte ladda filen. Kontrollera formatet: {e}")

    # 2. Spara Scenario
    with col_save:
        # Samla in alla relevanta input-värden i en diktamen
        scenario_data_to_save = {
            'antal_lgh_main': st.session_state.antal_lgh_main,
            'uh_per_sensor': st.session_state.uh_per_sensor,
            'lora_cost': st.session_state.lora_cost,
            'web_cost': st.session_state.web_cost,
            'app_cost': st.session_state.app_cost,
            
            # Flik 1 specifika nycklar
            'pris_sensor_temp': st.session_state.pris_sensor_temp,
            'pris_install_temp': st.session_state.pris_install_temp,
            'startkostnad_temp': st.session_state.startkostnad_temp,
            'kvm_snitt': st.session_state.kvm_snitt,
            'kwh_kvm': st.session_state.kwh_kvm,
            'pris_kwh': st.session_state.pris_kwh,
            'besparing_temp': st.session_state.besparing_temp,
            'uh_besparing_temp': st.session_state.uh_besparing_temp
        }
        json_data = json.dumps(scenario_data_to_save, indent=4)
        
        st.download_button(
            label="Spara Scenario (.json)",
            data=json_data,
            file_name="iot_temp_scenario.json",
            mime="application/json",
            help="Sparar alla aktuella reglagevärden till en fil."
        )
    st.markdown("---")
    
    # --- FLIK 1 INPUTS ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Initial Investering")
        if 'pris_sensor_temp' not in st.session_state: st.session_state.pris_sensor_temp = 688
        pris_sensor_temp = st.number_input("Pris per Temp-sensor (kr)", value=st.session_state.pris_sensor_temp, key='pris_sensor_temp')
        
        if 'pris_install_temp' not in st.session_state: st.session_state.pris_install_temp = 409
        pris_install_temp = st.number_input("Installation/Konfig. per sensor (kr)", value=st.session_state.pris_install_temp, key='pris_install_temp') 
        
        if 'startkostnad_temp' not in st.session_state: st.session_state.startkostnad_temp = 27500
        startkostnad_projekt_temp = st.number_input("Projektstartkostnad (kr)", value=st.session_state.startkostnad_temp, key='startkostnad_temp')
        total_initial_temp = antal_lgh * (pris_sensor_temp * 1.01 + pris_install_temp) + startkostnad_projekt_temp # 1% reserv

    with col2:
        st.subheader("Besparingsparametrar")
        if 'kvm_snitt' not in st.session_state: st.session_state.kvm_snitt = 67
        kvm_snitt = st.number_input("Snittyta per lgh (kvm)", value=st.session_state.kvm_snitt, key='kvm_snitt')
        
        if 'kwh_kvm' not in st.session_state: st.session_state.kwh_kvm =
