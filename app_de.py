import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import json

# --- KONSTANTER OCH MAPPNING (DEUTSCH) ---
CALC_OPTIONS = {
    "🌡️ Temperatur & Energie": "temp", 
    "💧 IMD: Wasserverbrauch": "imd", 
    "🚨 Wasserschadenschutz": "skada"
}
CALC_KEY_LIST = list(CALC_OPTIONS.values()) 

# --- FUNKTIONEN FÜR BERECHNUNGEN UND VISUALISIERUNG ---

def create_cashflow_chart(initial_cost, net_annual_flow, title):
    """Generiert das kumulierte Cashflow-Diagramm."""
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
        name="Kumuliertes Ergebnis",
        marker_color=['#ef553b' if x < 0 else '#00cc96' for x in cashflow]
    ))
    fig.update_layout(title=title, xaxis_title="Jahr", yaxis_title="SEK", template="plotly_white")
    return fig, cashflow

def display_kpis(initial, netto, payback):
    """Zeigt die drei Schlüsselkennzahlen (KPIs) an."""
    col1_kpi, col2_kpi, col3_kpi = st.columns(3)
    initial = initial if initial is not None and initial >= 0 else 0
    netto = netto if netto is not None else 0
    payback = payback if payback is not None and payback >= 0 else 0

    col1_kpi.metric("Gesamtinvestition", f"{initial:,.0f} SEK".replace(",", " "))
    col2_kpi.metric("Jährliche Nettoeinsparung", f"{netto:,.0f} SEK".replace(",", " "), delta_color="normal")
    col3_kpi.metric("Amortisationszeit", f"{payback:.1f} Jahre" if payback > 0 else "N/A")

# --- HAUPTAPPLIKATION ---

st.set_page_config(page_title="IoT ROI Rechner", layout="wide")

st.title("💰 IoT ROI Rechner")
st.markdown("---")

# --- ANLEITUNG & WIKI ---
with st.expander("ℹ️ Anleitung & Wiki – So verwenden Sie den Rechner"):
    st.markdown("""
    Dieser Rechner hilft Ihnen, die **Rentabilität (Return on Investment, ROI)** für verschiedene IoT-Lösungen in Immobilien abzuschätzen.

    ### 1. Kalkulation wählen
    Verwenden Sie die Seitenleiste links (`🔎 Kalkulation wählen`), um zwischen den drei Analysebereichen zu wechseln: **Temperatur & Energie**, **IMD Wasserverbrauch** und **Wasserschadenschutz**.

    ### 2. Allgemeine Kosten (Seitenleiste)
    * Die Felder in der Seitenleiste (`⚙️ Allgemeine Betriebskosten`) – wie Anzahl der Wohnungen, Wartungskosten und jährliche Festgebühren – wirken sich auf **alle drei** Kalkulationen aus. Passen Sie diese zuerst an.

    ### 3. Das Szenario anpassen
    * Im Hauptfenster für Ihre ausgewählte Kalkulation passen Sie die **individuellen Parameter** (z. B. Sensorpreise, Installationskosten und Einsparprozentsätze) für dieses spezifische Szenario an.
    * Das Ergebnis (KPIs und Cashflow-Diagramm) wird sofort aktualisiert.

    ### 4. Szenarien speichern und laden (Varianten teilen)
    Sie können Ihre exakten Parametereinstellungen speichern, um sie später zu verwenden, zu archivieren oder zu vergleichen.
    * **Speichern:** Klicken Sie auf **"Speichern [Kalkulationsname] Szenario (.json)"**, um eine JSON-Datei mit allen aktuellen Einstellungen für die aktive Kalkulation herunterzuladen.
    * **Laden:** Verwenden Sie **"Laden [Kalkulationsname] Szenario (.json)"** und wählen Sie eine zuvor gespeicherte Datei aus. **Hinweis:** Nach dem Laden müssen Sie möglicherweise einmal auf die Kalkulation in der Seitenleiste klicken, um alle Regler aktualisiert zu sehen.
    
    **HINWEIS: Die Unterstützung für Link-Sharing/URL-Parameter wurde in dieser Version zugunsten der Stabilität entfernt.**
    """)
