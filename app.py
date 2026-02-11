import os
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image
import time
import base64

st.set_page_config("THERAPIEKONZEPT", layout="wide")

# --- Database ---
DB_PATH = "app.db"
TIMES = ["Nüchtern", "Morgens", "Mittags", "Abends", "Nachts"]

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def fetch_supplements(conn):
    """Get supplements with categories - FIXED ORDER"""
    return pd.read_sql("""
        SELECT * FROM supplements 
        ORDER BY 
            CASE 
                WHEN id LIKE 'CAT%' THEN category
                ELSE category
            END,
            CASE 
                WHEN id LIKE 'CAT%' THEN 0  -- Categories first
                ELSE 1  -- Supplements after
            END,
            id
    """, conn)

def fetch_patient_names(conn):
    """Get all patient names for autocomplete"""
    return pd.read_sql("SELECT patient_name FROM patients ORDER BY patient_name", conn)

def save_patient_data(conn, patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data):
    """Save patient data and all prescriptions to database"""
    try:
        cursor = conn.cursor()
        
        # First, get or create patient ID
        cursor.execute("SELECT id FROM patients WHERE patient_name = ?", (patient_data["patient"],))
        result = cursor.fetchone()
        
        if result:
            patient_id = result[0]
            # Update existing patient
            update_sql = """
            UPDATE patients SET 
                geburtsdatum=?, geschlecht=?, groesse=?, gewicht=?, 
                therapiebeginn=?, dauer=?, tw_besprochen=?, allergie=?, diagnosen=?
            WHERE id=?
            """
            cursor.execute(update_sql, (
                patient_data["geburtsdatum"], patient_data["geschlecht"], 
                patient_data["groesse"], patient_data["gewicht"],
                patient_data["therapiebeginn"], patient_data["dauer"],
                patient_data["tw_besprochen"], patient_data["allergie"], 
                patient_data["diagnosen"], patient_id
            ))
        else:
            # Insert new patient
            insert_sql = """
            INSERT INTO patients 
            (patient_name, geburtsdatum, geschlecht, groesse, gewicht, therapiebeginn, dauer, tw_besprochen, allergie, diagnosen)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(insert_sql, (
                patient_data["patient"], patient_data["geburtsdatum"], 
                patient_data["geschlecht"], patient_data["groesse"], 
                patient_data["gewicht"], patient_data["therapiebeginn"],
                patient_data["dauer"], patient_data["tw_besprochen"],
                patient_data["allergie"], patient_data["diagnosen"]
            ))
            patient_id = cursor.lastrowid
        
        # Delete existing prescriptions
        cursor.execute("DELETE FROM patient_prescriptions WHERE patient_id = ?", (patient_id,))
        
        # Insert NEM prescriptions
        nem_sql = """
        INSERT INTO patient_prescriptions 
        (patient_id, supplement_id, dauer, darreichungsform, dosierung, nuechtern, morgens, mittags, abends, nachts, kommentar)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """
        
        for prescription in nem_prescriptions:
            cursor.execute("SELECT id FROM supplements WHERE name = ?", (prescription["name"],))
            supplement_row = cursor.fetchone()
            if supplement_row:
                supplement_id = supplement_row[0]
                # Convert all values to strings with proper defaults
                prescription_values = (
                    patient_id,
                    supplement_id,
                    str(prescription.get("Gesamt-dosierung", "")),  # Updated to Gesamt-dosierung
                    str(prescription.get("Darreichungsform", "")),
                    str(prescription.get("Pro einnahme", "")),  # Updated to Pro einnahme
                    str(prescription.get("Nüchtern", "")),
                    str(prescription.get("Morgens", "")),
                    str(prescription.get("Mittags", "")),
                    str(prescription.get("Abends", "")),
                    str(prescription.get("Nachts", "")),
                    str(prescription.get("Kommentar", ""))
                )
                cursor.execute(nem_sql, prescription_values)
        
        # Create tables for other tab data if they don't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_therapieplan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_ernaehrung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_infusion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
        """)
        
        # Save other tab data
        # Therapieplan
        cursor.execute("DELETE FROM patient_therapieplan WHERE patient_id = ?", (patient_id,))
        therapieplan_sql = """
        INSERT INTO patient_therapieplan 
        (patient_id, data)
        VALUES (?, ?)
        """
        cursor.execute(therapieplan_sql, (patient_id, str(therapieplan_data)))
        
        # Ernährung
        cursor.execute("DELETE FROM patient_ernaehrung WHERE patient_id = ?", (patient_id,))
        ernaehrung_sql = """
        INSERT INTO patient_ernaehrung 
        (patient_id, data)
        VALUES (?, ?)
        """
        cursor.execute(ernaehrung_sql, (patient_id, str(ernaehrung_data)))
        
        # Infusion
        cursor.execute("DELETE FROM patient_infusion WHERE patient_id = ?", (patient_id,))
        infusion_sql = """
        INSERT INTO patient_infusion 
        (patient_id, data)
        VALUES (?, ?)
        """
        cursor.execute(infusion_sql, (patient_id, str(infusion_data)))
        
        conn.commit()
        return True
    except Exception as e:
        conn.rollback()
        st.error(f"Fehler beim Speichern: {str(e)}")
        return False

def delete_patient_data(conn, patient_name):
    """Delete patient and all their data"""
    try:
        cursor = conn.cursor()
        
        # Get patient ID
        cursor.execute("SELECT id FROM patients WHERE patient_name = ?", (patient_name,))
        result = cursor.fetchone()
        
        if result:
            patient_id = result[0]
            # Delete all related data (CASCADE will handle patient_prescriptions)
            cursor.execute("DELETE FROM patient_therapieplan WHERE patient_id = ?", (patient_id,))
            cursor.execute("DELETE FROM patient_ernaehrung WHERE patient_id = ?", (patient_id,))
            cursor.execute("DELETE FROM patient_infusion WHERE patient_id = ?", (patient_id,))
            # Delete patient (CASCADE will delete prescriptions)
            cursor.execute("DELETE FROM patients WHERE id = ?", (patient_id,))
            conn.commit()
            return True
        return False
    except Exception as e:
        conn.rollback()
        st.error(f"Fehler beim Löschen: {str(e)}")
        return False

