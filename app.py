import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# --- KONSTANTER OCH MAPPNING ---
CALC_OPTIONS = {
    "🌡️ Temperatur & Energi": "temp", 
    "💧 IMD: Vattenförbrukning": "imd", 
    "🚨 Vattenskadeskydd": "skada"
}
CALC_KEY_LIST = list(CALC_OPTIONS.values()) 

# --- FUNKTIONER ---

def safe_float_input(label, default_value, key):
    """Använder st.text_input för att ta bort pilar och konverterar till float.
       Återgår till default_value om inmatningen är tom eller ogiltig."""
    value_str = st.text_input(label, value=str(default_value).replace(',', '.'), key=key)
    try:
        return float(value_str.replace(',', '.'))
    except ValueError:
        return default_value

def safe_int_input(label, default_value, key):
    """Använder st.text_input för att ta bort pilar och konverterar till int."""
    value_str = st.text_input(label, value=str(default_value), key=key)
    try:
        return int(float(value_str.replace(',', '.'))) # Använd float mellan för att hantera decimaler vid inmatning
    except ValueError:
        return default_value

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
    initial = initial if initial is not None and initial >= 0 else 0
    netto = netto if netto is not None else 0
    payback = payback if payback is not None and payback >= 0 else 0

    col1_kpi.metric("Total Investering", f"{initial:,.0f} kr".replace(",", " "))
    col2_kpi.metric("Årlig Nettobesparing", f"{netto:,.0f} kr".replace(",", " "), delta_color="normal")
    col3_kpi.metric("Payback-tid", f"{payback:.1f} år" if payback > 0 else "N/A")

# --- HUVUDAPPLIKATION ---

st.set_page_config(page_title="IoT ROI Kalkylator", layout="wide")

st.title("💰 IoT ROI Kalkylator")
st.markdown("---")

# --- INSTRUKTIONER (WIKI) ---
with st.expander("ℹ️ Instruktioner & Wiki – Hur du använder kalkylatorn"):
    st.markdown("""
    Denna kalkylator hjälper dig att uppskatta **Return on Investment (ROI)** för olika IoT-lösningar i fastigheter.

    ### 1. Välj Kalkyl
    Använd sidofältet till vänster (`🔎 Välj Kalkyl`) för att växla mellan de tre analysområdena: **Temperatur & Energi**, **IMD Vattenförbrukning**, och **Vattenskadeskydd**.

    ### 2. Gemensamma Kostnader (Sidebar)
    * Fälten i sidofältet (`⚙️ Gemensamma Driftskostnader`) – som Antal lägenheter, underhållskostnader och fasta årliga avgifter – påverkar **alla tre** kalkylerna. Justera dem först.

    ### 3. Justera Scenariot
    * I huvudfönstret för din valda kalkyl justerar du de **unika parametrarna** (t.ex. sensorpriser, installationskostnader och besparingsprocenter) för just det scenariot.
    * Klicka på **"Beräkna ROI"** för att uppdatera resultatet.

    ### 4. Spara och Ladda Scenarier (Dela Varianter)
    Du kan spara dina exakta parameterinställningar för senare användning, arkivering eller jämförelser.
    * **Spara:** Använd knappen **"Spara [Kalkylnamn] Scenario (.json)"** för att ladda ner en JSON-fil med alla aktuella inställningar för den aktiva kalkylen.
    * **Ladda:** Använd knappen **"Ladda [Kalkylnamn] Scenario (.json)"** och välj en tidigare sparad fil. **Obs:** Efter laddning kan du behöva klicka på **"Beräkna ROI"** för att säkerställa att alla värden används i kalkylen.
    """)
st.markdown("---")

# --- INITIALISERING AV SESSION STATE ---
# ... (Behåll initialiseringen från föregående kod) ...

if 'antal_lgh_main' not in st.session_state: st.session_state.antal_lgh_main = 1000
if 'uh_per_sensor' not in st.session_state: st.session_state.uh_per_sensor = 100
if 'lora_cost' not in st.session_state: st.session_state.lora_cost = 75
if 'web_cost' not in st.session_state: st.session_state.web_cost = 50
if 'app_cost' not in st.session_state: st.session_state.app_cost = 5000

if 'pris_sensor_temp' not in st.session_state: st.session_state.pris_sensor_temp = 688.0
if 'pris_install_temp' not in st.session_state: st.session_state.pris_install_temp = 409.0
if 'startkostnad_temp' not in st.session_state: st.session_state.startkostnad_temp = 27500.0
if 'kvm_snitt' not in st.session_state: st.session_state.kvm_snitt = 67.0
if 'kwh_kvm' not in st.session_state: st.session_state.kwh_kvm = 130.6
if 'pris_kwh' not in st.session_state: st.session_state.pris_kwh = 1.02
if 'besparing_temp' not in st.session_state: st.session_state.besparing_temp = 6.0
if 'uh_besparing_temp' not in st.session_state: st.session_state.uh_besparing_temp = 200.0