st.markdown("---")

# --- INITIALISIERUNG DES SESSION STATE (Eingabewerte) ---

# Gemeinsame Eingaben (Variablennamen bleiben Schwedisch, da sie nicht angezeigt werden)
if 'antal_lgh_main' not in st.session_state: st.session_state.antal_lgh_main = 1000
if 'uh_per_sensor' not in st.session_state: st.session_state.uh_per_sensor = 100
if 'lora_cost' not in st.session_state: st.session_state.lora_cost = 75
if 'web_cost' not in st.session_state: st.session_state.web_cost = 50
if 'app_cost' not in st.session_state: st.session_state.app_cost = 5000

# Flik 1: Temperatur & Energie
if 'pris_sensor_temp' not in st.session_state: st.session_state.pris_sensor_temp = 688
if 'pris_install_temp' not in st.session_state: st.session_state.pris_install_temp = 409
if 'startkostnad_temp' not in st.session_state: st.session_state.startkostnad_temp = 27500
if 'kvm_snitt' not in st.session_state: st.session_state.kvm_snitt = 67
if 'kwh_kvm' not in st.session_state: st.session_state.kwh_kvm = 130.6
if 'pris_kwh' not in st.session_state: st.session_state.pris_kwh = 1.02
if 'besparing_temp' not in st.session_state: st.session_state.besparing_temp = 6.0
if 'uh_besparing_temp' not in st.session_state: st.session_state.uh_besparing_temp = 200

# Flik 2: IMD Vatten
if 'pris_sensor_imd' not in st.session_state: st.session_state.pris_sensor_imd = 1875
if 'pris_install_imd' not in st.session_state: st.session_state.pris_install_imd = 459
if 'besparing_lgh_vatten' not in st.session_state: st.session_state.besparing_lgh_vatten = 500
if 'besparing_lgh_uh_imd' not in st.session_state: st.session_state.besparing_lgh_uh_imd = 200

# Flik 3: Vattenskadeskydd
if 'pris_sensor_skada' not in st.session_state: st.session_state.pris_sensor_skada = 714.42
if 'pris_install_skada' not in st.session_state: st.session_state.pris_install_skada = 523
if 'kostnad_skada' not in st.session_state: st.session_state.kostnad_skada = 70000
if 'frekvens_skada' not in st.session_state: st.session_state.frekvens_skada = 50
if 'besparing_skada_pct' not in st.session_state: st.session_state.besparing_skada_pct = 60.0
if 'uh_besparing_skada_lgh' not in st.session_state: st.session_state.uh_besparing_skada_lgh = 171


# --- NAVIGATION UND SEITENLEISTE FÜR ALLGEMEINE EINGABEN ---

with st.sidebar:
    st.header("🔎 Kalkulation wählen")
    
    # EINFACHE UND STABILE NAVIGATION MIT st.radio
    display_options = ["— Wählen Sie eine Kalkulation —"] + list(CALC_OPTIONS.keys())
    
    selected_calc_name = st.radio(
        "Wählen Sie den Bereich, den Sie analysieren möchten:", 
        options=display_options,
        index=0, # Startet auf der leeren Option
        key='radio_calc_selection'
    )
    
    # Bestimmt den aktiven Tab basierend auf der Auswahl
    if selected_calc_name == "— Wählen Sie eine Kalkulation —":
        active_tab = "" # Leerer String bedeutet Willkommensnachricht
    else:
        active_tab = CALC_OPTIONS[selected_calc_name]
    
    st.markdown("---")
    st.header("⚙️ Allgemeine Betriebskosten")
    
    # ... Sidebar-Eingaben ...
    antal_lgh = st.number_input("Anzahl der Wohnungen in der Immobilie", value=st.session_state.antal_lgh_main, step=10, key='antal_lgh_main')
    
    st.subheader("Jährliche Kosten pro Sensor/Wohnung")
    underhall_per_sensor = st.number_input("Wartung/Batterie pro Sensor/Jahr (SEK)", value=st.session_state.uh_per_sensor, key='uh_per_sensor')
    lora_kostnad = st.number_input("LoRaWAN-Anschluss pro Sensor/Jahr (SEK)", value=st.session_state.lora_cost, key='lora_cost')
    webiot_kostnad = st.number_input("Plattformskosten pro Sensor/Jahr (SEK)", value=st.session_state.web_cost, key='web_cost')
    
    st.subheader("Jahres-Festgebühr")
    applikation_kostnad = st.number_input("Anwendungskosten (feste Gebühr/Jahr)", value=st.session_state.app_cost, key='app_cost')
    
    # Gesamte jährliche Betriebskosten (wird in allen Kalkulationen verwendet)
    total_drift_ar_per_sensor = underhall_per_sensor + lora_kostnad + webiot_kostnad
    total_drift_ar = (antal_lgh * total_drift_ar_per_sensor) + applikation_kostnad