def load_patient_data(conn, patient_name):
    """Load patient data and all prescriptions from database"""
    try:
        # Load patient data
        patient_sql = "SELECT * FROM patients WHERE patient_name = ?"
        patient_df = pd.read_sql(patient_sql, conn, params=(patient_name,))
        
        if patient_df.empty:
            # Patient doesn't exist - return empty data
            return {}, [], {}, {}, {}
        
        patient_data = patient_df.iloc[0].to_dict()
        patient_id = patient_data["id"]
        
        # Load NEM prescriptions
        nem_sql = """
        SELECT s.name, pp.dauer, pp.darreichungsform, pp.dosierung, pp.nuechtern, pp.morgens, 
               pp.mittags, pp.abends, pp.nachts, pp.kommentar
        FROM patient_prescriptions pp
        JOIN supplements s ON pp.supplement_id = s.id
        WHERE pp.patient_id = ?
        """
        nem_df = pd.read_sql(nem_sql, conn, params=(patient_id,))
        
        nem_prescriptions = []
        if not nem_df.empty:
            for _, row in nem_df.iterrows():
                # Ensure all fields are properly converted to strings
                prescription = {
                    "name": str(row["name"]) if pd.notna(row["name"]) else "",
                    "Gesamt-dosierung": str(row["dauer"]) if pd.notna(row['dauer']) else "",  # Updated to Gesamt-dosierung
                    "Darreichungsform": str(row["darreichungsform"]) if pd.notna(row["darreichungsform"]) else "",
                    "Pro einnahme": str(row["dosierung"]) if pd.notna(row["dosierung"]) else "",  # Updated to Pro einnahme
                    "Nüchtern": str(row["nuechtern"]) if pd.notna(row["nuechtern"]) else "",
                    "Morgens": str(row["morgens"]) if pd.notna(row["morgens"]) else "",
                    "Mittags": str(row["mittags"]) if pd.notna(row["mittags"]) else "",
                    "Abends": str(row["abends"]) if pd.notna(row["abends"]) else "",
                    "Nachts": str(row["nachts"]) if pd.notna(row["nachts"]) else "",
                    "Kommentar": str(row["kommentar"]) if pd.notna(row["kommentar"]) else ""
                }
                nem_prescriptions.append(prescription)
        
        # Create tables if they don't exist
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_therapieplan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_ernaehrung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS patient_infusion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
        """)
        conn.commit()
        
        # Load other tab data
        therapieplan_sql = "SELECT data FROM patient_therapieplan WHERE patient_id = ?"
        therapieplan_df = pd.read_sql(therapieplan_sql, conn, params=(patient_id,))
        therapieplan_data = eval(therapieplan_df.iloc[0]["data"]) if not therapieplan_df.empty else {}
        
        ernaehrung_sql = "SELECT data FROM patient_ernaehrung WHERE patient_id = ?"
        ernaehrung_df = pd.read_sql(ernaehrung_sql, conn, params=(patient_id,))
        ernaehrung_data = eval(ernaehrung_df.iloc[0]["data"]) if not ernaehrung_df.empty else {}
        
        infusion_sql = "SELECT data FROM patient_infusion WHERE patient_id = ?"
        infusion_df = pd.read_sql(infusion_sql, conn, params=(patient_id,))
        infusion_data = eval(infusion_df.iloc[0]["data"]) if not infusion_df.empty else {}
        
        return patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data
    except Exception as e:
        st.error(f"Fehler beim Laden: {str(e)}")
        return None, [], {}, {}, {}

# Replace the existing CSS with this updated version:
st.markdown("""
<style>
.header-container {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 10px 0;
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
/* Success message styling */
.success-message {
    background-color: #d4edda;
    color: #155724;
    padding: 12px;
    border-radius: 4px;
    border: 1px solid #c3e6cb;
    margin: 10px 0;
}

/* Main color theme - Replace red with RGB(38, 96, 65) */
.stButton > button {
    background-color: rgb(38, 96, 65) !important;
    color: white !important;
    border: 1px solid rgb(30, 76, 52) !important;
}

.stButton > button:hover {
    background-color: rgb(30, 76, 52) !important;
    border-color: rgb(25, 63, 43) !important;
    color: white !important;
}

/* Primary button styling */
.stButton > button[kind="primary"] {
    background-color: rgb(38, 96, 65) !important;
    color: white !important;
}

.stButton > button[kind="primary"]:hover {
    background-color: rgb(30, 76, 52) !important;
}

/* Secondary button styling */
.stButton > button[kind="secondary"] {
    background-color: rgb(240, 242, 246) !important;
    color: rgb(38, 96, 65) !important;
    border: 1px solid rgb(38, 96, 65) !important;
}

.stButton > button[kind="secondary"]:hover {
    background-color: rgb(230, 232, 236) !important;
    color: rgb(30, 76, 52) !important;
    border-color: rgb(30, 76, 52) !important;
}

/* Delete confirmation buttons */
.stButton > button[key="confirm_delete"] {
    background-color: rgb(220, 53, 69) !important;
    color: white !important;
    border: 1px solid rgb(200, 35, 51) !important;
}

.stButton > button[key="confirm_delete"]:hover {
    background-color: rgb(200, 35, 51) !important;
}

/* Tabs styling */
/* Tabs full width and 50/50 */
.stTabs [data-baseweb="tab-list"] {
    gap: 0px !important;  /* Remove gap between tabs */
    width: 100% !important;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 4px 4px 0px 0px;
    padding-top: 10px;
    padding-bottom: 10px;
    color: rgb(38, 96, 65);
    flex: 1 !important;  /* Make tabs flexible */
    text-align: center !important;
    justify-content: center !important;
    width: 50% !important;  /* Each tab takes 50% */
    margin: 0 !important;
}

.stTabs [aria-selected="true"] {
    background-color: rgb(38, 96, 65) !important;
    color: white !important;
}

/* Checkbox styling */
[data-testid="stCheckbox"] span {
    color: rgb(38, 96, 65) !important;
}

/* Radio button styling */
[data-testid="stRadio"] span {
    color: rgb(38, 96, 65) !important;
}

/* Selectbox/Multiselect styling */
[data-testid="stSelectbox"] span, 
[data-testid="stMultiSelect"] span {
    color: rgb(38, 96, 65) !important;
}

/* Text input/textarea focus */
.stTextInput > div > div > input:focus,
.stTextArea > div > div > textarea:focus {
    border-color: rgb(38, 96, 65) !important;
    box-shadow: 0 0 0 0.2rem rgba(38, 96, 65, 0.25) !important;
}
hr {
    margin: 2px 0 !important;
}

            
/* Number input focus */
.stNumberInput > div > div > input:focus {
    border-color: rgb(38, 96, 65) !important;
    box-shadow: 0 0 0 0.2rem rgba(38, 96, 65, 0.25) !important;
}

/* Date input focus */
[data-testid="stDateInput"] > div > div > input:focus {
    border-color: rgb(38, 96, 65) !important;
    box-shadow: 0 0 0 0.2rem rgba(38, 96, 65, 0.25) !important;
}

/* Error messages */
.stAlert.st-emotion-cache-1wrcr25 {
    border-left-color: rgb(38, 96, 65) !important;
}

/* Warning messages */
.stAlert.st-emotion-cache-1wrcr25.eeusbqq4 {
    border-left-color: rgb(255, 193, 7) !important;
}

/* Success messages */
.stAlert.st-emotion-cache-1wrcr25.e1f1d6gn3 {
    border-left-color: rgb(25, 135, 84) !important;
}

/* PDF header color */
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
    <div style="font-size:14px; line-height:1.4;">
    Clausewitzstr. 2<br>
    10629 Berlin-Charlottenburg<br>
    +49 30 6633110<br>
    info@revitaclinic.de<br>
    www.revitaclinic.de
    </div>
    """, unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)



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

def patient_inputs(conn):
    from datetime import date
    import streamlit as st

    # --------------------------------------------------
    # Get patient names
    # --------------------------------------------------
    patient_names_df = fetch_patient_names(conn)
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
    # Handle suggestion click BEFORE text_input
    # --------------------------------------------------
    if st.session_state.clicked_suggestion:
        name = st.session_state.clicked_suggestion

        result = load_patient_data(conn, name)
        if result[0]:
            patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result

            st.session_state.patient_data = patient_data
            st.session_state.nem_prescriptions = nem_prescriptions
            st.session_state.therapieplan_data = therapieplan_data
            st.session_state.ernaehrung_data = ernaehrung_data
            st.session_state.infusion_data = infusion_data

            st.session_state.last_loaded_patient = name
            st.session_state.display_patient_name = name
            st.session_state.just_loaded_patient = True

        st.session_state.clicked_suggestion = None
        st.rerun()

    # --------------------------------------------------
    # Determine text_input value
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

        # User starts typing a NEW patient → clear old data
        if (
            st.session_state.last_loaded_patient
            and typed
            and typed not in patient_names
        ):
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
    # Suggestions (ONLY if not just loaded)
    # --------------------------------------------------
    suggestions = [n for n in patient_names if typed and typed.lower() in n.lower()]

    if typed and suggestions and not st.session_state.just_loaded_patient:
        st.write("**Vorschläge:**")
        for name in suggestions[:7]:
            if st.button(name, key=f"suggest_{name}"):
                st.session_state.clicked_suggestion = name
                st.rerun()

    # --------------------------------------------------
    # Auto-load on Enter (exact match)
    # --------------------------------------------------
    patient_name_input = typed

    if (
        patient_name_input
        and patient_name_input in patient_names
        and patient_name_input != st.session_state.last_loaded_patient
        and not st.session_state.just_loaded_patient
    ):
        result = load_patient_data(conn, patient_name_input)
        if result[0]:
            patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result

            st.session_state.patient_data = patient_data
            st.session_state.nem_prescriptions = nem_prescriptions
            st.session_state.therapieplan_data = therapieplan_data
            st.session_state.ernaehrung_data = ernaehrung_data
            st.session_state.infusion_data = infusion_data

            st.session_state.last_loaded_patient = patient_name_input
            st.session_state.display_patient_name = patient_name_input
            st.session_state.just_loaded_patient = True
            st.rerun()

    # Reset flag AFTER UI is stable
    if st.session_state.just_loaded_patient:
        st.session_state.just_loaded_patient = False

    # --------------------------------------------------
    # Defaults
    # --------------------------------------------------
    pdata = st.session_state.patient_data or {}

    default_geburtsdatum = pdata.get("geburtsdatum", date.today())
    default_geschlecht = pdata.get("geschlecht", "M")
    default_groesse = int(pdata.get("groesse", 0))
    default_gewicht = int(pdata.get("gewicht", 0))
    default_therapiebeginn = pdata.get("therapiebeginn", date.today())
    default_dauer_value = pdata.get("dauer", 6)
    default_tw_besprochen = pdata.get("tw_besprochen", "Ja")
    default_allergie = pdata.get("allergie", "")
    default_diagnosen = pdata.get("diagnosen", "")

    # --------------------------------------------------
    # Layout
    # --------------------------------------------------
    c1, c2, c3, c4, c5, c6, c7 = st.columns(7)

    with c1:
        geburtsdatum = st.date_input(
            "Geburtsdatum",
            value=default_geburtsdatum,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD.MM.YYYY",
        )

    with c2:
        geschlecht = st.radio(
            "Geschlecht", ["M", "W"], horizontal=True,
            index=0 if default_geschlecht == "M" else 1
        )

    with c3:
        groesse = st.number_input("Grösse (cm)", min_value=0, value=default_groesse)

    with c4:
        gewicht = st.number_input("Gewicht (kg)", min_value=0, value=default_gewicht)

    with c5:
        therapiebeginn = st.date_input(
            "Therapiebeginn",
            value=default_therapiebeginn,
            format="DD.MM.YYYY",
        )

    with c6:
        dauer = st.selectbox(
            "Dauer (Monate)",
            list(range(1, 13)),
            index=default_dauer_value - 1,
        )

    with c7:
        tw_besprochen = st.radio(
            "TW besprochen?",
            ["Ja", "Nein"],
            horizontal=True,
            index=0 if default_tw_besprochen == "Ja" else 1,
        )

    bekannte_allergie = st.text_input("Bekannte Allergie?", value=default_allergie)

    diagnosen = st.text_area(
        "Diagnosen",
        value=default_diagnosen,
        height=100,
        placeholder="Relevante Diagnosen...",
    )

    # --------------------------------------------------
    # RETURN (UNCHANGED)
    # --------------------------------------------------
    data = {
        "patient": patient_name_input,
        "geburtsdatum": geburtsdatum,
        "geschlecht": geschlecht,
        "groesse": groesse,
        "gewicht": gewicht,
        "therapiebeginn": therapiebeginn,
        "dauer": dauer,
        "tw_besprochen": tw_besprochen,
        "allergie": bekannte_allergie,
        "diagnosen": diagnosen,
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

    # Content based on tab
    if tab_name == "NEM" and isinstance(supplements, list):
        # Supplements Table
        table_width = 277
        pdf.set_fill_color(38, 96, 65)
        pdf.set_text_color(255, 255, 255)
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(table_width, 8, "NAHRUNGSERGÄNZUNGSMITTEL (NEM) VO", 0, 1, "L", True)

        headers = ["Supplement", "Gesamt-dosierung", "Darreichungsform", "Pro einnahme", "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]  # Updated header
        base_widths = [50, 20, 35, 20, 18, 18, 18, 18, 18]  # Increased width for Pro einnahme
        used_width = sum(base_widths)
        comment_width = table_width - used_width
        widths = base_widths + [comment_width]

        pdf.set_font("Helvetica", "B", 10)
        for w, h in zip(widths, headers):
            pdf.cell(w, 8, h, 1, 0, "C", True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)

        for s in supplements:
            row = [
                clean_text(s.get("name", "")),
                clean_text(s.get("Gesamt-dosierung", "")),
                clean_text(s.get("Darreichungsform", "")),
                clean_text(s.get("Pro einnahme", "")),  # Updated to Pro einnahme
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
            "zaehne_zu_pruefen": "Zähne zu überprüfen",
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
            "ausleitung_inf": "Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom mit Infusionen",
            "ausleitung_oral": "Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom oral",
            "mikronaehrstoffe": "Einnahme von Mikronährstoffen (NEM-Verordnung)",
            "infusionsbehandlung": "Infusionsbehandlung",
            "neuraltherapie": "Neuraltherapie",
            "eigenblut": "Eigenbluttherapie",
            "medikamente": "Medikamentenverordnung",
            "bio_isopath": "Biologische / Isopathische Therapie",
            "timewaver_analyse": "Timewaver Analyse",
            "timewaver_freq": "Timewaver Frequency Behandlung",
            "weitere_labor": "Weitere Labordiagnostik (z. B. IMD, Dedimed, MMD, NextGen Onco)",
            "ernaehrung": "Ernährungsänderung und -beratung",
            "hypnose": "Hypnosetherapie",
            "yager": "Yagertherapie",
            "energetisch": "Energetische Behandlung (Marie / Noreen / Martin / KU / Sandra)",
            
            # Therapieformen
            "darmsanierung_ern": "Darmsanierung nach Paracelsus Klinik",
            "leberdetox_ern": "Leberdetox",
            "lowcarb": "Low Carb Ernährung (viel Protein und viel gesundes Fett/Öl)",
            "proteinmenge": "Proteinmenge",
            "fasten": "Intermittierendes Fasten / 4-tägiges Fasten",
            "krebsdiaet": "Krebs-Diät nach Dr. Coy / Dr. Strunz / Budwig",
            "keto": "Ketogene Ernährung",
            "oelziehen": "Ölziehen mit Kokosöl (2x10 Min. nach dem Zähneputzen)",
            "detox_vacc": "Detox vacc Protokoll (3–12 Monate, gelb markiert)",
            "abnehmen": "Abnehmen mit Akupunktur nach Uwe Richter",
            "salz": "Gut gesalzene Kost mit Himalaya- oder Meersalz (fluoridfrei)",
            "phosphat": "Phosphatreiche Nahrungsmittel",
            "kalium": "Kaliumreiche Nahrungsmittel",
            "basisch": "Basische Ernährung (pflanzlich)",
            "fluoridfrei": "Fluoridfreies Leben (Zahnpasta, Salz etc.)",
            "wasserfilter": "Wasserfilter (Umkehrosmose oder Tischfilter, z. B. Maunaway)",
            "atem": "Atemtherapie (z. B. Wim Hof oder Yoga)",
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
                "zaehne", "zaehne_zu_pruefen", "darm_biofilm", "darmsanierung", 
                "darmsanierung_dauer", "hydrocolon", "parasiten", "parasiten_bio",
                "leberdetox", "nierenprogramm", "infektion_bakt", "infektion_virus",
                "ausleitung_inf", "ausleitung_oral", "mikronaehrstoffe", "infusionsbehandlung",
                "neuraltherapie", "eigenblut", "medikamente", "bio_isopath",
                "timewaver_analyse", "timewaver_freq", "weitere_labor", "ernaehrung",
                "hypnose", "yager", "energetisch"
            ],
            "Therapieformen": [
                "darmsanierung_ern", "leberdetox_ern", "lowcarb", "proteinmenge",
                "fasten", "krebsdiaet", "keto", "oelziehen", "detox_vacc",
                "abnehmen", "salz", "phosphat", "kalium", "basisch", "fluoridfrei",
                "wasserfilter", "atem", "beratung", "ruecken", "cardio",
                "ausdauer", "trampolin", "barre"
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
            # Infusionstherapie
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
            "vitamin_c": "Vitamin C Hochdosis (g)",
            "zusaetze": "Zusätze auswählen"
        }
        
        # Define all infusion keys for a single section
        infusion_keys = [
            "mito_energy", "schwermetalltest", "procain_basen", "procain_2percent",
            "artemisinin", "perioperative", "detox_standard", "detox_maxi",
            "aufbauinfusion", "infektions_infusion", "immun_booster", "oxyvenierung",
            "energetisierungsinfusion", "naehrstoffinfusion", "anti_aging",
            "nerven_aufbau", "leberentgiftung", "anti_oxidantien", "aminoinfusion",
            "relax_infusion", "eisen_infusion", "vitamin_c", "zusaetze"
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
    
    return bytes(pdf.output(dest="S"))
        
# --- Main app ---
def main():
    conn = get_conn()
    df = fetch_supplements(conn)

    # --- Patient Info ---
    patient = patient_inputs(conn)

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
        save_button = st.button("Alle Daten speichern", use_container_width=True, type="primary")
    with col2:
        # Delete button - only show if patient exists in database
        patient_names = fetch_patient_names(conn)['patient_name'].tolist()
        if patient["patient"] and patient["patient"] in patient_names:
            if st.button("Patient löschen", use_container_width=True, type="secondary"):
                st.session_state.show_delete_confirmation = True
    
    # Show save success message if set
    if st.session_state.get("show_save_success", False):
        st.markdown('<div class="success-message">Alle Daten wurden erfolgreich gespeichert!</div>', unsafe_allow_html=True)
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
                if delete_patient_data(conn, patient["patient"]):
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

    # TAB 1: Combined THERAPIEPLAN (Diagnostik & Überprüfung, Ernährung, Infusion)
    with tabs[0]:
        therapieplan_data = st.session_state.therapieplan_data
        ernaehrung_data = st.session_state.ernaehrung_data
        infusion_data = st.session_state.infusion_data
        
        # Add CSS for green section headers
        st.markdown("""
        <style>
        .green-section-header {
            background-color: rgb(38, 96, 65);
            color: white;
            padding: 10px;
            border-radius: 4px;
            margin: 1px 0 10px 0;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Section 1: Diagnostik & Überprüfung
        st.markdown('<div class="green-section-header">Diagnostik & Überprüfung</div>', unsafe_allow_html=True)
        
        # Sub-section: Diagnostik & Überprüfung
        st.markdown("")
        col1, col2 = st.columns(2)
        with col1:
            zaehne = st.checkbox("Überprüfung der Zähne/Kieferknochen mittels OPG (Panoramaaufnahme mit lachendem Gebiss) / DVT", 
                            value=therapieplan_data.get("zaehne", False))
        with col2:
            zaehne_zu_pruefen = st.text_input("Zähne zu überprüfen:", 
                                            value=therapieplan_data.get("zaehne_zu_pruefen", ""))

        # Sub-section: Darm & Entgiftung
        st.markdown("**Darm & Entgiftung**")
        col1, col2 = st.columns(2)
        with col1:
            darm_biofilm = st.checkbox("Darm - Biofilmentfernung nach www.regenbogenkreis.de (Express-Darmkur 4 Tageskur)", 
                                    value=therapieplan_data.get("darm_biofilm", False))
            darmsanierung = st.checkbox("Darmsanierung nach Paracelsus Klinik (Rezept von Praxis)", 
                                    value=therapieplan_data.get("darmsanierung", False))
            darmsanierung_dauer = st.multiselect("Darmsanierung Dauer:", ["4 Wo", "6 Wo", "8 Wo"], 
                                            default=therapieplan_data.get("darmsanierung_dauer", []))
            hydrocolon = st.checkbox("mit Hydrocolon (Darmspülung) 2x insgesamt, Abstand 14 Tage mit Rekolonisierungs-Shot", 
                                value=therapieplan_data.get("hydrocolon", False))
            parasiten = st.checkbox("Parasitenbehandlung mit Vermox (3 Tage)", 
                                value=therapieplan_data.get("parasiten", False))
        with col2:
            parasiten_bio = st.checkbox("Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)", 
                                    value=therapieplan_data.get("parasiten_bio", False))
            leberdetox = st.checkbox("Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5x alle 4–6 Wochen)", 
                                value=therapieplan_data.get("leberdetox", False))
            nierenprogramm = st.checkbox("Nierenprogramm nach Dr. Clark – 4 Wochen – bitte bei www.drclarkcenter.de beziehen", 
                                        value=therapieplan_data.get("nierenprogramm", False))

        # Sub-section: Infektionen & Ausleitung
        st.markdown("**Infektionen & Ausleitung**")
        col1, col2 = st.columns(2)
        with col1:
            infektion_bakt = st.text_input("Infektionsbehandlung für Bakterien (Borr./Helicob.):", 
                                        value=therapieplan_data.get("infektion_bakt", ""))
        with col2:
            infektion_virus = st.text_input("Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona):", 
                                        value=therapieplan_data.get("infektion_virus", ""))
        
        col1, col2 = st.columns(2)
        with col1:
            ausleitung_inf = st.checkbox("Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom mit Infusionen", 
                                        value=therapieplan_data.get("ausleitung_inf", False))
        with col2:
            ausleitung_oral = st.checkbox("Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom oral", 
                                        value=therapieplan_data.get("ausleitung_oral", False))

        # Sub-section: Therapieformen
        st.markdown("**Therapieformen**")
        col1, col2 = st.columns(2)
        with col1:
            mikronaehrstoffe = st.checkbox("Einnahme von Mikronährstoffen (NEM-Verordnung)", 
                                        value=therapieplan_data.get("mikronaehrstoffe", False))
            infusionsbehandlung = st.checkbox("Infusionsbehandlung", 
                                            value=therapieplan_data.get("infusionsbehandlung", False))
            neuraltherapie = st.checkbox("Neuraltherapie", 
                                        value=therapieplan_data.get("neuraltherapie", False))
            eigenblut = st.checkbox("Eigenbluttherapie", 
                                value=therapieplan_data.get("eigenblut", False))
            medikamente = st.checkbox("Medikamentenverordnung", 
                                    value=therapieplan_data.get("medikamente", False))
        with col2:
            bio_isopath = st.checkbox("Biologische / Isopathische Therapie", 
                                    value=therapieplan_data.get("bio_isopath", False))
            timewaver_analyse = st.checkbox("Timewaver Analyse", 
                                        value=therapieplan_data.get("timewaver_analyse", False))
            timewaver_freq = st.checkbox("Timewaver Frequency Behandlung", 
                                        value=therapieplan_data.get("timewaver_freq", False))
            weitere_labor = st.checkbox("Weitere Labordiagnostik (z. B. IMD, Dedimed, MMD, NextGen Onco)", 
                                    value=therapieplan_data.get("weitere_labor", False))

        # Sub-section: Ergänzende Therapieformen
        st.markdown("**Ergänzende Therapieformen**")
        col1, col2 = st.columns(2)
        with col1:
            ernaehrung = st.checkbox("Ernährungsänderung und -beratung", 
                                value=therapieplan_data.get("ernaehrung", False))
            hypnose = st.checkbox("Hypnosetherapie", 
                                value=therapieplan_data.get("hypnose", False))
        with col2:
            yager = st.checkbox("Yagertherapie", 
                            value=therapieplan_data.get("yager", False))
            energetisch = st.checkbox("Energetische Behandlung (Marie / Noreen / Martin / KU / Sandra)", 
                                    value=therapieplan_data.get("energetisch", False))
        
        st.markdown("---")
        
        # Section 2: Therapieformen
        st.markdown('<div class="green-section-header">Therapieformen</div>', unsafe_allow_html=True)
        
        # Sub-section: Darmsanierung / Leberdetox
        st.markdown("**Darmsanierung / Leberdetox**")
        col1, col2 = st.columns(2)
        with col1:
            darmsanierung_ern = st.checkbox("Darmsanierung nach Paracelsus Klinik", 
                                    value=ernaehrung_data.get("darmsanierung", False))
        with col2:
            leberdetox_ern = st.radio("Leberdetox", ["Keine", "2 Tage Kurz-Intensiv", "5 Tage Standard"], 
                                index=["Keine", "2 Tage Kurz-Intensiv", "5 Tage Standard"].index(
                                    ernaehrung_data.get("leberdetox", "Keine")))

        # Sub-section: Ernährungskonzepte
        st.markdown("**Ernährungskonzepte**")
        col1, col2 = st.columns(2)
        with col1:
            lowcarb = st.checkbox("Low Carb Ernährung (viel Protein und viel gesundes Fett/Öl)", 
                                value=ernaehrung_data.get("lowcarb", False))
            proteinmenge = st.text_input("Proteinmenge", placeholder="z. B. 1,5 g / kg KG", 
                                    value=ernaehrung_data.get("proteinmenge", ""))
            fasten = st.checkbox("Intermittierendes Fasten / 4-tägiges Fasten", 
                            value=ernaehrung_data.get("fasten", False))
            krebsdiaet = st.checkbox("Krebs-Diät nach Dr. Coy / Dr. Strunz / Budwig", 
                                value=ernaehrung_data.get("krebsdiaet", False))
        with col2:
            keto = st.checkbox("Ketogene Ernährung", 
                            value=ernaehrung_data.get("keto", False))
            oelziehen = st.checkbox("Ölziehen mit Kokosöl (2x10 Min. nach dem Zähneputzen)", 
                                value=ernaehrung_data.get("oelziehen", False))
            detox_vacc = st.checkbox("Detox vacc Protokoll (3–12 Monate, gelb markiert)", 
                                value=ernaehrung_data.get("detox_vacc", False))

        # Sub-section: Sonstige Empfehlungen
        st.markdown("**Sonstige Empfehlungen**")
        col1, col2 = st.columns(2)
        with col1:
            abnehmen = st.checkbox("Abnehmen mit Akupunktur nach Uwe Richter", 
                                value=ernaehrung_data.get("abnehmen", False))
            salz = st.checkbox("Gut gesalzene Kost mit Himalaya- oder Meersalz (fluoridfrei)", 
                            value=ernaehrung_data.get("salz", False))
            phosphat = st.checkbox("Phosphatreiche Nahrungsmittel", 
                                value=ernaehrung_data.get("phosphat", False))
            kalium = st.checkbox("Kaliumreiche Nahrungsmittel", 
                            value=ernaehrung_data.get("kalium", False))
            basisch = st.checkbox("Basische Ernährung (pflanzlich)", 
                                value=ernaehrung_data.get("basisch", False))
        with col2:
            fluoridfrei = st.checkbox("Fluoridfreies Leben (Zahnpasta, Salz etc.)", 
                                    value=ernaehrung_data.get("fluoridfrei", False))
            wasserfilter = st.checkbox("Wasserfilter (Umkehrosmose oder Tischfilter, z. B. Maunaway)", 
                                    value=ernaehrung_data.get("wasserfilter", False))
            atem = st.checkbox("Atemtherapie (z. B. Wim Hof oder Yoga)", 
                            value=ernaehrung_data.get("atem", False))
            beratung = st.checkbox("Ernährungsberatung", 
                                value=ernaehrung_data.get("beratung", False))

        # Sub-section: Bewegung
        st.markdown("**Bewegung**")
        col1, col2 = st.columns(2)
        with col1:
            ruecken = st.checkbox("Rückentraining (z. B. Kieser Training)", 
                                value=ernaehrung_data.get("ruecken", False))
            cardio = st.checkbox("Cardio", 
                            value=ernaehrung_data.get("cardio", False))
        with col2:
            ausdauer = st.checkbox("Ausdauertraining", 
                                value=ernaehrung_data.get("ausdauer", False))
            trampolin = st.checkbox("Trampolin", 
                                value=ernaehrung_data.get("trampolin", False))
            barre = st.checkbox("Barre Mobility – Bewegungsapparat in Balance (150€)", 
                            value=ernaehrung_data.get("barre", False))


        # Update session states for Therapieplan and Ernährung tabs only
                # Combined data collection for Therapieplan tab only
        combined_therapieplan_data = {
            # From Diagnostik & Überprüfung
            "zaehne": zaehne,
            "zaehne_zu_pruefen": zaehne_zu_pruefen,
            "darm_biofilm": darm_biofilm,
            "darmsanierung": darmsanierung,
            "darmsanierung_dauer": darmsanierung_dauer,
            "hydrocolon": hydrocolon,
            "parasiten": parasiten,
            "parasiten_bio": parasiten_bio,
            "leberdetox": leberdetox,
            "nierenprogramm": nierenprogramm,
            "infektion_bakt": infektion_bakt,
            "infektion_virus": infektion_virus,
            "ausleitung_inf": ausleitung_inf,
            "ausleitung_oral": ausleitung_oral,
            "mikronaehrstoffe": mikronaehrstoffe,
            "infusionsbehandlung": infusionsbehandlung,
            "neuraltherapie": neuraltherapie,
            "eigenblut": eigenblut,
            "medikamente": medikamente,
            "bio_isopath": bio_isopath,
            "timewaver_analyse": timewaver_analyse,
            "timewaver_freq": timewaver_freq,
            "weitere_labor": weitere_labor,
            "ernaehrung": ernaehrung,
            "hypnose": hypnose,
            "yager": yager,
            "energetisch": energetisch,
            
            # From Therapieformen
            "darmsanierung_ern": darmsanierung_ern,
            "leberdetox_ern": leberdetox_ern,
            "lowcarb": lowcarb,
            "proteinmenge": proteinmenge,
            "fasten": fasten,
            "krebsdiaet": krebsdiaet,
            "keto": keto,
            "oelziehen": oelziehen,
            "detox_vacc": detox_vacc,
            "abnehmen": abnehmen,
            "salz": salz,
            "phosphat": phosphat,
            "kalium": kalium,
            "basisch": basisch,
            "fluoridfrei": fluoridfrei,
            "wasserfilter": wasserfilter,
            "atem": atem,
            "beratung": beratung,
            "ruecken": ruecken,
            "cardio": cardio,
            "ausdauer": ausdauer,
            "trampolin": trampolin,
            "barre": barre
        }

        # Update session states for Therapieplan and Ernährung tabs only
        st.session_state.therapieplan_data = {
            "zaehne": zaehne,
            "zaehne_zu_pruefen": zaehne_zu_pruefen,
            "darm_biofilm": darm_biofilm,
            "darmsanierung": darmsanierung,
            "darmsanierung_dauer": darmsanierung_dauer,
            "hydrocolon": hydrocolon,
            "parasiten": parasiten,
            "parasiten_bio": parasiten_bio,
            "leberdetox": leberdetox,
            "nierenprogramm": nierenprogramm,
            "infektion_bakt": infektion_bakt,
            "infektion_virus": infektion_virus,
            "ausleitung_inf": ausleitung_inf,
            "ausleitung_oral": ausleitung_oral,
            "mikronaehrstoffe": mikronaehrstoffe,
            "infusionsbehandlung": infusionsbehandlung,
            "neuraltherapie": neuraltherapie,
            "eigenblut": eigenblut,
            "medikamente": medikamente,
            "bio_isopath": bio_isopath,
            "timewaver_analyse": timewaver_analyse,
            "timewaver_freq": timewaver_freq,
            "weitere_labor": weitere_labor,
            "ernaehrung": ernaehrung,
            "hypnose": hypnose,
            "yager": yager,
            "energetisch": energetisch
        }
        
        st.session_state.ernaehrung_data = {
            "darmsanierung": darmsanierung_ern,
            "leberdetox": leberdetox_ern,
            "lowcarb": lowcarb,
            "proteinmenge": proteinmenge,
            "fasten": fasten,
            "krebsdiaet": krebsdiaet,
            "keto": keto,
            "oelziehen": oelziehen,
            "detox_vacc": detox_vacc,
            "abnehmen": abnehmen,
            "salz": salz,
            "phosphat": phosphat,
            "kalium": kalium,
            "basisch": basisch,
            "fluoridfrei": fluoridfrei,
            "wasserfilter": wasserfilter,
            "atem": atem,
            "beratung": beratung,
            "ruecken": ruecken,
            "cardio": cardio,
            "ausdauer": ausdauer,
            "trampolin": trampolin,
            "barre": barre
        }

        # Single PDF button at the end
        if st.button("Therapieplan PDF generieren"):
            pdf_bytes = generate_pdf(patient, combined_therapieplan_data, "THERAPIEPLAN")
            filename = f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf"
            
            # Set auto-download
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": filename,
                "mime": "application/pdf"
            }
            st.rerun()
    
    

        # TAB 3: Infusionstherapie
    
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

                # Gesamt-dosierung options
                gesamt_dosierung_options = [
                    "", "1", "2", "3", "4", "5", "6", "7", "8", "9", "10", 
                    "12", "14", "16", "18", "20", "22", "24", "26", "28", "30",
                    "35", "40", "45", "50", "60", "70", "80", "90", "100",
                    "120", "150", "180", "200", "250", "300", "400", "500"
                ]

                # Define dosage options based on Darreichungsform
                def get_pro_einnahme_options(darreichungsform):
                    """Return appropriate Pro einnahme options based on Darreichungsform"""
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

                # CSS for better styling
                st.markdown("""
                    <style>
                    div[data-testid="stVerticalBlock"] > div {
                        margin-bottom: -6px !important;
                    }
                    [data-testid="stCheckbox"] {
                        margin-top: -6px !important;
                        margin-bottom: -6px !important;
                    }
                    .custom-input input {
                        height: 30px !important;
                        font-size: 14px !important;
                        padding: 4px 6px !important;
                    }
                    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:not(:first-child) p {
                        text-align: center !important;
                        margin-bottom: 0px !important;
                    }
                    [data-testid="stHorizontalBlock"] > div[data-testid="column"]:first-child p {
                        text-align: left !important;
                        margin-bottom: 0px !important;
                    }
                    /* Add this for the new color theme */
                    .stButton > button {
                        background-color: rgb(38, 96, 65) !important;
                        color: white !important;
                    }
                    .stButton > button:hover {
                        background-color: rgb(30, 76, 52) !important;
                    }
                    /* Category header styling for expander */
                    .streamlit-expanderHeader {
                        background-color: rgb(38, 96, 65) !important;
                        color: white !important;
                        font-weight: bold !important;
                        font-size: 16px !important;
                        border-radius: 4px !important;
                    }
                    .streamlit-expanderHeader:hover {
                        background-color: rgb(30, 76, 52) !important;
                    }
                    .streamlit-expanderHeader svg {
                        fill: white !important;
                    }
                    /* Reduce padding in expander content */
                    .streamlit-expanderContent {
                        padding-top: 10px !important;
                        padding-bottom: 10px !important;
                    }
                    </style>
                """, unsafe_allow_html=True)

                # Header row - Updated to Pro einnahme
                header_cols = st.columns([2.2, 0.9, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])
                headers = ["Supplement", "Gesamt-dosierung", "Darreichungsform", "Pro einnahme",  # Updated header
                        "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]

                for col, text in zip(header_cols, headers):
                    col.markdown(f"**{text}**")

                st.markdown("---")

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

                            override_key = f"gesamt_dosierung_override_{row['id']}"  # Updated key name

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
                                initial_pro_einnahme = loaded_prescription.get("Pro einnahme", "")  # Updated field
                                initial_nue = loaded_prescription.get("Nüchtern", "")
                                initial_morg = loaded_prescription.get("Morgens", "")
                                initial_mitt = loaded_prescription.get("Mittags", "")
                                initial_abend = loaded_prescription.get("Abends", "")
                                initial_nacht = loaded_prescription.get("Nachts", "")
                                initial_comment = loaded_prescription.get("Kommentar", "")
                            else:
                                initial_gesamt_dosierung = st.session_state[override_key] if st.session_state[override_key] is not None else ""
                                initial_form = DEFAULT_FORMS.get(supplement_name, "Kapseln")
                                initial_pro_einnahme = ""
                                initial_nue = ""
                                initial_morg = ""
                                initial_mitt = ""
                                initial_abend = ""
                                initial_nacht = ""
                                initial_comment = ""

                            # Create unique keys for each widget
                            gesamt_dosierung_key = f"{row['id']}_gesamt_dosierung"
                            form_key = f"{row['id']}_darreichungsform"
                            pro_einnahme_key = f"{row['id']}_pro_einnahme"  # Updated key name
                            custom_form_key = f"{row['id']}_custom_dosage"
                            nue_key = f"{row['id']}_Nuechtern"
                            morg_key = f"{row['id']}_Morgens"
                            mitt_key = f"{row['id']}_Mittags"
                            abend_key = f"{row['id']}_Abends"
                            nacht_key = f"{row['id']}_Nachts"
                            comment_key = f"{row['id']}_comment"

                            # Gesamt-dosierung dropdown
                            gesamt_dosierung_index = 0
                            if initial_gesamt_dosierung in gesamt_dosierung_options:
                                gesamt_dosierung_index = gesamt_dosierung_options.index(initial_gesamt_dosierung)
                            
                            gesamt_dosierung_val = cols[1].selectbox(
                                "", gesamt_dosierung_options, index=gesamt_dosierung_index,
                                key=gesamt_dosierung_key, label_visibility="collapsed"
                            )

                            # Darreichungsform dropdown
                            dosage_presets = ["Kapseln", "Lösung", "Tabletten", "Pulver", "Tropfen", "Sachet", "Öl", "Spray", "Creme", "Gel", "Flüssig", "Tee", "Pflaster", "Andere:"]
                            
                            default_form_for_supplement = DEFAULT_FORMS.get(supplement_name, "Kapseln")
                            form_index = 0
                            if initial_form:
                                if initial_form in dosage_presets:
                                    form_index = dosage_presets.index(initial_form)
                                elif initial_form.strip():
                                    form_index = dosage_presets.index("Andere:")
                            else:
                                if default_form_for_supplement in dosage_presets:
                                    form_index = dosage_presets.index(default_form_for_supplement)
                            
                            selected_form = cols[2].selectbox(
                                "", dosage_presets, index=form_index,
                                key=form_key, label_visibility="collapsed"
                            )

                            # Pro einnahme dropdown - dynamically updates based on Darreichungsform
                            # Get current form value from session state if available
                            current_form = st.session_state.get(form_key, selected_form)
                            pro_einnahme_options = get_pro_einnahme_options(current_form)
                            
                            pro_einnahme_index = 0
                            if initial_pro_einnahme in pro_einnahme_options:
                                pro_einnahme_index = pro_einnahme_options.index(initial_pro_einnahme)
                            
                            pro_einnahme_val = cols[3].selectbox(
                                "", pro_einnahme_options, index=pro_einnahme_index,
                                key=pro_einnahme_key, label_visibility="collapsed"
                            )

                            # Custom dosage text input
                            custom_form = ""
                            if selected_form == "Andere:":
                                custom_form_value = initial_form if initial_form and initial_form not in dosage_presets else ""
                                custom_form = cols[2].text_input(
                                    "", key=custom_form_key, placeholder="z. B. Pulver",
                                    value=custom_form_value,
                                    label_visibility="collapsed"
                                )

                            # Sync override state
                            if gesamt_dosierung_val:  # Only set override if there's a value
                                st.session_state[override_key] = gesamt_dosierung_val
                            else:
                                st.session_state[override_key] = None

                            # Intake dropdowns
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

                            # Kommentar field
                            comment = cols[9].text_input(
                                "", key=comment_key, placeholder="Kommentar",
                                value=initial_comment or "", label_visibility="collapsed"
                            )

                            # Get the final form value
                            final_form = custom_form if custom_form else selected_form
                            if final_form == "Andere:":
                                final_form = ""
                            
                            # Create prescription data for this supplement - UPDATED field name
                            prescription_data = {
                                "name": supplement_name,
                                "Gesamt-dosierung": gesamt_dosierung_val,
                                "Darreichungsform": final_form,
                                "Pro einnahme": pro_einnahme_val,  # Updated field name
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
                pdf_submitted = st.form_submit_button("NEM PDF generieren")

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
                        # Check Pro einnahme
                        elif prescription.get("Pro einnahme", "").strip():  # Updated field name
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

    with tabs[2]:
        infusion_data = st.session_state.infusion_data
        
        # Add CSS for green section headers
        st.markdown("""
        <style>
        .green-section-header {
            background-color: rgb(38, 96, 65);
            color: white;
            padding: 10px;
            border-radius: 4px;
            margin: 1px 0 10px 0;
            font-weight: bold;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Section: Infusionstherapie
        st.markdown('<div class="green-section-header">Infusionstherapie</div>', unsafe_allow_html=True)
        
        # Sub-section: Infusionen
        st.markdown("**Infusionen**")
        col1, col2 = st.columns(2)
        with col1:
            mito_energy = st.checkbox("Mito-Energy Behandlung (Mito-Gerät, Wirkbooster)", 
                                    value=infusion_data.get("mito_energy", False))
            schwermetalltest = st.checkbox("Schwermetalltest mit DMSA und Ca EDTA", 
                                        value=infusion_data.get("schwermetalltest", False))
            procain_basen = st.checkbox("Procain Baseninfusion mit Magnesium", 
                                    value=infusion_data.get("procain_basen", False))
            procain_2percent = st.text_input("Procain 2% (ml)", 
                                        value=infusion_data.get("procain_2percent", ""))
            artemisinin = st.checkbox("Artemisinin Infusion mit 2x Lysin", 
                                    value=infusion_data.get("artemisinin", False))
            perioperative = st.checkbox("Perioperative Infusion (3 Infusionen)", 
                                    value=infusion_data.get("perioperative", False))
            detox_standard = st.checkbox("Detox-Infusion Standard", 
                                    value=infusion_data.get("detox_standard", False))
        with col2:
            detox_maxi = st.checkbox("Detox-Infusion Maxi", 
                                value=infusion_data.get("detox_maxi", False))
            aufbauinfusion = st.checkbox("Aufbauinfusion nach Detox", 
                                    value=infusion_data.get("aufbauinfusion", False))
            infektions_infusion = st.text_input("Infektions-Infusion / H2O2 (Anzahl / ml)", 
                                            value=infusion_data.get("infektions_infusion", ""))
            immun_booster = st.selectbox("Immun-Boosterung Typ", ["", "Typ 1", "Typ 2", "Typ 3"], 
                                    index=["", "Typ 1", "Typ 2", "Typ 3"].index(
                                        infusion_data.get("immun_booster", "")))
            oxyvenierung = st.checkbox("Oxyvenierung (10–40 ml, 10er Serie)", 
                                    value=infusion_data.get("oxyvenierung", False))
            energetisierungsinfusion = st.multiselect("Energetisierungsinfusion mit", 
                                                    ["Vitamin B Shot", "Q10 Boostershot"],
                                                    default=infusion_data.get("energetisierungsinfusion", []))
        
        col1, col2 = st.columns(2)
        with col1:
            naehrstoffinfusion = st.multiselect("Nährstoffinfusion mit", 
                                            ["Glutathion", "Alpha Liponsäure"],
                                            default=infusion_data.get("naehrstoffinfusion", []))
            anti_aging = st.checkbox("Anti Aging Infusion komplett", 
                                value=infusion_data.get("anti_aging", False))
            nerven_aufbau = st.checkbox("Nerven Aufbau Infusion", 
                                    value=infusion_data.get("nerven_aufbau", False))
            leberentgiftung = st.checkbox("Leberentgiftungsinfusion", 
                                        value=infusion_data.get("leberentgiftung", False))
        with col2:
            anti_oxidantien = st.checkbox("Anti-Oxidantien Infusion", 
                                        value=infusion_data.get("anti_oxidantien", False))
            aminoinfusion = st.checkbox("Aminoinfusion leaky gut (5–10)", 
                                    value=infusion_data.get("aminoinfusion", False))
            relax_infusion = st.checkbox("Relax Infusion", 
                                    value=infusion_data.get("relax_infusion", False))
            eisen_infusion = st.text_input("Eisen Infusion (Ferinject) mg / Anzahl", 
                                        value=infusion_data.get("eisen_infusion", ""))
            vitamin_c = st.text_input("Vitamin C Hochdosis (g)", 
                                    value=infusion_data.get("vitamin_c", ""))

        # Sub-section: Zusätze
        st.markdown("**Zusätze**")
        zusaetze = st.multiselect(
            "Zusätze auswählen",
            ["Vit.B Komplex", "Vit.B6/B12/Folsäure", "Vit.D 300 kIE", "Vit.B3", "Biotin", "Glycin",
            "Cholincitrat", "Zink inject", "Magnesium 400mg", "TAD (red.Glut.)", "Arginin", "Glutamin",
            "Taurin", "Ornithin", "Prolin/Lysin", "Lysin", "PC 1000mg"],
            default=infusion_data.get("zusaetze", [])
        )
        
        # Update session state for infusion data
        st.session_state.infusion_data = {
            "mito_energy": mito_energy,
            "schwermetalltest": schwermetalltest,
            "procain_basen": procain_basen,
            "procain_2percent": procain_2percent,
            "artemisinin": artemisinin,
            "perioperative": perioperative,
            "detox_standard": detox_standard,
            "detox_maxi": detox_maxi,
            "aufbauinfusion": aufbauinfusion,
            "infektions_infusion": infektions_infusion,
            "immun_booster": immun_booster,
            "oxyvenierung": oxyvenierung,
            "energetisierungsinfusion": energetisierungsinfusion,
            "naehrstoffinfusion": naehrstoffinfusion,
            "anti_aging": anti_aging,
            "nerven_aufbau": nerven_aufbau,
            "leberentgiftung": leberentgiftung,
            "anti_oxidantien": anti_oxidantien,
            "aminoinfusion": aminoinfusion,
            "relax_infusion": relax_infusion,
            "eisen_infusion": eisen_infusion,
            "vitamin_c": vitamin_c,
            "zusaetze": zusaetze
        }
        
        # Combined data for PDF generation
        combined_infusion_data = st.session_state.infusion_data
        
        # PDF button for Infusionstherapie
        if st.button("Infusionstherapie PDF generieren"):
            pdf_bytes = generate_pdf(patient, combined_infusion_data, "INFUSIONSTHERAPIE")
            filename = f"RevitaClinic_Infusionstherapie_{patient.get('patient','')}.pdf"
            
            # Set auto-download
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": filename,
                "mime": "application/pdf"
            }
            st.rerun()

    # Handle save button (saves all tabs)
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
            if save_patient_data(conn, patient, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data):
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