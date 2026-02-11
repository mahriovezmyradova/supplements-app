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
        key="patient_name_input"
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
    
    # Kontrolltermine defaults
    default_kontrolltermin_4 = pdata.get("kontrolltermin_4", False)
    default_kontrolltermin_12 = pdata.get("kontrolltermin_12", False)
    default_kontrolltermin_kommentar = pdata.get("kontrolltermin_kommentar", "")

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
            index=default_dauer_value - 1,
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
        height=100,
        placeholder="Relevante Diagnosen...",
        key="diagnosen_input"
    )

    # --------------------------------------------------
    # Kontrolltermine (now available for all tabs)
    # --------------------------------------------------
    st.markdown("---")
    st.markdown("#### Kontrolltermine")
    
    col1, col2 = st.columns(2)
    with col1:
        kontrolltermin_4 = st.checkbox("4 Wochen", value=default_kontrolltermin_4, key="kontrolltermin_4_input")
    with col2:
        kontrolltermin_12 = st.checkbox("12 Wochen", value=default_kontrolltermin_12, key="kontrolltermin_12_input")
    
    kontrolltermin_kommentar = st.text_input("Kommentar:", value=default_kontrolltermin_kommentar, key="kontrolltermin_kommentar_input")

    # --------------------------------------------------
    # RETURN (with Kontrolltermine included)
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
        # Kontrolltermine
        "kontrolltermin_4": kontrolltermin_4,
        "kontrolltermin_12": kontrolltermin_12,
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
        save_button = st.button("Alle Daten speichern", use_container_width=True, type="primary", key="save_button")
    with col2:
        # Delete button - only show if patient exists in database
        patient_names = fetch_patient_names(conn)['patient_name'].tolist()
        if patient["patient"] and patient["patient"] in patient_names:
            if st.button("Patient löschen", use_container_width=True, type="secondary", key="delete_button"):
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
                            value=therapieplan_data.get("zaehne", False),
                            key="zaehne_checkbox")
        with col2:
            zaehne_zu_pruefen = st.text_input("Zähne zu überprüfen (OPG/DVT):", 
                                            value=therapieplan_data.get("zaehne_zu_pruefen", ""),
                                            key="zaehne_zu_pruefen_input")

        # Sub-section: Labor & Diagnostik
        st.markdown("**Labor & Diagnostik**")
        col1, col2 = st.columns(2)
        with col1:
            lab_imd = st.text_input("IMD:", value=therapieplan_data.get("lab_imd", ""), key="lab_imd_input")
        with col2:
            lab_mmd = st.text_input("MMD:", value=therapieplan_data.get("lab_mmd", ""), key="lab_mmd_input")
        
        col1, col2 = st.columns(2)
        with col1:
            lab_nextgen = st.text_input("NextGen Onco:", value=therapieplan_data.get("lab_nextgen", ""), key="lab_nextgen_input")
        with col2:
            lab_sonstiges = st.text_input("Sonstiges:", value=therapieplan_data.get("lab_sonstiges", ""), key="lab_sonstiges_input")

        # Sub-section: Bewegungsapparat & Schwermetalle
        st.markdown("**Bewegungsapparat & Schwermetalle**")
        col1, col2 = st.columns(2)
        with col1:
            analyse_bewegungsapparat = st.checkbox("Analyse Bewegungsapparat (Martin)", 
                                                value=therapieplan_data.get("analyse_bewegungsapparat", False),
                                                key="analyse_bewegungsapparat_checkbox")
        with col2:
            schwermetalltest = st.checkbox("Schwermetalltest mit DMSA und Ca EDTA", 
                                        value=therapieplan_data.get("schwermetalltest", False),
                                        key="schwermetalltest_checkbox")

        st.markdown("---")

        # Sub-section: Darm & Entgiftung
        st.markdown("**Darm & Entgiftung**")
        col1, col2 = st.columns(2)
        with col1:
            darm_biofilm = st.checkbox("Darm - Biofilmentfernung nach www.regenbogenkreis.de (Express-Darmkur 4 Tageskur)", 
                                    value=therapieplan_data.get("darm_biofilm", False),
                                    key="darm_biofilm_checkbox")
            darmsanierung = st.checkbox("Darmsanierung nach Paracelsus Klinik (Rezept von Praxis)", 
                                    value=therapieplan_data.get("darmsanierung", False),
                                    key="darmsanierung_checkbox")
            darmsanierung_dauer = st.multiselect("Darmsanierung Dauer:", ["4 Wo", "6 Wo", "8 Wo"], 
                                            default=therapieplan_data.get("darmsanierung_dauer", []),
                                            key="darmsanierung_dauer_select")
        with col2:
            hydrocolon = st.checkbox("mit Hydrocolon (Darmspülung) 2x insgesamt, Abstand 14 Tage mit Rekolonisierungs-Shot", 
                                value=therapieplan_data.get("hydrocolon", False),
                                key="hydrocolon_checkbox")
            parasiten = st.checkbox("Parasitenbehandlung mit Vermox (3 Tage)", 
                                value=therapieplan_data.get("parasiten", False),
                                key="parasiten_checkbox")
            parasiten_bio = st.checkbox("Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)", 
                                    value=therapieplan_data.get("parasiten_bio", False),
                                    key="parasiten_bio_checkbox")
        
        col1, col2 = st.columns(2)
        with col1:
            leberdetox = st.checkbox("Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5x alle 4–6 Wochen)", 
                                value=therapieplan_data.get("leberdetox", False),
                                key="leberdetox_checkbox")
        with col2:
            nierenprogramm = st.checkbox("Nierenprogramm nach Dr. Clark – 4 Wochen – bitte bei www.drclarkcenter.de beziehen", 
                                        value=therapieplan_data.get("nierenprogramm", False),
                                        key="nierenprogramm_checkbox")

        # Sub-section: Infektionen & Ausleitung
        st.markdown("**Infektionen & Ausleitung**")
        col1, col2 = st.columns(2)
        with col1:
            infektion_bakt = st.text_input("Infektionsbehandlung für Bakterien (Borr./Helicob.):", 
                                        value=therapieplan_data.get("infektion_bakt", ""),
                                        key="infektion_bakt_input")
        with col2:
            infektion_virus = st.text_input("Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona):", 
                                        value=therapieplan_data.get("infektion_virus", ""),
                                        key="infektion_virus_input")
        
        col1, col2 = st.columns(2)
        with col1:
            ausleitung_inf = st.checkbox("Schwermetallausleitung Infusion", 
                                    value=therapieplan_data.get("ausleitung_inf", False),
                                    key="ausleitung_inf_checkbox")
        with col2:
            ausleitung_oral = st.checkbox("Schwermetallausleitung oral", 
                                    value=therapieplan_data.get("ausleitung_oral", False),
                                    key="ausleitung_oral_checkbox")

        st.markdown("---")

        # Section 2: Therapieformen
        st.markdown('<div class="green-section-header">Therapieformen</div>', unsafe_allow_html=True)
        
        # Sub-section: Haupttherapien
        st.markdown("**Haupttherapien**")
        col1, col2 = st.columns(2)
        with col1:
            mikronaehrstoffe = st.checkbox("Einnahme Mikronährstoffen (NEM-Verordnung) (siehe separate PDF)", 
                                        value=therapieplan_data.get("mikronaehrstoffe", False),
                                        key="mikronaehrstoffe_checkbox")
            infusionsbehandlung = st.checkbox("Infusionstherapie (siehe separate PDF)", 
                                            value=therapieplan_data.get("infusionsbehandlung", False),
                                            key="infusionsbehandlung_checkbox")
            neuraltherapie = st.checkbox("Neuraltherapie", 
                                        value=therapieplan_data.get("neuraltherapie", False),
                                        key="neuraltherapie_checkbox")
        with col2:
            eigenblut = st.checkbox("Eigenbluttherapie", 
                                value=therapieplan_data.get("eigenblut", False),
                                key="eigenblut_checkbox")
            aethetisch = st.checkbox("Ästhetische Behandlung (Botox/PRP/Fäden/Hyaloron)", 
                                    value=therapieplan_data.get("aethetisch", False),
                                    key="aethetisch_checkbox")
            ozontherapie = st.checkbox("Ozontherapie", 
                                    value=therapieplan_data.get("ozontherapie", False),
                                    key="ozontherapie_checkbox")
        
        col1, col2 = st.columns(2)
        with col1:
            medikamente = st.checkbox("Medikamentenverordnung - Rezept für:", 
                                    value=therapieplan_data.get("medikamente", False),
                                    key="medikamente_checkbox")
            medikamente_text = st.text_input("Rezept Details:", 
                                            value=therapieplan_data.get("medikamente_text", ""),
                                            key="medikamente_text_input")
        with col2:
            timewaver_freq = st.checkbox("TimeWaver Frequency Behandlung", 
                                        value=therapieplan_data.get("timewaver_freq", False),
                                        key="timewaver_freq_checkbox")

        # Sub-section: Biologische & Komplementäre Therapien
        st.markdown("**Biologische & Komplementäre Therapien**")
        col1, col2 = st.columns(2)
        with col1:
            bio_isopath = st.checkbox("Biologische Isopathische Therapie", 
                                    value=therapieplan_data.get("bio_isopath", False),
                                    key="bio_isopath_checkbox")
            akupunktur = st.checkbox("Akupunktur", 
                                    value=therapieplan_data.get("akupunktur", False),
                                    key="akupunktur_checkbox")
            homoeopathie = st.checkbox("Homöopathie (Anna)", 
                                    value=therapieplan_data.get("homoeopathie", False),
                                    key="homoeopathie_checkbox")
        with col2:
            bioresonanz = st.checkbox("Bioresonanz (Anna)", 
                                    value=therapieplan_data.get("bioresonanz", False),
                                    key="bioresonanz_checkbox")
            hypnose = st.checkbox("Hypnosetherapie (Noreen Martin Miro)", 
                                value=therapieplan_data.get("hypnose", False),
                                key="hypnose_checkbox")
            yager = st.checkbox("Yagertherapie", 
                            value=therapieplan_data.get("yager", False),
                            key="yager_checkbox")

        # Sub-section: Weitere Maßnahmen
        st.markdown("**Weitere Maßnahmen**")
        col1, col2 = st.columns(2)
        with col1:
            atemtherapie = st.checkbox("Atemtherapie", 
                                    value=therapieplan_data.get("atemtherapie", False),
                                    key="atemtherapie_checkbox")
            bewegung = st.checkbox("Bewegung", 
                                value=therapieplan_data.get("bewegung", False),
                                key="bewegung_checkbox")
            ernaehrung = st.checkbox("Ernährungsberatung", 
                                    value=therapieplan_data.get("ernaehrung", False),
                                    key="ernaehrung_checkbox")
            darmsanierung_ern = st.checkbox("Darmsanierung", 
                                        value=therapieplan_data.get("darmsanierung_ern", False),
                                        key="darmsanierung_ern_checkbox")
        with col2:
            leberreinigung = st.checkbox("Leberreinigung", 
                                    value=therapieplan_data.get("leberreinigung", False),
                                    key="leberreinigung_checkbox")
            lowcarb = st.checkbox("Low Carb Ernährung", 
                                value=therapieplan_data.get("lowcarb", False),
                                key="lowcarb_checkbox")
            fasten = st.checkbox("Intermittierendes Fasten", 
                            value=therapieplan_data.get("fasten", False),
                            key="fasten_checkbox")
            krebsdiaet = st.checkbox("Krebs Diät nach Dr. Coy/Dr. Strunz/angelehnt Budwig", 
                                    value=therapieplan_data.get("krebsdiaet", False),
                                    key="krebsdiaet_checkbox")
        
        col1, col2 = st.columns(2)
        with col1:
            ketogene = st.checkbox("Ketogene Ernährung", 
                                value=therapieplan_data.get("ketogene", False),
                                key="ketogene_checkbox")
            basisch = st.checkbox("Basische Ernährung", 
                                value=therapieplan_data.get("basisch", False),
                                key="basisch_checkbox")
            naehrstoff_ausgleich = st.text_input("Nährstoffmängel ausgleichen:", 
                                            value=therapieplan_data.get("naehrstoff_ausgleich", ""),
                                            key="naehrstoff_ausgleich_input")
        with col2:
            therapie_sonstiges = st.text_input("Sonstiges:", 
                                            value=therapieplan_data.get("therapie_sonstiges", ""),
                                            key="therapie_sonstiges_input")

        # Sub-section: Individuelle Behandlungen
        st.markdown("**Individuelle Behandlungen**")
        col1, col2 = st.columns(2)
        with col1:
            magenband = st.checkbox("Magenband", 
                                value=therapieplan_data.get("magenband", False),
                                key="magenband_checkbox")
        with col2:
            energie_behandlungen = st.checkbox("Energiebehandlungen bei Marie", 
                                            value=therapieplan_data.get("energie_behandlungen", False),
                                            key="energie_behandlungen_checkbox")

        st.markdown("---")

        # Sub-section: Gesprächstermine
        st.markdown("**Gesprächstermine**")
        col1, col2 = st.columns(2)
        with col1:
            zwischengespraech_4 = st.checkbox("Zwischengespräch nach 4 Wochen (1/2h)", 
                                            value=therapieplan_data.get("zwischengespraech_4", False),
                                            key="zwischengespraech_4_checkbox")
        with col2:
            zwischengespraech_8 = st.checkbox("Zwischengespräch nach weiteren 8 Wochen (1/2h)", 
                                            value=therapieplan_data.get("zwischengespraech_8", False),
                                            key="zwischengespraech_8_checkbox")

        # Update session states for Therapieplan
        st.session_state.therapieplan_data = {
            # Diagnostik & Überprüfung
            "zaehne": zaehne,
            "zaehne_zu_pruefen": zaehne_zu_pruefen,
            
            # Labor & Diagnostik
            "lab_imd": lab_imd,
            "lab_mmd": lab_mmd,
            "lab_nextgen": lab_nextgen,
            "lab_sonstiges": lab_sonstiges,
            
            # Bewegungsapparat & Schwermetalle
            "analyse_bewegungsapparat": analyse_bewegungsapparat,
            "schwermetalltest": schwermetalltest,
            
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
            
            # Weitere Maßnahmen
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
            
            # Individuelle Behandlungen
            "magenband": magenband,
            "energie_behandlungen": energie_behandlungen,
            
            # Gesprächstermine
            "zwischengespraech_4": zwischengespraech_4,
            "zwischengespraech_8": zwischengespraech_8,
        }

        # Update the PDF generation function call to use updated data
        if st.button("Therapieplan PDF generieren", key="therapieplan_pdf_button"):
            # Use the same data for PDF
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
        
        # Sub-section: RevitaClinic Infusionen
        st.markdown("**RevitaClinic Infusionen**")
        
        col1, col2 = st.columns(2)
        with col1:
            revita_immune = st.checkbox("RevitaImmune", value=infusion_data.get("revita_immune", False), key="revita_immune_checkbox")
            revita_immune_plus = st.checkbox("RevitaImmunePlus", value=infusion_data.get("revita_immune_plus", False), key="revita_immune_plus_checkbox")
            revita_heal = st.checkbox("Revita Heal (2x)", value=infusion_data.get("revita_heal", False), key="revita_heal_checkbox")
            revita_bludder = st.checkbox("RevitaBludder", value=infusion_data.get("revita_bludder", False), key="revita_bludder_checkbox")
            revita_ferro = st.checkbox("RevitaFerro", value=infusion_data.get("revita_ferro", False), key="revita_ferro_checkbox")
            revita_energy = st.checkbox("RevitaEnergyBoost", value=infusion_data.get("revita_energy", False), key="revita_energy_checkbox")
            revita_focus = st.checkbox("RevitaFocus", value=infusion_data.get("revita_focus", False), key="revita_focus_checkbox")
        with col2:
            revita_nad = st.checkbox("RevitaNAD+", value=infusion_data.get("revita_nad", False), key="revita_nad_checkbox")
            revita_relax = st.checkbox("RevitaRelax", value=infusion_data.get("revita_relax", False), key="revita_relax_checkbox")
            revita_fit = st.checkbox("RevitaFit", value=infusion_data.get("revita_fit", False), key="revita_fit_checkbox")
            revita_hangover = st.checkbox("RevitaHangover", value=infusion_data.get("revita_hangover", False), key="revita_hangover_checkbox")
            revita_beauty = st.checkbox("RevitaBeauty", value=infusion_data.get("revita_beauty", False), key="revita_beauty_checkbox")
            revita_antiaging = st.checkbox("RevitaAnti-Aging", value=infusion_data.get("revita_antiaging", False), key="revita_antiaging_checkbox")
            revita_detox = st.checkbox("RevitaDetox", value=infusion_data.get("revita_detox", False), key="revita_detox_checkbox")
        
        col1, col2 = st.columns(2)
        with col1:
            revita_chelate = st.checkbox("RevitaChelate", value=infusion_data.get("revita_chelate", False), key="revita_chelate_checkbox")
            revita_liver = st.checkbox("RevitaLiver", value=infusion_data.get("revita_liver", False), key="revita_liver_checkbox")
            revita_leakygut = st.checkbox("RevitaLeaky-gut", value=infusion_data.get("revita_leakygut", False), key="revita_leakygut_checkbox")
        with col2:
            revita_infection = st.checkbox("RevitaInfection", value=infusion_data.get("revita_infection", False), key="revita_infection_checkbox")
            revita_joint = st.checkbox("RevitaJoint", value=infusion_data.get("revita_joint", False), key="revita_joint_checkbox")

        st.markdown("---")
        
        # Sub-section: Standard Infusionen
        st.markdown("**Standard Infusionen**")
        col1, col2 = st.columns(2)
        with col1:
            mito_energy = st.checkbox("Mito-Energy Behandlung (Mito-Gerät, Wirkbooster)", 
                                    value=infusion_data.get("mito_energy", False),
                                    key="mito_energy_checkbox")
            schwermetalltest = st.checkbox("Schwermetalltest mit DMSA und Ca EDTA", 
                                        value=infusion_data.get("schwermetalltest", False),
                                        key="schwermetalltest_checkbox2")
            procain_basen = st.checkbox("Procain Baseninfusion mit Magnesium", 
                                    value=infusion_data.get("procain_basen", False),
                                    key="procain_basen_checkbox")
            procain_2percent = st.text_input("Procain 2% (ml)", 
                                        value=infusion_data.get("procain_2percent", ""),
                                        key="procain_2percent_input")
            artemisinin = st.checkbox("Artemisinin Infusion mit 2x Lysin", 
                                    value=infusion_data.get("artemisinin", False),
                                    key="artemisinin_checkbox")
        with col2:
            perioperative = st.checkbox("Perioperative Infusion (3 Infusionen)", 
                                    value=infusion_data.get("perioperative", False),
                                    key="perioperative_checkbox")
            detox_standard = st.checkbox("Detox-Infusion Standard", 
                                    value=infusion_data.get("detox_standard", False),
                                    key="detox_standard_checkbox")
            detox_maxi = st.checkbox("Detox-Infusion Maxi", 
                                value=infusion_data.get("detox_maxi", False),
                                key="detox_maxi_checkbox")
            aufbauinfusion = st.checkbox("Aufbauinfusion nach Detox", 
                                    value=infusion_data.get("aufbauinfusion", False),
                                    key="aufbauinfusion_checkbox")
            infektions_infusion = st.text_input("Infektions-Infusion / H2O2 (Anzahl / ml)", 
                                            value=infusion_data.get("infektions_infusion", ""),
                                            key="infektions_infusion_input")
        
        col1, col2 = st.columns(2)
        with col1:
            immun_booster = st.selectbox("Immun-Boosterung Typ", ["", "Typ 1", "Typ 2", "Typ 3"], 
                                    index=["", "Typ 1", "Typ 2", "Typ 3"].index(
                                        infusion_data.get("immun_booster", "")),
                                    key="immun_booster_select")
            oxyvenierung = st.checkbox("Oxyvenierung (10–40 ml, 10er Serie)", 
                                    value=infusion_data.get("oxyvenierung", False),
                                    key="oxyvenierung_checkbox")
            energetisierungsinfusion = st.multiselect("Energetisierungsinfusion mit", 
                                                    ["Vitamin B Shot", "Q10 Boostershot"],
                                                    default=infusion_data.get("energetisierungsinfusion", []),
                                                    key="energetisierungsinfusion_select")
            naehrstoffinfusion = st.multiselect("Nährstoffinfusion mit", 
                                            ["Glutathion", "Alpha Liponsäure"],
                                            default=infusion_data.get("naehrstoffinfusion", []),
                                            key="naehrstoffinfusion_select")
        with col2:
            anti_aging = st.checkbox("Anti Aging Infusion komplett", 
                                value=infusion_data.get("anti_aging", False),
                                key="anti_aging_checkbox")
            nerven_aufbau = st.checkbox("Nerven Aufbau Infusion", 
                                    value=infusion_data.get("nerven_aufbau", False),
                                    key="nerven_aufbau_checkbox")
            leberentgiftung = st.checkbox("Leberentgiftungsinfusion", 
                                        value=infusion_data.get("leberentgiftung", False),
                                        key="leberentgiftung_checkbox")
            anti_oxidantien = st.checkbox("Anti-Oxidantien Infusion", 
                                        value=infusion_data.get("anti_oxidantien", False),
                                        key="anti_oxidantien_checkbox")
        
        col1, col2 = st.columns(2)
        with col1:
            aminoinfusion = st.checkbox("Aminoinfusion leaky gut (5–10)", 
                                    value=infusion_data.get("aminoinfusion", False),
                                    key="aminoinfusion_checkbox")
            relax_infusion = st.checkbox("Relax Infusion", 
                                    value=infusion_data.get("relax_infusion", False),
                                    key="relax_infusion_checkbox")
        with col2:
            eisen_infusion = st.text_input("Eisen Infusion (Ferinject) mg / Anzahl", 
                                        value=infusion_data.get("eisen_infusion", ""),
                                        key="eisen_infusion_input")

        st.markdown("---")
        
        # Sub-section: Single Ingredients / Einzel
        st.markdown("**Single Ingredients / Einzel**")
        col1, col2 = st.columns(2)
        with col1:
            vitamin_c = st.text_input("Hochdosis Vitamin C (g)", 
                                    value=infusion_data.get("vitamin_c", ""),
                                    key="vitamin_c_input")
            vitamin_b_komplex = st.text_input("Vit. B-Komplex", 
                                            value=infusion_data.get("vitamin_b_komplex", ""),
                                            key="vitamin_b_komplex_input")
            vitamin_d = st.text_input("Vit. D", 
                                    value=infusion_data.get("vitamin_d", ""),
                                    key="vitamin_d_input")
        with col2:
            vitamin_b6_b12_folsaeure = st.text_input("Vit. B6/B12/Folsäure", 
                                                    value=infusion_data.get("vitamin_b6_b12_folsaeure", ""),
                                                    key="vitamin_b6_b12_folsaeure_input")
            vitamin_b3 = st.text_input("Vit. B3", 
                                    value=infusion_data.get("vitamin_b3", ""),
                                    key="vitamin_b3_input")

        st.markdown("---")
        
        # Sub-section: Häufigkeit & Dauer
        st.markdown("**Häufigkeit & Dauer**")
        col1, col2 = st.columns(2)
        with col1:
            wochen_haeufigkeit = st.selectbox("Wie oft", 
                                            ["", "1x/Woche", "2x/Woche", "3x/Woche", "Täglich"],
                                            index=["", "1x/Woche", "2x/Woche", "3x/Woche", "Täglich"].index(
                                                infusion_data.get("wochen_haeufigkeit", "")),
                                            key="wochen_haeufigkeit_select")
            therapie_beginn = st.date_input("Therapie Beginn",
                                            value=infusion_data.get("therapie_beginn", date.today()),
                                            format="DD.MM.YYYY",
                                            key="therapie_beginn_input2")
        with col2:
            therapie_ende = st.date_input("Therapie Ende",
                                        value=infusion_data.get("therapie_ende", date.today()),
                                        format="DD.MM.YYYY",
                                        key="therapie_ende_input")
            therapie_dauer = st.text_input("Dauer (Wochen/Monate)",
                                        value=infusion_data.get("therapie_dauer", ""),
                                        key="therapie_dauer_input")

        st.markdown("---")
        
        # Sub-section: Zusätze
        st.markdown("**Zusätze**")
        zusaetze = st.multiselect(
            "Zusätze auswählen",
            ["Vit.B Komplex", "Vit.B6/B12/Folsäure", "Vit.D 300 kIE", "Vit.B3", "Biotin", "Glycin",
            "Cholincitrat", "Zink inject", "Magnesium 400mg", "TAD (red.Glut.)", "Arginin", "Glutamin",
            "Taurin", "Ornithin", "Prolin/Lysin", "Lysin", "PC 1000mg", "Oxyvenierung", "Mito-Energy"],
            default=infusion_data.get("zusaetze", []),
            key="zusaetze_select"
        )
        
        # Update session state for infusion data
        st.session_state.infusion_data = {
            # RevitaClinic Infusionen
            "revita_immune": revita_immune,
            "revita_immune_plus": revita_immune_plus,
            "revita_heal": revita_heal,
            "revita_bludder": revita_bludder,
            "revita_ferro": revita_ferro,
            "revita_energy": revita_energy,
            "revita_focus": revita_focus,
            "revita_nad": revita_nad,
            "revita_relax": revita_relax,
            "revita_fit": revita_fit,
            "revita_hangover": revita_hangover,
            "revita_beauty": revita_beauty,
            "revita_antiaging": revita_antiaging,
            "revita_detox": revita_detox,
            "revita_chelate": revita_chelate,
            "revita_liver": revita_liver,
            "revita_leakygut": revita_leakygut,
            "revita_infection": revita_infection,
            "revita_joint": revita_joint,
            
            # Standard Infusionen
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
            
            # Single Ingredients
            "vitamin_c": vitamin_c,
            "vitamin_b_komplex": vitamin_b_komplex,
            "vitamin_d": vitamin_d,
            "vitamin_b6_b12_folsaeure": vitamin_b6_b12_folsaeure,
            "vitamin_b3": vitamin_b3,
            
            # Häufigkeit & Dauer
            "wochen_haeufigkeit": wochen_haeufigkeit,
            "therapie_beginn": therapie_beginn,
            "therapie_ende": therapie_ende,
            "therapie_dauer": therapie_dauer,
            
            # Zusätze
            "zusaetze": zusaetze
        }
        
        # Combined data for PDF generation
        combined_infusion_data = st.session_state.infusion_data
        
        # PDF button for Infusionstherapie
        if st.button("Infusionstherapie PDF generieren", key="infusion_pdf_button"):
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