import os
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image
import time
import base64
from supabase_db import SupabaseDB


st.set_page_config("THERAPIEKONZEPT", layout="wide")

# --- Database ---
@st.cache_resource
def get_db():
    return SupabaseDB()

# Initialize database connection
db = get_db()

def fetch_supplements():
    """Get supplements with categories"""
    return db.fetch_supplements()

def fetch_patient_names():
    """Get all patient names for autocomplete"""
    df = db.fetch_patient_names()
    return df

def save_patient_data(patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data):
    """Save patient data and all prescriptions to database"""
    return db.save_patient_data(patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data)

def delete_patient_data(patient_name):
    """Delete patient and all their data"""
    return db.delete_patient_data(patient_name)

def load_patient_data(patient_name):
    """Load patient data and all prescriptions from database"""
    return db.load_patient_data(patient_name)

# Enhanced CSS with larger fonts and proper divider spacing
st.markdown("""
<style>
.header-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 8px 0 !important;
}
.header-logo {
    flex: 1;
    text-align: left;
}
.header-title {
    flex: 2;
    text-align: center;
    margin: 0;
}
.header-address {
    flex: 1;
    text-align: right;
}
.header-address div {
    padding: 3px !important;
    line-height: 1.4 !important;
    font-size: 13px !important;
}

/* Main color theme - larger buttons */
.stButton > button {
    background-color: rgb(38, 96, 65) !important;
    color: white !important;
    border: 1px solid rgb(30, 76, 52) !important;
    padding: 10px 20px !important;
    font-size: 15px !important;
    border-radius: 6px !important;
}

/* Tabs styling - larger */
.stTabs {
    margin-top: 10px !important;
}

.stTabs [data-baseweb="tab-list"] {
    gap: 0px !important;
    width: 100% !important;
    margin-bottom: 10px !important;
}

.stTabs [data-baseweb="tab"] {
    height: 50px !important;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 4px 4px 0px 0px;
    padding: 12px 12px !important;
    color: rgb(38, 96, 65);
    flex: 1 !important;
    text-align: center !important;
    justify-content: center !important;
    width: 50% !important;
    margin: 0 !important;
    font-size: 16px !important;
    font-weight: 500 !important;
}

/* Checkbox styling - larger */
[data-testid="stCheckbox"] {
    margin: 5px 0 !important;
}

[data-testid="stCheckbox"] span {
    color: rgb(38, 96, 65) !important;
    font-size: 15px !important;
}

/* Radio button styling - larger */
[data-testid="stRadio"] {
    margin: 8px 0 !important;
}

[data-testid="stRadio"] span {
    color: rgb(38, 96, 65) !important;
    font-size: 15px !important;
}

/* Selectbox/Multiselect styling - larger */
[data-testid="stSelectbox"], [data-testid="stMultiSelect"] {
    margin-bottom: 10px !important;
}

[data-testid="stSelectbox"] span, [data-testid="stMultiSelect"] span {
    color: rgb(38, 96, 65) !important;
    font-size: 15px !important;
}

/* Text input/textarea styling - larger */
.stTextInput, .stTextArea, .stNumberInput, .stDateInput {
    margin-bottom: 10px !important;
}

.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
[data-testid="stDateInput"] > div > div > input {
    padding: 10px 12px !important;
    font-size: 15px !important;
    border-radius: 6px !important;
    border: 1px solid #ced4da !important;
}

/* Labels - larger */
.stTextInput label, .stTextArea label, .stNumberInput label, 
.stDateInput label, .stSelectbox label, .stMultiSelect label {
    font-size: 14px !important;
    font-weight: 500 !important;
    margin-bottom: 5px !important;
    color: #333 !important;
}

/* Success message styling */
.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 15px !important;
    border-radius: 8px !important;
    border: 1px solid #c3e6cb;
    margin: 15px 0 !important;
    font-size: 15px !important;
    font-weight: 500 !important;
}

/* General spacing */
.main > div {
    padding: 15px 20px !important;
}

/* Element spacing */
.stMarkdown, .stTextInput, .stNumberInput, .stDateInput, 
.stSelectbox, .stMultiSelect, .stCheckbox, .stRadio, 
.stButton, .stAlert {
    margin-bottom: 15px !important;
}

/* Form spacing */
div[data-testid="stForm"] {
    padding: 20px !important;
    border-radius: 10px !important;
}

/* Column spacing */
div[data-testid="column"] {
    padding: 0 10px !important;
}

/* Text elements - larger */
p, li, .stMarkdown, .stText {
    line-height: 1.6 !important;
    font-size: 15px !important;
}

/* Expanders - larger */
.streamlit-expanderHeader {
    font-size: 16px !important;
    font-weight: 600 !important;
    padding: 12px 12px !important;
}

.streamlit-expanderContent {
    padding: 20px 15px !important;
}

/* Section dividers - with proper spacing */
hr {
    margin: 25px 0 !important;
    border-width: 1px !important;
    border-color: #ddd !important;
}

/* Headers - larger */
.stMarkdown h1 {
    font-size: 2.2rem !important;
    margin-bottom: 10px !important;
}

.stMarkdown h2 {
    font-size: 1.8rem !important;
    margin-top: 25px !important;
    margin-bottom: 10px !important;
}

.stMarkdown h3 {
    font-size: 1.5rem !important;
    margin-top: 20px !important;
    margin-bottom: 10px !important;
}

.stMarkdown h4 {
    font-size: 1.3rem !important;
    margin-top: 15px !important;
    margin-bottom: 10px !important;
}

/* Section headers - larger */
.green-section-header {
    background-color: rgb(38, 96, 65) !important;
    color: white !important;
    padding: 12px 18px !important;
    border-radius: 6px !important;
    margin: 20px 0 15px 0 !important;
    font-weight: bold !important;
    font-size: 1.4rem !important;
    letter-spacing: 0.3px !important;
}

.section-subheader {
    font-weight: bold !important;
    font-size: 1.3rem !important;
    margin: 20px 0 12px 0 !important;
    color: rgb(38, 96, 65) !important;
    border-bottom: 2px solid rgb(38, 96, 65) !important;
    padding-bottom: 5px !important;
}

/* Progress bar */
.progress-container {
    margin: 20px 0 30px 0 !important;
    padding: 10px !important;
}

/* NEM sticky header */
.sticky-header {
    padding: 12px 0 !important;
    margin-bottom: 10px !important;
}

.sticky-header .stMarkdown {
    font-size: 14px !important;
}

/* Dropdown options - larger */
div[role="listbox"] ul li {
    font-size: 15px !important;
    padding: 10px 15px !important;
}

/* Caption */
.stCaption {
    font-size: 14px !important;
    color: #666 !important;
    margin-top: 8px !important;
    margin-bottom: 10px !important;
}

/* Container borders */
.stContainer {
    border-radius: 8px !important;
}

/* ========== INFUSION STYLING ========== */
/* Infusion row styling for perfect alignment */
.infusion-row {
    display: flex;
    align-items: center;
    gap: 8px;
    height: 40px;
}

.infusion-checkbox-wrapper {
    display: flex;
    align-items: center;
    height: 40px;
}

.infusion-checkbox-wrapper [data-testid="stCheckbox"] {
    margin: 0;
    padding: 0;
    display: flex;
    align-items: center;
}

.infusion-checkbox-wrapper [data-testid="stCheckbox"] label {
    display: flex;
    align-items: center;
    margin: 0;
    padding: 0;
    min-height: unset;
}

.infusion-label-container {
    display: flex;
    align-items: center;
    height: 40px;
}

/* Info icon - larger */
.info-icon {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    width: 20px;
    height: 20px;
    border-radius: 50%;
    background-color: rgb(38, 96, 65);
    color: white;
    font-size: 13px;
    font-weight: bold;
    cursor: help;
    margin-left: 6px;
    line-height: 1;
    position: relative;
}

.info-icon:hover::after {
    content: attr(data-tooltip);
    position: absolute;
    left: 25px;
    top: -12px;
    background-color: #333;
    color: white;
    padding: 8px 12px;
    border-radius: 4px;
    font-size: 13px;
    white-space: nowrap;
    z-index: 1000;
    box-shadow: 0 2px 5px rgba(0,0,0,0.2);
}

/* Procain row styling */
.procain-container {
    margin-top: 8px;
    width: 100%;
}

.procain-container .stTextInput {
    margin-top: 8px;
    margin-bottom: 0;
}

.procain-container .stTextInput input {
    padding: 8px 12px !important;
    font-size: 14px !important;
}

/* Infusion header styling */
.infusion-header {
    font-size: 15px !important;
    font-weight: bold !important;
    color: rgb(38, 96, 65) !important;
    margin: 0 !important;
}

/* Infusion section spacing */
.infusion-section {
    margin-bottom: 10px;
}

/* Infusion label text */
.infusion-label-container span:first-child,
.infusion-label-text {
    font-size: 15px !important;
}

/* Additional fields in infusion section */
.weitere-angaben {
    font-size: 15px !important;
}

/* Multiselect in infusion section */
.infusion-multiselect .stMultiSelect {
    margin-bottom: 12px !important;
}

.infusion-multiselect label {
    font-size: 14px !important;
}

/* ========== END INFUSION STYLING ========== */

/* Patient data columns */
[data-testid="column"] .stDateInput, 
[data-testid="column"] .stRadio, 
[data-testid="column"] .stNumberInput,
[data-testid="column"] .stSelectbox {
    margin-bottom: 10px !important;
}

/* Kontrolltermine checkboxes */
[data-testid="column"] .stCheckbox {
    margin: 5px 0 !important;
}

/* Suggestions buttons */
div[data-testid="stHorizontalBlock"] button {
    margin: 3px !important;
    padding: 6px 10px !important;
    font-size: 14px !important;
}

/* Alert messages */
.stAlert {
    padding: 15px !important;
    margin: 20px 0 !important;
    font-size: 15px !important;
    border-left-width: 5px !important;
}

/* Table text */
.stTable {
    font-size: 14px !important;
}

/* Number input buttons */
.stNumberInput button {
    padding: 0 10px !important;
    font-size: 15px !important;
}

/* Date input */
[data-testid="stDateInput"] input {
    font-size: 15px !important;
}

/* Select box placeholder */
.stSelectbox div[data-baseweb="select"] span {
    font-size: 15px !important;
}

/* Multi-select tags */
[data-baseweb="tag"] span {
    font-size: 14px !important;
    padding: 3px 8px !important;
}

/* Checkbox groups */
.row-container {
    display: flex;
    gap: 20px;
    margin-bottom: 10px;
}

/* PDF header */
.pdf-header {
    background-color: rgb(38, 96, 65) !important;
    color: white !important;
}
</style>
""", unsafe_allow_html=True)


# Header with three columns
col1, col2, col3 = st.columns([1.2, 3, 0.7])

with col1:
    st.markdown('<div class="header-logo">', unsafe_allow_html=True)
    if os.path.exists("clinic_logo.png"):
        st.image("clinic_logo.png", width=200)
    st.markdown('</div>', unsafe_allow_html=True)