# --- 2. INHALTSBLÖCKE GESTEUERT DURCH active_tab ---

# --- WILLKOMMENSBILDSCHIRM (Neuer Startmodus) ---
if active_tab == "":
    st.info("👋 Willkommen! Bitte wählen Sie links in der Seitenleiste eine Kalkulation (z.B. '🌡️ Temperatur & Energie'), um mit der Berechnung des ROI zu beginnen.")
    st.snow() # Effekt: Schnee/Konfetti

# --- KALKULATION 1: TEMPERATUR & ENERGIE ---
elif active_tab == "temp":
    st.header("Temperatur- und Energiekalkulation")
    st.markdown("Fokus: Angepasste Wärmeverteilung, reduzierter Wartungsaufwand, optimierte Energie.")
    st.markdown("---")

    # --- FUNKTIONEN FÜR SPEICHERN/LADEN SZENARIO (TEMPERATUR) ---
    st.subheader("Szenario speichern/laden (Temperatur)")
    col_save, col_load = st.columns([1, 2])
    
    # 1. Szenario laden
    with col_load:
        uploaded_file = st.file_uploader("Temperatur Szenario laden (.json)", type="json", key='temp_scenario_uploader')
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("Temperatur Szenario geladen! Die Seite wird neu geladen, um die aktualisierten Werte anzuzeigen.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Die Datei konnte nicht geladen werden. Überprüfen Sie das Format: {e}")

    # 2. Szenario speichern
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
            label="Speichern Temperatur Szenario (.json)",
            data=json_data,
            file_name="iot_temp_scenario.json",
            mime="application/json",
            help="Speichert alle aktuellen Reglerwerte in einer Datei."
        )
    st.markdown("---")
    
    # --- KALKULATION 1 EINGABEN ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Anfangsinvestition")
        pris_sensor_temp = st.number_input("Preis pro Temp-Sensor (SEK)", value=st.session_state.pris_sensor_temp, key='pris_sensor_temp')
        pris_install_temp = st.number_input("Installation/Konfig. pro Sensor (SEK)", value=st.session_state.pris_install_temp, key='pris_install_temp') 
        startkostnad_projekt_temp = st.number_input("Projektstartkosten (SEK)", value=st.session_state.startkostnad_temp, key='startkostnad_temp')
        total_initial_temp = antal_lgh * (pris_sensor_temp * 1.01 + pris_install_temp) + startkostnad_projekt_temp # 1% Reserve

    with col2:
        st.subheader("Einsparparameter")
        kvm_snitt = st.number_input("Durchschnittliche Fläche pro Wohnung (qm)", value=st.session_state.kvm_snitt, key='kvm_snitt')
        energiforbrukning_kvm = st.number_input("Verbrauch (kWh/m²/Jahr)", value=st.session_state.kwh_kvm, key='kwh_kvm')
        energipris = st.number_input("Energiepreis (SEK/kWh)", value=st.session_state.pris_kwh, key='pris_kwh')
        besparing_procent = st.slider("Erwartete Energieeinsparung (%)", 0.0, 15.0, value=st.session_state.besparing_temp, step=0.1, key='besparing_temp')
        underhall_besparing_lgh = st.number_input("Reduzierte Wartung/Wohnung (SEK/Jahr)", value=st.session_state.uh_besparing_temp, key='uh_besparing_temp')
        
        total_kwh_fastighet = antal_lgh * kvm_snitt * energiforbrukning_kvm
        besparing_energi_kr = total_kwh_fastighet * energipris * (besparing_procent / 100)
        besparing_underhall_kr = antal_lgh * underhall_besparing_lgh
        total_besparing_temp = besparing_energi_kr + besparing_underhall_kr
        netto_temp = total_besparing_temp - total_drift_ar
        payback_temp = total_initial_temp / netto_temp if netto_temp > 0 else 0

    display_kpis(total_initial_temp, netto_temp, payback_temp)
    fig_temp, _ = create_cashflow_chart(total_initial_temp, netto_temp, "Kumulierter Cashflow (Temperatur)")
    st.plotly_chart(fig_temp, use_container_width=True)