if 'pris_sensor_imd' not in st.session_state: st.session_state.pris_sensor_imd = 1875.0
if 'pris_install_imd' not in st.session_state: st.session_state.pris_install_imd = 459.0
if 'besparing_lgh_vatten' not in st.session_state: st.session_state.besparing_lgh_vatten = 500.0
if 'besparing_lgh_uh_imd' not in st.session_state: st.session_state.besparing_lgh_uh_imd = 200.0

if 'pris_sensor_skada' not in st.session_state: st.session_state.pris_sensor_skada = 714.42
if 'pris_install_skada' not in st.session_state: st.session_state.pris_install_skada = 523.0
if 'kostnad_skada' not in st.session_state: st.session_state.kostnad_skada = 70000.0
if 'frekvens_skada' not in st.session_state: st.session_state.frekvens_skada = 50.0
if 'besparing_skada_pct' not in st.session_state: st.session_state.besparing_skada_pct = 60.0
if 'uh_besparing_skada_lgh' not in st.session_state: st.session_state.uh_besparing_skada_lgh = 171.0


# --- NAVIGATION OCH SIDEBAR FÖR GEMENSAMMA INDATA ---

with st.sidebar:
    st.header("🔎 Välj Kalkyl")
    
    display_options = ["— Välj en kalkyl —"] + list(CALC_OPTIONS.keys())
    
    selected_calc_name = st.radio(
        "Välj det område du vill analysera:", 
        options=display_options,
        index=0, 
        key='radio_calc_selection'
    )
    
    if selected_calc_name == "— Välj en kalkyl —":
        active_tab = "" 
    else:
        active_tab = CALC_OPTIONS[selected_calc_name]
    
    st.markdown("---")
    st.header("⚙️ Gemensamma Driftskostnader")
    
    # Använder safe_int_input för att ta bort pilar
    antal_lgh = safe_int_input("Antal lägenheter i fastigheten", st.session_state.antal_lgh_main, key='antal_lgh_main')
    
    st.subheader("Årliga Kostnader per Sensor/Lgh")
    underhall_per_sensor = safe_float_input("Underhåll/batteri per sensor/år (kr)", st.session_state.uh_per_sensor, key='uh_per_sensor')
    lora_kostnad = safe_float_input("LoRaWAN anslutning per sensor/år (kr)", st.session_state.lora_cost, key='lora_cost')
    webiot_kostnad = safe_float_input("Plattformskostnad per sensor/år (kr)", st.session_state.web_cost, key='web_cost')
    
    st.subheader("Fast Årlig Avgfit")
    applikation_kostnad = safe_float_input("Applikationskostnad (fast avgift/år)", st.session_state.app_cost, key='app_cost')
    
    # Total årlig drift (Används i alla kalkyler)
    total_drift_ar_per_sensor = underhall_per_sensor + lora_kostnad + webiot_kostnad
    total_drift_ar = (antal_lgh * total_drift_ar_per_sensor) + applikation_kostnad


# --- 2. INNEHÅLLSBLOCK STYRS AV active_tab ---

# --- VÄLKOMSTSKÄRM (Nytt startläge) ---
if active_tab == "":
    st.info("👋 Välkommen! Vänligen välj en kalkyl i sidofältet till vänster (t.ex. '🌡️ Temperatur & Energi') för att börja beräkna ROI.")
    st.snow() 