with col2:
    st.markdown('<div class="header-title">', unsafe_allow_html=True)
    st.markdown("<h1 style='text-align: center; margin: 0;'>THERAPIEKONZEPT</h1>", unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

with col3:
    st.markdown('<div class="header-address">', unsafe_allow_html=True)
    st.markdown("""
    <div style="font-size:15px; line-height:1.8;">
    Clausewitzstr. 2<br>
    10629 Berlin-Charlottenburg<br>
    +49 30 6633110<br>
    info@revitaclinic.de<br>
    www.revitaclinic.de
    </div>
    """, unsafe_allow_html=True)
    #st.markdown('</div>', unsafe_allow_html=True)

#st.markdown("<hr>", unsafe_allow_html=True)



DEFAULT_FORMS = {
    # Basis (1)
    "Magnesiumbisglycinat": "Pulver",
    "Magnesiumthreonat": "Pulver",
    "liposomales Magnesium 200mg": "Kapseln",
    "Vitamin C / Na Ascorbat": "Pulver",
    "Vitamin C 1000mg": "Kapseln",
    "Ascorbyl Palmitat / liposomales Vitamin C": "Kapseln",
    "L-Carnitin (Carnipure)": "Kapseln",
    "L-Carnitin (Carnipure) Lösung": "Lösung",
    "Kapselmischung nach UR V.9 Arnika": "Kapseln",
    "Multi Mischung Vitamine & Mineralien": "Kapseln",
    "Benfothiamin": "Kapseln",
    "Vitamin B6 – P5P aktiviert": "Kapseln",
    "Mangan 10mg": "Tabletten",
    "Nattokinase 100mg": "Kapseln",
    "Q10 400mg": "Kapseln",
    "Selen 300 (100 Stk) Arnika": "Kapseln",
    "Selen 200 Na-Selenit": "Kapseln",
    "Vitamin E 800 IU E8 Tocotrienol": "Kapseln",
    "Polyphenol Arnika": "Kapseln",
    "Vitamin D3": "Tropfen",
    "Vitamin K2 1000µg": "Kapseln",
    "Calcium": "Tabletten",
    "OPC": "Kapseln",
    "Lugolsche Lösung (Jod) 5%": "Tropfen",
    "Kelp mit Jod": "Tabletten",
    "Zink 25mg (Zink-Glycinat)": "Kapseln",
    "Eisen": "Tabletten",
    "R-Alpha Liponsäure 400mg": "Kapseln",
    "Lactoferrin": "Kapseln",
    "Quercetin 500mg": "Kapseln",
    "Enzyme Multienzym / Superenzym": "Kapseln",
    "Sulbutiamin": "Kapseln",
    "Spermidin": "Kapseln",
    "Berberin (plaquefrei)": "Kapseln",
    "Benfotiamin (B1 fürs Nervensystem)": "Kapseln",
    "Huperzin": "Kapseln",
    "Kalium": "Pulver",
    "Lithiumorotat 1mg": "Tabletten",
    "Lithiumorotat 5mg": "Tabletten",
    
    # Gehirn / Gedächtnis (2)
    "Omega-3 Öl 1 EL = 2g EPA/DHA": "Öl",
    "Alpha GPC": "Kapseln",
    "Phosphatidylserin / Phosphatidylcholin": "Kapseln",
    "NMN 500mg": "Kapseln",
    "NAD+ liposomal 500mg": "Kapseln",
    "Citicolin": "Kapseln",
    "Trans-Resveratrol 1000mg": "Kapseln",
    "Astaxanthin 18mg": "Kapseln",
    "Lutein 40mg": "Kapseln",
    "Piracetam (Memory)": "Kapseln",
    "Aniracetam (Learning)": "Kapseln",
    
    # Aminosäuren (3)
    "MAP (Aminosäuremischung)": "Pulver",
    "Proteinshake 2 Messlöffel": "Pulver",
    "Tyrosin 500mg": "Kapseln",
    "5-HTP 200mg": "Kapseln",
    "5-HTP 300mg": "Kapseln",
    "5-HTP 600mg": "Kapseln",
    "SAMe 400mg": "Tabletten",
    "Phenylalanin 500mg": "Kapseln",
    "GABA 1g": "Kapseln",
    "Tryptophan 1000mg": "Kapseln",
    "Tryptophan 500mg": "Kapseln",
    "Lysin": "Pulver",
    "Prolin": "Pulver",
    "Arginin 1g": "Kapseln",
    "Citrullin": "Kapseln",
    "Ornithin": "Kapseln",
    "Histidin": "Kapseln",
    "BCAA 1g": "Kapseln",
    "Glycin 1000mg": "Kapseln",
    "Taurin": "Pulver",
    "Methionin 500mg": "Kapseln",
    "Kreatin Monohydrat": "Pulver",
    "Carnosin 500mg": "Kapseln",
    "Amin (artgerecht)": "Pulver",
    
    # Entgiftung oral (4)
    "MSM 1000mg": "Tabletten",
    "liposomales Glutathion": "Kapseln",
    "Zeolith": "Pulver",
    "DMSA 100mg": "Kapseln",
    "Ca EDTA 750mg": "Kapseln",
    "Chlorella Algen": "Tabletten",
    "NAC 600mg": "Kapseln",
    "NAC 800mg": "Kapseln",
    "TUDCA 500mg": "Kapseln",
    "Lymphdiaral / Lymphomyosot": "Tropfen",
    "Ceres Geranium robertianum": "Tropfen",
    "Mineralien und Spurenelemente Mischung": "Pulver",
    "NACET 100mg": "Kapseln",
    "Bromelain 750mg": "Kapseln",
    "Sulforaphan 35mg": "Kapseln",
    "Tamarindenextrakt": "Kapseln",
    "Chelidonium": "Tropfen",
    "Hyperikum": "Tropfen",
    "Colostrum (freeze-dried)": "Pulver",
    
    # Darmsanierung nach Paracelsus Kl. (5)
    "Symbiolact Pur": "Pulver",
    "Probio-Cult AKK1": "Pulver",
    "Glutamin 1g": "Kapseln",
    "Mucosa Compositum": "Tabletten",
    "Basenpulver": "Pulver",
    "Vermox": "Tabletten",
    
    # Leberdetox nach Paracelsus Kl. (6)
    "Okoubaka": "Tropfen",
    "Bittersalz": "Pulver",
    "Bile Acid Factors": "Kapseln",
    "Mariendistel / Carduus Marianus / Taraxacum": "Tropfen",
    "Bitterliebe": "Kapseln",
    
    # Schlafen (7)
    "Baldrian / Hopfen": "Kapseln",
    "Melatonin": "Tabletten",
    
    # Gelenke / Bindegewebe (8)
    "Glucosamin 10g": "Pulver",
    "Chondroitin 10g": "Pulver",
    "Silizium G7": "Flüssig",
    "Kollagen": "Pulver",
    "Isagenix SuperKollagen": "Pulver",
    
    # Infektionsbehandlung (9)
    "Disulfiram": "Tabletten",
    "Quentakehl": "Kapseln",
    "Lysin 1g": "Kapseln",
    "Weihrauch (Boswelliasäure)": "Kapseln",
    "Curcuma": "Kapseln",
    "CurcumaXan Spray Arnika": "Spray",
    "Helicobacter-Therapie": "Kapseln",
    "Symbiolact comp.": "Pulver",
    "Artemisia annua 600mg": "Kapseln",
    "Artemisia annua Pulver": "Pulver",
    "Amantadin 100mg": "Tabletten",
    "Hydroxychloroquin (HCQ) 200mg": "Tabletten",
    "Ivermectin": "Tabletten",
    "Schwarzkümmelöl": "Kapseln",
    "Astragalus": "Kapseln",
    "Andrographis 400mg": "Kapseln",
    "Andrographis 500mg": "Kapseln",
    "AHCC 500mg": "Kapseln",
    
    # Hormone (10)
    "Östradiol 0,03%": "Creme",
    "Östradiol 0,06%": "Creme",
    "Progesteroncreme 3%": "Creme",
    "Progesteroncreme 10%": "Creme",
    "DHEA 2% Creme": "Creme",
    "Estradiol 0,04% / Estriol 1,6% / Testosteron 0,2%": "Creme",
    "DHEA 5% Gel": "Gel",
    "Testosteron 10% Gel": "Gel",
    "Testosteron 8mg (Frauen)": "Gel",
    "Testosteron 50mg": "Gel",
    "Testosteron 100mg": "Gel",
    "Testosteron 150mg": "Gel",
    "Progesteron 25mg (Männer)": "Kapseln",
    "DHEA 5mg": "Kapseln",
    "DHEA 10mg": "Kapseln",
    "DHEA 25mg": "Kapseln",
    "DHEA 50mg": "Kapseln",
    "Pregnenolon 10mg": "Kapseln",
    "Pregnenolon 30mg": "Kapseln",
    "Pregnenolon 50mg": "Kapseln",
    "Pregnenolon 100mg": "Kapseln",
    "Phytocortal 100ml": "Tropfen",
    "Ceres Ribes nigrum": "Tropfen",
    "Lion's Mane Mushroom Extrakt 500mg": "Kapseln",
    "LDN 1mg": "Tabletten",
    "LDN 1,5mg": "Tabletten",
    "LDN 4mg": "Tabletten",
    "LDN 4,5mg": "Tabletten",
    
    # Biologische Therapie (11)
    "Ceres Solidago comp.": "Tropfen",
    
    # Sonstiges (12)
    "Pro Human Probiotikum": "Kapseln",
    "Thymusextrakt": "Kapseln",
    "Nierenextrakt": "Kapseln",
    "Leberextrakt": "Kapseln",
    "Adrenal Organzellextrakt": "Kapseln",
    "Frischpflanzensaft": "Flüssig",
    "Löwenzahn / Sellerie / Bärlauch": "Flüssig",
    "Kaktusfeige": "Kapseln",
    "Kiefernadeltee": "Tee",
    "Weidenröschen (Fireweed)": "Tee",
    "SuperPatches einzeln": "Pflaster",
    "SuperPatches Packung 28er": "Pflaster"
}

def therapy_progress_bar(therapiebeginn, dauer_monate):
    """
    Display a therapy progress bar with a small person figure
    showing the current week of therapy
    """
    from datetime import date, datetime
    
    if not therapiebeginn or not dauer_monate:
        return
    
    # Calculate weeks passed
    today = date.today()
    
    # Handle date
    if isinstance(therapiebeginn, str):
        try:
            therapiebeginn = datetime.strptime(therapiebeginn, "%Y-%m-%d").date()
        except:
            return
    elif not isinstance(therapiebeginn, date):
        return
    
    # If therapy hasn't started yet
    if today < therapiebeginn:
        return
    
    days_passed = (today - therapiebeginn).days
    weeks_passed = days_passed // 7
    total_weeks = dauer_monate * 4
    progress = min(100, (weeks_passed / total_weeks * 100) if total_weeks > 0 else 0)
    
    # Create a VERY simple HTML progress bar
    html = f"""
    <div style="margin: 20px 0; padding: 15px; background: #f0f2f6; border-radius: 10px;">
        <div style="font-weight: bold; color: rgb(38, 96, 65); margin-bottom: 10px;">
            Therapie-Fortschritt: Woche {weeks_passed} von {total_weeks}
        </div>
        <div style="position: relative; height: 40px; background: #ddd; border-radius: 20px;">
            <div style="width: {progress}%; height: 100%; background: rgb(38, 96, 65); border-radius: 20px;"></div>
            <div style="position: absolute; top: 0; left: {progress}%; transform: translateX(-50%);">
                <div style="background: white; border-radius: 50%; width: 40px; height: 40px; 
                            border: 2px solid rgb(38, 96, 65); display: flex; align-items: center; 
                            justify-content: center; box-shadow: 0 2px 5px rgba(0,0,0,0.2);">
                    <span style="font-size: 24px;">👤</span>
                </div>
            </div>
        </div>
    </div>
    """
    
    st.markdown(html, unsafe_allow_html=True)


def get_current_therapy_week(therapiebeginn):
    """Helper function to get current therapy week number"""
    from datetime import date, datetime
    
    if not therapiebeginn:
        return 0
    
    today = date.today()
    if isinstance(therapiebeginn, str):
        try:
            therapiebeginn = datetime.strptime(therapiebeginn, "%Y-%m-%d").date()
        except:
            return 0
    
    days_passed = (today - therapiebeginn).days
    return max(0, days_passed // 7)

def patient_inputs():
    from datetime import date
    import streamlit as st

    # --------------------------------------------------
    # Get patient names
    # --------------------------------------------------
    patient_names_df = fetch_patient_names()
    patient_names = patient_names_df["patient_name"].tolist() if not patient_names_df.empty else []

    # --------------------------------------------------
    # Session state initialization
    # --------------------------------------------------
    defaults = {
        "patient_data": {},
        "nem_prescriptions": [],
        "therapieplan_data": {},
        "ernaehrung_data": {},
        "infusion_data": {},
        "last_loaded_patient": None,
        "just_loaded_patient": False,
        "current_patient_input": "",
        "clicked_suggestion": None,
        "display_patient_name": "",
    }

    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # --------------------------------------------------
    # Header
    # --------------------------------------------------
    st.markdown("#### Patientendaten")

    # --------------------------------------------------
    # Handle suggestion click
    # --------------------------------------------------
    if st.session_state.clicked_suggestion:
        name = st.session_state.clicked_suggestion

        result = load_patient_data(name)
        if result[0]:
            patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result

            # Update ALL session state at once
            st.session_state.patient_data = patient_data
            st.session_state.nem_prescriptions = nem_prescriptions if nem_prescriptions else []
            st.session_state.therapieplan_data = therapieplan_data if therapieplan_data else {}
            st.session_state.ernaehrung_data = ernaehrung_data if ernaehrung_data else {}
            st.session_state.infusion_data = infusion_data if infusion_data else {}

            st.session_state.last_loaded_patient = name
            st.session_state.display_patient_name = name
            st.session_state.just_loaded_patient = True

        st.session_state.clicked_suggestion = None
        st.rerun()

    # --------------------------------------------------
    # Text input
    # --------------------------------------------------
    display_value = (
        st.session_state.display_patient_name
        if st.session_state.display_patient_name
        else st.session_state.patient_data.get("patient", "")
    )

    typed = st.text_input(
        "Geben Sie den Namen ein und drücken Sie die Eingabetaste, um Vorschläge zu suchen.",
        value=display_value,
        placeholder="Vor- und Nachname",
    )

    # --------------------------------------------------
    # Track typing
    # --------------------------------------------------
    if typed != st.session_state.current_patient_input:
        st.session_state.current_patient_input = typed

        if (
            st.session_state.last_loaded_patient
            and typed
            and typed not in patient_names
        ):
            # Clear all data when typing a new patient
            st.session_state.patient_data = {}
            st.session_state.nem_prescriptions = []
            st.session_state.therapieplan_data = {}
            st.session_state.ernaehrung_data = {}
            st.session_state.infusion_data = {}
            st.session_state.last_loaded_patient = None
            st.session_state.display_patient_name = ""
            st.session_state.just_loaded_patient = False
            st.rerun()

    st.session_state.display_patient_name = typed

    # --------------------------------------------------
    # Suggestions
    # --------------------------------------------------
    if typed and typed not in patient_names and not st.session_state.just_loaded_patient:
        suggestions = [n for n in patient_names if typed and typed.lower() in n.lower()]
        
        if suggestions:
            st.write("**Vorschläge:**")
            cols = st.columns(3)
            for i, name in enumerate(suggestions[:9]):
                col_idx = i % 3
                with cols[col_idx]:
                    if st.button(name, key=f"suggest_{name}", use_container_width=True):
                        st.session_state.clicked_suggestion = name
                        st.rerun()

    # --------------------------------------------------
    # Auto-load on Enter
    # --------------------------------------------------
    if (
        typed
        and typed in patient_names
        and typed != st.session_state.last_loaded_patient
        and not st.session_state.just_loaded_patient
    ):
        result = load_patient_data(typed)
        if result[0]:
            patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result

            st.session_state.patient_data = patient_data
            st.session_state.nem_prescriptions = nem_prescriptions if nem_prescriptions else []
            st.session_state.therapieplan_data = therapieplan_data if therapieplan_data else {}
            st.session_state.ernaehrung_data = ernaehrung_data if ernaehrung_data else {}
            st.session_state.infusion_data = infusion_data if infusion_data else {}

            st.session_state.last_loaded_patient = typed
            st.session_state.display_patient_name = typed
            st.session_state.just_loaded_patient = True
            st.rerun()

    # Reset flag
    if st.session_state.just_loaded_patient:
        st.session_state.just_loaded_patient = False

    # --------------------------------------------------
    # Defaults
    # --------------------------------------------------
    pdata = st.session_state.patient_data or {}

    def parse_date(date_val):
        if isinstance(date_val, str):
            try:
                return date.fromisoformat(date_val)
            except:
                return date.today()
        return date_val if isinstance(date_val, date) else date.today()

    default_geburtsdatum = parse_date(pdata.get("geburtsdatum", date.today()))
    default_geschlecht = pdata.get("geschlecht", "M")
    default_groesse = int(pdata.get("groesse", 0)) if pdata.get("groesse") else 0
    default_gewicht = int(pdata.get("gewicht", 0)) if pdata.get("gewicht") else 0
    default_therapiebeginn = parse_date(pdata.get("therapiebeginn", date.today()))
    
    dauer_value = pdata.get("dauer", 6)
    if isinstance(dauer_value, str):
        try:
            default_dauer_value = int(dauer_value)
        except:
            default_dauer_value = 6
    else:
        default_dauer_value = dauer_value
    
    default_tw_besprochen = pdata.get("tw_besprochen", "Ja")
    default_allergie = pdata.get("allergie", "")
    default_diagnosen = pdata.get("diagnosen", "")
    
    default_kontrolltermin_4 = pdata.get("kontrolltermin_4", False)
    default_kontrolltermin_12 = pdata.get("kontrolltermin_12", False)
    default_kontrolltermin_24 = pdata.get("kontrolltermin_24", False)
    default_kontrolltermin_kommentar = pdata.get("kontrolltermin_kommentar", "")

    # --------------------------------------------------
    # Form fields layout
    # --------------------------------------------------
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    with c1:
        geburtsdatum = st.date_input(
            "Geburtsdatum",
            value=default_geburtsdatum,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD.MM.YYYY",
            key="geburtsdatum_input"
        )

    with c2:
        geschlecht = st.radio(
            "Geschlecht", ["M", "W"], horizontal=True,
            index=0 if default_geschlecht == "M" else 1,
            key="geschlecht_input"
        )

    with c3:
        groesse = st.number_input("Grösse (cm)", min_value=0, value=default_groesse, key="groesse_input")

    with c4:
        gewicht = st.number_input("Gewicht (kg)", min_value=0, value=default_gewicht, key="gewicht_input")

    with c5:
        therapiebeginn = st.date_input(
            "Therapiebeginn",
            value=default_therapiebeginn,
            format="DD.MM.YYYY",
            key="therapiebeginn_input"
        )

    with c6:
        dauer = st.selectbox(
            "Dauer (Monate)",
            list(range(1, 13)),
            index=default_dauer_value - 1 if 1 <= default_dauer_value <= 12 else 5,
            key="dauer_input"
        )

    with c7:
        tw_besprochen = st.radio(
            "TW besprochen?",
            ["Ja", "Nein"],
            horizontal=True,
            index=0 if default_tw_besprochen == "Ja" else 1,
            key="tw_besprochen_input"
        )

    bekannte_allergie = st.text_input("Bekannte Allergie?", value=default_allergie, key="allergie_input")

    diagnosen = st.text_area(
        "Diagnosen",
        value=default_diagnosen,
        height=120,
        placeholder="Relevante Diagnosen...",
        key="diagnosen_input"
    )

    # --------------------------------------------------
    # Kontrolltermine
    # --------------------------------------------------
    st.markdown("---")
    st.markdown("#### Kontrolltermine")

    col1, col2, col3 = st.columns(3)
    with col1:
        kontrolltermin_4 = st.checkbox("4 Wochen", value=default_kontrolltermin_4, key="kontrolltermin_4_input")
    with col2:
        kontrolltermin_12 = st.checkbox("12 Wochen", value=default_kontrolltermin_12, key="kontrolltermin_12_input")
    with col3:
        kontrolltermin_24 = st.checkbox("24 Monate", value=default_kontrolltermin_24, key="kontrolltermin_24_input")

    kontrolltermin_kommentar = st.text_input("Kommentar:", value=default_kontrolltermin_kommentar, key="kontrolltermin_kommentar_input")

    # --------------------------------------------------
    # Therapy Progress Bar
    # --------------------------------------------------
    st.markdown("---")
    therapy_progress_bar(therapiebeginn, dauer)

    # --------------------------------------------------
    # RETURN
    # --------------------------------------------------
    data = {
        "patient": typed,
        "geburtsdatum": geburtsdatum,
        "geschlecht": geschlecht,
        "groesse": groesse,
        "gewicht": gewicht,
        "therapiebeginn": therapiebeginn,
        "dauer": dauer,
        "tw_besprochen": tw_besprochen,
        "allergie": bekannte_allergie,
        "diagnosen": diagnosen,
        "kontrolltermin_4": kontrolltermin_4,
        "kontrolltermin_12": kontrolltermin_12,
        "kontrolltermin_24": kontrolltermin_24,
        "kontrolltermin_kommentar": kontrolltermin_kommentar,
    }

    return data


# --- Helpers ---
def _fmt_dt(d):
    try:
        return d.strftime("%d.%m.%Y")
    except Exception:
        return ""

class PDF(FPDF):
    def header(self):
        if os.path.exists("clinic_logo.png"):
            try:
                self.image("clinic_logo.png", 10, 8, 40)
            except:
                pass
        
        # Add title between logo and address
        self.set_font("Helvetica", "B", 16)
        self.set_xy(100, 13)
        self.cell(100, 10, "THERAPIEKONZEPT - NEM", 0, 0, "C")
        
        self.set_font("Helvetica", "", 10)
        self.set_xy(230, 10)
        self.multi_cell(60, 5,
            "Clausewitzstr. 2\n10629 Berlin-Charlottenburg\n+49 30 6633110\ninfo@revitaclinic.de",
            0, "R"
        )
        self.ln(12)


def generate_pdf(patient, supplements, tab_name="NEM"):
    pdf = PDF("L", "mm", "A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Helper function to clean text
    def clean_text(text):
        if not text:
            return ""
        text = str(text)
        text = text.replace('•', '-')  # Replace bullet with dash
        text = text.replace('–', '-')  # en dash
        text = text.replace('—', '-')  # em dash
        text = text.replace('−', '-')  # minus sign
        return text

    # Patient info
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Vor- und Nachname:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, clean_text(patient.get("patient", "")), 0, 1)
    pdf.ln(2)

    col_w = [38, 38, 30, 30, 42, 28, 35, 70]
    
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[0], 6, "Geburtsdatum:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[1], 6, _fmt_dt(patient.get("geburtsdatum")), 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[2], 6, "Geschlecht:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[3], 6, patient.get("geschlecht", ""), 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[4], 6, "Grösse:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[5], 6, f"{patient.get('groesse','')} cm", 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[6], 6, "Gewicht:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[7], 6, f"{patient.get('gewicht','')} kg", 0, 1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[0], 6, "Therapiebeginn:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[1], 6, _fmt_dt(patient.get("therapiebeginn")), 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[2], 6, "Dauer:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[3], 6, f"{patient.get('dauer','')} Monate", 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[4], 6, "TW besprochen?:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[5], 6, patient.get("tw_besprochen", ""), 0, 0)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[6], 6, "Bekannte Allergie:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    allergie_text = patient.get("allergie", "")
    if len(allergie_text) > 45:
        allergie_text = allergie_text[:42] + "..."
    pdf.cell(col_w[7], 6, clean_text(allergie_text), 0, 1)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Diagnosen:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    diagnosen = clean_text(patient.get("diagnosen", "") or "-")
    pdf.multi_cell(0, 5, diagnosen, 0, "L")
    pdf.ln(3)

    # Kontrolltermine
    pdf.ln(3)
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Kontrolltermine:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    
    kontrolltermine_text = ""
    if patient.get("kontrolltermin_4", False):
        kontrolltermine_text += "- 4 Wochen\n"
    if patient.get("kontrolltermin_12", False):
        kontrolltermine_text += "- 12 Wochen\n"
    if patient.get("kontrolltermin_24", False):  # Add this
        kontrolltermine_text += "- 24 Monate\n"
    
    kontrolltermin_kommentar = clean_text(patient.get("kontrolltermin_kommentar", ""))
    if kontrolltermin_kommentar:
        if kontrolltermine_text:
            kontrolltermine_text += f"Kommentar: {kontrolltermin_kommentar}"
        else:
            kontrolltermine_text = f"Kommentar: {kontrolltermin_kommentar}"
    
    if not kontrolltermine_text:
        kontrolltermine_text = "- Keine Angaben"
    
    pdf.multi_cell(0, 5, kontrolltermine_text, 0, "L")
    pdf.ln(3)

    # Content based on tab
    if tab_name == "NEM" and isinstance(supplements, list):
        # Supplements Table
        table_width = 277
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(table_width, 8, "NAHRUNGSERGÄNZUNGSMITTEL (NEM) VO", 0, 1, "L", True)

        headers = ["Supplement", "Gesamt-dosierung", "Darreichungsform", "Pro Einnahme", "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]
        base_widths = [50, 20, 35, 20, 18, 18, 18, 18, 18]
        used_width = sum(base_widths)
        comment_width = table_width - used_width
        widths = base_widths + [comment_width]

        # Store header row for repeating on new pages
        def table_header():
            pdf.set_fill_color(38, 96, 65)
            pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 10)
            for w, h in zip(widths, headers):
                pdf.cell(w, 8, h, 1, 0, "C", True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0)
            pdf.set_font("Helvetica", "", 9)

        # Print initial header
        table_header()

        # Keep track of row count for page breaks
        row_count = 0
        rows_per_page = 25  # Adjust based on your font size and page layout

        for s in supplements:
            row = [
                clean_text(s.get("name", "")),
                clean_text(s.get("Gesamt-dosierung", "")),
                clean_text(s.get("Darreichungsform", "")),
                clean_text(s.get("Pro Einnahme", "")),
                clean_text(s.get("Nüchtern", "")),
                clean_text(s.get("Morgens", "")),
                clean_text(s.get("Mittags", "")),
                clean_text(s.get("Abends", "")),
                clean_text(s.get("Nachts", "")),
                clean_text(s.get("Kommentar", ""))
            ]

            comment_text = row[-1] or ""
            line_height = 8
            comment_lines = int(pdf.get_string_width(comment_text) / (widths[-1] - 2)) + 1 if comment_text else 1
            row_height = max(line_height, line_height * comment_lines)

            # Check if we need a new page
            if pdf.get_y() + row_height > pdf.page_break_trigger:
                pdf.add_page()
                table_header()  # Repeat header on new page
                row_count = 0

            for i, (w, text, header) in enumerate(zip(widths[:-1], row[:-1], headers[:-1])):
                align = "L" if i == 0 else "C"
                if header in ["Nüchtern", "Morgens", "Mittags", "Abends", "Nachts"]:
                    display_text = f"{text}x" if str(text).strip() else ""
                else:
                    display_text = str(text)
                pdf.cell(w, row_height, display_text, 1, 0, align)

            x = pdf.get_x()
            y = pdf.get_y()
            pdf.multi_cell(widths[-1], line_height, comment_text, 1)
            pdf.set_xy(x + widths[-1], y)
            pdf.ln(row_height)
            
            row_count += 1

    elif tab_name == "THERAPIEPLAN" and isinstance(supplements, dict):
        # For Therapieplan tab - includes Diagnostik & Überprüfung + Therapieformen
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "THERAPIEPLAN", 0, 1, "C", True)
        pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        
        # Define mapping from keys to human-readable labels for Therapieplan tab
        label_mapping = {
            # Diagnostik & Überprüfung
            "zaehne": "Überprüfung der Zähne/Kieferknochen mittels OPG (Panoramaaufnahme mit lachendem Gebiss) / DVT",
            "zaehne_zu_pruefen": "Zähne zu überprüfen (OPG/DVT)",
            "darm_biofilm": "Darm - Biofilmentfernung nach www.regenbogenkreis.de (Express-Darmkur 4 Tageskur)",
            "darmsanierung": "Darmsanierung nach Paracelsus Klinik (Rezept von Praxis)",
            "darmsanierung_dauer": "Darmsanierung Dauer",
            "hydrocolon": "mit Hydrocolon (Darmspülung) 2x insgesamt, Abstand 14 Tage mit Rekolonisierungs-Shot",
            "parasiten": "Parasitenbehandlung mit Vermox (3 Tage)",
            "parasiten_bio": "Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)",
            "leberdetox": "Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5x alle 4–6 Wochen)",
            "nierenprogramm": "Nierenprogramm nach Dr. Clark – 4 Wochen – bitte bei www.drclarkcenter.de beziehen",
            "infektion_bakt": "Infektionsbehandlung für Bakterien (Borr./Helicob.)",
            "infektion_virus": "Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona)",
            "ausleitung_inf": "Schwermetallausleitung Infusion",
            "ausleitung_oral": "Schwermetallausleitung oral",
            "mikronaehrstoffe": "Einnahme Mikronährstoffen (NEM-Verordnung) (siehe separate PDF)",
            "infusionsbehandlung": "Infusionstherapie (siehe separate PDF)",
            "neuraltherapie": "Neuraltherapie",
            "eigenblut": "Eigenbluttherapie",
            "medikamente": "Medikamentenverordnung - Rezept für",
            "bio_isopath": "Biologische Isopathische Therapie",
            "timewaver_freq": "TimeWaver Frequency Behandlung",
            "ernaehrung": "Ernährungsberatung",
            "hypnose": "Hypnosetherapie (Noreen Martin Miro)",
            "yager": "Yagertherapie",
            "aethetisch": "Ästhetische Behandlung (Botox/PRP/Fäden/Hyaloron)",
            "ozontherapie": "Ozontherapie",
            "medikamente_text": "Medikamentenverordnung - Rezept Details",
            "akupunktur": "Akupunktur",
            "homoeopathie": "Homöopathie (Anna)",
            "bioresonanz": "Bioresonanz (Anna)",
            "leberreinigung": "Leberreinigung",
            "ketogene": "Ketogene Ernährung",
            "naehrstoff_ausgleich": "Nährstoffmängel ausgleichen",
            "therapie_sonstiges": "Sonstiges (Therapie)",
            "magenband": "Magenband",
            "energie_behandlungen": "Energiebehandlungen bei Marie",
            "zwischengespraech_4": "Zwischengespräch nach 4 Wochen (1/2h)",
            "zwischengespraech_8": "Zwischengespräch nach weiteren 8 Wochen (1/2h)",
            "lab_imd": "IMD",
            "lab_mmd": "MMD",
            "lab_nextgen": "NextGen Onco",
            "lab_sonstiges": "Sonstiges (Labordiagnostik)",
            "analyse_bewegungsapparat": "Analyse Bewegungsapparat (Martin)",
            "schwermetalltest": "Schwermetalltest mit DMSA und Ca EDTA",
            
            # Therapieformen
            "darmsanierung_ern": "Darmsanierung",
            "leberdetox_ern": "Leberdetox",
            "lowcarb": "Low Carb Ernährung",
            "proteinmenge": "Proteinmenge",
            "fasten": "Intermittierendes Fasten",
            "krebsdiaet": "Krebs Diät nach Dr. Coy/Dr. Strunz/angelehnt Budwig",
            "keto": "Ketogene Ernährung",
            "oelziehen": "Ölziehen mit Kokosöl (2x10 Min. nach dem Zähneputzen)",
            "detox_vacc": "Detox vacc Protokoll (3–12 Monate, gelb markiert)",
            "abnehmen": "Abnehmen mit Akupunktur nach Uwe Richter",
            "salz": "Gut gesalzene Kost mit Himalaya- oder Meersalz (fluoridfrei)",
            "phosphat": "Phosphatreiche Nahrungsmittel",
            "kalium": "Kaliumreiche Nahrungsmittel",
            "basisch": "Basische Ernährung",
            "fluoridfrei": "Fluoridfreies Leben (Zahnpasta, Salz etc.)",
            "wasserfilter": "Wasserfilter (Umkehrosmose oder Tischfilter, z. B. Maunaway)",
            "atem": "Atemtherapie",
            "beratung": "Ernährungsberatung",
            "ruecken": "Rückentraining (z. B. Kieser Training)",
            "cardio": "Cardio",
            "ausdauer": "Ausdauertraining",
            "trampolin": "Trampolin",
            "barre": "Barre Mobility – Bewegungsapparat in Balance (150€)"
        }
        
        # Define which keys belong to which section in Therapieplan tab
        section_keys = {
            "Diagnostik & Überprüfung": [
                "zaehne", "zaehne_zu_pruefen", "lab_imd", "lab_mmd", "lab_nextgen", 
                "lab_sonstiges", "analyse_bewegungsapparat", "schwermetalltest",
                "darm_biofilm", "darmsanierung", "darmsanierung_dauer", "hydrocolon", 
                "parasiten", "parasiten_bio", "leberdetox", "nierenprogramm", 
                "infektion_bakt", "infektion_virus", "ausleitung_inf", "ausleitung_oral"
            ],
            "Therapieformen": [
                "mikronaehrstoffe", "infusionsbehandlung", "neuraltherapie", "eigenblut",
                "aethetisch", "ozontherapie", "medikamente", "medikamente_text", 
                "timewaver_freq", "bio_isopath", "akupunktur", "homoeopathie", 
                "bioresonanz", "hypnose", "yager", "atemtherapie", "bewegung", 
                "ernaehrung", "darmsanierung_ern", "leberreinigung", "lowcarb", 
                "fasten", "krebsdiaet", "ketogene", "basisch", "naehrstoff_ausgleich",
                "therapie_sonstiges", "magenband", "energie_behandlungen",
                "zwischengespraech_4", "zwischengespraech_8"
            ]
        }
        
        # Display each section
        for section_name, keys in section_keys.items():
            pdf.set_font("Helvetica", "B", 12)
            pdf.cell(0, 8, section_name, 0, 1)
            pdf.set_font("Helvetica", "", 10)
            
            has_items_in_section = False
            
            for key in keys:
                if key in supplements:
                    value = supplements[key]
                    if value:
                        has_items_in_section = True
                        label = label_mapping.get(key, key)  # Get human-readable label
                        
                        # For boolean True values (checkboxes that are checked)
                        if isinstance(value, bool) and value:
                            pdf.cell(0, 6, f"- {clean_text(label)}", 0, 1)
                        # For string values (text inputs)
                        elif isinstance(value, str) and value.strip():
                            pdf.cell(0, 6, f"- {clean_text(label)}: {clean_text(value)}", 0, 1)
                        # For list values (multiselects)
                        elif isinstance(value, list) and value:
                            cleaned_values = [clean_text(str(v)) for v in value]
                            pdf.cell(0, 6, f"- {clean_text(label)}: {', '.join(cleaned_values)}", 0, 1)
            
            if not has_items_in_section:
                pdf.cell(0, 6, "- Keine Angaben", 0, 1)
            
            pdf.ln(3)  # Add some space between sections

    elif tab_name == "INFUSIONSTHERAPIE" and isinstance(supplements, dict):
        # For Infusionstherapie tab
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, "INFUSIONSTHERAPIE", 0, 1, "C", True)
        pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        
        # Define mapping from keys to human-readable labels for Infusionstherapie tab
        label_mapping = {
            # RevitaClinic Infusionen
            "revita_immune": "RevitaImmune",
            "revita_immune_plus": "RevitaImmunePlus",
            "revita_heal": "Revita Heal (2x)",
            "revita_bludder": "RevitaBludder",
            "revita_ferro": "RevitaFerro",
            "revita_energy": "RevitaEnergyBoost",
            "revita_focus": "RevitaFocus",
            "revita_nad": "RevitaNAD+",
            "revita_relax": "RevitaRelax",
            "revita_fit": "RevitaFit",
            "revita_hangover": "RevitaHangover",
            "revita_beauty": "RevitaBeauty",
            "revita_antiaging": "RevitaAnti-Aging",
            "revita_detox": "RevitaDetox",
            "revita_chelate": "RevitaChelate",
            "revita_liver": "RevitaLiver",
            "revita_leakygut": "RevitaLeaky-gut",
            "revita_infection": "RevitaInfection",
            "revita_joint": "RevitaJoint",
            
            # Standard Infusionen
            "mito_energy": "Mito-Energy Behandlung (Mito-Gerät, Wirkbooster)",
            "schwermetalltest": "Schwermetalltest mit DMSA und Ca EDTA",
            "procain_basen": "Procain Baseninfusion mit Magnesium",
            "procain_2percent": "Procain 2% (ml)",
            "artemisinin": "Artemisinin Infusion mit 2x Lysin",
            "perioperative": "Perioperative Infusion (3 Infusionen)",
            "detox_standard": "Detox-Infusion Standard",
            "detox_maxi": "Detox-Infusion Maxi",
            "aufbauinfusion": "Aufbauinfusion nach Detox",
            "infektions_infusion": "Infektions-Infusion / H2O2 (Anzahl / ml)",
            "immun_booster": "Immun-Boosterung Typ",
            "oxyvenierung": "Oxyvenierung (10–40 ml, 10er Serie)",
            "energetisierungsinfusion": "Energetisierungsinfusion mit",
            "naehrstoffinfusion": "Nährstoffinfusion mit",
            "anti_aging": "Anti Aging Infusion komplett",
            "nerven_aufbau": "Nerven Aufbau Infusion",
            "leberentgiftung": "Leberentgiftungsinfusion",
            "anti_oxidantien": "Anti-Oxidantien Infusion",
            "aminoinfusion": "Aminoinfusion leaky gut (5–10)",
            "relax_infusion": "Relax Infusion",
            "eisen_infusion": "Eisen Infusion (Ferinject) mg / Anzahl",
            "vitamin_c": "Hochdosis Vitamin C (g)",
            "vitamin_b_komplex": "Vit. B-Komplex",
            "vitamin_d": "Vit. D",
            "vitamin_b6_b12_folsaeure": "Vit. B6/B12/Folsäure",
            "vitamin_b3": "Vit. B3",
            "zusaetze": "Zusätze auswählen",
            "wochen_haeufigkeit": "Wie oft",
            "therapie_beginn": "Therapie Beginn",
            "therapie_ende": "Therapie Ende",
            "therapie_dauer": "Dauer (Wochen/Monate)"
        }
        
        # Define all infusion keys for a single section
        infusion_keys = [
            # RevitaClinic Infusionen
            "revita_immune", "revita_immune_plus", "revita_heal", "revita_bludder",
            "revita_ferro", "revita_energy", "revita_focus", "revita_nad",
            "revita_relax", "revita_fit", "revita_hangover", "revita_beauty",
            "revita_antiaging", "revita_detox", "revita_chelate", "revita_liver",
            "revita_leakygut", "revita_infection", "revita_joint",
            
            # Standard Infusionen
            "mito_energy", "schwermetalltest", "procain_basen", "procain_2percent",
            "artemisinin", "perioperative", "detox_standard", "detox_maxi",
            "aufbauinfusion", "infektions_infusion", "immun_booster", "oxyvenierung",
            "energetisierungsinfusion", "naehrstoffinfusion", "anti_aging",
            "nerven_aufbau", "leberentgiftung", "anti_oxidantien", "aminoinfusion",
            "relax_infusion", "eisen_infusion", "vitamin_c", "vitamin_b_komplex",
            "vitamin_d", "vitamin_b6_b12_folsaeure", "vitamin_b3",
            "wochen_haeufigkeit", "therapie_beginn", "therapie_ende", "therapie_dauer",
            "zusaetze"
        ]
        
        # Display Infusionen section
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Infusionen", 0, 1)
        pdf.set_font("Helvetica", "", 10)
        
        has_items_in_section = False
        
        for key in infusion_keys:
            if key in supplements:
                value = supplements[key]
                if value:
                    has_items_in_section = True
                    label = label_mapping.get(key, key)  # Get human-readable label
                    
                    # For boolean True values (checkboxes that are checked)
                    if isinstance(value, bool) and value:
                        pdf.cell(0, 6, f"- {clean_text(label)}", 0, 1)
                    # For string values (text inputs)
                    elif isinstance(value, str) and value.strip():
                        pdf.cell(0, 6, f"- {clean_text(label)}: {clean_text(value)}", 0, 1)
                    # For list values (multiselects)
                    elif isinstance(value, list) and value:
                        cleaned_values = [clean_text(str(v)) for v in value]
                        pdf.cell(0, 6, f"- {clean_text(label)}: {', '.join(cleaned_values)}", 0, 1)
        
        if not has_items_in_section:
            pdf.cell(0, 6, "- Keine Angaben", 0, 1)
        
        pdf.ln(3)  # Add some space

    else:
        # Fallback for unknown tab or data format
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, f"{tab_name.upper() if isinstance(tab_name, str) else 'DOKUMENT'}", 0, 1, "C", True)
        pdf.ln(5)
        
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "Keine Daten verfügbar.", 0, 1)
    
    from io import BytesIO
    # Return the PDF as bytes for Streamlit download
    return pdf.output(dest='S').encode('latin-1')

       