# --- KALKULATION 2: IMD: WASSERVERBRAUCH ---
elif active_tab == "imd":
    st.header("IMD: Wasserverbrauchskalkulation")
    st.markdown("Fokus: Reduzierung des Wasser- und Warmwasserverbrauchs durch individuelle Messung und Abrechnung (IMD), z.B. Quandify.")
    st.markdown("---")
    
    # --- FUNKTIONEN FÜR SPEICHERN/LADEN SZENARIO (IMD) ---
    st.subheader("Szenario speichern/laden (IMD)")
    col_save, col_load = st.columns([1, 2])
    
    # 1. Szenario laden
    with col_load:
        uploaded_file = st.file_uploader("IMD Szenario laden (.json)", type="json", key='imd_scenario_uploader') 
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("IMD Szenario geladen! Die Seite wird neu geladen, um die aktualisierten Werte anzuzeigen.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Die Datei konnte nicht geladen werden. Überprüfen Sie das Format: {e}")

    # 2. Szenario speichern
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
            label="Speichern IMD Szenario (.json)",
            data=json_data,
            file_name="iot_imd_scenario.json",
            mime="application/json",
            help="Speichert alle aktuellen Reglerwerte in einer Datei."
        )
    st.markdown("---")
    
    col3, col4 = st.columns(2)
    
    with col3:
        st.subheader("Anfangsinvestition (IMD-Zähler)")
        pris_sensor_imd = st.number_input("Preis pro Wasserzähler/Sensor (SEK)", value=st.session_state.pris_sensor_imd, key='pris_sensor_imd')
        pris_install_imd = st.number_input("Installation/Konfig pro Zähler (SEK)", value=st.session_state.pris_install_imd, key='pris_install_imd') 
        total_initial_imd = antal_lgh * (pris_sensor_imd + pris_install_imd) + (5 * pris_sensor_imd) # Fünf Reservesensoren hinzugefügt
        
    with col4:
        st.subheader("Einsparparameter (Verbrauch)")
        besparing_per_lgh_vatten = st.number_input("Wasser/Warmwasser-Einsparung pro Wohnung/Jahr (SEK)", value=st.session_state.besparing_lgh_vatten, key='besparing_lgh_vatten')
        besparing_per_lgh_underhall = st.number_input("Reduzierte Wartung/Wohnung (SEK/Jahr)", value=st.session_state.besparing_lgh_uh_imd, key='besparing_lgh_uh_imd')
        
        total_besparing_imd = antal_lgh * (besparing_per_lgh_vatten + besparing_per_lgh_underhall)
        netto_imd = total_besparing_imd - total_drift_ar
        payback_imd = total_initial_imd / netto_imd if netto_imd > 0 else 0

    display_kpis(total_initial_imd, netto_imd, payback_imd)
    fig_imd, _ = create_cashflow_chart(total_initial_imd, netto_imd, "Kumulierter Cashflow (IMD Wasser)")
    st.plotly_chart(fig_imd, use_container_width=True)

