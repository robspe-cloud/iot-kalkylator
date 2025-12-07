import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- FUNKTIONER FÖR BERÄKNINGAR ---

def calculate_temp_kpi(antal_lgh, kvm_snitt, pris_sensor, pris_install, pris_konfig, startkostnad_projekt, underhall_per_sensor, lora_kostnad, webiot_kostnad, applikation_kostnad, energiforbrukning_kvm, energipris, besparing_procent, underhall_besparing_lgh):
    """Beräknar KPI:er för Temperatur/Energi-kalkylen."""
    
    # 1. Initiala Kostnader (Temperaturen)
    kostnad_sensor_tot = (antal_lgh * pris_sensor) + (antal_lgh * 0.01 * pris_sensor) # +1% reserv
    kostnad_install_tot = antal_lgh * pris_install
    kostnad_konfig_tot = antal_lgh * pris_konfig
    total_initial = kostnad_sensor_tot + kostnad_install_tot + kostnad_konfig_tot + startkostnad_projekt

    # 2. Årliga Driftskostnader
    drift_underhall = antal_lgh * underhall_per_sensor
    drift_lora = antal_lgh * lora_kostnad
    drift_webiot = antal_lgh * webiot_kostnad
    total_drift_ar = drift_underhall + drift_lora + drift_webiot + applikation_kostnad

    # 3. Årliga Besparingar
    total_kwh_fastighet = antal_lgh * kvm_snitt * energiforbrukning_kvm
    besparing_energi_kr = total_kwh_fastighet * energipris * (besparing_procent / 100)
    besparing_underhall_kr = antal_lgh * underhall_besparing_lgh

    total_besparing_ar = besparing_energi_kr + besparing_underhall_kr

    # 4. Netto & Payback
    netto_ar = total_besparing_ar - total_drift_ar
    payback_tid = total_initial / netto_ar if netto_ar > 0 else 0
    
    return total_initial, netto_ar, payback_tid

def calculate_water_kpi(antal_lgh, pris_sensor_vatten, pris_install_vatten, kostnad_vattenskada, frekvens_vattenskada, besparing_procent_skador, total_drift_ar):
    """Beräknar KPI:er för Vatten/Läcka-kalkylen."""
    
    # 1. Initiala Kostnader (Vatten)
    # Observera: Har tagit bort startkostnad/konfig från denna kalkyl för enkelhet, men de kan läggas till om de skiljer sig från temp-kalkylen
    kostnad_sensor_tot = antal_lgh * pris_sensor_vatten
    kostnad_install_tot = antal_lgh * pris_install_vatten
    total_initial = kostnad_sensor_tot + kostnad_install_tot

    # 2. Besparingar Vattenskador
    # Baserat på Excel-logik: Undvikandet av ett visst antal dyra skador per år.
    # Total årlig skadekostnad i fastigheten * besparing i %
    besparing_skador_kr = (antal_lgh / 1000) * (frekvens_vattenskada * kostnad_vattenskada) * besparing_procent_skador

    # 3. Netto & Payback
    # Vi återanvänder total_drift_ar för enkelhet (antag att LoraWAN/Plattform är samma)
    netto_ar = besparing_skador_kr - total_drift_ar
    payback_tid = total_initial / netto_ar if netto_ar > 0 else 0
    
    return total_initial, netto_ar, payback_tid

# --- HUVUDAPPLIKATION ---

st.set_page_config(page_title="IoT ROI Kalkylator", layout="wide")

st.title("💰 ROI Kalkylator: Fastighets-IoT")
st.markdown("Välj kalkylator nedan för att se ROI och besparingar för temperatursensorer eller vattenläckage-sensorer.")
st.markdown("---")

# FLIKAR
tab1, tab2 = st.tabs(["🌡️ Temperatur & Energi (Standard)", "💧 Vatten & Läckage (Quandify/Skada)"])