# --- FLIK 1: TEMPERATUR & ENERGI ---
elif active_tab == "temp":
    st.header("Temperatur- och Energikalkyl")
    st.markdown("Fokus: Justerad värmedistribution, minskat underhåll, optimerad energi.")
    st.markdown("---")
    
    # --- ÅTERINFÖRD: SPARA/LADDA SCENARIO FUNKTION ---
    st.subheader("Spara/Ladda Scenario (Temperatur)")
    col_save, col_load = st.columns([1, 2])
    
    # Spara-knapp
    with col_save:
        scenario_data_to_save = {
            'antal_lgh_main': st.session_state.antal_lgh_main, 'uh_per_sensor': st.session_state.uh_per_sensor,
            'lora_cost': st.session_state.lora_cost, 'web_cost': st.session_state.web_cost,
            'app_cost': st.session_state.app_cost, 'pris_sensor_temp': st.session_state.pris_sensor_temp,
            'pris_install_temp': st.session_state.pris_install_temp, 'startkostnad_temp': st.session_state.startkostnad_temp,
            'kvm_snitt': st.session_state.kvm_snitt, 'kwh_kvm': st.session_state.kwh_kvm,
            'pris_kwh': st.session_state.pris_kwh, 'besparing_temp': st.session_state.besparing_temp,
            'uh_besparing_temp': st.session_state.uh_besparing_temp
        }
        json_data = json.dumps(scenario_data_to_save, indent=4)
        
        st.download_button(
            label="Spara Temperatur Scenario (.json)",
            data=json_data,
            file_name="iot_temp_scenario.json",
            mime="application/json",
            help="Sparar alla aktuella reglagevärden till en fil."
        )
    
    # Ladda-knapp (Flyttad under Spara)
    with col_load:
        uploaded_file = st.file_uploader("Ladda Temperatur Scenario (.json)", type="json", key='temp_scenario_uploader')
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("Temperatur Scenario laddat! Klicka på 'Beräkna ROI' för att visa de nya resultaten.")
            except Exception as e:
                st.error(f"Kunde inte ladda filen. Kontrollera formatet: {e}")

    st.markdown("---")

    
    # STARTA FORMULÄR FÖR ATT HANTERA INPUTS
    with st.form(key='temp_form'):
        col1, col2 = st.columns(2)
        
        with col1:
            st.subheader("Initial Investering")
            # Använder safe_float/int_input för att ta bort pilar
            pris_sensor_temp = safe_float_input("Pris per Temp-sensor (kr)", st.session_state.pris_sensor_temp, key='pris_sensor_temp_form')
            pris_install_temp = safe_float_input("Installation/Konfig. per sensor (kr)", st.session_state.pris_install_temp, key='pris_install_temp_form') 
            startkostnad_projekt_temp = safe_float_input("Projektstartkostnad (kr)", st.session_state.startkostnad_temp, key='startkostnad_temp_form')
            
            # --- BERÄKNING: INITIAL KOSTNAD ---
            total_initial_temp = antal_lgh * (pris_sensor_temp * 1.01 + pris_install_temp) + startkostnad_projekt_temp 

        with col2:
            st.subheader("Besparingsparametrar")
            kvm_snitt = safe_float_input("Snittyta per lgh (kvm)", st.session_state.kvm_snitt, key='kvm_snitt_form')
            energiforbrukning_kvm = safe_float_input("Förbrukning (kWh/m²/år)", st.session_state.kwh_kvm, key='kwh_kvm_form')
            energipris = safe_float_input("Energipris (kr/kWh)", st.session_state.pris_kwh, key='pris_kwh_form')
            besparing_procent = st.slider("Förväntad energibesparing (%)", 0.0, 15.0, value=st.session_state.besparing_temp, step=0.1, key='besparing_temp_form')
            underhall_besparing_lgh = safe_float_input("Minskat underhåll/lgh (kr/år)", st.session_state.uh_besparing_temp, key='uh_besparing_temp_form')
            
            # --- BERÄKNING: NETTO/BESPARING ---
            total_kwh_fastighet = antal_lgh * kvm_snitt * energiforbrukning_kvm
            besparing_energi_kr = total_kwh_fastighet * energipris * (besparing_procent / 100)
            besparing_underhall_kr = antal_lgh * underhall_besparing_lgh
            total_besparing_temp = besparing_energi_kr + besparing_underhall_kr
            netto_temp = total_besparing_temp - total_drift_ar
            payback_temp = total_initial_temp / netto_temp if netto_temp > 0 else 0
        
        # Knappen för att utlösa omkörning (Commit)
        if st.form_submit_button(label='Beräkna ROI', type='primary'):
            # Uppdatera session_state med formulärvärden efter commit, för att spara dem
            st.session_state.pris_sensor_temp = pris_sensor_temp
            st.session_state.pris_install_temp = pris_install_temp
            st.session_state.startkostnad_temp = startkostnad_projekt_temp
            st.session_state.kvm_snitt = kvm_snitt
            st.session_state.kwh_kvm = energiforbrukning_kvm
            st.session_state.pris_kwh = energipris
            st.session_state.besparing_temp = besparing_procent
            st.session_state.uh_besparing_temp = underhall_besparing_lgh

    # --- RESULTAT DISPLAY (Utanför Form) ---
    display_kpis(total_initial_temp, netto_temp, payback_temp)
    fig_temp, _ = create_cashflow_chart(total_initial_temp, netto_temp, "Ackumulerat Kassaflöde (Temperatur)")
    st.plotly_chart(fig_temp, use_container_width=True)

