import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- FUNKTIONER FÖR BERÄKNINGAR ---

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

# FLIKAR
tab1, tab2, tab3 = st.tabs(["🌡️ Temperatur & Energi", "💧 IMD: Vattenförbrukning", "🚨 Vattenskadeskydd"])

# --- SIDEBAR FÖR GEMENSAMMA INDATA (LORA/PLATTFORM) ---
with st.sidebar:
    st.header("⚙️ Gemensamma Driftskostnader")
    antal_lgh = st.number_input("Antal lägenheter i fastigheten", value=1000, step=10, key='antal_lgh_main')

    st.subheader("Årliga Kostnader per Sensor/Lgh")
    underhall_per_sensor = st.number_input("Underhåll/batteri per sensor/år (kr)", value=100, key='uh_per_sensor')
    lora_kostnad = st.number_input("LoRaWAN anslutning per sensor/år (kr)", value=75, key='lora_cost')
    webiot_kostnad = st.number_input("Plattformskostnad per sensor/år (kr)", value=50, key='web_cost')
    
    st.subheader("Fast Årlig Avgfit")
    applikation_kostnad = st.number_input("Applikationskostnad (fast avgift/år)", value=5000, key='app_cost')
    
    # Total årlig drift (Används i alla kalkyler)
    total_drift_ar_per_sensor = underhall_per_sensor + lora_kostnad + webiot_kostnad
    total_drift_ar = (antal_lgh * total_drift_ar_per_sensor) + applikation_kostnad

# --- FLIK 1: TEMPERATUR & ENERGI (OFÖRÄNDRAD) ---
with tab1:
    st.header("Temperatur- och Energikalkyl")
    st.markdown("Fokus: Justerad värmedistribution, minskat underhåll, optimerad energi.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Initial Investering")
        pris_sensor_temp = st.number_input("Pris per Temp-sensor (kr)", value=688, key='pris_sensor_temp')
        pris_install_temp = st.number_input("Installation/Konfig. per sensor (kr)", value=409, key='pris_install_temp') # 375+34.4
        startkostnad_projekt_temp = st.number_input("Projektstartkostnad (kr)", value=27500, key='startkostnad_temp')
        total_initial_temp = antal_lgh * (pris_sensor_temp * 1.01 + pris_install_temp) + startkostnad_projekt_temp # 1% reserv

    with col2:
        st.subheader("Besparingsparametrar")
        kvm_snitt = st.number_input("Snittyta per lgh (kvm)", value=67, key='kvm_snitt')
        energiforbrukning_kvm = st.number_input("Förbrukning (kWh/m²/år)", value=130.6, key='kwh_kvm')
        energipris = st.number_input("Energipris (kr/kWh)", value=1.02, key='pris_kwh')
        besparing_procent = st.slider("Förväntad energibesparing (%)", 0.0, 15.0, 6.0, 0.1, key='besparing_temp')
        underhall_besparing_lgh = st.number_input("Minskat underhåll/lgh (kr/år)", value=200, key='uh_besparing_temp')
        
        total_kwh_fastighet = antal_lgh * kvm_snitt * energiforbrukning_kvm
        besparing_energi_kr = total_kwh_fastighet * energipris * (besparing_procent / 100)
        besparing_underhall_kr = antal_lgh * underhall_besparing_lgh
        total_besparing_temp = besparing_energi_kr + besparing_underhall_kr
        netto_temp = total_besparing_temp - total_drift_ar
        payback_temp = total_initial_temp / netto_temp if netto_temp > 0 else 0

    display_kpis(total_initial_temp, netto_temp, payback_temp)
    fig_temp, _ = create_cashflow_chart(total_initial_temp, netto_temp, "Ackumulerat Kassaflöde (Temperatur)")
    st.plotly_chart(fig_temp, use_container_width=True)