# --- SIDEBAR FÖR GEMENSAMMA INDATA ---
with st.sidebar:
    st.header("⚙️ Gemensamma Inställningar")
    antal_lgh = st.number_input("Antal lägenheter i fastigheten", value=1000, step=10, key='antal_lgh_main')

    st.subheader("Årliga Driftskostnader (Gemensamma)")
    # Vi använder dessa i båda kalkylerna för att förenkla
    underhall_per_sensor = st.number_input("Underhåll/batteri per sensor/år (kr)", value=100, key='uh_per_sensor')
    lora_kostnad = st.number_input("LoRaWAN anslutning per sensor/år (kr)", value=75, key='lora_cost')
    webiot_kostnad = st.number_input("Plattformskostnad per sensor/år (kr)", value=50, key='web_cost')
    applikation_kostnad = st.number_input("Applikationskostnad (fast avgift/år)", value=5000, key='app_cost')
    
    # Total årlig drift per sensor (används i kalkylen)
    total_drift_ar_per_sensor = underhall_per_sensor + lora_kostnad + webiot_kostnad
    total_drift_ar = (antal_lgh * total_drift_ar_per_sensor) + applikation_kostnad


# --- FLIK 1: TEMPERATUR & ENERGI ---
with tab1:
    st.header("Temperatur- och Energikalkyl")
    st.markdown("Beräkna ROI baserat på justerad värmedistribution och minskat underhåll.")
    st.markdown("---")

    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Initial Investering (Temperatur)")
        pris_sensor_temp = st.number_input("Pris per Temp-sensor (kr, inkl. 1% reserv)", value=688, key='pris_sensor_temp')
        pris_install_temp = st.number_input("Installation/Konfig. per sensor (kr)", value=409, key='pris_install_temp') # 375+34.4
        startkostnad_projekt_temp = st.number_input("Projektstartkostnad (kr)", value=27500, key='startkostnad_temp')

    with col2:
        st.subheader("Besparingsparametrar (Energi)")
        kvm_snitt = st.number_input("Snittyta per lgh (kvm)", value=67, key='kvm_snitt')
        energiforbrukning_kvm = st.number_input("Förbrukning (kWh/m²/år)", value=130.6, key='kwh_kvm')
        energipris = st.number_input("Energipris (kr/kWh)", value=1.02, key='pris_kwh')
        besparing_procent = st.slider("Förväntad energibesparing (%)", 0.0, 15.0, 6.0, 0.1, key='besparing_temp')
        underhall_besparing_lgh = st.number_input("Minskat underhåll/lgh (kr/år)", value=200, key='uh_besparing_temp')


    # Beräkna & Visa Resultat
    initial_temp, netto_temp, payback_temp = calculate_temp_kpi(
        antal_lgh, kvm_snitt, pris_sensor_temp, pris_install_temp, 0, startkostnad_projekt_temp,
        underhall_per_sensor, lora_kostnad, webiot_kostnad, applikation_kostnad, 
        energiforbrukning_kvm, energipris, besparing_procent, underhall_besparing_lgh
    )

    st.markdown("---")
    
    # Visa KPI:er
    col1_kpi, col2_kpi, col3_kpi = st.columns(3)
    col1_kpi.metric("Total Investering", f"{initial_temp:,.0f} kr".replace(",", " "))
    col2_kpi.metric("Årlig Nettobesparing", f"{netto_temp:,.0f} kr".replace(",", " "), delta_color="normal")
    col3_kpi.metric("Payback-tid", f"{payback_temp:.1f} år")

    # Kassaflödesanalys
    years = list(range(1, 11))
    cashflow = []
    current_balance = -initial_temp

    for year in years:
        current_balance += netto_temp
        cashflow.append(current_balance)

    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=years,
        y=cashflow,
        name="Ackumulerat Resultat",
        marker_color=['#ef553b' if x < 0 else '#00cc96' for x in cashflow]
    ))
    fig.update_layout(title="Ackumulerat Kassaflöde (10 år)", xaxis_title="År", yaxis_title="SEK", template="plotly_white")
    st.plotly_chart(fig, use_container_width=True)