# --- KALKULATION 3: WASSERSCHADENSCHUTZ ---
elif active_tab == "skada":
    st.header("Wasserschadenschutzkalkulation")
    st.markdown("Fokus: Vermeidung kostspieliger Wasserschäden durch frühzeitige Erkennung mittels Leckagesensoren, z.B. Elsys.")
    st.markdown("---")
    
    # --- FUNKTIONEN FÜR SPEICHERN/LADEN SZENARIO (WASSERSCHADEN) ---
    st.subheader("Szenario speichern/laden (Wasserschaden)")
    col_save, col_load = st.columns([1, 2])
    
    # 1. Szenario laden
    with col_load:
        uploaded_file = st.file_uploader("Wasserschaden Szenario laden (.json)", type="json", key='skada_scenario_uploader') 
        if uploaded_file is not None:
            try:
                scenario_data = json.load(uploaded_file)
                for key, value in scenario_data.items():
                    if key in st.session_state:
                        st.session_state[key] = value
                st.success("Wasserschaden Szenario geladen! Die Seite wird neu geladen, um die aktualisierten Werte anzuzeigen.")
                st.experimental_rerun()
            except Exception as e:
                st.error(f"Die Datei konnte nicht geladen werden. Überprüfen Sie das Format: {e}")

    # 2. Szenario speichern
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
            label="Speichern Wasserschaden Szenario (.json)",
            data=json_data,
            file_name="iot_skada_scenario.json",
            mime="application/json",
            help="Speichert alle aktuellen Reglerwerte in einer Datei."
        )
    st.markdown("---")
    
    col5, col6 = st.columns(2)

    with col5:
        st.subheader("Anfangsinvestition (Leckagesensor)")
        pris_sensor_skada = st.number_input("Preis pro Leckagesensor (SEK)", value=st.session_state.pris_sensor_skada, key='pris_sensor_skada')
        pris_install_skada = st.number_input("Installation/Konfig pro Sensor (SEK)", value=st.session_state.pris_install_skada, key='pris_install_skada') 
        total_initial_skada = antal_lgh * (pris_sensor_skada + pris_install_skada)
        
    with col6:
        st.subheader("Einsparparameter (Schadensminderung)")
        kostnad_vattenskada = st.number_input("Durchschnittliche Kosten pro Wasserschaden (SEK)", value=st.session_state.kostnad_skada, key='kostnad_skada')
        frekvens_vattenskada = st.number_input("Anzahl der Wasserschäden pro 1000 Wohnungen/Jahr (Ohne IoT)", value=st.session_state.frekvens_skada, key='frekvens_skada')
        besparing_procent_skador = st.slider("Erwartete Reduzierung der Schadenskosten (%)", 0.0, 90.0, value=st.session_state.besparing_skada_pct, step=5.0, key='besparing_skada_pct')
        
        # Berechnung
        tot_skadekostnad_utan_iot = (antal_lgh / 1000) * (frekvens_vattenskada * kostnad_vattenskada)
        besparing_skador_kr = tot_skadekostnad_utan_iot * (besparing_procent_skador / 100)
        
        uh_besparing_skada_lgh = st.number_input("Sonstige Wartungseinsparungen pro Wohnung/Jahr (SEK)", value=st.session_state.uh_besparing_skada_lgh, key='uh_besparing_skada_lgh')
        
        total_besparing_skada = besparing_skador_kr + (antal_lgh * uh_besparing_skada_lgh)
        netto_skada = total_besparing_skada - total_drift_ar
        payback_skada = total_initial_skada / netto_skada if netto_skada > 0 else 0

    display_kpis(total_initial_skada, netto_skada, payback_skada)
    fig_skada, _ = create_cashflow_chart(total_initial_skada, netto_skada, "Kumulierter Cashflow (Wasserschadenschutz)")
    st.plotly_chart(fig_skada, use_container_width=True)
    
    with st.expander("Berechnungsdetails"):
        st.write(f"Einsparung durch vermiedene Schadenskosten ({besparing_procent_skador:.1f}% von {tot_skadekostnad_utan_iot:,.0f} SEK): **{besparing_skador_kr:,.0f} SEK**")
        st.write(f"Sonstige Wartungseinsparungen (aus Excel): **{antal_lgh * uh_besparing_skada_lgh:,.0f} SEK**")
