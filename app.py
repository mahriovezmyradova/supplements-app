import os
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import date, timedelta
from PIL import Image
import time
import base64
from supabase_db import SupabaseDB


st.set_page_config("THERAPIEKONZEPT", layout="wide")

# --- Database ---
@st.cache_resource
def get_db():
    return SupabaseDB()

db = get_db()

def fetch_supplements():
    return db.fetch_supplements()

def fetch_patient_names():
    return db.fetch_patient_names()

def save_patient_data(patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data):
    return db.save_patient_data(patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data)

def delete_patient_data(patient_name):
    return db.delete_patient_data(patient_name)

def load_patient_data(patient_name):
    return db.load_patient_data(patient_name)


# =========================================================
# CSS
# =========================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Sans:ital,opsz,wght@0,9..40,300;0,9..40,400;0,9..40,500;0,9..40,600;0,9..40,700;1,9..40,300&family=DM+Serif+Display:ital@0;1&display=swap');

html, body, [class*="css"], .stApp {
    font-family: 'DM Sans', sans-serif !important;
    font-size: 16px !important;
    color: #1a1a2e !important;
    background-color: #f8f9fb !important;
}
.main > div { padding: 12px 24px !important; }

.stButton > button {
    background-color: rgb(38, 96, 65) !important; color: white !important; border: none !important;
    padding: 11px 22px !important; font-size: 15px !important; font-weight: 600 !important;
    border-radius: 8px !important; letter-spacing: 0.3px !important; transition: all 0.2s ease !important;
    box-shadow: 0 2px 6px rgba(38,96,65,0.25) !important; font-family: 'DM Sans', sans-serif !important;
}
.stButton > button:hover {
    background-color: rgb(28, 76, 50) !important; box-shadow: 0 4px 12px rgba(38,96,65,0.35) !important;
    transform: translateY(-1px) !important;
}
.stTabs { margin-top: 6px !important; }
.stTabs [data-baseweb="tab-list"] {
    gap: 0px !important; width: 100% !important; margin-bottom: 0px !important;
    background: transparent !important; border-bottom: 2px solid #e0e4ea !important;
}
.stTabs [data-baseweb="tab"] {
    height: 52px !important; background-color: transparent !important; border-radius: 0 !important;
    padding: 12px 20px !important; color: #666 !important; flex: 1 !important; text-align: center !important;
    justify-content: center !important; margin: 0 !important; font-size: 16px !important;
    font-weight: 500 !important; font-family: 'DM Sans', sans-serif !important;
    border-bottom: 3px solid transparent !important; transition: all 0.2s ease !important;
}
.stTabs [aria-selected="true"] {
    color: rgb(38, 96, 65) !important; border-bottom: 3px solid rgb(38, 96, 65) !important;
    font-weight: 700 !important; background: transparent !important;
}
.stTextInput > div > div > input,
.stTextArea > div > div > textarea,
.stNumberInput > div > div > input,
[data-testid="stDateInput"] > div > div > input {
    padding: 10px 14px !important; font-size: 16px !important; border-radius: 8px !important;
    border: 1.5px solid #d4dae3 !important; background: #fff !important;
    font-family: 'DM Sans', sans-serif !important; transition: border-color 0.2s ease !important;
}
.stTextInput > div > div > input:focus, .stTextArea > div > div > textarea:focus {
    border-color: rgb(38, 96, 65) !important; box-shadow: 0 0 0 3px rgba(38,96,65,0.1) !important;
}
textarea { font-size: 16px !important; line-height: 1.7 !important; font-family: 'DM Sans', sans-serif !important; }
.stTextInput label, .stTextArea label, .stNumberInput label,
.stDateInput label, .stSelectbox label, .stMultiSelect label,
.stRadio label, .stCheckbox label {
    font-size: 15px !important; font-weight: 600 !important; color: #2d3748 !important;
    margin-bottom: 4px !important; font-family: 'DM Sans', sans-serif !important; letter-spacing: 0.1px !important;
}
[data-testid="stCheckbox"] { margin: 3px 0 !important; }
[data-testid="stCheckbox"] span { color: #2d3748 !important; font-size: 15px !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stCheckbox"] input[type="checkbox"] { accent-color: rgb(38, 96, 65) !important; }
[data-testid="stRadio"] { margin: 4px 0 !important; }
[data-testid="stRadio"] span { color: #2d3748 !important; font-size: 16px !important; font-family: 'DM Sans', sans-serif !important; }
[data-testid="stSelectbox"] div[data-baseweb="select"] > div,
[data-testid="stMultiSelect"] div[data-baseweb="select"] > div {
    border-radius: 8px !important; border: 1.5px solid #d4dae3 !important;
    background: #fff !important; font-size: 15px !important; min-height: 44px !important;
}
[data-testid="stSelectbox"] span, [data-testid="stMultiSelect"] span { font-size: 15px !important; font-family: 'DM Sans', sans-serif !important; }
[data-baseweb="tag"] { background-color: rgba(38,96,65,0.1) !important; border-radius: 6px !important; }
[data-baseweb="tag"] span { font-size: 14px !important; color: rgb(38,96,65) !important; font-weight: 500 !important; }
.success-message {
    background-color: #d4f4e2; color: #1a5c37; padding: 16px 20px !important; border-radius: 10px !important;
    border: 1.5px solid #a8e0c0; margin: 12px 0 !important; font-size: 15px !important;
    font-weight: 600 !important; font-family: 'DM Sans', sans-serif !important;
}
.green-section-header {
    background: linear-gradient(135deg, rgb(38, 96, 65) 0%, rgb(50, 120, 82) 100%) !important;
    color: white !important; padding: 14px 20px !important; border-radius: 10px !important;
    margin: 8px 0 6px 0 !important; font-weight: 700 !important; font-size: 1.15rem !important;
    letter-spacing: 0.5px !important; font-family: 'DM Sans', sans-serif !important;
    box-shadow: 0 3px 10px rgba(38,96,65,0.2) !important;
}
.section-subheader {
    font-weight: 700 !important; font-size: 1.05rem !important; margin: 12px 0 8px 0 !important;
    color: rgb(38, 96, 65) !important; border-bottom: 2px solid rgba(38,96,65,0.2) !important;
    padding-bottom: 6px !important; font-family: 'DM Sans', sans-serif !important; letter-spacing: 0.2px !important;
}
hr { margin: 16px 0 !important; border-width: 1px !important; border-color: #e8ecf0 !important; }
.stMarkdown h1 { font-size: 2rem !important; font-family: 'DM Serif Display', serif !important; }
.stMarkdown h2 { font-size: 1.6rem !important; font-family: 'DM Serif Display', serif !important; }
.stMarkdown h3 { font-size: 1.35rem !important; font-family: 'DM Serif Display', serif !important; }
.stMarkdown h4 { font-size: 1.1rem !important; font-family: 'DM Sans', sans-serif !important; font-weight: 700 !important; color: #1a1a2e !important; }
.streamlit-expanderHeader {
    font-size: 15px !important; font-weight: 600 !important; padding: 12px 16px !important;
    background: #f0f4f0 !important; border-radius: 8px !important; color: rgb(38, 96, 65) !important;
    font-family: 'DM Sans', sans-serif !important; border: 1.5px solid rgba(38,96,65,0.15) !important;
    transition: background 0.2s ease !important;
}
.streamlit-expanderHeader:hover { background: #e6efe9 !important; }
.streamlit-expanderContent {
    padding: 16px 12px !important; border: 1.5px solid rgba(38,96,65,0.1) !important;
    border-top: none !important; border-radius: 0 0 8px 8px !important; background: #fafcfa !important;
}
.stAlert { padding: 14px 18px !important; margin: 10px 0 !important; font-size: 15px !important; border-radius: 8px !important; font-family: 'DM Sans', sans-serif !important; }
.sticky-header { padding: 10px 0 !important; margin-bottom: 6px !important; border-bottom: 2px solid rgb(38, 96, 65) !important; }
.sticky-header .stMarkdown { font-size: 14px !important; font-weight: 700 !important; color: rgb(38, 96, 65) !important; }
.infusion-header { font-size: 14px !important; font-weight: 700 !important; color: rgb(38, 96, 65) !important; margin: 0 !important; letter-spacing: 0.3px !important; font-family: 'DM Sans', sans-serif !important; }
.infusion-label-text { font-size: 15px !important; }
.info-icon {
    display: inline-flex; align-items: center; justify-content: center; width: 18px; height: 18px;
    border-radius: 50%; background-color: rgba(38,96,65,0.15); color: rgb(38, 96, 65);
    font-size: 11px; font-weight: bold; cursor: help; margin-left: 5px; line-height: 1;
    position: relative; transition: background 0.2s ease;
}
.info-icon:hover { background-color: rgb(38,96,65); color: white; }
.info-icon:hover::after {
    content: attr(data-tooltip); position: absolute; left: 22px; top: -10px;
    background-color: #1a1a2e; color: white; padding: 6px 10px; border-radius: 6px;
    font-size: 13px; white-space: nowrap; z-index: 1000; box-shadow: 0 4px 12px rgba(0,0,0,0.2);
}
div[data-testid="column"] { padding: 0 8px !important; }
.stMarkdown, .stTextInput, .stNumberInput, .stDateInput,
.stSelectbox, .stMultiSelect, .stCheckbox, .stRadio, .stButton, .stAlert { margin-bottom: 8px !important; }
p, li, .stMarkdown p { line-height: 1.65 !important; font-size: 15px !important; font-family: 'DM Sans', sans-serif !important; }
.stCaption { font-size: 13px !important; color: #888 !important; font-family: 'DM Sans', sans-serif !important; }
div[role="listbox"] ul li { font-size: 15px !important; padding: 9px 14px !important; font-family: 'DM Sans', sans-serif !important; }
div[data-testid="stHorizontalBlock"] button { margin: 3px !important; padding: 7px 12px !important; font-size: 14px !important; }
.stNumberInput button { padding: 0 10px !important; font-size: 15px !important; }
.progress-container { margin: 16px 0 24px 0 !important; padding: 12px !important; }

/* ===== SCHEDULE TABLE ===== */
.sched-wrap {
    background: #f6faf7;
    border: 1.5px solid rgba(38,96,65,0.18);
    border-radius: 10px;
    padding: 14px 16px 10px 16px;
    margin-top: 4px;
}
.sched-item-label {
    font-size: 13px;
    font-weight: 600;
    color: #1a4430;
    margin: 10px 0 4px 0;
    font-family: 'DM Sans', sans-serif;
}
.sched-pill {
    display: inline-block;
    background: rgba(38,96,65,0.12);
    color: rgb(28,76,50);
    border-radius: 20px;
    padding: 3px 12px;
    font-size: 12px;
    font-weight: 600;
    margin-top: 4px;
    font-family: 'DM Sans', sans-serif;
}
.sched-empty {
    font-size: 13px;
    color: #aaa;
    font-style: italic;
    padding: 6px 0 4px 0;
    font-family: 'DM Sans', sans-serif;
}
.sched-divider {
    border: none;
    border-top: 1px solid rgba(38,96,65,0.1);
    margin: 8px 0 4px 0;
}
</style>
""", unsafe_allow_html=True)


# =========================================================
# HEADER
# =========================================================
col1, col2, col3 = st.columns([1.2, 3, 0.7])
with col1:
    st.markdown('<div class="header-logo">', unsafe_allow_html=True)
    if os.path.exists("clinic_logo.png"):
        st.image("clinic_logo.png", width=200)
    st.markdown('</div>', unsafe_allow_html=True)
with col2:
    st.markdown("<h1 style='text-align:center;margin:0;font-family:DM Serif Display,serif;color:rgb(38,96,65);'>THERAPIEKONZEPT</h1>", unsafe_allow_html=True)
with col3:
    st.markdown("""<div style="font-size:14px;line-height:1.8;color:#555;text-align:right;">
    Clausewitzstr. 2<br>10629 Berlin-Charlottenburg<br>+49 30 6633110<br>info@revitaclinic.de<br>www.revitaclinic.de
    </div>""", unsafe_allow_html=True)


DEFAULT_FORMS = {
    "Magnesiumbisglycinat": "Pulver", "Magnesiumthreonat": "Pulver",
    "liposomales Magnesium 200mg": "Kapseln", "Vitamin C / Na Ascorbat": "Pulver",
    "Vitamin C 1000mg": "Kapseln", "Ascorbyl Palmitat / liposomales Vitamin C": "Kapseln",
    "L-Carnitin (Carnipure)": "Kapseln", "L-Carnitin (Carnipure) Lösung": "Lösung",
    "Kapselmischung nach UR V.9 Arnika": "Kapseln", "Multi Mischung Vitamine & Mineralien": "Kapseln",
    "Benfothiamin": "Kapseln", "Vitamin B6 – P5P aktiviert": "Kapseln", "Mangan 10mg": "Tabletten",
    "Nattokinase 100mg": "Kapseln", "Q10 400mg": "Kapseln", "Selen 300 (100 Stk) Arnika": "Kapseln",
    "Selen 200 Na-Selenit": "Kapseln", "Vitamin E 800 IU E8 Tocotrienol": "Kapseln",
    "Polyphenol Arnika": "Kapseln", "Vitamin D3": "Tropfen", "Vitamin K2 1000µg": "Kapseln",
    "Calcium": "Tabletten", "OPC": "Kapseln", "Lugolsche Lösung (Jod) 5%": "Tropfen",
    "Kelp mit Jod": "Tabletten", "Zink 25mg (Zink-Glycinat)": "Kapseln", "Eisen": "Tabletten",
    "R-Alpha Liponsäure 400mg": "Kapseln", "Lactoferrin": "Kapseln", "Quercetin 500mg": "Kapseln",
    "Enzyme Multienzym / Superenzym": "Kapseln", "Sulbutiamin": "Kapseln", "Spermidin": "Kapseln",
    "Berberin (plaquefrei)": "Kapseln", "Benfotiamin (B1 fürs Nervensystem)": "Kapseln",
    "Huperzin": "Kapseln", "Kalium": "Pulver", "Lithiumorotat 1mg": "Tabletten",
    "Lithiumorotat 5mg": "Tabletten", "Omega-3 Öl 1 EL = 2g EPA/DHA": "Öl",
    "Alpha GPC": "Kapseln", "Phosphatidylserin / Phosphatidylcholin": "Kapseln",
    "NMN 500mg": "Kapseln", "NAD+ liposomal 500mg": "Kapseln", "Citicolin": "Kapseln",
    "Trans-Resveratrol 1000mg": "Kapseln", "Astaxanthin 18mg": "Kapseln", "Lutein 40mg": "Kapseln",
    "Piracetam (Memory)": "Kapseln", "Aniracetam (Learning)": "Kapseln",
    "MAP (Aminosäuremischung)": "Pulver", "Proteinshake 2 Messlöffel": "Pulver",
    "Tyrosin 500mg": "Kapseln", "5-HTP 200mg": "Kapseln", "5-HTP 300mg": "Kapseln",
    "5-HTP 600mg": "Kapseln", "SAMe 400mg": "Tabletten", "Phenylalanin 500mg": "Kapseln",
    "GABA 1g": "Kapseln", "Tryptophan 1000mg": "Kapseln", "Tryptophan 500mg": "Kapseln",
    "Lysin": "Pulver", "Prolin": "Pulver", "Arginin 1g": "Kapseln", "Citrullin": "Kapseln",
    "Ornithin": "Kapseln", "Histidin": "Kapseln", "BCAA 1g": "Kapseln", "Glycin 1000mg": "Kapseln",
    "Taurin": "Pulver", "Methionin 500mg": "Kapseln", "Kreatin Monohydrat": "Pulver",
    "Carnosin 500mg": "Kapseln", "Amin (artgerecht)": "Pulver", "MSM 1000mg": "Tabletten",
    "liposomales Glutathion": "Kapseln", "Zeolith": "Pulver", "DMSA 100mg": "Kapseln",
    "Ca EDTA 750mg": "Kapseln", "Chlorella Algen": "Tabletten", "NAC 600mg": "Kapseln",
    "NAC 800mg": "Kapseln", "TUDCA 500mg": "Kapseln", "Lymphdiaral / Lymphomyosot": "Tropfen",
    "Ceres Geranium robertianum": "Tropfen", "Mineralien und Spurenelemente Mischung": "Pulver",
    "NACET 100mg": "Kapseln", "Bromelain 750mg": "Kapseln", "Sulforaphan 35mg": "Kapseln",
    "Tamarindenextrakt": "Kapseln", "Chelidonium": "Tropfen", "Hyperikum": "Tropfen",
    "Colostrum (freeze-dried)": "Pulver", "Symbiolact Pur": "Pulver", "Probio-Cult AKK1": "Pulver",
    "Glutamin 1g": "Kapseln", "Mucosa Compositum": "Tabletten", "Basenpulver": "Pulver",
    "Vermox": "Tabletten", "Okoubaka": "Tropfen", "Bittersalz": "Pulver",
    "Bile Acid Factors": "Kapseln", "Mariendistel / Carduus Marianus / Taraxacum": "Tropfen",
    "Bitterliebe": "Kapseln", "Baldrian / Hopfen": "Kapseln", "Melatonin": "Tabletten",
    "Glucosamin 10g": "Pulver", "Chondroitin 10g": "Pulver", "Silizium G7": "Flüssig",
    "Kollagen": "Pulver", "Isagenix SuperKollagen": "Pulver", "Disulfiram": "Tabletten",
    "Quentakehl": "Kapseln", "Lysin 1g": "Kapseln", "Weihrauch (Boswelliasäure)": "Kapseln",
    "Curcuma": "Kapseln", "CurcumaXan Spray Arnika": "Spray", "Helicobacter-Therapie": "Kapseln",
    "Symbiolact comp.": "Pulver", "Artemisia annua 600mg": "Kapseln", "Artemisia annua Pulver": "Pulver",
    "Amantadin 100mg": "Tabletten", "Hydroxychloroquin (HCQ) 200mg": "Tabletten",
    "Ivermectin": "Tabletten", "Schwarzkümmelöl": "Kapseln", "Astragalus": "Kapseln",
    "Andrographis 400mg": "Kapseln", "Andrographis 500mg": "Kapseln", "AHCC 500mg": "Kapseln",
    "Östradiol 0,03%": "Creme", "Östradiol 0,06%": "Creme", "Progesteroncreme 3%": "Creme",
    "Progesteroncreme 10%": "Creme", "DHEA 2% Creme": "Creme",
    "Estradiol 0,04% / Estriol 1,6% / Testosteron 0,2%": "Creme", "DHEA 5% Gel": "Gel",
    "Testosteron 10% Gel": "Gel", "Testosteron 8mg (Frauen)": "Gel", "Testosteron 50mg": "Gel",
    "Testosteron 100mg": "Gel", "Testosteron 150mg": "Gel", "Progesteron 25mg (Männer)": "Kapseln",
    "DHEA 5mg": "Kapseln", "DHEA 10mg": "Kapseln", "DHEA 25mg": "Kapseln", "DHEA 50mg": "Kapseln",
    "Pregnenolon 10mg": "Kapseln", "Pregnenolon 30mg": "Kapseln", "Pregnenolon 50mg": "Kapseln",
    "Pregnenolon 100mg": "Kapseln", "Phytocortal 100ml": "Tropfen", "Ceres Ribes nigrum": "Tropfen",
    "Lion's Mane Mushroom Extrakt 500mg": "Kapseln", "LDN 1mg": "Tabletten",
    "LDN 1,5mg": "Tabletten", "LDN 4mg": "Tabletten", "LDN 4,5mg": "Tabletten",
    "Ceres Solidago comp.": "Tropfen", "Pro Human Probiotikum": "Kapseln",
    "Thymusextrakt": "Kapseln", "Nierenextrakt": "Kapseln", "Leberextrakt": "Kapseln",
    "Adrenal Organzellextrakt": "Kapseln", "Frischpflanzensaft": "Flüssig",
    "Löwenzahn / Sellerie / Bärlauch": "Flüssig", "Kaktusfeige": "Kapseln",
    "Kiefernadeltee": "Tee", "Weidenröschen (Fireweed)": "Tee",
    "SuperPatches einzeln": "Pflaster", "SuperPatches Packung 28er": "Pflaster",
}


# =========================================================
# HELPERS
# =========================================================

def _parse_date_safe(v, fallback=None):
    if isinstance(v, date): return v
    if isinstance(v, str):
        try: return date.fromisoformat(v)
        except: pass
    return fallback or date.today()


def therapy_progress_bar(therapiebeginn, dauer_monate,
                         kt4=False, kt12=False, kt24=False,
                         kt4_date=None, kt12_date=None, kt24_date=None):
    """Progress bar with Kontrolltermin vertical markers."""
    if not therapiebeginn or not dauer_monate:
        return
    today = date.today()
    tb = _parse_date_safe(therapiebeginn)
    if today < tb:
        return
    days_passed  = (today - tb).days
    weeks_passed = days_passed // 7
    total_weeks  = int(dauer_monate) * 4
    progress     = min(100, (weeks_passed / total_weeks * 100) if total_weeks > 0 else 0)

    markers_html = ""
    marker_labels_html = ""
    for enabled, kt_date, fallback_weeks, name in [
        (kt4,  kt4_date,  4,  "4 Wo"),
        (kt12, kt12_date, 12, "12 Wo"),
        (kt24, kt24_date, 96, "24 Mo"),
    ]:
        if not enabled:
            continue
        d = _parse_date_safe(kt_date, tb + timedelta(weeks=fallback_weeks))
        mp = min(100, max(0, (d - tb).days / (total_weeks * 7) * 100))
        markers_html += f"""
<div style="position:absolute;left:calc({mp}% - 1px);top:0;height:100%;width:2px;
            background:rgba(38,96,65,0.7);border-radius:1px;z-index:2;"></div>"""
        marker_labels_html += f"""
<div style="position:absolute;left:calc({mp}%);transform:translateX(-50%);
            top:42px;font-size:11px;font-weight:600;color:rgb(38,96,65);
            white-space:nowrap;font-family:'DM Sans',sans-serif;">
    {name}<br><span style="font-weight:400;font-size:10px;">{d.strftime('%d.%m.%y')}</span>
</div>"""

    extra_mb = "48px" if markers_html else "8px"
    html = f"""
<div style="margin:12px 0 {extra_mb} 0;padding:16px 20px;background:#f0f4f0;border-radius:12px;border:1.5px solid rgba(38,96,65,0.15);">
    <div style="font-weight:700;color:rgb(38,96,65);margin-bottom:12px;font-size:15px;font-family:'DM Sans',sans-serif;">
        Therapie-Fortschritt: Woche {weeks_passed} von {total_weeks}
    </div>
    <div style="position:relative;height:36px;background:#dde8e2;border-radius:18px;overflow:visible;">
        <div style="width:{progress}%;height:100%;background:linear-gradient(90deg,rgb(38,96,65),rgb(60,140,90));border-radius:18px;transition:width 0.5s ease;"></div>
        <div style="position:absolute;top:-2px;left:calc({progress}% - 20px);">
            <div style="background:white;border-radius:50%;width:40px;height:40px;border:2.5px solid rgb(38,96,65);display:flex;align-items:center;justify-content:center;box-shadow:0 3px 8px rgba(38,96,65,0.25);">
                <span style="font-size:22px;">👤</span>
            </div>
        </div>
        {markers_html}
        {marker_labels_html}
    </div>
</div>"""
    st.markdown(html, unsafe_allow_html=True)


def get_current_therapy_week(therapiebeginn):
    from datetime import datetime
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


def compute_week_dates(therapiebeginn, week_start, week_end):
    if not therapiebeginn or not week_start or not week_end:
        return None, None
    try:
        ws = int(week_start)
        we = int(week_end)
        start = therapiebeginn + timedelta(weeks=ws - 1)
        end = therapiebeginn + timedelta(weeks=we) - timedelta(days=1)
        return start, end
    except Exception:
        return None, None


def _parse_saved_date(val, fallback):
    if isinstance(val, date):
        return val
    if isinstance(val, str):
        try:
            return date.fromisoformat(val)
        except Exception:
            pass
    return fallback


# =========================================================
# SCHEDULE PANEL  — PATCHED:
#   • No title rendered above the panel
#   • ALL items shown (not filtered to checked-only)
#   • Unchecked items greyed out + inputs disabled
#   • Pill summary only shown for checked items
# =========================================================

# =========================================================
# INLINE TIMING HELPERS
# Column layout: [left_content | Wo von | Wo bis | Häufigkeit | Von | Bis]
ROW_COLS = [3.0, 0.55, 0.55, 0.9, 1.0, 1.0]


def _sched_header():
    """One shared header row per section — call before the rows."""
    H = ("<div style='font-size:11px;font-weight:700;color:rgb(38,96,65);"
         "text-transform:uppercase;letter-spacing:.5px;padding:4px 2px 3px 2px;"
         "border-bottom:2px solid rgba(38,96,65,.2);white-space:nowrap;'>{}</div>")
    h = st.columns(ROW_COLS)
    h[0].markdown(H.format("&nbsp;"),         unsafe_allow_html=True)
    h[1].markdown(H.format("Wo&nbsp;von"),    unsafe_allow_html=True)
    h[2].markdown(H.format("Wo&nbsp;bis"),    unsafe_allow_html=True)
    h[3].markdown(H.format("Häufigkeit"),     unsafe_allow_html=True)
    h[4].markdown(H.format("Von&nbsp;Datum"), unsafe_allow_html=True)
    h[5].markdown(H.format("Bis&nbsp;Datum"), unsafe_allow_html=True)


def _extra_rows(section_key, kp, data_store, therapiebeginn, dauer, schedule_dict):
    """2 free-text extra rows per section for ad-hoc additions."""
    for i in range(1, 3):
        slug  = f"{section_key}_extra{i}"
        cols  = st.columns(ROW_COLS)
        with cols[0]:
            val = st.text_input("", value=data_store.get(slug + "_text", ""),
                key=slug + "_text_input", placeholder=f"Zusatz {i}...", label_visibility="collapsed")
        schedule_dict.update(
            _inline_timing(bool(val), slug, therapiebeginn, dauer, kp, data_store, cols))
        schedule_dict[slug + "_text"] = val


def _inline_timing(is_checked, slug, therapiebeginn, dauer_monate, key_prefix, data_store, cols):
    """
    Renders timing inputs into cols[1..5].
    Wo von / Wo bis = dropdowns bounded by dauer_monate.
    Von/Bis Datum always auto-calculated from therapiebeginn + chosen week.
    Returns dict to merge into schedule_data.
    """
    total_weeks  = max(1, int(dauer_monate) * 4)
    freq_options = ["", "1x/Woche", "2x/Woche", "3x/Woche", "4x/Woche", "5x/Woche", "täglich"]
    # Parse therapiebeginn — use the passed argument (already the widget value
    # from patient_inputs return dict), fall back to today only if truly missing.
    import datetime as _dt
    def _coerce_date(v):
        if isinstance(v, _dt.datetime): return v.date()
        if isinstance(v, _dt.date): return v
        if isinstance(v, str):
            for fmt in ("%Y-%m-%d", "%d.%m.%Y", "%d/%m/%Y"):
                try: return _dt.datetime.strptime(v, fmt).date()
                except: pass
        return None
    tb = _coerce_date(therapiebeginn) or _dt.date.today()

    w_start_key = f"{key_prefix}_{slug}_w_start"
    w_end_key   = f"{key_prefix}_{slug}_w_end"
    ds_key      = f"{key_prefix}_{slug}_date_start"
    de_key      = f"{key_prefix}_{slug}_date_end"
    freq_key    = f"{key_prefix}_{slug}_freq"

    week_opts = [str(w) for w in range(1, total_weeks + 1)]

    saved_ws = str(data_store.get(w_start_key, 1))
    if saved_ws not in week_opts: saved_ws = "1"
    saved_we = str(data_store.get(w_end_key, saved_ws))
    if saved_we not in week_opts: saved_we = saved_ws
    saved_freq = data_store.get(freq_key, "")
    if saved_freq not in freq_options: saved_freq = ""

    # Wo von dropdown
    ws_idx = week_opts.index(saved_ws)
    w_start_sel = cols[1].selectbox("", week_opts, index=ws_idx,
        key=f"ws_{key_prefix}_{slug}", disabled=not is_checked, label_visibility="collapsed")

    # Wo bis dropdown — options filtered so min = w_start
    w_start_int = int(w_start_sel)
    we_opts = [str(w) for w in range(w_start_int, total_weeks + 1)]
    if saved_we not in we_opts: saved_we = w_start_sel
    we_idx = we_opts.index(saved_we)
    w_end_sel = cols[2].selectbox("", we_opts, index=we_idx,
        key=f"we_{key_prefix}_{slug}", disabled=not is_checked, label_visibility="collapsed")

    fi   = freq_options.index(saved_freq) if saved_freq in freq_options else 0
    freq = cols[3].selectbox("", freq_options, index=fi,
        key=f"fr_{key_prefix}_{slug}", disabled=not is_checked, label_visibility="collapsed")

    # Compute dates from therapiebeginn + chosen week (the auto value).
    w_start_int = int(w_start_sel)
    w_end_int   = int(w_end_sel)
    auto_ds = tb + timedelta(weeks=w_start_int - 1)
    auto_de = tb + timedelta(weeks=w_end_int) - timedelta(days=1)

    # Dates always computed from therapiebeginn + chosen weeks.
    # Dynamic key: changes whenever auto date changes → Streamlit creates
    # a fresh widget with the correct value each time.
    ds_widget_key = f"ds_{key_prefix}_{slug}_{auto_ds.isoformat()}"
    de_widget_key = f"de_{key_prefix}_{slug}_{auto_de.isoformat()}"
    date_start = cols[4].date_input("", value=auto_ds, format="DD.MM.YYYY",
        key=ds_widget_key, disabled=not is_checked, label_visibility="collapsed")
    date_end   = cols[5].date_input("", value=auto_de, format="DD.MM.YYYY",
        key=de_widget_key, disabled=not is_checked, label_visibility="collapsed")

    return {
        w_start_key: w_start_sel, w_end_key: w_end_sel,
        ds_key: date_start,       de_key: date_end,
        freq_key: freq,
    }


def render_schedule_panel(title, items, therapiebeginn, dauer_monate, key_prefix, data_store):
    total_weeks = max(1, dauer_monate * 4)
    freq_options = ["", "1x/Woche", "2x/Woche", "3x/Woche", "4x/Woche", "5x/Woche", "täglich"]

    if not items:
        return {}

    schedule_data = {}

    st.markdown('<div class="sched-wrap">', unsafe_allow_html=True)

    for idx, (is_checked, label, key) in enumerate(items):
        w_start_key = f"{key_prefix}_{key}_w_start"
        w_end_key   = f"{key_prefix}_{key}_w_end"
        ds_key      = f"{key_prefix}_{key}_date_start"
        de_key      = f"{key_prefix}_{key}_date_end"
        freq_key    = f"{key_prefix}_{key}_freq"

        if idx > 0:
            st.markdown('<hr class="sched-divider">', unsafe_allow_html=True)

        # Label: bold+dark when checked, muted when unchecked
        label_color  = "#1a4430" if is_checked else "#aaa"
        label_weight = "600"     if is_checked else "400"
        st.markdown(
            f'<div class="sched-item-label" style="color:{label_color};font-weight:{label_weight};">'
            f'{label}</div>',
            unsafe_allow_html=True)

        c1, c2, c3 = st.columns([1, 1, 1])

        with c1:
            saved_ws = data_store.get(w_start_key, 1)
            try:    saved_ws = int(saved_ws)
            except: saved_ws = 1
            w_start = st.number_input(
                "Woche von", min_value=1, max_value=total_weeks,
                value=min(saved_ws, total_weeks),
                key=f"sched_{key_prefix}_{key}_ws", step=1,
                disabled=not is_checked)

        with c2:
            saved_we = data_store.get(w_end_key, w_start)
            try:    saved_we = max(int(saved_we), w_start)
            except: saved_we = w_start
            w_end = st.number_input(
                "Woche bis", min_value=w_start, max_value=total_weeks,
                value=min(max(saved_we, w_start), total_weeks),
                key=f"sched_{key_prefix}_{key}_we", step=1,
                disabled=not is_checked)

        with c3:
            saved_freq = data_store.get(freq_key, "")
            freq_idx = freq_options.index(saved_freq) if saved_freq in freq_options else 0
            freq = st.selectbox(
                "Häufigkeit", freq_options, index=freq_idx,
                key=f"sched_{key_prefix}_{key}_freq",
                disabled=not is_checked)

        # Auto-calculate dates
        auto_start, auto_end = compute_week_dates(therapiebeginn, w_start, w_end)

        d1, d2 = st.columns(2)
        with d1:
            fallback_ds = auto_start or therapiebeginn or date.today()
            saved_ds = _parse_saved_date(data_store.get(ds_key), fallback_ds)
            prev_auto_start, _ = compute_week_dates(
                therapiebeginn,
                data_store.get(w_start_key, w_start),
                data_store.get(w_end_key, w_end))
            if prev_auto_start and saved_ds == prev_auto_start and auto_start:
                saved_ds = auto_start
            date_start = st.date_input(
                "Von (Datum)", value=saved_ds,
                key=f"sched_{key_prefix}_{key}_ds", format="DD.MM.YYYY",
                disabled=not is_checked)

        with d2:
            fallback_de = auto_end or therapiebeginn or date.today()
            saved_de = _parse_saved_date(data_store.get(de_key), fallback_de)
            _, prev_auto_end = compute_week_dates(
                therapiebeginn,
                data_store.get(w_start_key, w_start),
                data_store.get(w_end_key, w_end))
            if prev_auto_end and saved_de == prev_auto_end and auto_end:
                saved_de = auto_end
            date_end = st.date_input(
                "Bis (Datum)", value=saved_de,
                key=f"sched_{key_prefix}_{key}_de", format="DD.MM.YYYY",
                disabled=not is_checked)

        # Pill — only when checked
        if is_checked:
            def fmtd(d):
                try:    return d.strftime("%d.%m.%y")
                except: return ""
            pill = f"Wo {w_start}–{w_end} · {fmtd(date_start)} – {fmtd(date_end)}"
            if freq:
                pill += f" · {freq}"
            st.markdown(f'<span class="sched-pill">{pill}</span>', unsafe_allow_html=True)

        schedule_data[w_start_key] = w_start
        schedule_data[w_end_key]   = w_end
        schedule_data[ds_key]      = date_start
        schedule_data[de_key]      = date_end
        schedule_data[freq_key]    = freq

    st.markdown('</div>', unsafe_allow_html=True)
    return schedule_data


def _fmt_dt(d):
    try:
        return d.strftime("%d.%m.%Y")
    except Exception:
        return ""


# =========================================================
# PDF
# =========================================================
class PDF(FPDF):
    def __init__(self, *args, tab_title="THERAPIEKONZEPT", **kwargs):
        super().__init__(*args, **kwargs)
        self._tab_title = tab_title

    def header(self):
        if os.path.exists("clinic_logo.png"):
            try:
                self.image("clinic_logo.png", 10, 8, 40)
            except:
                pass
        self.set_font("Helvetica", "B", 16)
        self.set_xy(60, 13)
        self.cell(150, 10, self._tab_title, 0, 0, "C")
        self.set_font("Helvetica", "", 10)
        self.set_xy(230, 10)
        self.multi_cell(60, 5,
            "Clausewitzstr. 2\n10629 Berlin-Charlottenburg\n+49 30 6633110\ninfo@revitaclinic.de",
            0, "R")
        self.ln(12)


def generate_pdf(patient, supplements, tab_name="NEM"):
    title_map = {
        "NEM": "THERAPIEKONZEPT - NEM",
        "THERAPIEPLAN": "THERAPIEKONZEPT - THERAPIEPLAN",
        "INFUSIONSTHERAPIE": "THERAPIEKONZEPT - INFUSIONSTHERAPIE",
    }
    pdf = PDF("L", "mm", "A4", tab_title=title_map.get(tab_name, f"THERAPIEKONZEPT - {tab_name}"))
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    def clean_text(text):
        if not text:
            return ""
        text = str(text)
        for src, dst in [('•','-'),('–','-'),('—','-'),('−','-')]:
            text = text.replace(src, dst)
        return text

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
    pdf.cell(0, 6, patient.get("tw_besprochen", ""), 0, 1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Bekannte Allergien:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, clean_text(patient.get("allergie", "") or "-"), 0, "L")
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Diagnosen:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    pdf.multi_cell(0, 5, clean_text(patient.get("diagnosen", "") or "-"), 0, "L")
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Kontrolltermine:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    kt = ""
    if patient.get("kontrolltermin_4"): kt += "- 4 Wochen\n"
    if patient.get("kontrolltermin_12"): kt += "- 12 Wochen\n"
    kk = clean_text(patient.get("kontrolltermin_kommentar", ""))
    if kk:
        kt += f"Kommentar: {kk}"
    pdf.multi_cell(0, 5, kt or "- Keine Angaben", 0, "L")
    pdf.ln(3)

    if tab_name == "NEM" and isinstance(supplements, list):
        table_width = 277
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(table_width, 8, "NAHRUNGSERGÄNZUNGSMITTEL (NEM) VO", 0, 1, "L", True)

        headers = ["Supplement","Gesamt-dos.","Darreichungsform","Pro Einnahme",
                   "Nüchtern","Morgens","Mittags","Abends","Nachts","Kommentar"]
        base_widths = [58, 20, 36, 22, 15, 15, 15, 15, 15]
        widths = base_widths + [table_width - sum(base_widths)]

        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 8)
        for w, h in zip(widths, headers):
            pdf.cell(w, 8, h, 1, 0, "C", True)
        pdf.ln()
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)

        for s in supplements:
            cells = [
                clean_text(s.get("name", "")),
                clean_text(s.get("Gesamt-dosierung", "")),
                clean_text(s.get("Darreichungsform", "")),
                clean_text(s.get("Pro Einnahme", "")),
                f"{clean_text(s.get('Nüchtern',''))}x" if s.get("Nüchtern","").strip() else "",
                f"{clean_text(s.get('Morgens',''))}x"  if s.get("Morgens","").strip()  else "",
                f"{clean_text(s.get('Mittags',''))}x"  if s.get("Mittags","").strip()  else "",
                f"{clean_text(s.get('Abends',''))}x"   if s.get("Abends","").strip()   else "",
                f"{clean_text(s.get('Nachts',''))}x"   if s.get("Nachts","").strip()   else "",
                clean_text(s.get("Kommentar", ""))
            ]
            line_height = 5
            max_lines = max(1, max(
                max(1, int(pdf.get_string_width(c) / (w - 4)) + 1) if c else 1
                for c, w in zip(cells, widths)
            ))
            row_height = line_height * max_lines

            if pdf.get_y() + row_height > pdf.page_break_trigger:
                pdf.add_page()
                pdf.set_fill_color(38, 96, 65)
                pdf.set_text_color(255, 255, 255)
                pdf.set_font("Helvetica", "B", 11)
                for w, h in zip(widths, headers):
                    pdf.cell(w, 8, h, 1, 0, "C", True)
                pdf.ln()
                pdf.set_text_color(0, 0, 0)
                pdf.set_font("Helvetica", "", 10)

            start_x, start_y = pdf.get_x(), pdf.get_y()
            for i, (cell, width) in enumerate(zip(cells, widths)):
                x = pdf.get_x()
                align = 'L' if i == 0 else 'C'
                if cell and pdf.get_string_width(cell) > width - 4:
                    pdf.set_xy(x, start_y)
                    pdf.multi_cell(width, line_height, cell, 1, align)
                    pdf.set_xy(x + width, start_y)
                else:
                    pdf.cell(width, row_height, cell, 1, 0, align)
            pdf.set_xy(start_x, start_y + row_height)

    elif tab_name in ("THERAPIEPLAN", "INFUSIONSTHERAPIE") and isinstance(supplements, dict):
        title_text = "THERAPIEPLAN" if tab_name == "THERAPIEPLAN" else "INFUSIONSTHERAPIE"
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, title_text, 0, 1, "C", True)
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)

        label_mapping = {
            "zaehne": "Überprüfung Zähne/Kieferknochen (OPG/DVT)",
            "zaehne_zu_pruefen": "Zähne zu überprüfen (OPG/DVT)",
            "darm_biofilm": "Darm - Biofilmentfernung (Express-Darmkur 4 Tageskur)",
            "darmsanierung": "Darmsanierung nach Paracelsus Klinik",
            "darmsanierung_dauer": "Darmsanierung Dauer",
            "hydrocolon": "Hydrocolon (Darmspülung) 2x, Abstand 14 Tage",
            "parasiten": "Parasitenbehandlung mit Vermox (3 Tage)",
            "parasiten_bio": "Biologisches Parasitenprogramm",
            "leberdetox": "Leberdetox nach Paracelsus Klinik",
            "nierenprogramm": "Nierenprogramm nach Dr. Clark (4 Wochen)",
            "infektion_bakt": "Infektionsbehandlung Bakterien",
            "infektion_virus": "Infektionsbehandlung Viren",
            "ausleitung_inf": "Schwermetallausleitung Infusion",
            "ausleitung_oral": "Schwermetallausleitung oral",
            "mikronaehrstoffe": "Mikronährstoffe (NEM-Verordnung)",
            "infusionsbehandlung": "Infusionstherapie",
            "neuraltherapie": "Neuraltherapie",
            "eigenblut": "Eigenbluttherapie",
            "ozontherapie": "Ozontherapie",
            "bio_isopath": "Biologische Isopathische Therapie",
            "timewaver_freq": "TimeWaver Frequency Behandlung",
            "ernaehrung": "Ernährungsberatung",
            "hypnose": "Hypnosetherapie",
            "yager": "Yagertherapie",
            "aethetisch": "Ästhetische Behandlung",
            "medikamente_text": "Medikamentenverordnung",
            "akupunktur": "Akupunktur",
            "homoeopathie": "Homöopathie (Anna)",
            "bioresonanz": "Bioresonanz (Anna)",
            "lowcarb": "Low Carb Ernährung",
            "fasten": "Intermittierendes Fasten",
            "krebsdiaet": "Krebs Diät",
            "ketogene": "Ketogene Ernährung",
            "basisch": "Basische Ernährung",
            "naehrstoff_ausgleich": "Nährstoffmängel ausgleichen",
            "therapie_sonstiges": "Sonstiges",
            "energie_behandlungen": "Energiebehandlungen bei Marie",
            "zwischengespraech_4": "Zwischengespräch nach 4 Wochen",
            "zwischengespraech_8": "Zwischengespräch nach 8 Wochen",
            "lab_imd": "IMD", "lab_mmd": "MMD", "lab_nextgen": "NextGen Onco",
            "lab_sonstiges": "Sonstiges (Labor)",
            "analyse_bewegungsapparat": "Analyse Bewegungsapparat (Martin)",
            "schwermetalltest_tp": "Schwermetalltest mit DMSA und Ca EDTA",
            "revita_immune": "RevitaImmune", "revita_immune_plus": "RevitaImmunePlus",
            "revita_heal": "Revita Heal (2x)", "revita_bludder": "RevitaBludder",
            "revita_ferro": "RevitaFerro", "revita_energy": "RevitaEnergyBoost",
            "revita_focus": "RevitaFocus", "revita_nad": "RevitaNAD+",
            "revita_relax": "RevitaRelax", "revita_fit": "RevitaFit",
            "revita_hangover": "RevitaHangover", "revita_beauty": "RevitaBeauty",
            "revita_antiaging": "RevitaAnti-Aging", "revita_detox": "RevitaDetox",
            "revita_chelate": "RevitaChelate", "revita_liver": "RevitaLiver",
            "revita_leakygut": "RevitaLeaky-gut", "revita_infection": "RevitaInfection",
            "revita_joint": "RevitaJoint",
            "mito_energy": "Mito-Energy Behandlung",
            "procain_basen": "Procain Baseninfusion mit Magnesium",
            "artemisinin": "Artemisinin Infusion mit 2x Lysin",
            "perioperative": "Perioperative Infusion (3 Infusionen)",
            "detox_standard": "Detox-Infusion Standard", "detox_maxi": "Detox-Infusion Maxi",
            "aufbauinfusion": "Aufbauinfusion nach Detox",
            "anti_aging": "Anti Aging Infusion komplett",
            "nerven_aufbau": "Nerven Aufbau Infusion",
            "leberentgiftung": "Leberentgiftungsinfusion",
            "anti_oxidantien": "Anti-Oxidantien Infusion",
            "aminoinfusion": "Aminoinfusion leaky gut",
            "relax_infusion": "Relax Infusion",
            "eisen_infusion": "Eisen Infusion (Ferinject)",
            "vitamin_c": "Hochdosis Vitamin C", "vitamin_b_komplex": "Vit. B-Komplex",
            "vitamin_d": "Vit. D", "vitamin_b6_b12_folsaeure": "Vit. B6/B12/Folsäure",
            "vitamin_b3": "Vit. B3", "zusaetze": "Zusätze",
            "infektions_infusion": "Infektions-Infusion / H2O2",
            "immun_booster": "Immun-Boosterung",
            "energetisierungsinfusion": "Energetisierungsinfusion",
            "naehrstoffinfusion": "Nährstoffinfusion",
            "oxyvenierung": "Oxyvenierung",
            "schwermetalltest": "Schwermetalltest DMSA/Ca EDTA",
        }

        # ── Therapie-Fortschritt progress bar as text ──
        import datetime as _dt2
        tb_raw = patient.get("therapiebeginn")
        tb_pdf = None
        if isinstance(tb_raw, _dt2.date): tb_pdf = tb_raw
        elif isinstance(tb_raw, str):
            try: tb_pdf = _dt2.date.fromisoformat(tb_raw)
            except: pass
        if tb_pdf:
            today_pdf = _dt2.date.today()
            dauer_pdf = int(patient.get("dauer", 6))
            total_w_pdf = dauer_pdf * 4
            weeks_done = max(0, (today_pdf - tb_pdf).days // 7)
            progress_pct = min(100, int(weeks_done / total_w_pdf * 100)) if total_w_pdf > 0 else 0
            bar_width = 200
            filled = int(bar_width * progress_pct / 100)
            pdf.set_fill_color(38, 96, 65)
            pdf.rect(pdf.get_x(), pdf.get_y(), filled, 5, 'F')
            pdf.set_fill_color(220, 232, 220)
            pdf.rect(pdf.get_x() + filled, pdf.get_y(), bar_width - filled, 5, 'F')
            pdf.ln(7)
            pdf.set_font("Helvetica", "B", 9)
            pdf.set_text_color(38, 96, 65)
            pdf.cell(0, 5, f"Therapie-Fortschritt: Woche {weeks_done} von {total_w_pdf} ({progress_pct}%)", 0, 1)
            # Kontrolltermine markers
            kt_items = []
            if patient.get("kontrolltermin_4"):
                kt_items.append(("4 Wochen", patient.get("kt4_date", "")))
            if patient.get("kontrolltermin_12"):
                kt_items.append(("12 Wochen", patient.get("kt12_date", "")))
            if patient.get("kontrolltermin_24"):
                kt_items.append(("24 Monate", patient.get("kt24_date", "")))
            if kt_items:
                pdf.set_font("Helvetica", "", 8)
                kt_str = "  |  ".join(
                    f"KT {name}: {_fmt_dt(v) if isinstance(v, _dt2.date) else str(v)}"
                    for name, v in kt_items)
                pdf.cell(0, 5, clean_text(kt_str), 0, 1)
            pdf.set_text_color(0, 0, 0)
            pdf.ln(2)

        # ═══════════════════════════════════════════════════════════
        # Build the prescription table.
        # A row is PRESCRIBED if:
        #   - bool key is True  (e.g. zaehne=True)
        #   - OR  _cb key is True (e.g. infektion_bakt_cb=True, lab_imd_cb=True)
        #   - OR  infusion checkbox key is True (inf_revita_immune_cb from session but
        #         stored as revita_immune=True in inf data)
        # For each prescribed item we look up its timing keys and comment.
        # Col order: Therapie | Wo.von | Wo.bis | Von | Bis | Häufigkeit | Kommentar
        # ═══════════════════════════════════════════════════════════

        # All suffix families we skip when scanning for "is this prescribed?"
        SKIP_SFXS = ("_w_start","_w_end","_date_start","_date_end","_freq",
                     "_text","_comment","_detail","_dauer","_zu_pruefen",
                     "_noreen","_martin","_miro","_typ","_botox","_prp",
                     "_faeden","_hyaloron","_comment","_2percent",
                     "kt4_date","kt12_date","kt24_date",
                     "kontrolltermin_4","kontrolltermin_12","kontrolltermin_24",
                     "kontrolltermin_kommentar","procain_2percent","zusaetze",
                     "diagnosen","allergie","geschlecht","groesse","gewicht",
                     "geburtsdatum","therapiebeginn","dauer","tw_besprochen","patient")
        def _is_skip(k):
            for s in SKIP_SFXS:
                if k.endswith(s) or k == s.lstrip("_"): return True
            return False

        # Helper: find timing for a given base slug
        def _timing(slug, prefix):
            """Returns (ws, we, ds, de, fr) strings for a slug."""
            # Try all prefix combinations including std_ variants
            for kp in (prefix, f"inf_std", "diag","haupt","bio","gesp","inf",""):
                base = f"{kp}_{slug}" if kp else slug
                ws = supplements.get(f"{base}_w_start","")
                if ws:
                    we  = supplements.get(f"{base}_w_end","")
                    ds  = supplements.get(f"{base}_date_start","")
                    de  = supplements.get(f"{base}_date_end","")
                    fr  = supplements.get(f"{base}_freq","")
                    ds_s = _fmt_dt(ds) if isinstance(ds, date) else (str(ds) if ds else "")
                    de_s = _fmt_dt(de) if isinstance(de, date) else (str(de) if de else "")
                    return str(ws), str(we), ds_s, de_s, str(fr) if fr else ""
            # Also try with std_ slug prefix
            std_slug = f"std_{slug}"
            for kp in ("inf",):
                base = f"{kp}_{std_slug}"
                ws = supplements.get(f"{base}_w_start","")
                if ws:
                    we  = supplements.get(f"{base}_w_end","")
                    ds  = supplements.get(f"{base}_date_start","")
                    de  = supplements.get(f"{base}_date_end","")
                    fr  = supplements.get(f"{base}_freq","")
                    ds_s = _fmt_dt(ds) if isinstance(ds, date) else (str(ds) if ds else "")
                    de_s = _fmt_dt(de) if isinstance(de, date) else (str(de) if de else "")
                    return str(ws), str(we), ds_s, de_s, str(fr) if fr else ""
            return "", "", "", "", ""

        # Build rows: [(label, comment, ws, we, ds, de, fr), ...]
        rows = []
        seen_labels = set()

        # Canonical ordered list of prescribed items
        # Check: boolean True, or _cb True
        def _prescribed(key):
            v = supplements.get(key)
            if v is True: return True
            if v is False or v is None: return False
            if isinstance(v, str) and v.strip(): return True
            if isinstance(v, list) and v: return True
            return False

        def _add_row(lbl, slug, prefix, comment_key=None):
            if lbl in seen_labels: return
            seen_labels.add(lbl)
            ws, we, ds, de, fr = _timing(slug, prefix)
            comment = ""
            if comment_key:
                cv = supplements.get(comment_key, "")
                if isinstance(cv, str): comment = cv
            rows.append((clean_text(lbl), clean_text(comment),
                         ws, we, ds, de, fr))

        # ── THERAPIEPLAN items ──
        # Section 1: Diagnostik
        for key, lbl in [
            ("zaehne",                "Ueberpr. Zaehne/Kieferknochen (OPG/DVT)"),
            ("analyse_bewegungsapparat","Analyse Bewegungsapparat (Martin)"),
            ("schwermetalltest_tp",   "Schwermetalltest DMSA/Ca EDTA"),
        ]:
            if _prescribed(key):
                comment = supplements.get("zaehne_zu_pruefen","") if key=="zaehne" else ""
                _add_row(lbl, key, "diag", None)
                if comment: rows[-1] = rows[-1][:1] + (clean_text(comment),) + rows[-1][2:]

        for key, lbl in [("lab_imd","IMD"),("lab_mmd","MMD"),
                          ("lab_nextgen","NextGen Onco"),("lab_sonstiges","Sonstiges (Labor)")]:
            cb = key + "_cb"
            if supplements.get(cb, False):
                _add_row(lbl, key, "diag", key)

        # Section 2: Haupttherapien
        for key, lbl in [
            ("darm_biofilm","Darm - Biofilmentfernung"),
            ("darmsanierung","Darmsanierung nach Paracelsus Klinik"),
            ("hydrocolon","Hydrocolon (Darmspuelung)"),
            ("parasiten","Parasitenbehandlung mit Vermox (3 Tage)"),
            ("parasiten_bio","Biologisches Parasitenprogramm"),
            ("leberdetox","Leberdetox nach Paracelsus Klinik"),
            ("nierenprogramm","Nierenprogramm nach Dr. Clark"),
            ("mikronaehrstoffe","Mikronaehrstoffe (NEM-Verordnung)"),
            ("infusionsbehandlung","Infusionstherapie"),
            ("neuraltherapie","Neuraltherapie"),
            ("eigenblut","Eigenbluttherapie"),
            ("ozontherapie","Ozontherapie"),
            ("ausleitung_inf","Schwermetallausleitung Infusion"),
            ("ausleitung_oral","Schwermetallausleitung oral"),
        ]:
            if _prescribed(key):
                _add_row(lbl, key, "haupt")

        for key, lbl in [
            ("infektion_bakt","Infektionsbehandlung Bakterien"),
            ("infektion_virus","Infektionsbehandlung Viren"),
            ("medikamente_text","Medikamentenverordnung - Rezept"),
        ]:
            cb = key + "_cb"
            if supplements.get(cb, False):
                _add_row(lbl, key, "haupt", key)

        # Section 3: Bio
        for key, lbl in [
            ("bio_isopath","Biologische Isopathische Therapie"),
            ("akupunktur","Akupunktur"),
            ("homoeopathie","Homoeopathie (Anna)"),
            ("bioresonanz","Bioresonanz (Anna)"),
            ("timewaver_freq","TimeWaver Frequency Behandlung"),
            ("hypnose","Hypnosetherapie"),
            ("yager","Yagertherapie"),
            ("energie_behandlungen","Energiebehandlungen bei Marie"),
        ]:
            if _prescribed(key):
                extra = []
                if key == "hypnose":
                    for sk, sn in [("hypnose_noreen","Noreen"),("hypnose_martin","Martin"),("hypnose_miro","Miro")]:
                        if supplements.get(sk): extra.append(sn)
                    if supplements.get("hypnose_typ","").strip():
                        extra.append(f"Typ: {supplements['hypnose_typ']}")
                _add_row(lbl, key, "bio", None)
                if extra: rows[-1] = (rows[-1][0], clean_text(", ".join(extra))) + rows[-1][2:]

        for key, lbl, cmt in [
            ("atemtherapie","Atemtherapie","atemtherapie_comment"),
            ("bewegung","Bewegung","bewegung_comment"),
            ("ernaehrung","Ernaehrungsberatung","ernaehrung_comment"),
            ("aethetisch","Aesthetische Behandlung","aethetisch_comment"),
            ("lowcarb","Low Carb Ernaehrung","lowcarb_comment"),
            ("fasten","Intermittierendes Fasten","fasten_comment"),
            ("krebsdiaet","Krebs Diaet","krebsdiaet_comment"),
            ("ketogene","Ketogene Ernaehrung","ketogene_comment"),
            ("basisch","Basische Ernaehrung","basisch_comment"),
        ]:
            if _prescribed(key):
                _add_row(lbl, key, "bio", cmt)
                if key == "aethetisch":
                    sub = [s for s,k in [("Botox","aethetisch_botox"),("PRP","aethetisch_prp"),
                                          ("Faeden","aethetisch_faeden"),("Hyaloron","aethetisch_hyaloron")]
                           if supplements.get(k)]
                    if sub: rows[-1] = (rows[-1][0], clean_text(", ".join(sub)+(" | "+rows[-1][1] if rows[-1][1] else ""))) + rows[-1][2:]

        for key, lbl in [("naehrstoff_ausgleich","Naehrstoffmaengel ausgleichen"),
                          ("therapie_sonstiges","Sonstiges")]:
            if supplements.get(key+"_cb", False):
                _add_row(lbl, key, "bio", key)

        # Section 4: Gespraeche
        for key, lbl in [("zwischengespraech_4","Zwischengespraech 4 Wochen (1/2h)"),
                          ("zwischengespraech_8","Zwischengespraech 8 Wochen (1/2h)")]:
            if _prescribed(key):
                _add_row(lbl, key, "gesp")

        # ── INFUSIONSTHERAPIE items ──
        for key, lbl in [
            ("revita_immune","RevitaImmune"),("revita_immune_plus","RevitaImmunePlus"),
            ("revita_heal","Revita Heal (2x)"),("revita_bludder","RevitaBludder"),
            ("revita_ferro","RevitaFerro"),("revita_energy","RevitaEnergyBoost"),
            ("revita_focus","RevitaFocus"),("revita_nad","RevitaNAD+"),
            ("revita_relax","RevitaRelax"),("revita_fit","RevitaFit"),
            ("revita_hangover","RevitaHangover"),("revita_beauty","RevitaBeauty"),
            ("revita_antiaging","RevitaAnti-Aging"),("revita_detox","RevitaDetox"),
            ("revita_chelate","RevitaChelate"),("revita_liver","RevitaLiver"),
            ("revita_leakygut","RevitaLeaky-gut"),("revita_infection","RevitaInfection"),
            ("revita_joint","RevitaJoint"),
            ("mito_energy","Mito-Energy Behandlung"),("oxyvenierung","Oxyvenierung"),
            ("schwermetalltest","Schwermetalltest DMSA/Ca EDTA"),
            ("procain_basen","Procain Baseninfusion"),("artemisinin","Artemisinin Infusion"),
            ("perioperative","Perioperative Infusion"),("detox_standard","Detox-Infusion Standard"),
            ("detox_maxi","Detox-Infusion Maxi"),("aufbauinfusion","Aufbauinfusion nach Detox"),
            ("anti_aging","Anti Aging Infusion"),("nerven_aufbau","Nerven Aufbau Infusion"),
            ("leberentgiftung","Leberentgiftungsinfusion"),
            ("anti_oxidantien","Anti-Oxidantien Infusion"),
            ("aminoinfusion","Aminoinfusion leaky gut"),("relax_infusion","Relax Infusion"),
            ("vitamin_c","Hochdosis Vitamin C"),("vitamin_b_komplex","Vit. B-Komplex"),
            ("vitamin_d","Vit. D"),("vitamin_b6_b12_folsaeure","Vit. B6/B12/Folsaeure"),
            ("vitamin_b3","Vit. B3"),
        ]:
            if _prescribed(key):
                _add_row(lbl, key, "inf")

        for key, lbl in [
            ("infektions_infusion","Infektions-Infusion / H2O2"),
            ("immun_booster","Immun-Boosterung"),
            ("energetisierungsinfusion","Energetisierungsinfusion"),
            ("naehrstoffinfusion","Naehrstoffinfusion"),
            ("eisen_infusion","Eisen Infusion (Ferinject)"),
        ]:
            if supplements.get(key+"_cb", False):
                cmt = supplements.get(key,"")
                cmt_str = cmt if isinstance(cmt,str) else (", ".join(str(v) for v in cmt) if isinstance(cmt,list) else "")
                _add_row(lbl, key, "inf", None)
                if cmt_str: rows[-1] = (rows[-1][0], clean_text(cmt_str)) + rows[-1][2:]

        # Extra rows from all sections
        for i in range(1, 3):
            for sec in ("diag","haupt","bio","gesp","inf"):
                slug  = f"{sec}_extra{i}"
                txt   = supplements.get(slug + "_text", "")
                if txt and str(txt).strip():
                    _add_row(str(txt), slug, sec)

        # ── Render table ──
        pdf.ln(2)
        # Col order: Therapie | Wo.von | Wo.bis | Von Datum | Bis Datum | Häufigkeit | Kommentar
        TW = 277  # total landscape A4 width minus margins
        # widths: therapy=70, wo_von=13, wo_bis=13, von=28, bis=28, hauf=22, kommentar=rest
        sw_t  = [70, 13, 13, 28, 28, 22]
        sw_k  = TW - sum(sw_t)   # kommentar gets the rest (~103)
        sw    = sw_t + [sw_k]
        hdrs  = ["Therapie / Verordnung","Wo.von","Wo.bis","Von Datum","Bis Datum","Haeufigkeit","Kommentar"]

        def _print_table_header():
            pdf.set_fill_color(38, 96, 65); pdf.set_text_color(255, 255, 255)
            pdf.set_font("Helvetica", "B", 8)
            for w, h in zip(sw, hdrs):
                pdf.cell(w, 7, h, 1, 0, "C", True)
            pdf.ln()
            pdf.set_text_color(0, 0, 0); pdf.set_font("Helvetica", "", 8)

        if rows:
            _print_table_header()
            LH = 5   # line height per line
            for lbl, comment, ws, we, ds, de, fr in rows:
                cells = [lbl, ws, we, ds, de, fr, comment]
                # Compute needed lines per cell
                def _lines(txt, w):
                    if not txt: return 1
                    return max(1, int(pdf.get_string_width(txt) / max(1, w - 4)) + 1)
                n_lines = max(_lines(c, w) for c, w in zip(cells, sw))
                rh = LH * n_lines
                if pdf.get_y() + rh > pdf.page_break_trigger:
                    pdf.add_page(); _print_table_header()
                sx, sy = pdf.get_x(), pdf.get_y()
                for i, (cell, width) in enumerate(zip(cells, sw)):
                    x = pdf.get_x()
                    needs_wrap = pdf.get_string_width(cell) > (width - 4) if cell else False
                    if needs_wrap:
                        pdf.set_xy(x, sy)
                        pdf.multi_cell(width, LH, cell, 1, 'L')
                        pdf.set_xy(x + width, sy)
                    else:
                        pdf.cell(width, rh, cell, 1, 0, 'L')
                pdf.set_xy(sx, sy + rh)
        else:
            pdf.set_font("Helvetica", "", 9)
            pdf.cell(0, 6, "- Keine Verordnungen eingetragen", 0, 1)

    else:
        pdf.set_font("Helvetica", "B", 14)
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.cell(0, 10, str(tab_name).upper(), 0, 1, "C", True)
        pdf.ln(5)
        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 10)
        pdf.cell(0, 6, "Keine Daten verfügbar.", 0, 1)

    return bytes(pdf.output(dest="S"))


# =========================================================
# PATIENT INPUTS
# =========================================================
def _apply_patient_to_session(pd_, nem, tp, ern, inf, name):
    """Push ALL loaded patient data into session state AND widget keys.
    Call this before st.rerun() so the next render picks up correct values."""
    st.session_state.patient_data      = pd_ or {}
    st.session_state.nem_prescriptions = nem or []
    st.session_state.therapieplan_data = tp  or {}
    st.session_state.ernaehrung_data   = ern or {}
    st.session_state.infusion_data     = inf or {}
    st.session_state.last_loaded_patient  = name
    st.session_state.display_patient_name = name
    st.session_state.just_loaded_patient  = True

    def _dt(v):
        if isinstance(v, date): return v
        if isinstance(v, str):
            try: return date.fromisoformat(v)
            except: pass
        return date.today()

    # ── Patient detail widgets ──
    st.session_state["geburtsdatum_input"]                = _dt(pd_.get("geburtsdatum"))
    st.session_state["therapiebeginn_input"]              = _dt(pd_.get("therapiebeginn"))
    st.session_state["geschlecht_input"]                  = pd_.get("geschlecht","M")
    try:    st.session_state["groesse_input"]             = int(pd_.get("groesse") or 0)
    except: st.session_state["groesse_input"]             = 0
    try:    st.session_state["gewicht_input"]             = int(pd_.get("gewicht") or 0)
    except: st.session_state["gewicht_input"]             = 0
    try:    st.session_state["dauer_input"]               = int(pd_.get("dauer") or 6)
    except: st.session_state["dauer_input"]               = 6
    st.session_state["tw_besprochen_input"]               = pd_.get("tw_besprochen","Ja")
    st.session_state["allergie_input"]                    = pd_.get("allergie","")
    st.session_state["diagnosen_input"]                   = pd_.get("diagnosen","")
    st.session_state["kontrolltermin_4_input"]            = bool(pd_.get("kontrolltermin_4",False))
    st.session_state["kontrolltermin_12_input"]           = bool(pd_.get("kontrolltermin_12",False))
    st.session_state["kontrolltermin_24_input"]           = bool(pd_.get("kontrolltermin_24",False))
    st.session_state["kontrolltermin_kommentar_input"]    = pd_.get("kontrolltermin_kommentar","")
    if pd_.get("kt4_date"):  st.session_state["kt4_date_input"]  = _dt(pd_.get("kt4_date"))
    if pd_.get("kt12_date"): st.session_state["kt12_date_input"] = _dt(pd_.get("kt12_date"))
    if pd_.get("kt24_date"): st.session_state["kt24_date_input"] = _dt(pd_.get("kt24_date"))

    # ── Therapieplan widgets — map widget_key → tp dict key ──
    _tp = tp or {}
    _tp_map = {
        "zaehne_checkbox":                   "zaehne",
        "zaehne_zu_pruefen_input":           "zaehne_zu_pruefen",
        "analyse_bewegungsapparat_checkbox": "analyse_bewegungsapparat",
        "schwermetalltest_tp_checkbox":      "schwermetalltest_tp",
        "lab_imd_cb":       "lab_imd_cb",   "lab_imd_input":       "lab_imd",
        "lab_mmd_cb":       "lab_mmd_cb",   "lab_mmd_input":       "lab_mmd",
        "lab_nextgen_cb":   "lab_nextgen_cb","lab_nextgen_input":   "lab_nextgen",
        "lab_sonstiges_cb": "lab_sonstiges_cb","lab_sonstiges_input":"lab_sonstiges",
        "darm_biofilm_checkbox":     "darm_biofilm",
        "darmsanierung_checkbox":    "darmsanierung",
        "darmsanierung_dauer_select":"darmsanierung_dauer",
        "hydrocolon_checkbox":       "hydrocolon",
        "parasiten_checkbox":        "parasiten",
        "parasiten_bio_checkbox":    "parasiten_bio",
        "leberdetox_checkbox":       "leberdetox",
        "nierenprogramm_checkbox":   "nierenprogramm",
        "mikronaehrstoffe_checkbox": "mikronaehrstoffe",
        "infusionsbehandlung_checkbox":"infusionsbehandlung",
        "neuraltherapie_checkbox":   "neuraltherapie",
        "eigenblut_checkbox":        "eigenblut",
        "ozontherapie_checkbox":     "ozontherapie",
        "ausleitung_inf_checkbox":   "ausleitung_inf",
        "ausleitung_oral_checkbox":  "ausleitung_oral",
        "infektion_bakt_cb":         "infektion_bakt_cb",
        "infektion_bakt_txt":        "infektion_bakt",
        "infektion_virus_cb":        "infektion_virus_cb",
        "infektion_virus_txt":       "infektion_virus",
        "medikamente_text_cb":       "medikamente_text_cb",
        "medikamente_text_txt":      "medikamente_text",
        "bio_isopath_checkbox":      "bio_isopath",
        "akupunktur_checkbox":       "akupunktur",
        "homoeopathie_checkbox":     "homoeopathie",
        "bioresonanz_checkbox":      "bioresonanz",
        "timewaver_freq_checkbox":   "timewaver_freq",
        "hypnose_checkbox":          "hypnose",
        "hypnose_noreen_checkbox":   "hypnose_noreen",
        "hypnose_martin_checkbox":   "hypnose_martin",
        "hypnose_miro_checkbox":     "hypnose_miro",
        "hypnose_typ_input":         "hypnose_typ",
        "yager_checkbox":            "yager",
        "energie_behandlungen_checkbox":"energie_behandlungen",
        "atemtherapie":              "atemtherapie",
        "atemtherapie_comment":      "atemtherapie_comment",
        "bewegung":                  "bewegung",
        "bewegung_comment":          "bewegung_comment",
        "ernaehrung":                "ernaehrung",
        "ernaehrung_comment":        "ernaehrung_comment",
        "aethetisch_checkbox":       "aethetisch",
        "aethetisch_comment_input":  "aethetisch_comment",
        "aethetisch_botox_checkbox": "aethetisch_botox",
        "aethetisch_prp_checkbox":   "aethetisch_prp",
        "aethetisch_faeden_checkbox":"aethetisch_faeden",
        "aethetisch_hyaloron_checkbox":"aethetisch_hyaloron",
        "lowcarb":                   "lowcarb",
        "lowcarb_comment":           "lowcarb_comment",
        "fasten":                    "fasten",
        "fasten_comment":            "fasten_comment",
        "krebsdiaet":                "krebsdiaet",
        "krebsdiaet_comment":        "krebsdiaet_comment",
        "ketogene":                  "ketogene",
        "ketogene_comment":          "ketogene_comment",
        "basisch":                   "basisch",
        "basisch_comment":           "basisch_comment",
        "naehrstoff_ausgleich_cb":   "naehrstoff_ausgleich_cb",
        "naehrstoff_ausgleich_input":"naehrstoff_ausgleich",
        "therapie_sonstiges_cb":     "therapie_sonstiges_cb",
        "therapie_sonstiges_input":  "therapie_sonstiges",
        "zwischengespraech_4_checkbox":"zwischengespraech_4",
        "zwischengespraech_8_checkbox":"zwischengespraech_8",
    }
    for wk, dk in _tp_map.items():
        if dk in _tp:
            st.session_state[wk] = _tp[dk]

    # ── Infusion checkbox widgets ──
    _inf = inf or {}
    for ik in ["revita_immune","revita_immune_plus","revita_heal","revita_bludder",
               "revita_ferro","revita_energy","revita_focus","revita_nad","revita_relax",
               "revita_fit","revita_hangover","revita_beauty","revita_antiaging",
               "revita_detox","revita_chelate","revita_liver","revita_leakygut",
               "revita_infection","revita_joint","std_mito_energy","std_oxyvenierung",
               "std_schwermetalltest","std_procain_basen","std_artemisinin",
               "std_perioperative","std_detox_standard","std_detox_maxi",
               "std_aufbauinfusion","std_anti_aging","std_nerven_aufbau",
               "std_leberentgiftung","std_anti_oxidantien","std_aminoinfusion",
               "std_relax_infusion","single_vitamin_c","single_vitamin_b_komplex",
               "single_vitamin_d","single_vitamin_b6_b12_folsaeure","single_vitamin_b3"]:
        if ik in _inf:
            st.session_state[f"inf_{ik}_cb"] = bool(_inf[ik])
    for wk in ["infektions_infusion_cb","immun_booster_cb","energetisierungsinfusion_cb",
               "naehrstoffinfusion_cb","eisen_infusion_cb"]:
        if wk in _inf: st.session_state[wk] = bool(_inf[wk])
    for wk in ["infektions_infusion_inp","immun_booster_sel","energetisierungsinfusion_sel",
               "naehrstoffinfusion_sel","eisen_infusion_inp"]:
        base = wk.rsplit("_",1)[0]
        if base in _inf: st.session_state[wk] = _inf[base]
    if "zusaetze" in _inf: st.session_state["zusaetze_select"] = _inf["zusaetze"]

    # ── Restore ALL timing widget keys (Wo von, Wo bis, Häufigkeit) ──
    # Keys in tp/inf data: "{prefix}_{slug}_w_start", "{prefix}_{slug}_freq" etc.
    # Widget keys: "ws_{prefix}_{slug}", "we_{prefix}_{slug}", "fr_{prefix}_{slug}"
    for data_dict, prefix_list in [
        (tp or {}, ["diag","haupt","bio","gesp"]),
        (inf or {}, ["inf"]),
    ]:
        for k, v in data_dict.items():
            if k.endswith("_w_start"):
                base = k[:-len("_w_start")]
                st.session_state[f"ws_{base}"] = str(v)
            elif k.endswith("_w_end"):
                base = k[:-len("_w_end")]
                st.session_state[f"we_{base}"] = str(v)
            elif k.endswith("_freq"):
                base = k[:-len("_freq")]
                st.session_state[f"fr_{base}"] = str(v) if v else ""

    # ── NEM: flag for main() to push after df is available ──
    st.session_state["_pending_nem_push"] = True


def patient_inputs():
    patient_names_df = fetch_patient_names()
    patient_names = patient_names_df["patient_name"].tolist() if not patient_names_df.empty else []

    defaults = {
        "patient_data": {}, "nem_prescriptions": [], "therapieplan_data": {},
        "ernaehrung_data": {}, "infusion_data": {}, "last_loaded_patient": None,
        "just_loaded_patient": False, "current_patient_input": "",
        "clicked_suggestion": None, "display_patient_name": "",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

    # ── Patient header: title + dropdown selector side by side ──
    hdr_col, dd_col = st.columns([2, 2])
    with hdr_col:
        st.markdown("#### Patientendaten")
    with dd_col:
        dd_options = ["— Patient auswählen —"] + patient_names
        dd_key = "patient_dropdown_select"
        # Apply deferred dropdown resets (must happen before widget renders)
        if st.session_state.pop("_reset_dropdown", False):
            st.session_state[dd_key] = "— Patient auswählen —"
        if "_set_dropdown" in st.session_state:
            st.session_state[dd_key] = st.session_state.pop("_set_dropdown")
        # After first render Streamlit stores the selected string, not an int
        _stored = st.session_state.get(dd_key, "— Patient auswählen —")
        if isinstance(_stored, int):
            _dd_idx = min(_stored, len(dd_options) - 1)
        elif isinstance(_stored, str) and _stored in dd_options:
            _dd_idx = dd_options.index(_stored)
        else:
            _dd_idx = 0
        sel_idx = st.selectbox("", dd_options, index=_dd_idx,
            key=dd_key, label_visibility="collapsed")
        if sel_idx and sel_idx != "— Patient auswählen —" and sel_idx != st.session_state.get("last_loaded_patient"):
            st.session_state.clicked_suggestion = sel_idx

    # ── Load patient (from dropdown or suggestion button) ──
    if st.session_state.clicked_suggestion:
        name   = st.session_state.clicked_suggestion
        result = load_patient_data(name)
        if result[0]:
            _apply_patient_to_session(*result, name)
        st.session_state.clicked_suggestion = None
        st.rerun()

    display_value = (st.session_state.display_patient_name
                     if st.session_state.display_patient_name
                     else st.session_state.patient_data.get("patient", ""))

    typed = st.text_input(
        "Name eingeben (Enter für Vorschläge) oder oben aus Dropdown wählen:",
        value=display_value, placeholder="Vor- und Nachname",
    )

    if typed != st.session_state.current_patient_input:
        st.session_state.current_patient_input = typed
        if (st.session_state.last_loaded_patient and typed and typed not in patient_names):
            for k in ["patient_data","nem_prescriptions","therapieplan_data","ernaehrung_data","infusion_data"]:
                st.session_state[k] = {} if k != "nem_prescriptions" else []
            st.session_state.last_loaded_patient = None
            st.session_state.display_patient_name = ""
            st.session_state.just_loaded_patient = False
            st.rerun()

    st.session_state.display_patient_name = typed

    # Vorschläge: show matching buttons when typing
    if typed and typed not in patient_names and not st.session_state.just_loaded_patient:
        suggestions = [n for n in patient_names if typed.lower() in n.lower()]
        if suggestions:
            st.markdown("**Vorschläge:**")
            cols = st.columns(min(len(suggestions), 3))
            for i, name in enumerate(suggestions[:9]):
                with cols[i % 3]:
                    if st.button(name, key=f"suggest_{name}", use_container_width=True):
                        st.session_state.clicked_suggestion = name
                        st.rerun()

    # Auto-load when exact name is typed
    if (typed and typed in patient_names
            and typed != st.session_state.last_loaded_patient
            and not st.session_state.just_loaded_patient):
        result = load_patient_data(typed)
        if result[0]:
            _apply_patient_to_session(*result, typed)
        st.rerun()

    if st.session_state.just_loaded_patient:
        st.session_state.just_loaded_patient = False

    pdata = st.session_state.patient_data or {}

    def parse_date(v):
        if isinstance(v, str):
            try: return date.fromisoformat(v)
            except: return date.today()
        return v if isinstance(v, date) else date.today()

    default_geburtsdatum   = parse_date(pdata.get("geburtsdatum", date.today()))
    default_geschlecht     = pdata.get("geschlecht", "M")
    default_groesse        = int(pdata.get("groesse", 0)) if pdata.get("groesse") else 0
    default_gewicht        = int(pdata.get("gewicht", 0)) if pdata.get("gewicht") else 0
    default_therapiebeginn = parse_date(pdata.get("therapiebeginn", date.today()))
    dauer_value            = pdata.get("dauer", 6)
    try:    default_dauer_value = int(dauer_value)
    except: default_dauer_value = 6
    default_tw_besprochen  = pdata.get("tw_besprochen", "Ja")
    default_allergie       = pdata.get("allergie", "")
    default_diagnosen      = pdata.get("diagnosen", "")
    default_kt4            = pdata.get("kontrolltermin_4", False)
    default_kt12           = pdata.get("kontrolltermin_12", False)
    default_kt24           = pdata.get("kontrolltermin_24", False)
    default_kt_kommentar   = pdata.get("kontrolltermin_kommentar", "")

    c1,c2,c3,c4,c5,c6,c7 = st.columns(7)
    with c1:
        geburtsdatum = st.date_input("Geburtsdatum", value=default_geburtsdatum,
            min_value=date(1900,1,1), max_value=date.today(), format="DD.MM.YYYY", key="geburtsdatum_input")
    with c2:
        geschlecht = st.radio("Geschlecht", ["M","W"], horizontal=True,
            index=0 if default_geschlecht=="M" else 1, key="geschlecht_input")
    with c3:
        groesse = st.number_input("Grösse (cm)", min_value=0, value=default_groesse, key="groesse_input")
    with c4:
        gewicht = st.number_input("Gewicht (kg)", min_value=0, value=default_gewicht, key="gewicht_input")
    with c5:
        therapiebeginn = st.date_input("Therapiebeginn", value=default_therapiebeginn,
            format="DD.MM.YYYY", key="therapiebeginn_input")
    with c6:
        dauer = st.selectbox("Dauer (Monate)", list(range(1,13)),
            index=default_dauer_value-1 if 1<=default_dauer_value<=12 else 5, key="dauer_input")
    with c7:
        tw_besprochen = st.radio("TW besprochen?", ["Ja","Nein"], horizontal=True,
            index=0 if default_tw_besprochen=="Ja" else 1, key="tw_besprochen_input")

    bekannte_allergie = st.text_area("Bekannte Allergien", value=default_allergie, height=90,
        placeholder="Bekannte Allergien eintragen...", key="allergie_input")
    diagnosen = st.text_area("Diagnosen", value=default_diagnosen, height=160,
        placeholder="Relevante Diagnosen...", key="diagnosen_input")

    st.markdown("---")
    st.markdown("#### Kontrolltermine")
    col1,col2,col3 = st.columns(3)
    with col1: kontrolltermin_4  = st.checkbox("4 Wochen",  value=default_kt4,  key="kontrolltermin_4_input")
    with col2: kontrolltermin_12 = st.checkbox("12 Wochen", value=default_kt12, key="kontrolltermin_12_input")
    with col3: kontrolltermin_24 = st.checkbox("24 Monate", value=default_kt24, key="kontrolltermin_24_input")
    kontrolltermin_kommentar = st.text_area("Kommentar:", value=default_kt_kommentar, height=100,
        placeholder="Kommentar zu Kontrollterminen...", key="kontrolltermin_kommentar_input")

    # Editable Kontrolltermin dates (shown only when checked)
    kt4_date = kt12_date = kt24_date = None
    if kontrolltermin_4 or kontrolltermin_12 or kontrolltermin_24:
        kd1, kd2, kd3 = st.columns(3)
        if kontrolltermin_4:
            def_kt4d = parse_date(pdata.get("kt4_date", (therapiebeginn + timedelta(weeks=4)).isoformat()))
            with kd1:
                kt4_date = st.date_input("Datum 4 Wochen", value=def_kt4d,
                    format="DD.MM.YYYY", key="kt4_date_input")
        if kontrolltermin_12:
            def_kt12d = parse_date(pdata.get("kt12_date", (therapiebeginn + timedelta(weeks=12)).isoformat()))
            with kd2:
                kt12_date = st.date_input("Datum 12 Wochen", value=def_kt12d,
                    format="DD.MM.YYYY", key="kt12_date_input")
        if kontrolltermin_24:
            def_kt24d = parse_date(pdata.get("kt24_date", (therapiebeginn + timedelta(weeks=96)).isoformat()))
            with kd3:
                kt24_date = st.date_input("Datum 24 Monate", value=def_kt24d,
                    format="DD.MM.YYYY", key="kt24_date_input")

    st.markdown("---")
    therapy_progress_bar(
        therapiebeginn, dauer,
        kt4=kontrolltermin_4, kt12=kontrolltermin_12, kt24=kontrolltermin_24,
        kt4_date=kt4_date, kt12_date=kt12_date, kt24_date=kt24_date,
    )

    return {
        "patient": typed, "geburtsdatum": geburtsdatum, "geschlecht": geschlecht,
        "groesse": groesse, "gewicht": gewicht, "therapiebeginn": therapiebeginn,
        "dauer": dauer, "tw_besprochen": tw_besprochen, "allergie": bekannte_allergie,
        "diagnosen": diagnosen, "kontrolltermin_4": kontrolltermin_4,
        "kontrolltermin_12": kontrolltermin_12, "kontrolltermin_24": kontrolltermin_24,
        "kontrolltermin_kommentar": kontrolltermin_kommentar,
        "kt4_date": kt4_date, "kt12_date": kt12_date, "kt24_date": kt24_date,
    }


# =========================================================
# MAIN
# =========================================================
def main():
    df = fetch_supplements()

    if st.session_state.get('just_loaded_patient', False):
        st.session_state.just_loaded_patient = False

    # ── Full wipe after delete: runs BEFORE patient_inputs() ───────────
    if st.session_state.get("_do_full_wipe"):
        # Wipe everything — only keep the reset dropdown flag
        keys_to_del = [k for k in list(st.session_state.keys())
                       if k != "_reset_dropdown"]
        for k in keys_to_del:
            del st.session_state[k]
        # Set all clean defaults
        st.session_state.update({
            "patient_data": {}, "nem_prescriptions": [],
            "therapieplan_data": {}, "ernaehrung_data": {}, "infusion_data": {},
            "last_loaded_patient": None, "display_patient_name": "",
            "current_patient_input": "", "just_loaded_patient": False,
            "clicked_suggestion": None, "show_delete_confirmation": False,
            "show_save_success": False, "auto_download_pdf": None,
            "nem_pdf_bytes": None, "category_states": {},
            "_just_saved_patient": "", "_reset_dropdown": True,
        })
        st.rerun()

    patient = patient_inputs()

    # ── Push NEM prescription values into widget keys after patient load ──
    if st.session_state.pop("_pending_nem_push", False):
        for presc in (st.session_state.nem_prescriptions or []):
            s_name = presc.get("name","")
            match = df[df["name"] == s_name]
            if match.empty: continue
            row_id = match.iloc[0]["id"]
            # Force-set widget keys so they display loaded values on next render
            st.session_state[f"{row_id}_gesamt_dosierung"]  = presc.get("Gesamt-dosierung","")
            st.session_state[f"{row_id}_darreichungsform"]  = presc.get("Darreichungsform", DEFAULT_FORMS.get(s_name,"Kapseln"))
            st.session_state[f"{row_id}_pro_Einnahme"]      = presc.get("Pro Einnahme","")
            st.session_state[f"{row_id}_Nuechtern"]         = presc.get("Nüchtern","")
            st.session_state[f"{row_id}_Morgens"]           = presc.get("Morgens","")
            st.session_state[f"{row_id}_Mittags"]           = presc.get("Mittags","")
            st.session_state[f"{row_id}_Abends"]            = presc.get("Abends","")
            st.session_state[f"{row_id}_Nachts"]            = presc.get("Nachts","")
            st.session_state[f"{row_id}_comment"]           = presc.get("Kommentar","")

    for _, row in df.iterrows():
        override_key = f"gesamt_dosierung_override_{row['id']}"
        if override_key not in st.session_state:
            st.session_state[override_key] = None

    for k in ['show_delete_confirmation','show_save_success']:
        if k not in st.session_state:
            st.session_state[k] = False
    if 'auto_download_pdf' not in st.session_state:
        st.session_state.auto_download_pdf = None
    if 'nem_pdf_bytes' not in st.session_state:
        st.session_state.nem_pdf_bytes = None

    patient_names_df = fetch_patient_names()
    patient_names = patient_names_df["patient_name"].tolist() if not patient_names_df.empty else []
    # Also treat as saved if we just saved this patient (DB list may be stale)
    _just_saved = st.session_state.get("_just_saved_patient", "")
    is_saved_patient = bool(
        patient["patient"] and (
            patient["patient"] in patient_names or
            patient["patient"] == _just_saved
        )
    )

    # ── Action buttons row ──────────────────────────────────────────────────
    _btn_cols = st.columns([1, 1, 6])
    with _btn_cols[0]:
        save_button = st.button("💾 Speichern", key="save_btn_main", use_container_width=True)
    with _btn_cols[1]:
        if is_saved_patient:
            if st.button("🗑 Löschen", key="del_btn_main", use_container_width=True):
                st.session_state.show_delete_confirmation = True

    delete_button = False  # legacy compat

    if st.session_state.get("show_save_success", False):
        st.markdown('<div class="success-message">✅ Alle Daten wurden erfolgreich gespeichert!</div>', unsafe_allow_html=True)
        time.sleep(3)
        st.session_state.show_save_success = False
        st.rerun()

    if st.session_state.get("show_delete_confirmation", False):
        st.markdown("---")
        st.warning("⚠️ **ACHTUNG: Dieser Vorgang kann nicht rückgängig gemacht werden!**")
        st.error(f"Das Löschen wird alle Daten für Patient '{patient['patient']}' unwiderruflich entfernen.")
        cc1, cc2 = st.columns(2)
        with cc1:
            if st.button("Ja, endgültig löschen", use_container_width=True, key="confirm_delete"):
                if delete_patient_data(patient["patient"]):
                    # DB deleted. Now wipe session state via two-pass flag.
                    st.session_state["_do_full_wipe"] = True
                    st.rerun()
                else:
                    st.error("Fehler beim Löschen — prüfen Sie die Konsole.")
        with cc2:
            if st.button("Abbrechen", use_container_width=True, key="cancel_delete"):
                st.session_state.show_delete_confirmation = False
                st.info("Löschen abgebrochen")
                st.rerun()

    st.markdown("---")
    tabs = st.tabs(["Therapieplan", "Nahrungsergänzungsmittel (NEM)", "Infusionstherapie"])

    # =========================================================
    # TAB 0: THERAPIEPLAN
    # Left side: exact Doc3 content unchanged.
    # Each checkbox row wrapped in st.columns(ROW_COLS) so timing
    # inputs appear inline on the same row — no separate right panel.
    # =========================================================
    with tabs[0]:
        tp = st.session_state.therapieplan_data
        therapieplan_schedule_data = {}

        def _row(label, cb_key, cb_val, slug, kp):
            cols = st.columns(ROW_COLS)
            with cols[0]:
                checked = st.checkbox(label, value=cb_val, key=cb_key)
            therapieplan_schedule_data.update(
                _inline_timing(checked, slug, patient["therapiebeginn"], patient["dauer"], kp, tp, cols))
            return checked

        # ---- SECTION 1: Diagnostik & Überprüfung ----
        with st.expander("Diagnostik & Überprüfung", expanded=tp.get("_sec_diagnostik_open", True)):
            _sched_header()
            st.markdown('<div class="section-subheader">Zähne</div>', unsafe_allow_html=True)
            zaehne = _row(
                "Überprüfung der Zähne/Kieferknochen mittels OPG (Panoramaaufnahme mit lachendem Gebiss) / DVT",
                "zaehne_checkbox", tp.get("zaehne", False), "zaehne", "diag")
            zaehne_zu_pruefen = ""
            if zaehne:
                zaehne_zu_pruefen = st.text_input("Zähne zu überprüfen (OPG/DVT):",
                    value=tp.get("zaehne_zu_pruefen", ""), key="zaehne_zu_pruefen_input")

            st.markdown('<div class="section-subheader">Bewegungsapparat & Schwermetalltest</div>', unsafe_allow_html=True)
            analyse_bewegungsapparat = _row("Analyse Bewegungsapparat (Martin)",
                "analyse_bewegungsapparat_checkbox", tp.get("analyse_bewegungsapparat", False),
                "analyse_bewegungsapparat", "diag")
            schwermetalltest_tp = _row("Schwermetalltest mit DMSA und Ca EDTA",
                "schwermetalltest_tp_checkbox", tp.get("schwermetalltest_tp", False),
                "schwermetalltest_tp", "diag")

            st.markdown('<div class="section-subheader">Labor & Diagnostik</div>', unsafe_allow_html=True)

            def _text_timing(label, key_input, key_slug, kp):
                """Checkbox + text input on left (same row), timing on right."""
                cb_key = key_input + "_cb"
                cols = st.columns(ROW_COLS)
                with cols[0]:
                    r1, r2 = st.columns([2.0, 2.0])
                    with r1: checked = st.checkbox(label, value=tp.get(cb_key, False), key=cb_key)
                    with r2: val = st.text_input("", value=tp.get(key_input, ""),
                        key=key_input + "_input", placeholder="Details...",
                        label_visibility="collapsed", disabled=not checked)
                therapieplan_schedule_data.update(
                    _inline_timing(checked, key_slug, patient["therapiebeginn"], patient["dauer"], kp, tp, cols))
                # save both checkbox and text value
                tp[cb_key] = checked
                return val if checked else ""

            lab_imd       = _text_timing("IMD:",          "lab_imd",       "lab_imd",       "diag")
            lab_mmd       = _text_timing("MMD:",          "lab_mmd",       "lab_mmd",       "diag")
            lab_nextgen   = _text_timing("NextGen Onco:", "lab_nextgen",   "lab_nextgen",   "diag")
            lab_sonstiges = _text_timing("Sonstiges:",    "lab_sonstiges", "lab_sonstiges", "diag")
            _extra_rows("diag", "diag", tp, patient["therapiebeginn"], patient["dauer"], therapieplan_schedule_data)

        # ---- SECTION 2: Haupttherapien ----
        with st.expander("Haupttherapien", expanded=tp.get("_sec_haupttherapien_open", False)):
            _sched_header()
            st.markdown('<div class="section-subheader">Darm & Entgiftung</div>', unsafe_allow_html=True)
            darm_biofilm = _row(
                "Darm - Biofilmentfernung nach www.regenbogenkreis.de (Express-Darmkur 4 Tageskur)",
                "darm_biofilm_checkbox", tp.get("darm_biofilm", False), "darm_biofilm", "haupt")
            darmsanierung = _row("Darmsanierung nach Paracelsus Klinik (Rezept von Praxis)",
                "darmsanierung_checkbox", tp.get("darmsanierung", False), "darmsanierung", "haupt")
            darmsanierung_dauer = []
            if darmsanierung:
                darmsanierung_dauer = st.multiselect("Darmsanierung Dauer:", ["4 Wo","6 Wo","8 Wo"],
                    default=tp.get("darmsanierung_dauer", []), key="darmsanierung_dauer_select")
            hydrocolon = _row(
                "mit Hydrocolon (Darmspülung) 2x insgesamt, Abstand 14 Tage mit Rekolonisierungs-Shot",
                "hydrocolon_checkbox", tp.get("hydrocolon", False), "hydrocolon", "haupt")
            parasiten = _row("Parasitenbehandlung mit Vermox (3 Tage)",
                "parasiten_checkbox", tp.get("parasiten", False), "parasiten", "haupt")
            parasiten_bio = _row("Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)",
                "parasiten_bio_checkbox", tp.get("parasiten_bio", False), "parasiten_bio", "haupt")
            leberdetox = _row("Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5x alle 4–6 Wochen)",
                "leberdetox_checkbox", tp.get("leberdetox", False), "leberdetox", "haupt")
            nierenprogramm = _row("Nierenprogramm nach Dr. Clark – 4 Wochen",
                "nierenprogramm_checkbox", tp.get("nierenprogramm", False), "nierenprogramm", "haupt")
            mikronaehrstoffe = _row("Einnahme Mikronährstoffen (NEM-Verordnung) (siehe separate PDF)",
                "mikronaehrstoffe_checkbox", tp.get("mikronaehrstoffe", False), "mikronaehrstoffe", "haupt")
            infusionsbehandlung = _row("Infusionstherapie (siehe separate PDF)",
                "infusionsbehandlung_checkbox", tp.get("infusionsbehandlung", False), "infusionsbehandlung", "haupt")
            neuraltherapie = _row("Neuraltherapie",
                "neuraltherapie_checkbox", tp.get("neuraltherapie", False), "neuraltherapie", "haupt")
            eigenblut = _row("Eigenbluttherapie",
                "eigenblut_checkbox", tp.get("eigenblut", False), "eigenblut", "haupt")
            ozontherapie = _row("Ozontherapie",
                "ozontherapie_checkbox", tp.get("ozontherapie", False), "ozontherapie", "haupt")

            st.markdown('<div class="section-subheader">Ausleitung & Infektionen</div>', unsafe_allow_html=True)
            ausleitung_inf = _row("Schwermetallausleitung Infusion (siehe separate Infusion PDF)",
                "ausleitung_inf_checkbox", tp.get("ausleitung_inf", False), "ausleitung_inf", "haupt")
            ausleitung_oral = _row("Schwermetallausleitung oral",
                "ausleitung_oral_checkbox", tp.get("ausleitung_oral", False), "ausleitung_oral", "haupt")
            # Checkbox rows with free-text detail field (label visible, checkbox prescribes it)
            def _cb_text_row(label, cb_key, text_key, cb_val, text_val, slug, kp):
                cols = st.columns(ROW_COLS)
                with cols[0]:
                    r1, r2 = st.columns([2.0, 2.0])
                    with r1: checked = st.checkbox(label, value=cb_val, key=cb_key)
                    with r2: txt = st.text_input("", value=text_val, key=text_key+"_txt",
                        placeholder="Details...", label_visibility="collapsed")
                therapieplan_schedule_data.update(
                    _inline_timing(checked, slug, patient["therapiebeginn"], patient["dauer"], kp, tp, cols))
                return checked, txt

            infektion_bakt, infektion_bakt_detail = _cb_text_row(
                "Infektionsbehandlung für Bakterien (Borr./Helicob.)",
                "infektion_bakt_cb", "infektion_bakt",
                tp.get("infektion_bakt_cb", False), tp.get("infektion_bakt", ""),
                "infektion_bakt", "haupt")
            infektion_virus, infektion_virus_detail = _cb_text_row(
                "Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona)",
                "infektion_virus_cb", "infektion_virus",
                tp.get("infektion_virus_cb", False), tp.get("infektion_virus", ""),
                "infektion_virus", "haupt")
            medikamente_text, medikamente_text_detail = _cb_text_row(
                "Medikamentenverordnung - Rezept für",
                "medikamente_text_cb", "medikamente_text",
                tp.get("medikamente_text_cb", False), tp.get("medikamente_text", ""),
                "medikamente_text", "haupt")
            _extra_rows("haupt", "haupt", tp, patient["therapiebeginn"], patient["dauer"], therapieplan_schedule_data)

        # ---- SECTION 3: Biologische & Komplementäre Therapien ----
        with st.expander("Biologische & Komplementäre Therapien", expanded=tp.get("_sec_bio_open", False)):
            _sched_header()
            bio_isopath = _row("Biologische Isopathische Therapie",
                "bio_isopath_checkbox", tp.get("bio_isopath", False), "bio_isopath", "bio")
            akupunktur = _row("Akupunktur",
                "akupunktur_checkbox", tp.get("akupunktur", False), "akupunktur", "bio")
            homoeopathie = _row("Homöopathie (Anna)",
                "homoeopathie_checkbox", tp.get("homoeopathie", False), "homoeopathie", "bio")
            bioresonanz = _row("Bioresonanz (Anna)",
                "bioresonanz_checkbox", tp.get("bioresonanz", False), "bioresonanz", "bio")
            timewaver_freq = _row("TimeWaver Frequency Behandlung",
                "timewaver_freq_checkbox", tp.get("timewaver_freq", False), "timewaver_freq", "bio")

            st.markdown('<div class="section-subheader">Hypnosetherapie</div>', unsafe_allow_html=True)
            hypnose = _row("Hypnosetherapie",
                "hypnose_checkbox", tp.get("hypnose", False), "hypnose", "bio")
            # Noreen / Martin / Miro compact on left, Hypnose Typ wide on right
            hc1, hc2, hc3, hc4, hc5 = st.columns([0.7, 0.7, 0.7, 0.3, 2.6])
            with hc1: hypnose_noreen = st.checkbox("Noreen", value=tp.get("hypnose_noreen", False), key="hypnose_noreen_checkbox")
            with hc2: hypnose_martin = st.checkbox("Martin", value=tp.get("hypnose_martin", False), key="hypnose_martin_checkbox")
            with hc3: hypnose_miro   = st.checkbox("Miro",   value=tp.get("hypnose_miro",   False), key="hypnose_miro_checkbox")
            with hc4: st.markdown("<div style='padding-top:8px;font-size:14px;white-space:nowrap;'>Typ:</div>", unsafe_allow_html=True)
            with hc5: hypnose_typ = st.text_input("", key="hypnose_typ_input", placeholder="Hypnose Typ...",
                    label_visibility="collapsed", value=tp.get("hypnose_typ", ""))
            yager = _row("Yagertherapie", "yager_checkbox", tp.get("yager", False), "yager", "bio")
            energie_behandlungen = _row("Energiebehandlungen bei Marie",
                "energie_behandlungen_checkbox", tp.get("energie_behandlungen", False), "energie_behandlungen", "bio")

            st.markdown('<div class="section-subheader">Ernährung & Bewegung</div>', unsafe_allow_html=True)

            def tight_row(label, key_cb, key_input, cb_val, input_val):
                cols = st.columns(ROW_COLS)
                with cols[0]:
                    r1, r2 = st.columns([2.0, 2.0])
                    with r1: val = st.checkbox(label, value=cb_val, key=key_cb)
                    with r2: txt = st.text_input("", key=key_input, value=input_val,
                                                  placeholder="Kommentar...", label_visibility="collapsed")
                therapieplan_schedule_data.update(
                    _inline_timing(val, key_cb, patient["therapiebeginn"], patient["dauer"], "bio", tp, cols))
                return val, txt

            atemtherapie, atemtherapie_comment = tight_row("Atemtherapie", "atemtherapie", "atemtherapie_comment",
                tp.get("atemtherapie", False), tp.get("atemtherapie_comment", ""))
            bewegung, bewegung_comment = tight_row("Bewegung", "bewegung", "bewegung_comment",
                tp.get("bewegung", False), tp.get("bewegung_comment", ""))
            ernaehrung, ernaehrung_comment = tight_row("Ernährungsberatung", "ernaehrung", "ernaehrung_comment",
                tp.get("ernaehrung", False), tp.get("ernaehrung_comment", ""))

            # Ästhetische Behandlung — inline timing + comment (2:2 split) + sub-checkboxes
            aet_cols = st.columns(ROW_COLS)
            with aet_cols[0]:
                ac1, ac2 = st.columns([2.0, 2.0])
                with ac1: aethetisch = st.checkbox("Ästhetische Behandlung",
                    value=tp.get("aethetisch", False), key="aethetisch_checkbox")
                with ac2: aethetisch_comment = st.text_input("", key="aethetisch_comment_input",
                    value=tp.get("aethetisch_comment", ""), placeholder="Kommentar...", label_visibility="collapsed")
            therapieplan_schedule_data.update(
                _inline_timing(aethetisch, "aethetisch", patient["therapiebeginn"], patient["dauer"], "bio", tp, aet_cols))
            # Behandlungsart always visible (not conditional on checkbox)
            st.markdown('<span style="font-size:13px;color:#555;">Behandlungsart:</span>', unsafe_allow_html=True)
            c1,c2,c3,c4 = st.columns(4)
            with c1: aethetisch_botox    = st.checkbox("Botox",   value=tp.get("aethetisch_botox", False),    key="aethetisch_botox_checkbox",    disabled=not aethetisch)
            with c2: aethetisch_prp      = st.checkbox("PRP",     value=tp.get("aethetisch_prp", False),      key="aethetisch_prp_checkbox",      disabled=not aethetisch)
            with c3: aethetisch_faeden   = st.checkbox("Fäden",   value=tp.get("aethetisch_faeden", False),   key="aethetisch_faeden_checkbox",   disabled=not aethetisch)
            with c4: aethetisch_hyaloron = st.checkbox("Hyaloron",value=tp.get("aethetisch_hyaloron", False), key="aethetisch_hyaloron_checkbox", disabled=not aethetisch)

            # Low Carb + all sub-checkboxes (including Nährstoffmängel + Sonstiges)
            lowcarb, lowcarb_comment = tight_row("Low Carb Ernährung", "lowcarb", "lowcarb_comment",
                tp.get("lowcarb", False), tp.get("lowcarb_comment", ""))

            def sub_tight_row(label, key_cb, key_input, cb_val, input_val):
                """Sub-checkbox of Low Carb — indented, disabled when Low Carb unchecked."""
                cols = st.columns(ROW_COLS)
                with cols[0]:
                    sub_c1, sub_c2 = st.columns([0.06, 0.94])
                    with sub_c2:
                        r1, r2 = st.columns([2.0, 2.0])
                        with r1: val = st.checkbox(label, value=cb_val, key=key_cb, disabled=not lowcarb)
                        with r2: txt = st.text_input("", key=key_input, value=input_val,
                                                      placeholder="Kommentar...", label_visibility="collapsed",
                                                      disabled=not lowcarb)
                therapieplan_schedule_data.update(
                    _inline_timing(val and lowcarb, key_cb, patient["therapiebeginn"], patient["dauer"], "bio", tp, cols))
                return val, txt

            def sub_text_timing(label, key_cb, key_input, key_slug, cb_val, input_val):
                """Checkbox + text-input sub-item of Low Carb — disabled when Low Carb unchecked."""
                cols = st.columns(ROW_COLS)
                with cols[0]:
                    sub_c1, sub_c2 = st.columns([0.06, 0.94])
                    with sub_c2:
                        r1, r2 = st.columns([2.0, 2.0])
                        with r1: checked = st.checkbox(label, value=cb_val, key=key_cb, disabled=not lowcarb)
                        with r2: val = st.text_input("", value=input_val,
                            key=key_input + "_input", placeholder="Kommentar...",
                            label_visibility="collapsed", disabled=not lowcarb)
                therapieplan_schedule_data.update(
                    _inline_timing(checked and lowcarb, key_slug, patient["therapiebeginn"], patient["dauer"], "bio", tp, cols))
                return checked, val

            st.markdown('<div style="border-left:2px solid rgba(38,96,65,0.25);margin-left:10px;padding-left:6px;">', unsafe_allow_html=True)
            fasten, fasten_comment = sub_tight_row("Intermittierendes Fasten", "fasten", "fasten_comment",
                tp.get("fasten", False), tp.get("fasten_comment", ""))
            krebsdiaet, krebsdiaet_comment = sub_tight_row("Krebs Diät", "krebsdiaet", "krebsdiaet_comment",
                tp.get("krebsdiaet", False), tp.get("krebsdiaet_comment", ""))
            ketogene, ketogene_comment = sub_tight_row("Ketogene Ernährung", "ketogene", "ketogene_comment",
                tp.get("ketogene", False), tp.get("ketogene_comment", ""))
            basisch, basisch_comment = sub_tight_row("Basische Ernährung", "basisch", "basisch_comment",
                tp.get("basisch", False), tp.get("basisch_comment", ""))
            naehrstoff_ausgleich, naehrstoff_ausgleich_comment = sub_text_timing(
                "Nährstoffmängel ausgleichen:", "naehrstoff_ausgleich_cb", "naehrstoff_ausgleich", "naehrstoff_ausgleich",
                tp.get("naehrstoff_ausgleich_cb", False), tp.get("naehrstoff_ausgleich", ""))
            therapie_sonstiges, therapie_sonstiges_comment = sub_text_timing(
                "Sonstiges:", "therapie_sonstiges_cb", "therapie_sonstiges", "therapie_sonstiges",
                tp.get("therapie_sonstiges_cb", False), tp.get("therapie_sonstiges", ""))
            st.markdown('</div>', unsafe_allow_html=True)
            _extra_rows("bio", "bio", tp, patient["therapiebeginn"], patient["dauer"], therapieplan_schedule_data)

        # ---- SECTION 4: Gespräche ----
        with st.expander("Gespräche", expanded=tp.get("_sec_gespraeche_open", False)):
            _sched_header()
            zwischengespraech_4 = _row("Zwischengespräch nach 4 Wochen (1/2h)",
                "zwischengespraech_4_checkbox", tp.get("zwischengespraech_4", False),
                "zwischengespraech_4", "gesp")
            zwischengespraech_8 = _row("Zwischengespräch nach weiteren 8 Wochen (1/2h)",
                "zwischengespraech_8_checkbox", tp.get("zwischengespraech_8", False),
                "zwischengespraech_8", "gesp")
            _extra_rows("gesp", "gesp", tp, patient["therapiebeginn"], patient["dauer"], therapieplan_schedule_data)

        # Update session state
        new_tp = {
            "zaehne": zaehne, "zaehne_zu_pruefen": zaehne_zu_pruefen,
            "analyse_bewegungsapparat": analyse_bewegungsapparat,
            "schwermetalltest_tp": schwermetalltest_tp,
            "lab_imd": lab_imd, "lab_mmd": lab_mmd, "lab_nextgen": lab_nextgen, "lab_sonstiges": lab_sonstiges,
            "darm_biofilm": darm_biofilm, "darmsanierung": darmsanierung, "darmsanierung_dauer": darmsanierung_dauer,
            "hydrocolon": hydrocolon, "parasiten": parasiten, "parasiten_bio": parasiten_bio,
            "leberdetox": leberdetox, "nierenprogramm": nierenprogramm,
            "ausleitung_inf": ausleitung_inf, "ausleitung_oral": ausleitung_oral,
            "infektion_bakt_cb": infektion_bakt, "infektion_bakt": infektion_bakt_detail,
            "infektion_virus_cb": infektion_virus, "infektion_virus": infektion_virus_detail,
            "medikamente_text_cb": medikamente_text, "medikamente_text": medikamente_text_detail,
            "mikronaehrstoffe": mikronaehrstoffe, "infusionsbehandlung": infusionsbehandlung,
            "neuraltherapie": neuraltherapie, "eigenblut": eigenblut, "ozontherapie": ozontherapie,
            "bio_isopath": bio_isopath, "akupunktur": akupunktur, "homoeopathie": homoeopathie,
            "bioresonanz": bioresonanz, "timewaver_freq": timewaver_freq,
            "hypnose": hypnose, "hypnose_noreen": hypnose_noreen, "hypnose_martin": hypnose_martin,
            "hypnose_miro": hypnose_miro, "hypnose_typ": hypnose_typ,
            "yager": yager, "energie_behandlungen": energie_behandlungen,
            "atemtherapie": atemtherapie, "atemtherapie_comment": atemtherapie_comment,
            "bewegung": bewegung, "bewegung_comment": bewegung_comment,
            "ernaehrung": ernaehrung, "ernaehrung_comment": ernaehrung_comment,
            "lowcarb": lowcarb, "lowcarb_comment": lowcarb_comment,
            "fasten": fasten, "fasten_comment": fasten_comment,
            "krebsdiaet": krebsdiaet, "krebsdiaet_comment": krebsdiaet_comment,
            "ketogene": ketogene, "ketogene_comment": ketogene_comment,
            "basisch": basisch, "basisch_comment": basisch_comment,
            "naehrstoff_ausgleich_cb": naehrstoff_ausgleich, "naehrstoff_ausgleich": naehrstoff_ausgleich_comment,
            "therapie_sonstiges_cb": therapie_sonstiges, "therapie_sonstiges": therapie_sonstiges_comment,
            "aethetisch": aethetisch, "aethetisch_botox": aethetisch_botox,
            "aethetisch_prp": aethetisch_prp, "aethetisch_faeden": aethetisch_faeden,
            "aethetisch_hyaloron": aethetisch_hyaloron, "aethetisch_comment": aethetisch_comment,
            "zwischengespraech_4": zwischengespraech_4, "zwischengespraech_8": zwischengespraech_8,
        }
        new_tp.update(therapieplan_schedule_data)
        st.session_state.therapieplan_data = new_tp

        if st.button("Therapieplan PDF generieren", key="therapieplan_pdf_button"):
            pdf_bytes = generate_pdf(patient, st.session_state.therapieplan_data, "THERAPIEPLAN")
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf",
                "mime": "application/pdf"
            }
            st.rerun()

    # =========================================================
    # TAB 1: NEM
    # =========================================================
    with tabs[1]:
        nem_container = st.container()
        with nem_container:
            if 'nem_form_initialized' not in st.session_state:
                st.session_state.nem_form_initialized = True
            if 'category_states' not in st.session_state:
                st.session_state.category_states = {}

            # No st.form wrapper — widgets update immediately, enabling
            # save-on-demand without requiring form submission first.
            if "last_main_dauer" not in st.session_state:
                st.session_state.last_main_dauer = patient["dauer"]

            def get_pro_Einnahme_options(df_form):
                    if not df_form: return [""]
                    f = df_form.lower()
                    if any(x in f for x in ["kapsel","tablette","pflaster"]):
                        return ["","1","2","3","4","5","6","7","8","9","10","½","¼","¾","1½","2½"]
                    elif any(x in f for x in ["tropfen","lösung","flüssig","öl","spray","creme","gel"]):
                        return ["","1","2","3","4","5","6","7","8","9","10","½","¼","¾","1½","2½","Tr","ML"]
                    elif any(x in f for x in ["pulver","sachet"]):
                        return ["","1","2","3","4","5","6","7","8","9","10","½","¼","¾","1½","2½","g","mg","EL","TL","ML"]
                    elif "tee" in f:
                        return ["","1","2","3","4","5","Beutel","TL","EL"]
                    return ["","1","2","3","4","5","6","7","8","9","10","½","¼","¾","1½","2½","g","mg","EL","TL","ML","Tr"]

            st.markdown('<div class="sticky-header">', unsafe_allow_html=True)
            header_cols = st.columns([2.3, 0.8, 1.2, 0.7, 0.7, 0.7, 0.7, 0.7, 0.7, 2])
            for col, text in zip(header_cols, ["Supplement","Gesamt-dosierung","Darreichungsform","Pro Einnahme","Nüchtern","Morgens","Mittags","Abends","Nachts","Kommentar"]):
                col.markdown(f"**{text}**")
            st.markdown('</div>', unsafe_allow_html=True)

            scroll_container = st.container(height=600, border=True)
            with scroll_container:
                all_supplements_data = []
                categories = {}
                current_category_name = None

                for _, row in df.iterrows():
                    if row["id"].startswith("CAT"):
                        current_category_name = row["name"].replace("CATEGORY: ", "")
                        categories[current_category_name] = []
                    elif current_category_name:
                        categories[current_category_name].append(row)

                for category_name, supplement_rows in categories.items():
                    if not supplement_rows: continue
                    if category_name not in st.session_state.category_states:
                        st.session_state.category_states[category_name] = False

                    with st.expander(f" {category_name}", expanded=st.session_state.category_states[category_name]):
                        for row in supplement_rows:
                            cols = st.columns([2.2, 0.9, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])
                            supplement_name = row["name"]
                            cols[0].markdown(supplement_name)

                            # Resolve initial values: prefer widget session state (already set),
                            # then loaded prescription, then defaults.
                            # This is the correct priority for both fresh and loaded states.
                            gd_key   = f"{row['id']}_gesamt_dosierung"
                            form_key = f"{row['id']}_darreichungsform"
                            pe_key   = f"{row['id']}_pro_Einnahme"
                            nue_key  = f"{row['id']}_Nuechtern"
                            morg_key = f"{row['id']}_Morgens"
                            mitt_key = f"{row['id']}_Mittags"
                            abend_key= f"{row['id']}_Abends"
                            nacht_key= f"{row['id']}_Nachts"
                            com_key  = f"{row['id']}_comment"

                            loaded_prescription = None
                            for p in (st.session_state.nem_prescriptions or []):
                                if p.get("name") == supplement_name:
                                    loaded_prescription = p
                                    break

                            # If session state key doesn't exist yet, seed it from loaded data
                            if gd_key not in st.session_state and loaded_prescription:
                                st.session_state[gd_key]   = loaded_prescription.get("Gesamt-dosierung","")
                                st.session_state[form_key] = loaded_prescription.get("Darreichungsform", DEFAULT_FORMS.get(supplement_name,"Kapseln"))
                                st.session_state[pe_key]   = loaded_prescription.get("Pro Einnahme","")
                                st.session_state[nue_key]  = loaded_prescription.get("Nüchtern","")
                                st.session_state[morg_key] = loaded_prescription.get("Morgens","")
                                st.session_state[mitt_key] = loaded_prescription.get("Mittags","")
                                st.session_state[abend_key]= loaded_prescription.get("Abends","")
                                st.session_state[nacht_key]= loaded_prescription.get("Nachts","")
                                st.session_state[com_key]  = loaded_prescription.get("Kommentar","")

                            i_gd    = st.session_state.get(gd_key,    "")
                            i_form  = st.session_state.get(form_key,  DEFAULT_FORMS.get(supplement_name,"Kapseln"))
                            i_pe    = st.session_state.get(pe_key,    "")
                            i_nue   = st.session_state.get(nue_key,   "")
                            i_morg  = st.session_state.get(morg_key,  "")
                            i_mitt  = st.session_state.get(mitt_key,  "")
                            i_abend = st.session_state.get(abend_key, "")
                            i_nacht = st.session_state.get(nacht_key, "")
                            i_com   = st.session_state.get(com_key,   "")

                            gd_options = ["","1","2","3","4","5","6","7","8","9","10","12","14","16","18","20","22","24","26","28","30","35","40","45","50","60","70","80","90","100","120","150","180","200","250","300","400","500"]
                            gd_val = cols[1].selectbox("", gd_options,
                                index=gd_options.index(i_gd) if i_gd in gd_options else 0,
                                key=gd_key, label_visibility="collapsed", accept_new_options=True)

                            dosage_presets = ["Kapseln","Lösung","Tabletten","Pulver","Tropfen","Sachet","Öl","Spray","Creme","Gel","Flüssig","Tee","Pflaster"]
                            sel_form = cols[2].selectbox("", dosage_presets,
                                index=dosage_presets.index(i_form) if i_form in dosage_presets else 0,
                                key=form_key, label_visibility="collapsed", accept_new_options=True)

                            pe_options = get_pro_Einnahme_options(sel_form)
                            pe_val = cols[3].selectbox("", pe_options,
                                index=pe_options.index(i_pe) if i_pe in pe_options else 0,
                                key=pe_key, label_visibility="collapsed", accept_new_options=True)

                            dose_options = ["","1","2","3","4","5"]
                            nue_val  = cols[4].selectbox("", dose_options, index=dose_options.index(i_nue)   if i_nue   in dose_options else 0, key=nue_key,  label_visibility="collapsed")
                            morg_val = cols[5].selectbox("", dose_options, index=dose_options.index(i_morg)  if i_morg  in dose_options else 0, key=morg_key, label_visibility="collapsed")
                            mitt_val = cols[6].selectbox("", dose_options, index=dose_options.index(i_mitt)  if i_mitt  in dose_options else 0, key=mitt_key, label_visibility="collapsed")
                            abend_val= cols[7].selectbox("", dose_options, index=dose_options.index(i_abend) if i_abend in dose_options else 0, key=abend_key,label_visibility="collapsed")
                            nacht_val= cols[8].selectbox("", dose_options, index=dose_options.index(i_nacht) if i_nacht in dose_options else 0, key=nacht_key,label_visibility="collapsed")
                            comment  = cols[9].text_input("", key=com_key, placeholder="Kommentar", value=i_com or "", label_visibility="collapsed")

                            all_supplements_data.append({
                                "name": supplement_name, "Gesamt-dosierung": gd_val,
                                "Darreichungsform": sel_form, "Pro Einnahme": pe_val,
                                "Nüchtern": nue_val, "Morgens": morg_val, "Mittags": mitt_val,
                                "Abends": abend_val, "Nachts": nacht_val, "Kommentar": comment
                            })

            # Update nem_prescriptions every render (no form boundary)
            st.session_state.nem_prescriptions = all_supplements_data

            if st.button("NEM PDF generieren", key="nem_pdf_button"):
                pdf_submitted = True
            else:
                pdf_submitted = False

            if pdf_submitted:
                pass  # nem_prescriptions already updated above
                pdf_data = [p for p in all_supplements_data if (
                    any(p.get(f,"").strip() for f in ["Nüchtern","Morgens","Mittags","Abends","Nachts"])
                    or p.get("Gesamt-dosierung","").strip()
                    or p.get("Pro Einnahme","").strip()
                    or p.get("Kommentar","").strip()
                    or (p.get("Darreichungsform","") != DEFAULT_FORMS.get(p["name"],"Kapseln") and p.get("Darreichungsform","").strip())
                )]
                if pdf_data:
                    pdf_bytes = generate_pdf(patient, pdf_data, "NEM")
                    st.session_state.auto_download_pdf = {
                        "data": pdf_bytes,
                        "filename": f"RevitaClinic_NEM_{patient.get('patient','')}.pdf",
                        "mime": "application/pdf"
                    }
                    st.success(f"✅ PDF mit {len(pdf_data)} NEM-Supplement(en) generiert!")
                    st.rerun()
                else:
                    st.warning("⚠️ Keine NEM-Supplemente ausgewählt.")

    # =========================================================
    # TAB 2: INFUSIONSTHERAPIE
    # Left side content 100% unchanged. Each checkbox row now uses
    # ROW_COLS so timing appears inline (no separate right panel).
    # =========================================================
    with tabs[2]:
        infusion_schedule_data = {}
        inf = st.session_state.infusion_data

        def _inf_row(label, key_prefix, tooltip, default_checked=False):
            """Infusion checkbox with label+tooltip on left, timing on right."""
            cols = st.columns(ROW_COLS)
            with cols[0]:
                cb_cols = st.columns([0.07, 0.93])
                with cb_cols[0]:
                    value = st.checkbox("", value=inf.get(key_prefix, default_checked),
                        key=f"inf_{key_prefix}_cb", label_visibility="collapsed")
                with cb_cols[1]:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:4px;margin-top:8px;">' +
                        f'<span style="font-size:14px;font-family:DM Sans,sans-serif;">{label}</span>' +
                        f'<span class="info-icon" data-tooltip="{tooltip}">ⓘ</span></div>',
                        unsafe_allow_html=True)
            infusion_schedule_data.update(
                _inline_timing(value, key_prefix, patient["therapiebeginn"], patient["dauer"], "inf", inf, cols))
            return value

        def _procain_row(label, key_prefix, tooltip):
            procain_key = f"inf_{key_prefix}_procain"
            current_procain = inf.get(procain_key, "")
            cols = st.columns(ROW_COLS)
            with cols[0]:
                cb_cols = st.columns([0.07, 0.93])
                with cb_cols[0]:
                    value = st.checkbox(" ", value=inf.get(key_prefix, False),
                        key=f"inf_{key_prefix}_cb", label_visibility="collapsed")
                with cb_cols[1]:
                    st.markdown(
                        f'<div style="display:flex;align-items:center;gap:6px;">' +
                        f'<span style="font-size:14px;white-space:nowrap;font-family:DM Sans,sans-serif;">{label}</span>' +
                        f'<span class="info-icon" data-tooltip="{tooltip}">ⓘ</span>' +
                        f'<input id="procain_input_{key_prefix}" type="text" placeholder="ml" value="{current_procain}"' +
                        f' style="width:50px;padding:4px 8px;font-size:13px;border-radius:6px;border:1.5px solid #d4dae3;font-family:DM Sans,sans-serif;">' +
                        f'</div>', unsafe_allow_html=True)
            infusion_schedule_data.update(
                _inline_timing(value, key_prefix, patient["therapiebeginn"], patient["dauer"], "inf", inf, cols))
            return value, current_procain

        st.markdown('<div class="green-section-header">Infusionstherapie</div>', unsafe_allow_html=True)
        _sched_header()

        st.markdown('<div class="section-subheader">RevitaClinic Infusionen</div>', unsafe_allow_html=True)
        revita_immune        = _inf_row("RevitaImmune",        "revita_immune",        "Vitamin C, Zink, Selen, Magnesium, B-Vitamine")
        revita_immune_plus   = _inf_row("RevitaImmunePlus",    "revita_immune_plus",   "Hochdosiert: Vitamin C, Zink, Selen, Magnesium, B-Vitamine, Glutathion")
        revita_heal          = _inf_row("Revita Heal (2x)",    "revita_heal",          "Vitamin C, Zink, Arginin, Glutamin, B-Vitamine, Magnesium")
        revita_bludder       = _inf_row("RevitaBludder",       "revita_bludder",       "Eisen, Vitamin B12, Folsäure, Vitamin C")
        revita_ferro         = _inf_row("RevitaFerro",         "revita_ferro",         "Ferinject (Eisen), Vitamin C")
        revita_energy        = _inf_row("RevitaEnergyBoost",   "revita_energy",        "Magnesium, B-Vitamine, Vitamin C, Coenzym Q10")
        revita_focus         = _inf_row("RevitaFocus",         "revita_focus",         "Magnesium, B-Vitamine, Vitamin C, Zink, Alpha-Liponsäure")
        revita_nad           = _inf_row("RevitaNAD+",          "revita_nad",           "NAD+ 500mg (oder 125mg), Magnesium, B-Vitamine")
        revita_relax         = _inf_row("RevitaRelax",         "revita_relax",         "Magnesium, B-Vitamine, Vitamin C, Calcium")
        revita_fit           = _inf_row("RevitaFit",           "revita_fit",           "Magnesium, B-Vitamine, Vitamin C, Aminosäuren, Coenzym Q10")
        revita_hangover      = _inf_row("RevitaHangover",      "revita_hangover",      "Elektrolyte, Vitamin C, B-Vitamine, Magnesium, Glutathion")
        revita_beauty        = _inf_row("RevitaBeauty",        "revita_beauty",        "Vitamin C, Biotin, Zink, Selen, B-Vitamine")
        revita_antiaging     = _inf_row("RevitaAnti-Aging",    "revita_antiaging",     "Glutathion, Vitamin C, Alpha-Liponsäure, Selen, Zink")
        revita_detox         = _inf_row("RevitaDetox",         "revita_detox",         "Glutathion, Vitamin C, Magnesium, B-Vitamine")
        revita_chelate       = _inf_row("RevitaChelate",       "revita_chelate",       "EDTA, DMSA, Vitamin C, Magnesium, Zink")
        revita_liver         = _inf_row("RevitaLiver",         "revita_liver",         "Glutathion, Vitamin C, B-Vitamine, Magnesium, Mariendistel-Extrakt")
        revita_leakygut      = _inf_row("RevitaLeaky-gut",     "revita_leakygut",      "Glutamin, Zink, Vitamin C, B-Vitamine, Magnesium")
        revita_infection     = _inf_row("RevitaInfection",     "revita_infection",     "Vitamin C, Zink, Selen, Magnesium, B-Vitamine, Glutathion")
        revita_joint         = _inf_row("RevitaJoint",         "revita_joint",         "Vitamin C, Magnesium, Zink, Mangan, B-Vitamine")

        st.markdown("---")
        st.markdown('<div class="section-subheader">Standard Infusionen</div>', unsafe_allow_html=True)
        mito_energy      = _inf_row("Mito-Energy Behandlung (Mito-Gerät, Wirkbooster)", "std_mito_energy",     "Mito-Energy Behandlung mit Wirkbooster")
        oxyvenierung     = _inf_row("Oxyvenierung (10–40 ml, 10er Serie)",              "std_oxyvenierung",    "Oxyvenierung (10–40 ml, 10er Serie)")
        schwermetalltest = _inf_row("Schwermetalltest mit DMSA und Ca EDTA",            "std_schwermetalltest","Test mit DMSA und Ca EDTA")
        procain_basen, procain_2percent = _procain_row("Procain Baseninfusion mit Magnesium", "std_procain_basen","Procain Baseninfusion mit Magnesium")
        artemisinin      = _inf_row("Artemisinin Infusion mit 2x Lysin",                "std_artemisinin",     "Artemisinin Infusion mit 2x Lysin")
        perioperative    = _inf_row("Perioperative Infusion (3 Infusionen)",            "std_perioperative",   "Perioperative Infusion (3 Infusionen)")
        detox_standard   = _inf_row("Detox-Infusion Standard",                          "std_detox_standard",  "Detox-Infusion Standard")
        detox_maxi       = _inf_row("Detox-Infusion Maxi",                              "std_detox_maxi",      "Detox-Infusion Maxi")
        aufbauinfusion   = _inf_row("Aufbauinfusion nach Detox",                        "std_aufbauinfusion",  "Aufbauinfusion nach Detox")
        anti_aging       = _inf_row("Anti Aging Infusion komplett",                     "std_anti_aging",      "Anti Aging Infusion komplett")
        nerven_aufbau    = _inf_row("Nerven Aufbau Infusion",                           "std_nerven_aufbau",   "Nerven Aufbau Infusion")
        leberentgiftung  = _inf_row("Leberentgiftungsinfusion",                         "std_leberentgiftung", "Leberentgiftungsinfusion")
        anti_oxidantien  = _inf_row("Anti-Oxidantien Infusion",                         "std_anti_oxidantien", "Anti-Oxidantien Infusion")
        aminoinfusion    = _inf_row("Aminoinfusion leaky gut (5–10)",                   "std_aminoinfusion",   "Aminoinfusion leaky gut (5–10)")
        relax_infusion   = _inf_row("Relax Infusion",                                   "std_relax_infusion",  "Relax Infusion")

        st.markdown("---")
        st.markdown('<div class="section-subheader">Weitere Angaben</div>', unsafe_allow_html=True)

        def _inf_text_timing(label, key_field, key_slug, widget_fn):
            """Text/select/multiselect on left, timing on right."""
            cols = st.columns(ROW_COLS)
            with cols[0]:
                val = widget_fn(label, key_field)
            infusion_schedule_data.update(
                _inline_timing(bool(val), key_slug, patient["therapiebeginn"], patient["dauer"], "inf", inf, cols))
            return val

        def _ti(label, key_field): return st.text_input(label, value=inf.get(key_field,""), key=key_field+"_input")
        def _ms_en(label, key_field): return st.multiselect(label, ["Vitamin B Shot","Q10 Boostershot"], default=inf.get(key_field,[]), key=key_field+"_select")
        def _ms_ns(label, key_field): return st.multiselect(label, ["Glutathion","Alpha Liponsäure"], default=inf.get(key_field,[]), key=key_field+"_select")
        def _sb(label, key_field):
            opts = ["","Typ 1","Typ 2","Typ 3"]
            return st.selectbox(label, opts, index=opts.index(inf.get(key_field,"")) if inf.get(key_field,"") in opts else 0, key=key_field+"_select")

        # Weitere Angaben rows — label shown as markdown in col[0] (left-aligned,
        # same height as timing widgets), widget shown below label in same col.
        def _wa_row(label, cb_key, text_key, text_opts=None, is_select=False, is_multi=False):
            """Checkbox on left + optional text/select widget, timing on right.
            Checkbox controls whether item goes to PDF."""
            cols = st.columns(ROW_COLS)
            with cols[0]:
                cb_c, wid_c = st.columns([2.0, 2.0])
                with cb_c:
                    checked = st.checkbox(label, value=inf.get(cb_key, False), key=cb_key)
                with wid_c:
                    if is_multi and text_opts:
                        val = st.multiselect("", text_opts,
                            default=inf.get(text_key, []),
                            key=text_key + "_sel",
                            label_visibility="collapsed",
                            disabled=not checked)
                    elif is_select and text_opts:
                        val = st.selectbox("", text_opts,
                            index=text_opts.index(inf.get(text_key, text_opts[0])) if inf.get(text_key, "") in text_opts else 0,
                            key=text_key + "_sel",
                            label_visibility="collapsed",
                            disabled=not checked)
                    else:
                        val = st.text_input("", value=inf.get(text_key, ""),
                            key=text_key + "_inp",
                            placeholder="Details...",
                            label_visibility="collapsed",
                            disabled=not checked)
            active = checked and (bool(val) if not isinstance(val, list) else len(val) > 0 or checked)
            infusion_schedule_data.update(
                _inline_timing(checked, text_key, patient["therapiebeginn"], patient["dauer"], "inf", inf, cols))
            return checked, val

        _if_cb, infektions_infusion = _wa_row(
            "Infektions-Infusion / H2O2", "infektions_infusion_cb", "infektions_infusion")
        _ib_cb, immun_booster = _wa_row(
            "Immun-Boosterung Typ", "immun_booster_cb", "immun_booster",
            text_opts=["","Typ 1","Typ 2","Typ 3"], is_select=True)
        _en_cb, energetisierungsinfusion = _wa_row(
            "Energetisierungsinfusion mit", "energetisierungsinfusion_cb", "energetisierungsinfusion",
            text_opts=["Vitamin B Shot","Q10 Boostershot"], is_multi=True)
        _ns_cb, naehrstoffinfusion = _wa_row(
            "Nährstoffinfusion mit", "naehrstoffinfusion_cb", "naehrstoffinfusion",
            text_opts=["Glutathion","Alpha Liponsäure"], is_multi=True)
        _ei_cb, eisen_infusion = _wa_row(
            "Eisen Infusion (Ferinject)", "eisen_infusion_cb", "eisen_infusion")

        st.markdown("---")
        st.markdown('<div class="section-subheader">Single Ingredients / Einzel</div>', unsafe_allow_html=True)
        vitamin_c                = _inf_row("Hochdosis Vitamin C (g)",    "single_vitamin_c",               "Hochdosiertes Vitamin C")
        vitamin_b_komplex        = _inf_row("Vit. B-Komplex",             "single_vitamin_b_komplex",       "Vitamin B-Komplex")
        vitamin_d                = _inf_row("Vit. D",                     "single_vitamin_d",               "Vitamin D")
        vitamin_b6_b12_folsaeure = _inf_row("Vit. B6/B12/Folsäure",      "single_vitamin_b6_b12_folsaeure","Vitamin B6, B12 und Folsäure")
        vitamin_b3               = _inf_row("Vit. B3",                    "single_vitamin_b3",              "Vitamin B3")

        st.markdown("---")
        _extra_rows("inf", "inf", inf, patient["therapiebeginn"], patient["dauer"], infusion_schedule_data)
        st.markdown('<div class="section-subheader">Zusätze</div>', unsafe_allow_html=True)
        zusaetze = st.multiselect("Zusätze auswählen",
            ["Vit.B Komplex","Vit.B6/B12/Folsäure","Vit.D 300 kIE","Vit.B3","Biotin","Glycin",
             "Cholincitrat","Zink inject","Magnesium 400mg","TAD (red.Glut.)","Arginin","Glutamin",
             "Taurin","Ornithin","Prolin/Lysin","Lysin","PC 1000mg","Oxyvenierung","Mito-Energy"],
            default=inf.get("zusaetze",[]), key="zusaetze_select")

        new_inf = {
            "infektions_infusion_cb": _if_cb, "immun_booster_cb": _ib_cb,
            "energetisierungsinfusion_cb": _en_cb, "naehrstoffinfusion_cb": _ns_cb,
            "eisen_infusion_cb": _ei_cb,
            "revita_immune": revita_immune, "revita_immune_plus": revita_immune_plus,
            "revita_heal": revita_heal, "revita_bludder": revita_bludder,
            "revita_ferro": revita_ferro, "revita_energy": revita_energy,
            "revita_focus": revita_focus, "revita_nad": revita_nad,
            "revita_relax": revita_relax, "revita_fit": revita_fit,
            "revita_hangover": revita_hangover, "revita_beauty": revita_beauty,
            "revita_antiaging": revita_antiaging, "revita_detox": revita_detox,
            "revita_chelate": revita_chelate, "revita_liver": revita_liver,
            "revita_leakygut": revita_leakygut, "revita_infection": revita_infection,
            "revita_joint": revita_joint,
            # std_* keys match the key_prefix used in _inf_row → timing stored correctly
            "std_mito_energy": mito_energy, "std_schwermetalltest": schwermetalltest,
            "std_procain_basen": procain_basen, "procain_2percent": procain_2percent,
            "std_artemisinin": artemisinin, "std_perioperative": perioperative,
            "std_detox_standard": detox_standard, "std_detox_maxi": detox_maxi,
            "std_aufbauinfusion": aufbauinfusion, "std_oxyvenierung": oxyvenierung,
            "std_anti_aging": anti_aging, "std_nerven_aufbau": nerven_aufbau,
            "std_leberentgiftung": leberentgiftung, "std_anti_oxidantien": anti_oxidantien,
            "std_aminoinfusion": aminoinfusion, "std_relax_infusion": relax_infusion,
            # alias without std_ prefix for PDF lookup
            "mito_energy": mito_energy, "schwermetalltest": schwermetalltest,
            "procain_basen": procain_basen, "artemisinin": artemisinin,
            "perioperative": perioperative, "detox_standard": detox_standard,
            "detox_maxi": detox_maxi, "aufbauinfusion": aufbauinfusion,
            "oxyvenierung": oxyvenierung, "anti_aging": anti_aging,
            "nerven_aufbau": nerven_aufbau, "leberentgiftung": leberentgiftung,
            "anti_oxidantien": anti_oxidantien, "aminoinfusion": aminoinfusion,
            "relax_infusion": relax_infusion,
            "infektions_infusion": infektions_infusion, "immun_booster": immun_booster,
            "energetisierungsinfusion": energetisierungsinfusion,
            "naehrstoffinfusion": naehrstoffinfusion, "eisen_infusion": eisen_infusion,
            "single_vitamin_c": vitamin_c, "single_vitamin_b_komplex": vitamin_b_komplex,
            "single_vitamin_d": vitamin_d,
            "single_vitamin_b6_b12_folsaeure": vitamin_b6_b12_folsaeure,
            "single_vitamin_b3": vitamin_b3,
            # alias without single_ for PDF
            "vitamin_c": vitamin_c, "vitamin_b_komplex": vitamin_b_komplex,
            "vitamin_d": vitamin_d, "vitamin_b6_b12_folsaeure": vitamin_b6_b12_folsaeure,
            "vitamin_b3": vitamin_b3, "zusaetze": zusaetze,
        }
        new_inf.update(infusion_schedule_data)
        st.session_state.infusion_data = new_inf

        if st.button("Infusionstherapie PDF generieren", key="infusion_pdf_button"):
            pdf_bytes = generate_pdf(patient, st.session_state.infusion_data, "INFUSIONSTHERAPIE")
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": f"RevitaClinic_Infusionstherapie_{patient.get('patient','')}.pdf",
                "mime": "application/pdf"
            }
            st.rerun()


    # =========================================================
    # SAVE HANDLER
    # =========================================================
    if save_button:
        if not patient["patient"].strip():
            st.error("Bitte Patientennamen eingeben!")
        else:
            def _d(v):
                if isinstance(v, date): return v.isoformat()
                return v if v is not None else None

            def _ser(obj):
                """Recursively serialize dates to ISO strings."""
                if isinstance(obj, dict):  return {k: _ser(v) for k,v in obj.items()}
                if isinstance(obj, list):  return [_ser(i) for i in obj]
                if isinstance(obj, date):  return obj.isoformat()
                return obj

            # ── 1. Patient record ──────────────────────────────
            patient_for_db = {
                "patient":                  patient["patient"].strip(),
                "geburtsdatum":             _d(patient.get("geburtsdatum")),
                "geschlecht":               patient.get("geschlecht","M"),
                "groesse":                  int(patient.get("groesse") or 0),
                "gewicht":                  int(patient.get("gewicht") or 0),
                "therapiebeginn":           _d(patient.get("therapiebeginn")),
                "dauer":                    int(patient.get("dauer") or 6),
                "tw_besprochen":            patient.get("tw_besprochen","Ja"),
                "allergie":                 patient.get("allergie",""),
                "diagnosen":                patient.get("diagnosen",""),
                "kontrolltermin_4":         bool(patient.get("kontrolltermin_4",False)),
                "kontrolltermin_12":        bool(patient.get("kontrolltermin_12",False)),
                "kontrolltermin_24":        bool(patient.get("kontrolltermin_24",False)),
                "kontrolltermin_kommentar": patient.get("kontrolltermin_kommentar",""),
                "kt4_date":                 _d(patient.get("kt4_date")),
                "kt12_date":                _d(patient.get("kt12_date")),
                "kt24_date":                _d(patient.get("kt24_date")),
            }

            # ── 2. NEM: collect from session state nem_prescriptions ──
            # The NEM form only commits on its own submit button.
            # But every time the form renders, the widget session state keys
            # ARE updated (Streamlit updates them on every interaction).
            # Collect from widget keys (available even without form submit).
            nem_to_save = []
            for _, df_row in df.iterrows():
                rid  = df_row["id"]
                name = df_row["name"]
                if rid.startswith("CAT"): continue
                gd   = str(st.session_state.get(f"{rid}_gesamt_dosierung","") or "")
                frm  = str(st.session_state.get(f"{rid}_darreichungsform","") or "")
                pe   = str(st.session_state.get(f"{rid}_pro_Einnahme","") or "")
                nue  = str(st.session_state.get(f"{rid}_Nuechtern","") or "")
                morg = str(st.session_state.get(f"{rid}_Morgens","") or "")
                mitt = str(st.session_state.get(f"{rid}_Mittags","") or "")
                abnd = str(st.session_state.get(f"{rid}_Abends","") or "")
                ncht = str(st.session_state.get(f"{rid}_Nachts","") or "")
                kom  = str(st.session_state.get(f"{rid}_comment","") or "")
                if any(x.strip() for x in [gd, pe, nue, morg, mitt, abnd, ncht, kom]):
                    nem_to_save.append({
                        "name":              name,
                        "Gesamt-dosierung":  gd,
                        "Darreichungsform":  frm,
                        "Pro Einnahme":      pe,
                        "Nüchtern":          nue,
                        "Morgens":           morg,
                        "Mittags":           mitt,
                        "Abends":            abnd,
                        "Nachts":            ncht,
                        "Kommentar":         kom,
                    })
            # Fall back to last committed NEM data if no widget keys found
            if not nem_to_save:
                nem_to_save = st.session_state.get("nem_prescriptions", [])

            # ── 3. Therapieplan + Infusion (already in session state, updated every render) ──
            tp_db  = _ser(st.session_state.get("therapieplan_data",  {}))
            inf_db = _ser(st.session_state.get("infusion_data",      {}))
            ern_db = _ser(st.session_state.get("ernaehrung_data",    {}))

            # Debug: print to console so errors are visible
            print(f"SAVING: patient={patient_for_db['patient']}, NEM={len(nem_to_save)} items")
            print(f"  tp keys: {len(tp_db)}, inf keys: {len(inf_db)}")

            ok = save_patient_data(patient_for_db, nem_to_save, tp_db, ern_db, inf_db)
            if ok:
                st.session_state.nem_prescriptions = nem_to_save
                st.session_state.show_save_success = True
                st.session_state.last_loaded_patient = patient_for_db["patient"]
                st.session_state["_set_dropdown"] = patient_for_db["patient"]
                # Flag: treat as saved patient immediately on next render
                st.session_state["_just_saved_patient"] = patient_for_db["patient"]
                st.rerun()
            else:
                st.error("❌ Fehler beim Speichern! Konsole prüfen.")

    # Auto-download PDF
    if st.session_state.get("auto_download_pdf"):
        pdf_data = st.session_state.auto_download_pdf
        st.download_button(
            "PDF herunterladen",
            data=pdf_data["data"],
            file_name=pdf_data["filename"],
            mime=pdf_data["mime"],
            key="auto_download"
        )
        st.session_state.auto_download_pdf = None


if __name__ == "__main__":
    main()