# --- Main app ---
def main():
    df = fetch_supplements()
    
    # CRITICAL: Check if we just loaded a patient and need to reset tab state
    if st.session_state.get('just_loaded_patient', False):
        # Force a clean rerun to ensure all tabs use fresh data
        st.session_state.just_loaded_patient = False
        # Don't rerun here - let the natural flow continue

    # --- Patient Info ---
    patient = patient_inputs()

    # Initialize override keys for each supplement in session_state
    for _, row in df.iterrows():
        override_key = f"gesamt_dosierung_override_{row['id']}"  # Updated key name
        if override_key not in st.session_state:
            st.session_state[override_key] = None

    # Initialize session state for delete confirmation
    if 'show_delete_confirmation' not in st.session_state:
        st.session_state.show_delete_confirmation = False
    
    # Initialize session state for save success message
    if 'show_save_success' not in st.session_state:
        st.session_state.show_save_success = False
    
    # Initialize session state for PDF generation
    if 'nem_pdf_bytes' not in st.session_state:
        st.session_state.nem_pdf_bytes = None
    
    # Initialize session state for auto-download
    if 'auto_download_pdf' not in st.session_state:
        st.session_state.auto_download_pdf = None

    # Save and Delete buttons at the top
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("Alle Daten speichern", use_container_width=True, type="primary", key="save_button")
    with col2:
        # Delete button - only show if patient exists in database
        patient_names_df = fetch_patient_names()
        patient_names = patient_names_df["patient_name"].tolist() if not patient_names_df.empty else []
        if patient["patient"] and patient["patient"] in patient_names:
            if st.button("Patient löschen", use_container_width=True, type="secondary"):
                st.session_state.show_delete_confirmation = True
    
    # Show save success message if set
    if st.session_state.get("show_save_success", False):
        st.markdown('<div class="success-message">✅ Alle Daten wurden erfolgreich gespeichert!</div>', unsafe_allow_html=True)
        # Clear the message after 3 seconds
        time.sleep(3)
        st.session_state.show_save_success = False
        st.rerun()
    
    # Delete confirmation dialog
    if st.session_state.get("show_delete_confirmation", False):
        st.markdown("---")
        st.warning("⚠️ **ACHTUNG: Dieser Vorgang kann nicht rückgängig gemacht werden!**")
        st.error(f"Das Löschen wird alle Daten für Patient '{patient['patient']}' unwiderruflich entfernen.")
        
        col_confirm1, col_confirm2 = st.columns(2)
        with col_confirm1:
            if st.button("Ja, endgültig löschen", use_container_width=True, key="confirm_delete"):
                if delete_patient_data(patient["patient"]):
                    st.success(f"Patient '{patient['patient']}' wurde gelöscht!")
                    # Clear session state
                    st.session_state.patient_data = {}
                    st.session_state.nem_prescriptions = []
                    st.session_state.therapieplan_data = {}
                    st.session_state.ernaehrung_data = {}
                    st.session_state.infusion_data = {}
                    st.session_state.last_loaded_patient = None
                    st.session_state.show_delete_confirmation = False
                    time.sleep(2)
                    st.rerun()
                else:
                    st.error("Fehler beim Löschen des Patienten!")
        with col_confirm2:
            if st.button("Abbrechen", use_container_width=True, key="cancel_delete"):
                st.session_state.show_delete_confirmation = False
                st.info("Löschen abgebrochen")
                st.rerun()

    # --- Tabs ---
    st.markdown("---")
    tabs = st.tabs([
        "Therapieplan",
        "Nahrungsergänzungsmittel (NEM)",
        "Infusionstherapie"
    ])

    # Initialize selected list for NEM prescriptions
    selected = []
    therapieplan_data = {}
    ernaehrung_data = {}
    infusion_data = {}

    with tabs[0]:  # Therapieplan Tab
            # SECTION 1: Diagnostik & Überprüfung (FIRST)
            st.markdown('<div class="green-section-header">Diagnostik & Überprüfung</div>', unsafe_allow_html=True)
            
            # Sub-section: Zähne - in one row (2 columns)
            st.markdown('<div class="section-subheader">Zähne</div>', unsafe_allow_html=True)
            col1, col2 = st.columns(2)
            with col1:
                zaehne = st.checkbox("Überprüfung der Zähne/Kieferknochen mittels OPG (Panoramaaufnahme mit lachendem Gebiss) / DVT", 
                                    value=st.session_state.therapieplan_data.get("zaehne", False),
                                    key="zaehne_checkbox")
            with col2:
                zaehne_zu_pruefen = st.text_input("Zähne zu überprüfen (OPG/DVT):", 
                                                value=st.session_state.therapieplan_data.get("zaehne_zu_pruefen", ""),
                                                key="zaehne_zu_pruefen_input")
            
            st.markdown("---")
            
            # Sub-section: Bewegungsapparat & Schwermetalle
            st.markdown('<div class="section-subheader">Bewegungsapparat & Schwermetalle</div>', unsafe_allow_html=True)
            
            analyse_bewegungsapparat = st.checkbox("Analyse Bewegungsapparat (Martin)", 
                                                value=st.session_state.therapieplan_data.get("analyse_bewegungsapparat", False),
                                                key="analyse_bewegungsapparat_checkbox")
            
            schwermetalltest = st.checkbox("Schwermetalltest mit DMSA und Ca EDTA", 
                                        value=st.session_state.therapieplan_data.get("schwermetalltest", False),
                                        key="schwermetalltest_checkbox")
            
            st.markdown("---")
            
            # Sub-section: Labor & Diagnostik
            st.markdown('<div class="section-subheader">Labor & Diagnostik</div>', unsafe_allow_html=True)
            
            lab_imd = st.text_input("IMD:", value=st.session_state.therapieplan_data.get("lab_imd", ""), key="lab_imd_input")
            lab_mmd = st.text_input("MMD:", value=st.session_state.therapieplan_data.get("lab_mmd", ""), key="lab_mmd_input")
            lab_nextgen = st.text_input("NextGen Onco:", value=st.session_state.therapieplan_data.get("lab_nextgen", ""), key="lab_nextgen_input")
            lab_sonstiges = st.text_input("Sonstiges:", value=st.session_state.therapieplan_data.get("lab_sonstiges", ""), key="lab_sonstiges_input")
            
            st.markdown("---")
            
            # SECTION 2: Therapieformen
            st.markdown('<div class="green-section-header">Therapieformen</div>', unsafe_allow_html=True)
            
            # SECTION 3: Darm & Entgiftung
            st.markdown('<div class="section-subheader">Darm & Entgiftung</div>', unsafe_allow_html=True)
            
            darm_biofilm = st.checkbox("Darm - Biofilmentfernung nach www.regenbogenkreis.de (Express-Darmkur 4 Tageskur)", 
                                    value=st.session_state.therapieplan_data.get("darm_biofilm", False),
                                    key="darm_biofilm_checkbox")
            
            darmsanierung = st.checkbox("Darmsanierung nach Paracelsus Klinik (Rezept von Praxis)", 
                                    value=st.session_state.therapieplan_data.get("darmsanierung", False),
                                    key="darmsanierung_checkbox")
            
            darmsanierung_dauer = st.multiselect("Darmsanierung Dauer:", ["4 Wo", "6 Wo", "8 Wo"], 
                                            default=st.session_state.therapieplan_data.get("darmsanierung_dauer", []),
                                            key="darmsanierung_dauer_select")
            
            hydrocolon = st.checkbox("mit Hydrocolon (Darmspülung) 2x insgesamt, Abstand 14 Tage mit Rekolonisierungs-Shot", 
                                    value=st.session_state.therapieplan_data.get("hydrocolon", False),
                                    key="hydrocolon_checkbox")
            
            parasiten = st.checkbox("Parasitenbehandlung mit Vermox (3 Tage)", 
                                value=st.session_state.therapieplan_data.get("parasiten", False),
                                key="parasiten_checkbox")
            
            parasiten_bio = st.checkbox("Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)", 
                                    value=st.session_state.therapieplan_data.get("parasiten_bio", False),
                                    key="parasiten_bio_checkbox")
            
            leberdetox = st.checkbox("Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5x alle 4–6 Wochen)", 
                                value=st.session_state.therapieplan_data.get("leberdetox", False),
                                key="leberdetox_checkbox")
            
            nierenprogramm = st.checkbox("Nierenprogramm nach Dr. Clark – 4 Wochen – bitte bei www.drclarkcenter.de beziehen", 
                                        value=st.session_state.therapieplan_data.get("nierenprogramm", False),
                                        key="nierenprogramm_checkbox")
            
            st.markdown("---")

            # Sub-section: Haupttherapien
            st.markdown('<div class="section-subheader">Haupttherapien</div>', unsafe_allow_html=True)
            
            mikronaehrstoffe = st.checkbox("Einnahme Mikronährstoffen (NEM-Verordnung) (siehe separate PDF)", 
                                        value=st.session_state.therapieplan_data.get("mikronaehrstoffe", False),
                                        key="mikronaehrstoffe_checkbox")
            
            infusionsbehandlung = st.checkbox("Infusionstherapie (siehe separate PDF)", 
                                            value=st.session_state.therapieplan_data.get("infusionsbehandlung", False),
                                            key="infusionsbehandlung_checkbox")
            
            neuraltherapie = st.checkbox("Neuraltherapie", 
                                        value=st.session_state.therapieplan_data.get("neuraltherapie", False),
                                        key="neuraltherapie_checkbox")
            
            eigenblut = st.checkbox("Eigenbluttherapie", 
                                    value=st.session_state.therapieplan_data.get("eigenblut", False),
                                    key="eigenblut_checkbox")
            
            aethetisch = st.checkbox("Ästhetische Behandlung (Botox/PRP/Fäden/Hyaloron)", 
                                    value=st.session_state.therapieplan_data.get("aethetisch", False),
                                    key="aethetisch_checkbox")
            
            ozontherapie = st.checkbox("Ozontherapie", 
                                        value=st.session_state.therapieplan_data.get("ozontherapie", False),
                                        key="ozontherapie_checkbox")
            
            medikamente = st.checkbox("Medikamentenverordnung - Rezept für:", 
                                    value=st.session_state.therapieplan_data.get("medikamente", False),
                                    key="medikamente_checkbox")
            
            # Text input for medikamente (shown after checkbox)
            if medikamente:
                medikamente_text = st.text_input("Rezept Details:", 
                                                value=st.session_state.therapieplan_data.get("medikamente_text", ""),
                                                key="medikamente_text_input")
            else:
                medikamente_text = ""
            
            timewaver_freq = st.checkbox("TimeWaver Frequency Behandlung", 
                                        value=st.session_state.therapieplan_data.get("timewaver_freq", False),
                                        key="timewaver_freq_checkbox")
            
            st.markdown("---")
            
            # Sub-section: Biologische & Komplementäre Therapien
            st.markdown('<div class="section-subheader">Biologische & Komplementäre Therapien</div>', unsafe_allow_html=True)
            
            bio_isopath = st.checkbox("Biologische Isopathische Therapie", 
                                    value=st.session_state.therapieplan_data.get("bio_isopath", False),
                                    key="bio_isopath_checkbox")
            
            akupunktur = st.checkbox("Akupunktur", 
                                    value=st.session_state.therapieplan_data.get("akupunktur", False),
                                    key="akupunktur_checkbox")
            
            homoeopathie = st.checkbox("Homöopathie (Anna)", 
                                    value=st.session_state.therapieplan_data.get("homoeopathie", False),
                                    key="homoeopathie_checkbox")
            
            bioresonanz = st.checkbox("Bioresonanz (Anna)", 
                                    value=st.session_state.therapieplan_data.get("bioresonanz", False),
                                    key="bioresonanz_checkbox")
            
            hypnose = st.checkbox("Hypnosetherapie (Noreen Martin Miro)", 
                                value=st.session_state.therapieplan_data.get("hypnose", False),
                                key="hypnose_checkbox")
            
            yager = st.checkbox("Yagertherapie", 
                                value=st.session_state.therapieplan_data.get("yager", False),
                                key="yager_checkbox")
            
            st.markdown("---")
            
            # Sub-section: Weitere Maßnahmen
            st.markdown('<div class="section-subheader">Weitere Maßnahmen</div>', unsafe_allow_html=True)
            
            atemtherapie = st.checkbox("Atemtherapie", 
                                    value=st.session_state.therapieplan_data.get("atemtherapie", False),
                                    key="atemtherapie_checkbox")
            
            bewegung = st.checkbox("Bewegung", 
                                value=st.session_state.therapieplan_data.get("bewegung", False),
                                key="bewegung_checkbox")
            
            ernaehrung = st.checkbox("Ernährungsberatung", 
                                    value=st.session_state.therapieplan_data.get("ernaehrung", False),
                                    key="ernaehrung_checkbox")
            
            darmsanierung_ern = st.checkbox("Darmsanierung", 
                                        value=st.session_state.therapieplan_data.get("darmsanierung_ern", False),
                                        key="darmsanierung_ern_checkbox")
            
            leberreinigung = st.checkbox("Leberreinigung", 
                                        value=st.session_state.therapieplan_data.get("leberreinigung", False),
                                        key="leberreinigung_checkbox")
            
            lowcarb = st.checkbox("Low Carb Ernährung", 
                                value=st.session_state.therapieplan_data.get("lowcarb", False),
                                key="lowcarb_checkbox")
            
            fasten = st.checkbox("Intermittierendes Fasten", 
                                value=st.session_state.therapieplan_data.get("fasten", False),
                                key="fasten_checkbox")
            
            krebsdiaet = st.checkbox("Krebs Diät nach Dr. Coy/Dr. Strunz/angelehnt Budwig", 
                                    value=st.session_state.therapieplan_data.get("krebsdiaet", False),
                                    key="krebsdiaet_checkbox")
            
            ketogene = st.checkbox("Ketogene Ernährung", 
                                value=st.session_state.therapieplan_data.get("ketogene", False),
                                key="ketogene_checkbox")
            
            basisch = st.checkbox("Basische Ernährung", 
                                value=st.session_state.therapieplan_data.get("basisch", False),
                                key="basisch_checkbox")
            
            # Text inputs for Weitere Maßnahmen
            naehrstoff_ausgleich = st.text_input("Nährstoffmängel ausgleichen:", 
                                                value=st.session_state.therapieplan_data.get("naehrstoff_ausgleich", ""),
                                                key="naehrstoff_ausgleich_input")
            
            therapie_sonstiges = st.text_input("Sonstiges:", 
                                            value=st.session_state.therapieplan_data.get("therapie_sonstiges", ""),
                                            key="therapie_sonstiges_input")
            
            st.markdown("---")
            
            # Sub-section: Individuelle Behandlungen
            st.markdown('<div class="section-subheader">Individuelle Behandlungen</div>', unsafe_allow_html=True)
            
            magenband = st.checkbox("Magenband", 
                                value=st.session_state.therapieplan_data.get("magenband", False),
                                key="magenband_checkbox")
            
            energie_behandlungen = st.checkbox("Energiebehandlungen bei Marie", 
                                            value=st.session_state.therapieplan_data.get("energie_behandlungen", False),
                                            key="energie_behandlungen_checkbox")
            
            st.markdown("---")
            
            # Sub-section: Gesprächstermine
            st.markdown('<div class="section-subheader">Gesprächstermine</div>', unsafe_allow_html=True)
            
            zwischengespraech_4 = st.checkbox("Zwischengespräch nach 4 Wochen (1/2h)", 
                                            value=st.session_state.therapieplan_data.get("zwischengespraech_4", False),
                                            key="zwischengespraech_4_checkbox")
            
            zwischengespraech_8 = st.checkbox("Zwischengespräch nach weiteren 8 Wochen (1/2h)", 
                                            value=st.session_state.therapieplan_data.get("zwischengespraech_8", False),
                                            key="zwischengespraech_8_checkbox")
            
            st.markdown("---")
            
            # SECTION 4: Infektionen & Ausleitung
            st.markdown('<div class="green-section-header">Infektionen & Ausleitung</div>', unsafe_allow_html=True)

            # Ausleitung checkboxes first
            st.markdown('<div class="section-subheader">Ausleitung</div>', unsafe_allow_html=True)

            ausleitung_inf = st.checkbox("Schwermetallausleitung Infusion", 
                                        value=st.session_state.therapieplan_data.get("ausleitung_inf", False),
                                        key="ausleitung_inf_checkbox")

            ausleitung_oral = st.checkbox("Schwermetallausleitung oral", 
                                        value=st.session_state.therapieplan_data.get("ausleitung_oral", False),
                                        key="ausleitung_oral_checkbox")

            st.markdown("---")

            # Infektionen text fields (after Ausleitung)
            st.markdown('<div class="section-subheader">Infektionen</div>', unsafe_allow_html=True)

            col1, col2 = st.columns(2)
            with col1:
                infektion_bakt = st.text_input("Infektionsbehandlung für Bakterien (Borr./Helicob.):", 
                                            value=st.session_state.therapieplan_data.get("infektion_bakt", ""),
                                            key="infektion_bakt_input")
            with col2:
                infektion_virus = st.text_input("Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona):", 
                                            value=st.session_state.therapieplan_data.get("infektion_virus", ""),
                                            key="infektion_virus_input")
        
            # Update session state for Therapieplan with all current values
            st.session_state.therapieplan_data = {
                # Diagnostik & Überprüfung
                "zaehne": zaehne,
                "zaehne_zu_pruefen": zaehne_zu_pruefen,
                "analyse_bewegungsapparat": analyse_bewegungsapparat,
                "schwermetalltest": schwermetalltest,
                "lab_imd": lab_imd,
                "lab_mmd": lab_mmd,
                "lab_nextgen": lab_nextgen,
                "lab_sonstiges": lab_sonstiges,
                
                # Therapieformen
                "mikronaehrstoffe": mikronaehrstoffe,
                "infusionsbehandlung": infusionsbehandlung,
                "neuraltherapie": neuraltherapie,
                "eigenblut": eigenblut,
                "aethetisch": aethetisch,
                "ozontherapie": ozontherapie,
                "medikamente": medikamente,
                "medikamente_text": medikamente_text,
                "timewaver_freq": timewaver_freq,
                "bio_isopath": bio_isopath,
                "akupunktur": akupunktur,
                "homoeopathie": homoeopathie,
                "bioresonanz": bioresonanz,
                "hypnose": hypnose,
                "yager": yager,
                "atemtherapie": atemtherapie,
                "bewegung": bewegung,
                "ernaehrung": ernaehrung,
                "darmsanierung_ern": darmsanierung_ern,
                "leberreinigung": leberreinigung,
                "lowcarb": lowcarb,
                "fasten": fasten,
                "krebsdiaet": krebsdiaet,
                "ketogene": ketogene,
                "basisch": basisch,
                "naehrstoff_ausgleich": naehrstoff_ausgleich,
                "therapie_sonstiges": therapie_sonstiges,
                "magenband": magenband,
                "energie_behandlungen": energie_behandlungen,
                "zwischengespraech_4": zwischengespraech_4,
                "zwischengespraech_8": zwischengespraech_8,
                
                # Darm & Entgiftung
                "darm_biofilm": darm_biofilm,
                "darmsanierung": darmsanierung,
                "darmsanierung_dauer": darmsanierung_dauer,
                "hydrocolon": hydrocolon,
                "parasiten": parasiten,
                "parasiten_bio": parasiten_bio,
                "leberdetox": leberdetox,
                "nierenprogramm": nierenprogramm,
                
                # Infektionen & Ausleitung
                "infektion_bakt": infektion_bakt,
                "infektion_virus": infektion_virus,
                "ausleitung_inf": ausleitung_inf,
                "ausleitung_oral": ausleitung_oral,
            }

            # PDF button for Therapieplan
            if st.button("Therapieplan PDF generieren", key="therapieplan_pdf_button"):
                pdf_bytes = generate_pdf(patient, st.session_state.therapieplan_data, "THERAPIEPLAN")
                filename = f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf"
                
                # Set auto-download
                st.session_state.auto_download_pdf = {
                    "data": pdf_bytes,
                    "filename": filename,
                    "mime": "application/pdf"
                }
                st.rerun()

    with tabs[1]:
        # Store NEM prescriptions in a container
        nem_container = st.container()
        
        with nem_container:
            # Initialize form data
            if 'nem_form_initialized' not in st.session_state:
                st.session_state.nem_form_initialized = True
            
            # Initialize expanded state for categories
            if 'category_states' not in st.session_state:
                st.session_state.category_states = {}
            
            # Use a form for better data handling
            with st.form("nem_form", clear_on_submit=False):
                if "last_main_dauer" not in st.session_state:
                    st.session_state.last_main_dauer = patient["dauer"]

                # Define dosage options based on Darreichungsform
                def get_pro_Einnahme_options(darreichungsform):
                    """Return appropriate Pro Einnahme options based on Darreichungsform"""
                    if not darreichungsform:
                        return [""]
                    
                    darreichungsform = darreichungsform.lower()
                    
                    # Count-based options for discrete forms
                    if any(form in darreichungsform for form in ["kapsel", "tablette", "pflaster"]):
                        return ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", 
                            "½", "¼", "¾", "1½", "2½"]
                    
                    # Volume-based options for liquids
                    elif any(form in darreichungsform for form in ["tropfen", "lösung", "flüssig", "öl", "spray", "creme", "gel"]):
                        return ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                            "½", "¼", "¾", "1½", "2½", "Tr", "ML"]
                    
                    # Weight-based options for powders
                    elif any(form in darreichungsform for form in ["pulver", "sachet"]):
                        return ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                            "½", "¼", "¾", "1½", "2½", "g", "mg", "EL", "TL", "ML"]
                    
                    # Tea-specific options
                    elif "tee" in darreichungsform:
                        return ["", "1", "2", "3", "4", "5", "Beutel", "TL", "EL"]
                    
                    # Default options
                    return ["", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10",
                        "½", "¼", "¾", "1½", "2½", "g", "mg", "EL", "TL", "ML", "Tr"]

                # -------- STICKY HEADER ROW --------
                st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
                header_cols = st.columns([2.3, 0.8, 1.2, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 2])
                headers = ["Supplement", "Gesamt-dosierung", "Darreichungsform", "Pro Einnahme",
                        "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]

                for col, text in zip(header_cols, headers):
                    col.markdown(f"**{text}**")
                st.markdown('</div>', unsafe_allow_html=True)

                # -------- SCROLLABLE CONTAINER for categories and supplements --------
                # Using Streamlit's native container with height parameter
                scroll_container = st.container(height=600, border=True)

                with scroll_container:
                    # Create lists for different purposes
                    all_supplements_data = []  # For saving - includes ALL supplements
                    
                    # Get all categories and their supplements
                    categories = {}
                    current_category_id = None
                    current_category_name = None
                    
                    # Group by category
                    for _, row in df.iterrows():
                        if row["id"].startswith("CAT"):
                            # This is a category row
                            current_category_id = row["category"]
                            current_category_name = row["name"].replace("CATEGORY: ", "")
                            categories[current_category_name] = []
                        elif current_category_name:
                            # This is a supplement in the current category
                            categories[current_category_name].append(row)
                    
                    # Now display categories in order with expanders
                    for category_name, supplement_rows in categories.items():
                        # Skip empty categories
                        if not supplement_rows:
                            continue
                        
                        # Create expander for each category
                        # Initialize category state if not exists
                        if category_name not in st.session_state.category_states:
                            st.session_state.category_states[category_name] = False
                        
                        # Display category as expander
                        with st.expander(f" {category_name}", 
                                        expanded=st.session_state.category_states[category_name]):
                            
                            # Display all supplements in this category
                            for row in supplement_rows:
                                cols = st.columns([2.2, 0.9, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])

                                # Supplement name
                                supplement_name = row["name"]
                                cols[0].markdown(supplement_name)

                                # Check if we have loaded prescriptions for this supplement
                                loaded_prescription = None
                                if st.session_state.nem_prescriptions:
                                    for prescription in st.session_state.nem_prescriptions:
                                        if prescription.get("name") == supplement_name:
                                            loaded_prescription = prescription
                                            break

                                # Determine initial values
                                if loaded_prescription:
                                    initial_gesamt_dosierung = loaded_prescription.get("Gesamt-dosierung", "")
                                    initial_form = loaded_prescription.get("Darreichungsform", "")
                                    initial_pro_Einnahme = loaded_prescription.get("Pro Einnahme", "")
                                    initial_nue = loaded_prescription.get("Nüchtern", "")
                                    initial_morg = loaded_prescription.get("Morgens", "")
                                    initial_mitt = loaded_prescription.get("Mittags", "")
                                    initial_abend = loaded_prescription.get("Abends", "")
                                    initial_nacht = loaded_prescription.get("Nachts", "")
                                    initial_comment = loaded_prescription.get("Kommentar", "")
                                else:
                                    initial_gesamt_dosierung = ""
                                    initial_form = DEFAULT_FORMS.get(supplement_name, "Kapseln")
                                    initial_pro_Einnahme = ""
                                    initial_nue = ""
                                    initial_morg = ""
                                    initial_mitt = ""
                                    initial_abend = ""
                                    initial_nacht = ""
                                    initial_comment = ""

                                # Create unique keys for each widget
                                gesamt_dosierung_key = f"{row['id']}_gesamt_dosierung"
                                form_key = f"{row['id']}_darreichungsform"
                                pro_Einnahme_key = f"{row['id']}_pro_Einnahme"
                                nue_key = f"{row['id']}_Nuechtern"
                                morg_key = f"{row['id']}_Morgens"
                                mitt_key = f"{row['id']}_Mittags"
                                abend_key = f"{row['id']}_Abends"
                                nacht_key = f"{row['id']}_Nachts"
                                comment_key = f"{row['id']}_comment"

                                # -------- GESAMT-DOSIERUNG (editable selectbox) --------
                                gesamt_dosierung_options = [
                                    "", "1","2","3","4","5","6","7","8","9","10",
                                    "12","14","16","18","20","22","24","26","28","30",
                                    "35","40","45","50","60","70","80","90","100",
                                    "120","150","180","200","250","300","400","500"
                                ]

                                gesamt_dosierung_val = cols[1].selectbox(
                                    "",
                                    gesamt_dosierung_options,
                                    index=gesamt_dosierung_options.index(initial_gesamt_dosierung)
                                        if initial_gesamt_dosierung in gesamt_dosierung_options else 0,
                                    key=gesamt_dosierung_key,
                                    label_visibility="collapsed",
                                    accept_new_options=True
                                )

                                # -------- DARREICHUNGSFORM (editable selectbox) --------
                                dosage_presets = [
                                    "Kapseln","Lösung","Tabletten","Pulver","Tropfen",
                                    "Sachet","Öl","Spray","Creme","Gel","Flüssig",
                                    "Tee","Pflaster"
                                ]

                                selected_form = cols[2].selectbox(
                                    "",
                                    dosage_presets,
                                    index=dosage_presets.index(initial_form)
                                        if initial_form in dosage_presets else 0,
                                    key=form_key,
                                    label_visibility="collapsed",
                                    accept_new_options=True
                                )

                                # -------- PRO Einnahme (editable selectbox) --------
                                pro_Einnahme_options = get_pro_Einnahme_options(selected_form)

                                pro_Einnahme_val = cols[3].selectbox(
                                    "",
                                    pro_Einnahme_options,
                                    index=pro_Einnahme_options.index(initial_pro_Einnahme)
                                        if initial_pro_Einnahme in pro_Einnahme_options else 0,
                                    key=pro_Einnahme_key,
                                    label_visibility="collapsed",
                                    accept_new_options=True
                                )

                                # -------- INTAKE TIMES --------
                                dose_options = ["", "1", "2", "3", "4", "5"]
                                
                                nue_val = cols[4].selectbox("", dose_options, 
                                                        index=dose_options.index(initial_nue) if initial_nue in dose_options else 0,
                                                        key=nue_key, label_visibility="collapsed")
                                morg_val = cols[5].selectbox("", dose_options,
                                                        index=dose_options.index(initial_morg) if initial_morg in dose_options else 0,
                                                        key=morg_key, label_visibility="collapsed")
                                mitt_val = cols[6].selectbox("", dose_options,
                                                        index=dose_options.index(initial_mitt) if initial_mitt in dose_options else 0,
                                                        key=mitt_key, label_visibility="collapsed")
                                abend_val = cols[7].selectbox("", dose_options,
                                                            index=dose_options.index(initial_abend) if initial_abend in dose_options else 0,
                                                            key=abend_key, label_visibility="collapsed")
                                nacht_val = cols[8].selectbox("", dose_options,
                                                            index=dose_options.index(initial_nacht) if initial_nacht in dose_options else 0,
                                                            key=nacht_key, label_visibility="collapsed")

                                # -------- COMMENT --------
                                comment = cols[9].text_input(
                                    "", key=comment_key, placeholder="Kommentar",
                                    value=initial_comment or "", label_visibility="collapsed"
                                )
                                
                                # Create prescription data for this supplement
                                prescription_data = {
                                    "name": supplement_name,
                                    "Gesamt-dosierung": gesamt_dosierung_val,
                                    "Darreichungsform": selected_form,
                                    "Pro Einnahme": pro_Einnahme_val,
                                    "Nüchtern": nue_val,
                                    "Morgens": morg_val,
                                    "Mittags": mitt_val,
                                    "Abends": abend_val,
                                    "Nachts": nacht_val,
                                    "Kommentar": comment
                                }
                                
                                # ALWAYS add to all_supplements_data for saving
                                all_supplements_data.append(prescription_data)

                # Form submit buttons
                pdf_submitted = st.form_submit_button("NEM PDF generieren", key="nem_pdf_button")

            # Handle form submissions OUTSIDE the form context
            if pdf_submitted:
                # Update session state with ALL data for saving
                st.session_state.nem_prescriptions = all_supplements_data
                
                # Filter supplements for PDF - only include supplements with actual prescription data
                pdf_supplements_data = []
                for prescription in all_supplements_data:
                    # Check if there's any actual prescription data
                    has_prescription_data = False
                    
                    # Check intake times
                    intake_fields = ["Nüchtern", "Morgens", "Mittags", "Abends", "Nachts"]
                    for field in intake_fields:
                        if prescription.get(field, "").strip():
                            has_prescription_data = True
                            break
                    
                    # If no intake times, check other prescription fields
                    if not has_prescription_data:
                        # Check Gesamt-dosierung
                        if prescription.get("Gesamt-dosierung", "").strip():
                            has_prescription_data = True
                        # Check Pro Einnahme
                        elif prescription.get("Pro Einnahme", "").strip():
                            has_prescription_data = True
                        # Check comment
                        elif prescription.get("Kommentar", "").strip():
                            has_prescription_data = True
                        # Check if form is different from default
                        elif prescription.get("Darreichungsform", "").strip() and prescription["Darreichungsform"] != DEFAULT_FORMS.get(prescription["name"], "Kapseln"):
                            has_prescription_data = True
                    
                    if has_prescription_data:
                        pdf_supplements_data.append(prescription)
                
                # Only generate PDF if there are actual prescriptions
                if pdf_supplements_data:
                    # Generate PDF and trigger auto-download
                    pdf_bytes = generate_pdf(patient, pdf_supplements_data, "NEM")
                    filename = f"RevitaClinic_NEM_{patient.get('patient','')}.pdf"
                    
                    # Set auto-download in session state
                    st.session_state.auto_download_pdf = {
                        "data": pdf_bytes,
                        "filename": filename,
                        "mime": "application/pdf"
                    }
                    
                    # Show success message
                    st.success(f"✅ PDF mit {len(pdf_supplements_data)} NEM-Supplement(en) generiert!")
                    
                    # Force rerun to trigger download
                    st.rerun()
                else:
                    st.warning("⚠️ Keine NEM-Supplemente ausgewählt. Bitte mindestens ein Supplement mit Dosierung oder Einnahmezeiten ausfüllen.")
         
    with tabs[2]:  # Infusionstherapie Tab
        # Section: Infusionstherapie
        st.markdown('<div class="green-section-header">Infusionstherapie</div>', unsafe_allow_html=True)
        
        # Header row for the 3-column layout
        header_cols = st.columns([2, 1, 1])
        with header_cols[0]:
            st.markdown('<p class="infusion-header">Infusion</p>', unsafe_allow_html=True)
        with header_cols[1]:
            st.markdown('<p class="infusion-header">Anzahl Wochen</p>', unsafe_allow_html=True)
        with header_cols[2]:
            st.markdown('<p class="infusion-header">Häufigkeit/Woche</p>', unsafe_allow_html=True)
        
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: rgb(38, 96, 65); border-width: 2px;'>", unsafe_allow_html=True)
        
        # Helper function to create infusion row with perfect alignment
        def infusion_row(label, key_prefix, tooltip, default_checked=False, default_weeks="", default_freq=""):
            checkbox_key = f"inf_{key_prefix}_cb"
            weeks_key = f"inf_{key_prefix}_weeks"
            freq_key = f"inf_{key_prefix}_freq"

            cols = st.columns([2, 1, 1])

            with cols[0]:
                row = st.columns([0.08, 0.92])

                with row[0]:
                    value = st.checkbox(
                        "",
                        value=st.session_state.infusion_data.get(key_prefix, default_checked),
                        key=checkbox_key,
                        label_visibility="collapsed"
                    )

                with row[1]:
                    st.markdown(
                        f"""
                        <div style="
                            display:flex;
                            align-items:center;
                            gap:4px;
                            margin-top:8px;
                        ">
                            <span style="font-size:15px; line-height:1;">{label}</span>
                            <span class="info-icon" data-tooltip="{tooltip}" style="margin-left:2px;">ⓘ</span>
                        </div>
                        """,
                        unsafe_allow_html=True
                    )

            with cols[1]:
                weeks_options = ["", "1 Woche", "2 Wochen", "3 Wochen", "4 Wochen", "6 Wochen", "8 Wochen", "12 Wochen"]
                weeks_value = st.selectbox(
                    "",
                    weeks_options,
                    index=weeks_options.index(st.session_state.infusion_data.get(weeks_key, default_weeks))
                    if st.session_state.infusion_data.get(weeks_key, default_weeks) in weeks_options else 0,
                    key=weeks_key,
                    label_visibility="collapsed",
                    placeholder="Wochen"
                )

            with cols[2]:
                freq_options = ["", "1x/Woche", "2x/Woche", "3x/Woche", "4x/Woche", "5x/Woche", "6x/Woche", "7x/Woche (täglich)"]
                freq_value = st.selectbox(
                    "",
                    freq_options,
                    index=freq_options.index(st.session_state.infusion_data.get(freq_key, default_freq))
                    if st.session_state.infusion_data.get(freq_key, default_freq) in freq_options else 0,
                    key=freq_key,
                    label_visibility="collapsed",
                    placeholder="Häufigkeit"
                )

            return value, weeks_value, freq_value

        # Special function for Procain row with additional text field
        def procain_row(label, key_prefix, tooltip, default_checked=False, default_weeks="", default_freq="", default_procain=""):
            checkbox_key = f"inf_{key_prefix}_cb"
            weeks_key = f"inf_{key_prefix}_weeks"
            freq_key = f"inf_{key_prefix}_freq"
            procain_key = f"inf_{key_prefix}_procain"
            
            if "infusion_data" not in st.session_state:
                st.session_state.infusion_data = {}

            current_procain = st.session_state.infusion_data.get(procain_key, default_procain)
            
            cols = st.columns([2, 1, 1])
            
            with cols[0]:
                cb_col, label_col = st.columns([0.1, 0.9])
                
                with cb_col:
                    value = st.checkbox(
                        " ",
                        value=st.session_state.infusion_data.get(key_prefix, default_checked),
                        key=checkbox_key,
                        label_visibility="collapsed"
                    )
                
                with label_col:
                    input_id = f"procain_input_{key_prefix}"
                    # Keep original tooltip span
                    st.markdown(f'''
                    <div style="display: flex; align-items: center; gap: 6px;">
                        <span style="font-size: 15px; white-space: nowrap;">{label}</span>
                        <span class="info-icon" data-tooltip="{tooltip}">ⓘ</span>
                        <input id="{input_id}" type="text" placeholder="ml" value="{current_procain}" 
                            style="width: 50px; padding: 2px 6px; font-size: 14px; border-radius: 4px; border:1px solid #ccc;">
                    </div>
                    <script>
                    const htmlInput = document.getElementById('{input_id}');
                    htmlInput.addEventListener('input', function(e) {{
                        // Update session state directly
                        const data = window.parent.document.querySelectorAll('[data-testid="stTextInput"]');
                        for (let input of data) {{
                            if (input.value === input.defaultValue) {{
                                input.value = e.target.value;
                                input.dispatchEvent(new Event('input', {{ bubbles: true }}));
                                break;
                            }}
                        }}
                    }});
                    </script>
                    ''', unsafe_allow_html=True)
            
            with cols[1]:
                weeks_options = ["", "1 Woche", "2 Wochen", "3 Wochen", "4 Wochen", "6 Wochen", "8 Wochen", "12 Wochen"]
                weeks_value = st.selectbox(
                    " ",
                    weeks_options,
                    index=weeks_options.index(st.session_state.infusion_data.get(weeks_key, default_weeks)) 
                        if st.session_state.infusion_data.get(weeks_key, default_weeks) in weeks_options else 0,
                    key=weeks_key,
                    label_visibility="collapsed",
                    placeholder="Wochen"
                )
            
            with cols[2]:
                freq_options = ["", "1x/Woche", "2x/Woche", "3x/Woche", "4x/Woche", "5x/Woche", "6x/Woche", "7x/Woche (täglich)"]
                freq_value = st.selectbox(
                    " ",
                    freq_options,
                    index=freq_options.index(st.session_state.infusion_data.get(freq_key, default_freq)) 
                        if st.session_state.infusion_data.get(freq_key, default_freq) in freq_options else 0,
                    key=freq_key,
                    label_visibility="collapsed",
                    placeholder="Häufigkeit"
                )
            
            return value, weeks_value, freq_value, current_procain
        
        # Sub-section: RevitaClinic Infusionen
        st.markdown('<div class="section-subheader">RevitaClinic Infusionen</div>', unsafe_allow_html=True)
        
        # All RevitaClinic infusions
        revita_immune, revita_immune_weeks, revita_immune_freq = infusion_row(
            "RevitaImmune", 
            "revita_immune",
            "Vitamin C, Zink, Selen, Magnesium, B-Vitamine"
        )
        
        revita_immune_plus, revita_immune_plus_weeks, revita_immune_plus_freq = infusion_row(
            "RevitaImmunePlus", 
            "revita_immune_plus",
            "Hochdosiert: Vitamin C, Zink, Selen, Magnesium, B-Vitamine, Glutathion"
        )
        
        revita_heal, revita_heal_weeks, revita_heal_freq = infusion_row(
            "Revita Heal (2x)", 
            "revita_heal",
            "Vitamin C, Zink, Arginin, Glutamin, B-Vitamine, Magnesium"
        )
        
        revita_bludder, revita_bludder_weeks, revita_bludder_freq = infusion_row(
            "RevitaBludder", 
            "revita_bludder",
            "Eisen, Vitamin B12, Folsäure, Vitamin C"
        )
        
        revita_ferro, revita_ferro_weeks, revita_ferro_freq = infusion_row(
            "RevitaFerro", 
            "revita_ferro",
            "Ferinject (Eisen), Vitamin C"
        )
        
        revita_energy, revita_energy_weeks, revita_energy_freq = infusion_row(
            "RevitaEnergyBoost", 
            "revita_energy",
            "Magnesium, B-Vitamine, Vitamin C, Coenzym Q10"
        )
        
        revita_focus, revita_focus_weeks, revita_focus_freq = infusion_row(
            "RevitaFocus", 
            "revita_focus",
            "Magnesium, B-Vitamine, Vitamin C, Zink, Alpha-Liponsäure"
        )
        
        revita_nad, revita_nad_weeks, revita_nad_freq = infusion_row(
            "RevitaNAD+", 
            "revita_nad",
            "NAD+ 500mg (oder 125mg), Magnesium, B-Vitamine"
        )
        
        revita_relax, revita_relax_weeks, revita_relax_freq = infusion_row(
            "RevitaRelax", 
            "revita_relax",
            "Magnesium, B-Vitamine, Vitamin C, Calcium"
        )
        
        revita_fit, revita_fit_weeks, revita_fit_freq = infusion_row(
            "RevitaFit", 
            "revita_fit",
            "Magnesium, B-Vitamine, Vitamin C, Aminosäuren, Coenzym Q10"
        )
        
        revita_hangover, revita_hangover_weeks, revita_hangover_freq = infusion_row(
            "RevitaHangover", 
            "revita_hangover",
            "Elektrolyte, Vitamin C, B-Vitamine, Magnesium, Glutathion"
        )
        
        revita_beauty, revita_beauty_weeks, revita_beauty_freq = infusion_row(
            "RevitaBeauty", 
            "revita_beauty",
            "Vitamin C, Biotin, Zink, Selen, B-Vitamine"
        )
        
        revita_antiaging, revita_antiaging_weeks, revita_antiaging_freq = infusion_row(
            "RevitaAnti-Aging", 
            "revita_antiaging",
            "Glutathion, Vitamin C, Alpha-Liponsäure, Selen, Zink"
        )
        
        revita_detox, revita_detox_weeks, revita_detox_freq = infusion_row(
            "RevitaDetox", 
            "revita_detox",
            "Glutathion, Vitamin C, Magnesium, B-Vitamine"
        )
        
        revita_chelate, revita_chelate_weeks, revita_chelate_freq = infusion_row(
            "RevitaChelate", 
            "revita_chelate",
            "EDTA, DMSA, Vitamin C, Magnesium, Zink"
        )
        
        revita_liver, revita_liver_weeks, revita_liver_freq = infusion_row(
            "RevitaLiver", 
            "revita_liver",
            "Glutathion, Vitamin C, B-Vitamine, Magnesium, Mariendistel-Extrakt"
        )
        
        revita_leakygut, revita_leakygut_weeks, revita_leakygut_freq = infusion_row(
            "RevitaLeaky-gut", 
            "revita_leakygut",
            "Glutamin, Zink, Vitamin C, B-Vitamine, Magnesium"
        )
        
        revita_infection, revita_infection_weeks, revita_infection_freq = infusion_row(
            "RevitaInfection", 
            "revita_infection",
            "Vitamin C, Zink, Selen, Magnesium, B-Vitamine, Glutathion"
        )
        
        revita_joint, revita_joint_weeks, revita_joint_freq = infusion_row(
            "RevitaJoint", 
            "revita_joint",
            "Vitamin C, Magnesium, Zink, Mangan, B-Vitamine"
        )

        st.markdown("---")
        
        # Sub-section: Standard Infusionen
        st.markdown('<div class="section-subheader">Standard Infusionen</div>', unsafe_allow_html=True)
        
        # Header row for Standard Infusionen
        std_header_cols = st.columns([2, 1, 1])
        with std_header_cols[0]:
            st.markdown('<p class="infusion-header">Infusion</p>', unsafe_allow_html=True)
        with std_header_cols[1]:
            st.markdown('<p class="infusion-header">Anzahl Wochen</p>', unsafe_allow_html=True)
        with std_header_cols[2]:
            st.markdown('<p class="infusion-header">Häufigkeit/Woche</p>', unsafe_allow_html=True)
        
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: rgb(38, 96, 65); border-width: 2px;'>", unsafe_allow_html=True)
        
        # All Standard Infusionen
        mito_energy, mito_energy_weeks, mito_energy_freq = infusion_row(
            "Mito-Energy Behandlung (Mito-Gerät, Wirkbooster)", 
            "std_mito_energy",
            "Mito-Energy Behandlung mit Wirkbooster"
        )

        oxyvenierung, oxyvenierung_weeks, oxyvenierung_freq = infusion_row(
            "Oxyvenierung (10–40 ml, 10er Serie)", 
            "std_oxyvenierung",
            "Oxyvenierung (10–40 ml, 10er Serie)"
        )
        
        schwermetalltest, schwermetalltest_weeks, schwermetalltest_freq = infusion_row(
            "Schwermetalltest mit DMSA und Ca EDTA", 
            "std_schwermetalltest",
            "Test mit DMSA und Ca EDTA"
        )
        
        # Procain row with special handling
        procain_basen, procain_basen_weeks, procain_basen_freq, procain_2percent = procain_row(
            "Procain Baseninfusion mit Magnesium", 
            "std_procain_basen",
            "Procain Baseninfusion mit Magnesium"
        )
        
        artemisinin, artemisinin_weeks, artemisinin_freq = infusion_row(
            "Artemisinin Infusion mit 2x Lysin", 
            "std_artemisinin",
            "Artemisinin Infusion mit 2x Lysin"
        )
        
        perioperative, perioperative_weeks, perioperative_freq = infusion_row(
            "Perioperative Infusion (3 Infusionen)", 
            "std_perioperative",
            "Perioperative Infusion (3 Infusionen)"
        )
        
        detox_standard, detox_standard_weeks, detox_standard_freq = infusion_row(
            "Detox-Infusion Standard", 
            "std_detox_standard",
            "Detox-Infusion Standard"
        )
        
        detox_maxi, detox_maxi_weeks, detox_maxi_freq = infusion_row(
            "Detox-Infusion Maxi", 
            "std_detox_maxi",
            "Detox-Infusion Maxi"
        )
        
        aufbauinfusion, aufbauinfusion_weeks, aufbauinfusion_freq = infusion_row(
            "Aufbauinfusion nach Detox", 
            "std_aufbauinfusion",
            "Aufbauinfusion nach Detox"
        )
        
        anti_aging, anti_aging_weeks, anti_aging_freq = infusion_row(
            "Anti Aging Infusion komplett", 
            "std_anti_aging",
            "Anti Aging Infusion komplett"
        )
        
        nerven_aufbau, nerven_aufbau_weeks, nerven_aufbau_freq = infusion_row(
            "Nerven Aufbau Infusion", 
            "std_nerven_aufbau",
            "Nerven Aufbau Infusion"
        )
        
        leberentgiftung, leberentgiftung_weeks, leberentgiftung_freq = infusion_row(
            "Leberentgiftungsinfusion", 
            "std_leberentgiftung",
            "Leberentgiftungsinfusion"
        )
        
        anti_oxidantien, anti_oxidantien_weeks, anti_oxidantien_freq = infusion_row(
            "Anti-Oxidantien Infusion", 
            "std_anti_oxidantien",
            "Anti-Oxidantien Infusion"
        )
        
        aminoinfusion, aminoinfusion_weeks, aminoinfusion_freq = infusion_row(
            "Aminoinfusion leaky gut (5–10)", 
            "std_aminoinfusion",
            "Aminoinfusion leaky gut (5–10)"
        )
        
        relax_infusion, relax_infusion_weeks, relax_infusion_freq = infusion_row(
            "Relax Infusion", 
            "std_relax_infusion",
            "Relax Infusion"
        )

        st.markdown("---")
        
        # Additional fields
        st.markdown('<div class="section-subheader">Weitere Angaben</div>', unsafe_allow_html=True)
        
        infektions_infusion = st.text_input(
            "Infektions-Infusion / H2O2 (Anzahl / ml)", 
            value=st.session_state.infusion_data.get("infektions_infusion", ""),
            key="infektions_infusion_input",
            placeholder="Anzahl / ml"
        )
        
        immun_booster = st.selectbox(
            "Immun-Boosterung Typ", 
            ["", "Typ 1", "Typ 2", "Typ 3"], 
            index=["", "Typ 1", "Typ 2", "Typ 3"].index(st.session_state.infusion_data.get("immun_booster", "")) 
                if st.session_state.infusion_data.get("immun_booster", "") in ["", "Typ 1", "Typ 2", "Typ 3"] else 0,
            key="immun_booster_select",
            placeholder="Typ auswählen"
        )
        
        energetisierungsinfusion = st.multiselect(
            "Energetisierungsinfusion mit", 
            ["Vitamin B Shot", "Q10 Boostershot"],
            default=st.session_state.infusion_data.get("energetisierungsinfusion", []),
            key="energetisierungsinfusion_select",
            placeholder="Auswählen..."
        )
        
        naehrstoffinfusion = st.multiselect(
            "Nährstoffinfusion mit", 
            ["Glutathion", "Alpha Liponsäure"],
            default=st.session_state.infusion_data.get("naehrstoffinfusion", []),
            key="naehrstoffinfusion_select",
            placeholder="Auswählen..."
        )
        
        eisen_infusion = st.text_input(
            "Eisen Infusion (Ferinject) mg / Anzahl", 
            value=st.session_state.infusion_data.get("eisen_infusion", ""),
            key="eisen_infusion_input",
            placeholder="mg / Anzahl"
        )

        st.markdown("---")
        
        # Sub-section: Single Ingredients
        st.markdown('<div class="section-subheader">Single Ingredients / Einzel</div>', unsafe_allow_html=True)
        
        # Header row for Single Ingredients
        single_header_cols = st.columns([2, 1, 1])
        with single_header_cols[0]:
            st.markdown('<p class="infusion-header">Infusion</p>', unsafe_allow_html=True)
        with single_header_cols[1]:
            st.markdown('<p class="infusion-header">Anzahl Wochen</p>', unsafe_allow_html=True)
        with single_header_cols[2]:
            st.markdown('<p class="infusion-header">Häufigkeit/Woche</p>', unsafe_allow_html=True)
        
        st.markdown("<hr style='margin-top: 5px; margin-bottom: 20px; border-color: rgb(38, 96, 65); border-width: 2px;'>", unsafe_allow_html=True)
        
        # Single Ingredients
        vitamin_c, vitamin_c_weeks, vitamin_c_freq = infusion_row(
            "Hochdosis Vitamin C (g)", 
            "single_vitamin_c",
            "Hochdosiertes Vitamin C"
        )
        
        vitamin_b_komplex, vitamin_b_komplex_weeks, vitamin_b_komplex_freq = infusion_row(
            "Vit. B-Komplex", 
            "single_vitamin_b_komplex",
            "Vitamin B-Komplex"
        )
        
        vitamin_d, vitamin_d_weeks, vitamin_d_freq = infusion_row(
            "Vit. D", 
            "single_vitamin_d",
            "Vitamin D"
        )
        
        vitamin_b6_b12_folsaeure, vitamin_b6_b12_folsaeure_weeks, vitamin_b6_b12_folsaeure_freq = infusion_row(
            "Vit. B6/B12/Folsäure", 
            "single_vitamin_b6_b12_folsaeure",
            "Vitamin B6, B12 und Folsäure"
        )
        
        vitamin_b3, vitamin_b3_weeks, vitamin_b3_freq = infusion_row(
            "Vit. B3", 
            "single_vitamin_b3",
            "Vitamin B3"
        )

        st.markdown("---")
        
        # Sub-section: Zusätze
        st.markdown('<div class="section-subheader">Zusätze</div>', unsafe_allow_html=True)
        
        zusaetze = st.multiselect(
            "Zusätze auswählen",
            ["Vit.B Komplex", "Vit.B6/B12/Folsäure", "Vit.D 300 kIE", "Vit.B3", "Biotin", "Glycin",
            "Cholincitrat", "Zink inject", "Magnesium 400mg", "TAD (red.Glut.)", "Arginin", "Glutamin",
            "Taurin", "Ornithin", "Prolin/Lysin", "Lysin", "PC 1000mg", "Oxyvenierung", "Mito-Energy"],
            default=st.session_state.infusion_data.get("zusaetze", []),
            key="zusaetze_select",
            placeholder="Zusätze auswählen..."
        )
        
        # Update session state
        st.session_state.infusion_data = {
            # RevitaClinic Infusionen
            "revita_immune": revita_immune,
            "revita_immune_weeks": revita_immune_weeks,
            "revita_immune_freq": revita_immune_freq,
            "revita_immune_plus": revita_immune_plus,
            "revita_immune_plus_weeks": revita_immune_plus_weeks,
            "revita_immune_plus_freq": revita_immune_plus_freq,
            "revita_heal": revita_heal,
            "revita_heal_weeks": revita_heal_weeks,
            "revita_heal_freq": revita_heal_freq,
            "revita_bludder": revita_bludder,
            "revita_bludder_weeks": revita_bludder_weeks,
            "revita_bludder_freq": revita_bludder_freq,
            "revita_ferro": revita_ferro,
            "revita_ferro_weeks": revita_ferro_weeks,
            "revita_ferro_freq": revita_ferro_freq,
            "revita_energy": revita_energy,
            "revita_energy_weeks": revita_energy_weeks,
            "revita_energy_freq": revita_energy_freq,
            "revita_focus": revita_focus,
            "revita_focus_weeks": revita_focus_weeks,
            "revita_focus_freq": revita_focus_freq,
            "revita_nad": revita_nad,
            "revita_nad_weeks": revita_nad_weeks,
            "revita_nad_freq": revita_nad_freq,
            "revita_relax": revita_relax,
            "revita_relax_weeks": revita_relax_weeks,
            "revita_relax_freq": revita_relax_freq,
            "revita_fit": revita_fit,
            "revita_fit_weeks": revita_fit_weeks,
            "revita_fit_freq": revita_fit_freq,
            "revita_hangover": revita_hangover,
            "revita_hangover_weeks": revita_hangover_weeks,
            "revita_hangover_freq": revita_hangover_freq,
            "revita_beauty": revita_beauty,
            "revita_beauty_weeks": revita_beauty_weeks,
            "revita_beauty_freq": revita_beauty_freq,
            "revita_antiaging": revita_antiaging,
            "revita_antiaging_weeks": revita_antiaging_weeks,
            "revita_antiaging_freq": revita_antiaging_freq,
            "revita_detox": revita_detox,
            "revita_detox_weeks": revita_detox_weeks,
            "revita_detox_freq": revita_detox_freq,
            "revita_chelate": revita_chelate,
            "revita_chelate_weeks": revita_chelate_weeks,
            "revita_chelate_freq": revita_chelate_freq,
            "revita_liver": revita_liver,
            "revita_liver_weeks": revita_liver_weeks,
            "revita_liver_freq": revita_liver_freq,
            "revita_leakygut": revita_leakygut,
            "revita_leakygut_weeks": revita_leakygut_weeks,
            "revita_leakygut_freq": revita_leakygut_freq,
            "revita_infection": revita_infection,
            "revita_infection_weeks": revita_infection_weeks,
            "revita_infection_freq": revita_infection_freq,
            "revita_joint": revita_joint,
            "revita_joint_weeks": revita_joint_weeks,
            "revita_joint_freq": revita_joint_freq,
            
            # Standard Infusionen
            "mito_energy": mito_energy,
            "mito_energy_weeks": mito_energy_weeks,
            "mito_energy_freq": mito_energy_freq,
            "schwermetalltest": schwermetalltest,
            "schwermetalltest_weeks": schwermetalltest_weeks,
            "schwermetalltest_freq": schwermetalltest_freq,
            "procain_basen": procain_basen,
            "procain_basen_weeks": procain_basen_weeks,
            "procain_basen_freq": procain_basen_freq,
            "procain_2percent": procain_2percent,
            "artemisinin": artemisinin,
            "artemisinin_weeks": artemisinin_weeks,
            "artemisinin_freq": artemisinin_freq,
            "perioperative": perioperative,
            "perioperative_weeks": perioperative_weeks,
            "perioperative_freq": perioperative_freq,
            "detox_standard": detox_standard,
            "detox_standard_weeks": detox_standard_weeks,
            "detox_standard_freq": detox_standard_freq,
            "detox_maxi": detox_maxi,
            "detox_maxi_weeks": detox_maxi_weeks,
            "detox_maxi_freq": detox_maxi_freq,
            "aufbauinfusion": aufbauinfusion,
            "aufbauinfusion_weeks": aufbauinfusion_weeks,
            "aufbauinfusion_freq": aufbauinfusion_freq,
            "oxyvenierung": oxyvenierung,
            "oxyvenierung_weeks": oxyvenierung_weeks,
            "oxyvenierung_freq": oxyvenierung_freq,
            "anti_aging": anti_aging,
            "anti_aging_weeks": anti_aging_weeks,
            "anti_aging_freq": anti_aging_freq,
            "nerven_aufbau": nerven_aufbau,
            "nerven_aufbau_weeks": nerven_aufbau_weeks,
            "nerven_aufbau_freq": nerven_aufbau_freq,
            "leberentgiftung": leberentgiftung,
            "leberentgiftung_weeks": leberentgiftung_weeks,
            "leberentgiftung_freq": leberentgiftung_freq,
            "anti_oxidantien": anti_oxidantien,
            "anti_oxidantien_weeks": anti_oxidantien_weeks,
            "anti_oxidantien_freq": anti_oxidantien_freq,
            "aminoinfusion": aminoinfusion,
            "aminoinfusion_weeks": aminoinfusion_weeks,
            "aminoinfusion_freq": aminoinfusion_freq,
            "relax_infusion": relax_infusion,
            "relax_infusion_weeks": relax_infusion_weeks,
            "relax_infusion_freq": relax_infusion_freq,
            
            # Additional text fields
            "infektions_infusion": infektions_infusion,
            "immun_booster": immun_booster,
            "energetisierungsinfusion": energetisierungsinfusion,
            "naehrstoffinfusion": naehrstoffinfusion,
            "eisen_infusion": eisen_infusion,
            
            # Single Ingredients
            "vitamin_c": vitamin_c,
            "vitamin_c_weeks": vitamin_c_weeks,
            "vitamin_c_freq": vitamin_c_freq,
            "vitamin_b_komplex": vitamin_b_komplex,
            "vitamin_b_komplex_weeks": vitamin_b_komplex_weeks,
            "vitamin_b_komplex_freq": vitamin_b_komplex_freq,
            "vitamin_d": vitamin_d,
            "vitamin_d_weeks": vitamin_d_weeks,
            "vitamin_d_freq": vitamin_d_freq,
            "vitamin_b6_b12_folsaeure": vitamin_b6_b12_folsaeure,
            "vitamin_b6_b12_folsaeure_weeks": vitamin_b6_b12_folsaeure_weeks,
            "vitamin_b6_b12_folsaeure_freq": vitamin_b6_b12_folsaeure_freq,
            "vitamin_b3": vitamin_b3,
            "vitamin_b3_weeks": vitamin_b3_weeks,
            "vitamin_b3_freq": vitamin_b3_freq,
            
            # Zusätze
            "zusaetze": zusaetze,
        }
        
        # PDF button (only once!)
        if st.button("Infusionstherapie PDF generieren", key="infusion_pdf_button"):
            pdf_bytes = generate_pdf(patient, st.session_state.infusion_data, "INFUSIONSTHERAPIE")
            filename = f"RevitaClinic_Infusionstherapie_{patient.get('patient','')}.pdf"
            
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": filename,
                "mime": "application/pdf"
            }
            st.rerun()

    # Handle save button (saves all tabs)
    if save_button:
        if not patient["patient"]:
            st.error("Bitte Patientennamen eingeben!")
        else:
            # Get data from all tabs (already updated in session state)
            nem_prescriptions = st.session_state.nem_prescriptions
            therapieplan_data = st.session_state.therapieplan_data
            ernaehrung_data = st.session_state.ernaehrung_data
            infusion_data = st.session_state.infusion_data
            
            # Save all data
            if save_patient_data(patient, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data):
                # Set success flag
                st.session_state.show_save_success = True
                st.session_state.last_loaded_patient = patient["patient"]
                st.rerun()

    # Auto-download PDF section (appears at the end if any PDF was generated)
    if st.session_state.get("auto_download_pdf"):
        pdf_data = st.session_state.auto_download_pdf
        # Create a download button that will appear
        st.download_button(
            "PDF herunterladen",
            data=pdf_data["data"],
            file_name=pdf_data["filename"],
            mime=pdf_data["mime"],
            key="auto_download"
        )
        # Clear after download is offered
        st.session_state.auto_download_pdf = None

if __name__ == "__main__":
    main()