# --- FLIK 2: IMD: VATTENFÖRBRUKNING ---
with tab2:
    st.header("IMD: Vattenförbrukningskalkyl")
    st.markdown("Fokus: Minska vatten- och varmvattenförbrukning genom individuell mätning och debitering (IMD), t.ex. Quandify.")
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Initial Investering (IMD-mätare)")
        # Värden baserade på Kalkyl_vatten_Quandify_2024-09-18_B.xlsx
        pris_sensor_imd = st.number_input("Pris per Vattenmätare/Sensor (kr)", value=1875, key='pris_sensor_imd')
        pris_install_imd = st.number_input("Installation/Konfig per mätare (kr)", value=459, key='pris_install_imd') 
        # Här inkluderas inte fast projektkostnad för att hålla kalkylerna distinkta
        total_initial_imd = antal_lgh * (pris_sensor_imd + pris_install_imd) + (5 * pris_sensor_imd) # Lägger till 5 reservsensorer
        
    with col4:
        st.subheader("Besparingsparametrar (Förbrukning)")
        # Besparingar baseras primärt på beteendeförändring
        besparing_per_lgh_vatten = st.number_input("Vatten/Varmvatten-besparing per lgh/år (kr)", value=500, key='besparing_lgh_vatten')
        besparing_per_lgh_underhall = st.number_input("Minskat underhåll/lgh (kr/år)", value=200, key='besparing_lgh_uh_imd')
        
        total_besparing_imd = antal_lgh * (besparing_per_lgh_vatten + besparing_per_lgh_underhall)
        netto_imd = total_besparing_imd - total_drift_ar
        payback_imd = total_initial_imd / netto_imd if netto_imd > 0 else 0

    display_kpis(total_initial_imd, netto_imd, payback_imd)
    fig_imd, _ = create_cashflow_chart(total_initial_imd, netto_imd, "Ackumulerat Kassaflöde (IMD Vatten)")
    st.plotly_chart(fig_imd, use_container_width=True)

# --- FLIK 3: VATTENSKADESKYDD ---
with tab3:
    st.header("Vattenskadeskyddskalkyl")
    st.markdown("Fokus: Undvika kostsamma vattenskador genom tidig upptäckt av läckagesensorer, t.ex. Elsys.")
    st.markdown("---")
    
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Initial Investering (Läckagesensor)")
        # Värden baserade på Kalkyl_vattenskada_2024-09-18_B.xlsx
        pris_sensor_skada = st.number_input("Pris per Läckagesensor (kr)", value=714.42, key='pris_sensor_skada')
        pris_install_skada = st.number_input("Installation/Konfig per sensor (kr)", value=523, key='pris_install_skada') # Avrundat 522.97
        total_initial_skada = antal_lgh * (pris_sensor_skada + pris_install_skada)
        
    with col6:
        st.subheader("Besparingsparametrar (Skadereduktion)")
        # Värden baserade på Vattenskadecentrum-data och din kalkyl
        kostnad_vattenskada = st.number_input("Snittkostnad per vattenskada (kr)", value=70000, key='kostnad_skada')
        frekvens_vattenskada = st.number_input("Antal vattenskador per 1000 lgh/år (Utan IoT)", value=50, key='frekvens_skada')
        besparing_procent_skador = st.slider("Förväntad Minskning av Skadekostnad (%)", 0.0, 90.0, 60.0, 5.0, key='besparing_skada_pct')
        
        # Basberäkning: Total årlig skadekostnad i fastigheten
        tot_skadekostnad_utan_iot = (antal_lgh / 1000) * (frekvens_vattenskada * kostnad_vattenskada)
        
        # Besparing: Reduktionen av skadekostnaden
        besparing_skador_kr = tot_skadekostnad_utan_iot * (besparing_procent_skador / 100)
        
        # Enkel underhållsbesparing (Från Excel: 170 kr/lgh i UH-besparing, och en post på 500 kr/lgh i en annan excel)
        uh_besparing_skada_lgh = st.number_input("Övrig underhållsbesparing per lgh/år (kr)", value=171, key='uh_besparing_skada_lgh')
        
        total_besparing_skada = besparing_skador_kr + (antal_lgh * uh_besparing_skada_lgh)
        netto_skada = total_besparing_skada - total_drift_ar
        payback_skada = total_initial_skada / netto_skada if netto_skada > 0 else 0

    display_kpis(total_initial_skada, netto_skada, payback_skada)
    fig_skada, _ = create_cashflow_chart(total_initial_skada, netto_skada, "Ackumulerat Kassaflöde (Vattenskadeskydd)")
    st.plotly_chart(fig_skada, use_container_width=True)
    
    with st.expander("Beräkningsdetaljer"):
        st.write(f"Total årlig skadekostnad (utan IoT) baserat på inmatade värden: **{tot_skadekostnad_utan_iot:,.0f} kr**")
        st.write(f"Besparing från undvikta skadekostnader ({besparing_procent_skador:.1f}%): **{besparing_skador_kr:,.0f} kr**")
        st.write(f"Övrig underhållsbesparing: **{antal_lgh * uh_besparing_skada_lgh:,.0f} kr**")