# --- FLIK 2: VATTEN & LÄCKAGE ---
with tab2:
    st.header("Vatten- och Läckagekalkyl")
    st.markdown("Beräkna ROI baserat på minskad vattenförbrukning och undvikta vattenskadekostnader.")
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Initial Investering (Vatten/Läcka)")
        # Värden hämtade från Kalkyl_vatten_Quandify/Kalkyl_vattenskada
        val_sensor_vatten = st.selectbox("Välj Sensortyp", ["Quandify (IMD/Flöde)", "Elsys (Läckage)"], key='val_sensor_vatten')

        if val_sensor_vatten == "Quandify (IMD/Flöde)":
            pris_sensor_vatten = st.number_input("Pris per flödessensor/mätare (kr)", value=1875, key='pris_sensor_vatten_qd')
            pris_install_vatten = st.number_input("Installation/Konfig per mätare (kr)", value=459, key='pris_install_vatten_qd') # 375+46.8+reserv
            underhall_besparing_lgh_vatten = 500 # Från Excel: 500 kr/lgh/år i vatten/energi
        else:
            pris_sensor_vatten = st.number_input("Pris per läckagesensor (kr)", value=714.42, key='pris_sensor_vatten_el')
            pris_install_vatten = st.number_input("Installation/Konfig per sensor (kr)", value=523, key='pris_install_vatten_el')
            underhall_besparing_lgh_vatten = 171 # Från Excel: 170945/1000 lgh

        
    with col4:
        st.subheader("Besparingsparametrar (Skador)")
        # Värden baserade på genomsnittlig skadekostnad
        frekvens_vattenskada = st.number_input("Antal vattenskador per 1000 lgh/år (Utan IoT)", value=50, key='frekvens_skada')
        kostnad_vattenskada = st.number_input("Snittkostnad per vattenskada (kr)", value=70000, key='kostnad_skada')
        besparing_procent_skador = st.slider("Förväntad Minskning av Skadekostnad (%)", 0.0, 90.0, 60.0, 5.0, key='besparing_skada_pct')
        
    # Beräkna & Visa Resultat
    # Här adderar vi in den direkta besparingen i Netto-kalkylen (t.ex. 500 kr/lgh från Quandify)
    
    # 1. Besparing från minskade skador
    besparing_skador_kr = (antal_lgh / 1000) * (frekvens_vattenskada * kostnad_vattenskada) * (besparing_procent_skador / 100)
    
    # 2. Besparing från minskad vattenförbrukning/IMD (Baserat på vald sensor)
    besparing_forbrukning_kr = antal_lgh * underhall_besparing_lgh_vatten
    
    total_besparing_vatten = besparing_skador_kr + besparing_forbrukning_kr
    
    # 3. Initialkostnad
    initial_vatten = (antal_lgh * pris_sensor_vatten) + (antal_lgh * pris_install_vatten) 
    
    # 4. Netto
    netto_vatten = total_besparing_vatten - total_drift_ar
    payback_vatten = initial_vatten / netto_vatten if netto_vatten > 0 else 0


    st.markdown("---")
    
    # Visa KPI:er
    col1_kpi_vatten, col2_kpi_vatten, col3_kpi_vatten = st.columns(3)
    col1_kpi_vatten.metric("Total Investering", f"{initial_vatten:,.0f} kr".replace(",", " "))
    col2_kpi_vatten.metric("Årlig Nettobesparing", f"{netto_vatten:,.0f} kr".replace(",", " "), delta_color="normal")
    col3_kpi_vatten.metric("Payback-tid", f"{payback_vatten:.1f} år")
    
    # Kassaflödesanalys
    years_v = list(range(1, 11))
    cashflow_v = []
    current_balance_v = -initial_vatten

    for year in years_v:
        current_balance_v += netto_vatten
        cashflow_v.append(current_balance_v)

    fig_v = go.Figure()
    fig_v.add_trace(go.Bar(
        x=years_v,
        y=cashflow_v,
        name="Ackumulerat Resultat",
        marker_color=['#ef553b' if x < 0 else '#00cc96' for x in cashflow_v]
    ))
    fig_v.update_layout(title="Ackumulerat Kassaflöde (10 år)", xaxis_title="År", yaxis_title="SEK", template="plotly_white")
    st.plotly_chart(fig_v, use_container_width=True)

    with st.expander("Visa detaljerad kalkyl"):
        st.write(f"**Total Årlig Besparing (Vatten):** {total_besparing_vatten:,.0f} kr")
        st.write(f"- Beräknad besparing från minskade skadekostnader: {besparing_skador_kr:,.0f} kr")
        st.write(f"- Beräknad besparing från minskad vattenförbrukning/IMD (per lgh): {besparing_forbrukning_kr:,.0f} kr")
        st.write(f"- Årliga Driftskostnader (Gemensamma): -{total_drift_ar:,.0f} kr")
