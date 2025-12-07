import streamlit as st
import pandas as pd
import plotly.graph_objects as go

# --- SIDKONFIGURATION ---
st.set_page_config(page_title="IoT Kalkylator - Temperatur", layout="wide")

st.title("💰 Kalkylator: IoT-Temperatursensorer")
st.markdown("Beräkna ROI och besparingar genom att installera uppkopplade sensorer i fastigheten.")
st.markdown("---")

# --- SIDEBAR (INDATA) ---
st.sidebar.header("⚙️ Inställningar")

# Sektion 1: Fastighet
st.sidebar.subheader("Fastighet")
antal_lgh = st.sidebar.number_input("Antal lägenheter", value=1000, step=10)
kvm_snitt = st.sidebar.number_input("Snittyta per lgh (kvm)", value=67)

# Sektion 2: Kostnader (Initialt)
st.sidebar.subheader("Initiala Investeringar")
pris_sensor = st.sidebar.number_input("Pris per sensor (kr)", value=688)
pris_installation = st.sidebar.number_input("Installation per sensor (kr)", value=375)
pris_konfig = st.sidebar.number_input("Konfiguration/Provisionering (kr)", value=35) # Avrundat från 34.4
startkostnad_projekt = st.sidebar.number_input("Startkostnad projekt (kr)", value=27500)

# Sektion 3: Drift & Abonnemang
st.sidebar.subheader("Årliga Driftskostnader")
underhall_per_sensor = st.sidebar.number_input("Underhåll per sensor/år (kr)", value=100)
lora_kostnad = st.sidebar.number_input("LoRaWAN kostnad/år (kr)", value=75)
webiot_kostnad = st.sidebar.number_input("Plattformskostnad/år (kr)", value=50)
applikation_kostnad = st.sidebar.number_input("Applikationskostnad fast avgift (kr)", value=5000)

# Sektion 4: Besparingsparametrar
st.sidebar.subheader("Kalkylator Besparing")
energiforbrukning_kvm = st.sidebar.number_input("Förbrukning (kWh/m²/år)", value=130.6)
energipris = st.sidebar.number_input("Energipris (kr/kWh)", value=1.02)
besparing_procent = st.sidebar.slider("Förväntad energibesparing (%)", 0.0, 15.0, 6.0, 0.1)
underhall_besparing_lgh = st.sidebar.number_input("Minskat underhåll per lgh (kr/år)", value=200)

# --- BERÄKNINGAR ---

# 1. Initiala Kostnader
# Kostnad sensorer + reserv (1% reserv enligt excel)
kostnad_sensor_tot = (antal_lgh * pris_sensor) + (antal_lgh * 0.01 * pris_sensor)
kostnad_install_tot = antal_lgh * pris_installation
kostnad_konfig_tot = antal_lgh * pris_konfig
total_initial = kostnad_sensor_tot + kostnad_install_tot + kostnad_konfig_tot + startkostnad_projekt

# 2. Årliga Driftskostnader
drift_underhall = antal_lgh * underhall_per_sensor
drift_lora = antal_lgh * lora_kostnad
drift_webiot = antal_lgh * webiot_kostnad
total_drift_ar = drift_underhall + drift_lora + drift_webiot + applikation_kostnad

# 3. Årliga Besparingar
# Energi: Antal lgh * kvm * kWh/kvm * pris * besparing%
total_kwh_fastighet = antal_lgh * kvm_snitt * energiforbrukning_kvm
besparing_energi_kr = total_kwh_fastighet * energipris * (besparing_procent / 100)

# Underhållsbesparing
besparing_underhall_kr = antal_lgh * underhall_besparing_lgh

total_besparing_ar = besparing_energi_kr + besparing_underhall_kr

# 4. Netto
netto_ar = total_besparing_ar - total_drift_ar
payback_tid = total_initial / netto_ar if netto_ar > 0 else 0

# --- VISUALISERING (MAIN AREA) ---

# Visa KPI:er (Nyckeltal)
col1, col2, col3 = st.columns(3)
col1.metric("Total Investering", f"{total_initial:,.0f} kr".replace(",", " "))
col2.metric("Årlig Nettobesparing", f"{netto_ar:,.0f} kr".replace(",", " "), delta_color="normal")
col3.metric("Payback-tid", f"{payback_tid:.1f} år")

st.markdown("---")

# Kassaflödesanalys över 10 år
years = list(range(1, 11))
cashflow = []
cumulative_cashflow = []
current_balance = -total_initial

for year in years:
    current_balance += netto_ar
    cashflow.append(current_balance)

# Skapa Graf
fig = go.Figure()

# Lägg till staplar för årligt netto (ackumulerat)
fig.add_trace(go.Bar(
    x=years,
    y=cashflow,
    name="Ackumulerat Resultat",
    marker_color=['#ef553b' if x < 0 else '#00cc96' for x in cashflow]
))

fig.update_layout(
    title="Ackumulerat Kassaflöde (10 år)",
    xaxis_title="År",
    yaxis_title="SEK",
    template="plotly_white"
)

st.plotly_chart(fig, use_container_width=True)

# Visa Detaljerad Data i tabell
with st.expander("Visa detaljerad kalkyl"):
    st.write(f"**Initial kostnad specificerad:**")
    st.write(f"- Sensorer: {kostnad_sensor_tot:,.0f} kr")
    st.write(f"- Installation: {kostnad_install_tot:,.0f} kr")
    st.write(f"- Övrigt (Start/Konfig): {kostnad_konfig_tot + startkostnad_projekt:,.0f} kr")
    
    st.write(f"**Drift vs Besparing (per år):**")
    st.write(f"- Total Driftkostnad: -{total_drift_ar:,.0f} kr")
    st.write(f"- Energibesparing: +{besparing_energi_kr:,.0f} kr")
    st.write(f"- Underhållsbesparing: +{besparing_underhall_kr:,.0f} kr")