# --- FLIK 2: IMD: VATTENFÖRBRUKNING ---
elif active_tab == "imd":
    st.header("IMD: Vattenförbrukningskalkyl")
    st.markdown("Fokus: Minska vatten- och varmvattenförbrukning genom individuell mätning och debitering (IMD), t.ex. Quandify.")
    st.markdown("---")
    
    # --- ÅTERINFÖRD: SPARA/LADDA SCENARIO FUNKTION ---
    st.subheader("Spara/Ladda Scenario (IMD)")
    col_save, col_load = st.columns([1, 2])
    
    with col_save:
        scenario_data_to_save = {
            'antal_lgh_main': st.session_state.antal_lgh_main, 'uh_per_sensor': st.session_state.uh_per_sensor,
            'lora_cost': st.session_state.lora_cost, 'web_cost': st.session_state.web_cost,
            'app_cost': st.session_state.app_cost, 'pris_sensor_imd': st.session_state.pris_sensor_imd,
            'pris_install_imd': st.session_state.pris_install_imd, 'besparing_lgh_vatten': st.session_state.besparing_lgh_vatten,
            'besparing_lgh_uh_imd': st.session_state.besparing_lgh_uh_imd
        }
        json_data = json.dumps(scenario_data_to_save, indent=4)
        
        st.download_button(
            label="Spara IMD Scenario (.json)",
            data=json_data,
            file_name="iot_imd_scenario.json",
            mime="application/json",
            help="Sparar alla aktuella reglagevärden till en fil."
        )
    
    with col_load:
        uploaded_file = st.file_uploader("Ladda IMD Scenario (.json)", type="json", key='imd_scenario_uploader') 
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("IMD Scenario laddat! Klicka på 'Beräkna ROI' för att visa de nya resultaten.")
            except Exception as e:
                st.error(f"Kunde inte ladda filen. Kontrollera formatet: {e}")

    st.markdown("---")

    with st.form(key='imd_form'):
        col3, col4 = st.columns(2)
        
        with col3:
            st.subheader("Initial Investering (IMD-mätare)")
            pris_sensor_imd = safe_float_input("Pris per Vattenmätare/Sensor (kr)", st.session_state.pris_sensor_imd, key='pris_sensor_imd_form')
            pris_install_imd = safe_float_input("Installation/Konfig per mätare (kr)", st.session_state.pris_install_imd, key='pris_install_imd_form') 
            
            total_initial_imd = antal_lgh * (pris_sensor_imd + pris_install_imd) + (5 * pris_sensor_imd) 
            
        with col4:
            st.subheader("Besparingsparametrar (Förbrukning)")
            besparing_per_lgh_vatten = safe_float_input("Vatten/Varmvatten-besparing per lgh/år (kr)", st.session_state.besparing_lgh_vatten, key='besparing_lgh_vatten_form')
            besparing_per_lgh_underhall = safe_float_input("Minskat underhåll/lgh (kr/år)", st.session_state.besparing_lgh_uh_imd, key='besparing_lgh_uh_imd_form')
            
            total_besparing_imd = antal_lgh * (besparing_per_lgh_vatten + besparing_per_lgh_underhall)
            netto_imd = total_besparing_imd - total_drift_ar
            payback_imd = total_initial_imd / netto_imd if netto_imd > 0 else 0

        if st.form_submit_button(label='Beräkna ROI', type='primary'):
            st.session_state.pris_sensor_imd = pris_sensor_imd
            st.session_state.pris_install_imd = pris_install_imd
            st.session_state.besparing_lgh_vatten = besparing_per_lgh_vatten
            st.session_state.besparing_lgh_uh_imd = besparing_per_lgh_underhall

    display_kpis(total_initial_imd, netto_imd, payback_imd)
    fig_imd, _ = create_cashflow_chart(total_initial_imd, netto_imd, "Ackumulerat Kassaflöde (IMD Vatten)")
    st.plotly_chart(fig_imd, use_container_width=True)

# --- FLIK 3: VATTENSKADESKYDD ---
elif active_tab == "skada":
    st.header("Vattenskadeskyddskalkyl")
    st.markdown("Fokus: Undvika kostsamma vattenskador genom tidig upptäckt av läckagesensorer, t.ex. Elsys.")
    st.markdown("---")
    
    # --- ÅTERINFÖRD: SPARA/LADDA SCENARIO FUNKTION ---
    st.subheader("Spara/Ladda Scenario (Vattenskada)")
    col_save, col_load = st.columns([1, 2])
    
    with col_save:
        scenario_data_to_save = {
            'antal_lgh_main': st.session_state.antal_lgh_main, 'uh_per_sensor': st.session_state.uh_per_sensor,
            'lora_cost': st.session_state.lora_cost, 'web_cost': st.session_state.web_cost,
            'app_cost': st.session_state.app_cost, 'pris_sensor_skada': st.session_state.pris_sensor_skada,
            'pris_install_skada': st.session_state.pris_install_skada, 'kostnad_skada': st.session_state.kostnad_skada,
            'frekvens_skada': st.session_state.frekvens_skada, 'besparing_skada_pct': st.session_state.besparing_skada_pct,
            'uh_besparing_skada_lgh': st.session_state.uh_besparing_skada_lgh
        }
        json_data = json.dumps(scenario_data_to_save, indent=4)
        
        st.download_button(
            label="Spara Vattenskada Scenario (.json)",
            data=json_data,
            file_name="iot_skada_scenario.json",
            mime="application/json",
            help="Sparar alla aktuella reglagevärden till en fil."
        )
    
    with col_load:
        uploaded_file = st.file_uploader("Ladda Vattenskada Scenario (.json)", type="json", key='skada_scenario_uploader') 
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("Vattenskada Scenario laddat! Klicka på 'Beräkna ROI' för att visa de nya resultaten.")
            except Exception as e:
                st.error(f"Kunde inte ladda filen. Kontrollera formatet: {e}")

    st.markdown("---")
    
    with st.form(key='skada_form'):
        col5, col6 = st.columns(2)

        with col5:
            st.subheader("Initial Investering (Läckagesensor)")
            pris_sensor_skada = safe_float_input("Pris per Läckagesensor (kr)", st.session_state.pris_sensor_skada, key='pris_sensor_skada_form')
            pris_install_skada = safe_float_input("Installation/Konfig per sensor (kr)", st.session_state.pris_install_skada, key='pris_install_skada_form') 
            
            total_initial_skada = antal_lgh * (pris_sensor_skada + pris_install_skada)
            
        with col6:
            st.subheader("Besparingsparametrar (Skadereduktion)")
            kostnad_vattenskada = safe_float_input("Snittkostnad per vattenskada (kr)", st.session_state.kostnad_skada, key='kostnad_skada_form')
            frekvens_vattenskada = safe_float_input("Antal vattenskador per 1000 lgh/år (Utan IoT)", st.session_state.frekvens_skada, key='frekvens_skada_form')
            besparing_procent_skador = st.slider("Förväntad Minskning av Skadekostnad (%)", 0.0, 90.0, value=st.session_state.besparing_skada_pct, step=5.0, key='besparing_skada_pct_form')
            uh_besparing_skada_lgh = safe_float_input("Övrig underhållsbesparing per lgh/år (kr)", st.session_state.uh_besparing_skada_lgh, key='uh_besparing_skada_lgh_form')
            
            tot_skadekostnad_utan_iot = (antal_lgh / 1000) * (frekvens_vattenskada * kostnad_vattenskada)
            besparing_skador_kr = tot_skadekostnad_utan_iot * (besparing_procent_skador / 100)
            
            total_besparing_skada = besparing_skador_kr + (antal_lgh * uh_besparing_skada_lgh)
            netto_skada = total_besparing_skada - total_drift_ar
            payback_skada = total_initial_skada / netto_skada if netto_skada > 0 else 0

        if st.form_submit_button(label='Beräkna ROI', type='primary'):
            st.session_state.pris_sensor_skada = pris_sensor_skada
            st.session_state.pris_install_skada = pris_install_skada
            st.session_state.kostnad_skada = kostnad_vattenskada
            st.session_state.frekvens_skada = frekvens_vattenskada
            st.session_state.besparing_skada_pct = besparing_procent_skador
            st.session_state.uh_besparing_skada_lgh = uh_besparing_skada_lgh

    display_kpis(total_initial_skada, netto_skada, payback_skada)
    fig_skada, _ = create_cashflow_chart(total_initial_skada, netto_skada, "Ackumulerat Kassaflöde (Vattenskadeskydd)")
    st.plotly_chart(fig_skada, use_container_width=True)
    
    st.markdown("#### Beräkningsdetaljer")
    st.write(f"Besparing från undvikna skadekostnader ({st.session_state.besparing_skada_pct:.1f}% av {tot_skadekostnad_utan_iot:,.0f} kr): **{besparing_skador_kr:,.0f} kr**")
    st.write(f"Övrig underhållsbesparing (från Excel): **{antal_lgh * st.session_state.uh_besparing_skada_lgh:,.0f} kr**")
