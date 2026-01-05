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
    return pd.read_sql("SELECT * FROM supplements ORDER BY id", conn)

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
                    int(prescription["Dauer"].replace(" M", "")),
                    str(prescription.get("Darreichungsform", "")),
                    str(prescription.get("Dosierung", "")),
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
                    "Dauer": f"{int(row['dauer'])} M" if pd.notna(row['dauer']) else "0 M",
                    "Darreichungsform": str(row["darreichungsform"]) if pd.notna(row["darreichungsform"]) else "",
                    "Dosierung": str(row["dosierung"]) if pd.notna(row["dosierung"]) else "",
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
.stTabs [data-baseweb="tab-list"] {
    gap: 24px;
}

.stTabs [data-baseweb="tab"] {
    height: 50px;
    white-space: pre-wrap;
    background-color: #f0f2f6;
    border-radius: 4px 4px 0px 0px;
    gap: 1px;
    padding-top: 10px;
    padding-bottom: 10px;
    color: rgb(38, 96, 65);
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

# --- Default Darreichungsformen for known supplements ---
DEFAULT_FORMS = {
    "Magnesiumbisglycinat": "Pulver",
    "Magnesiumthreonat": "Pulver",
    "Liposomales Magnesium 200mg": "Kapseln",
    "Vitamin C Pulver/Na Ascorbatpulver": "Pulver",
    "Vitamin C 1000mg": "Kapseln",
    "L-Carnitin (Carnipure)": "Kapseln",
    "L-Carnitin (Carnipure) Lösung": "Lösung",
    "Q10 400mg": "Kapseln",
    "OPC": "Kapseln", 
    "Lugolsche (Jod) 5% Tropfen": "Lösung",
    "Lactoferrin": "Kapseln",
    "Alpha GPC": "Kapseln",
    "NMN 500mg": "Kapseln",
    "Citicoline": "Kapseln",
    "TransResveratol 1000mg": "Kapseln",
    "Astaxanthin 18mg": "Kapseln",
    "Lutein 40 mg": "Kapseln",
    "MAP (Aminosäuremischung)": "Pulver",
    "Tyrosin 500mg": "Kapseln",
    "Lysin": "Pulver",
    "Prolin": "Pulver"
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
        "clicked_suggestion": None,
        "patient_name_input": "",
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
        if result and result[0]:
            patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result

            st.session_state.patient_data = patient_data
            st.session_state.nem_prescriptions = nem_prescriptions
            st.session_state.therapieplan_data = therapieplan_data
            st.session_state.ernaehrung_data = ernaehrung_data
            st.session_state.infusion_data = infusion_data

            st.session_state.last_loaded_patient = name
            st.session_state.patient_name_input = name
            st.session_state.just_loaded_patient = True

        st.session_state.clicked_suggestion = None
        st.rerun()

    # --------------------------------------------------
    # Patient name input (SOURCE OF TRUTH)
    # --------------------------------------------------
    st.text_input(
        "Geben Sie den Namen ein und drücken Sie die Eingabetaste, um Vorschläge zu suchen.",
        key="patient_name_input",
        placeholder="Vor- und Nachname",
    )

    typed = st.session_state.patient_name_input.strip()

    # --------------------------------------------------
    # User typing → clear previously loaded patient
    # --------------------------------------------------
    if (
        st.session_state.last_loaded_patient
        and typed
        and typed != st.session_state.last_loaded_patient
        and typed not in patient_names
    ):
        st.session_state.patient_data = {}
        st.session_state.nem_prescriptions = []
        st.session_state.therapieplan_data = {}
        st.session_state.ernaehrung_data = {}
        st.session_state.infusion_data = {}
        st.session_state.last_loaded_patient = None
        st.session_state.just_loaded_patient = False

    # --------------------------------------------------
    # Suggestions
    # --------------------------------------------------
    suggestions = [
        n for n in patient_names
        if typed and typed.lower() in n.lower()
    ]

    if typed and suggestions and not st.session_state.just_loaded_patient:
        st.write("**Vorschläge:**")
        for name in suggestions[:7]:
            if st.button(name, key=f"suggest_{name}"):
                st.session_state.clicked_suggestion = name
                st.rerun()

    # --------------------------------------------------
    # Auto-load on Enter (exact match)
    # --------------------------------------------------
    if (
        typed
        and typed in patient_names
        and typed != st.session_state.last_loaded_patient
        and not st.session_state.just_loaded_patient
    ):
        result = load_patient_data(conn, typed)
        if result and result[0]:
            patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result

            st.session_state.patient_data = patient_data
            st.session_state.nem_prescriptions = nem_prescriptions
            st.session_state.therapieplan_data = therapieplan_data
            st.session_state.ernaehrung_data = ernaehrung_data
            st.session_state.infusion_data = infusion_data

            st.session_state.last_loaded_patient = typed
            st.session_state.just_loaded_patient = True
            st.rerun()

    # Reset flag after UI stabilizes
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
            "Geschlecht", ["M", "W"],
            horizontal=True,
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
        # Replace en dash and em dash with regular dash
        text = str(text)
        text = text.replace('–', '-')  # en dash
        text = text.replace('—', '-')  # em dash
        text = text.replace('−', '-')  # minus sign
        # Remove or replace other unsupported characters
        # Add more replacements as needed
        return text

    # REMOVE the duplicate title here since it's now in the header
    # Patient info starts directly
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Vor- und Nachname:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, clean_text(patient.get("patient", "")), 0, 1)  # Clean the text
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
    pdf.cell(col_w[7], 6, allergie_text, 0, 1)
    pdf.ln(3)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Diagnosen:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    diagnosen = patient.get("diagnosen", "") or "-"
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

        headers = ["Supplement", "Dauer", "Darreichungsform", "Dosierung", "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]
        base_widths = [50, 14, 35, 19, 18, 18, 18, 18, 18]
        used_width = sum(base_widths)
        comment_width = table_width - used_width
        widths = base_widths + [comment_width]

        pdf.set_font("Helvetica", "B", 10)
        for w, h in zip(widths, headers):
            pdf.cell(w, 8, h, 1, 0, "C", True)
        pdf.ln()

        pdf.set_text_color(0, 0, 0)
        pdf.set_font("Helvetica", "", 9)

        # Update the supplement rows to use clean_text
        for s in supplements:
            row = [
                clean_text(s.get("name", "")),  # Clean each field
                clean_text(s.get("Dauer", "")),
                clean_text(s.get("Darreichungsform", "")),
                clean_text(s.get("Dosierung", "")), 
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
    else:
        # For other tabs, display the data
        pdf.set_font("Helvetica", "B", 12)
        pdf.cell(0, 8, "Empfehlungen & Maßnahmen:", 0, 1, "L")
        pdf.ln(2)
        
        pdf.set_font("Helvetica", "", 10)
        if isinstance(supplements, dict):
            for key, value in supplements.items():
                if value:
                    if isinstance(value, bool) and value:
                        pdf.multi_cell(0, 5, f"• {key}", 0, "L")
                    elif isinstance(value, str) and value.strip():
                        pdf.multi_cell(0, 5, f"• {key}: {value}", 0, "L")
                    elif isinstance(value, list) and value:
                        pdf.multi_cell(0, 5, f"• {key}: {', '.join(value)}", 0, "L")

    return bytes(pdf.output(dest="S"))

# --- Main app ---
def main():
    conn = get_conn()
    df = fetch_supplements(conn)

    # --- Patient Info ---
    patient = patient_inputs(conn)

    # Initialize override keys for each supplement in session_state
    for _, row in df.iterrows():
        override_key = f"dauer_override_{row['id']}"
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
        "Nahrungsergänzungsmittel (NEM) VO",
        "Therapieplan – Übersicht & Maßnahmen",
        "Ernährungstherapie – Lifestyleänderung",
        "Infusionstherapie"
    ])

    # Initialize selected list for NEM prescriptions
    selected = []
    therapieplan_data = {}
    ernaehrung_data = {}
    infusion_data = {}

    with tabs[0]:
        # --------------------------------------------------
        # NEM SECTION
        # --------------------------------------------------
        nem_container = st.container()

        with nem_container:

            if "nem_form_initialized" not in st.session_state:
                st.session_state.nem_form_initialized = True

            if "last_main_dauer" not in st.session_state:
                st.session_state.last_main_dauer = patient["dauer"]

            with st.form("nem_form", clear_on_submit=False):

                # Sync Dauer overrides if main Dauer changes
                if st.session_state.last_main_dauer != patient["dauer"]:
                    for _, row in df.iterrows():
                        override_key = f"dauer_override_{row['id']}"
                        widget_key = f"{row['id']}_dauer"

                        if st.session_state.get(override_key) is None:
                            if st.session_state.get(widget_key) != patient["dauer"]:
                                st.session_state[widget_key] = patient["dauer"]

                    st.session_state.last_main_dauer = patient["dauer"]

                # ---------- UI HEADER ----------
                header_cols = st.columns([2.2, 0.7, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])
                headers = [
                    "Supplement", "Dauer (M)", "Darreichungsform", "Dosierung",
                    "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"
                ]
                for col, text in zip(header_cols, headers):
                    col.markdown(f"**{text}**")

                st.markdown("---")

                all_supplements_data = []

                # ---------- TABLE ROWS ----------
                for _, row in df.iterrows():
                    cols = st.columns([2.2, 0.7, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])

                    supplement_name = row["name"]
                    cols[0].markdown(supplement_name)

                    override_key = f"dauer_override_{row['id']}"

                    loaded = None
                    for p in st.session_state.nem_prescriptions:
                        if p.get("name") == supplement_name:
                            loaded = p
                            break

                    # ---------- INITIAL VALUES ----------
                    if loaded:
                        init_dauer = int(loaded["Dauer"].replace(" M", ""))
                        init_form = loaded["Darreichungsform"]
                        init_dos = loaded["Dosierung"]
                        init_nue = loaded["Nüchtern"]
                        init_morg = loaded["Morgens"]
                        init_mitt = loaded["Mittags"]
                        init_ab = loaded["Abends"]
                        init_na = loaded["Nachts"]
                        init_com = loaded["Kommentar"]
                    else:
                        init_dauer = (
                            st.session_state.get(override_key)
                            if st.session_state.get(override_key) is not None
                            else patient["dauer"]
                        )
                        init_form = DEFAULT_FORMS.get(supplement_name, "Kapseln")
                        init_dos = init_nue = init_morg = init_mitt = init_ab = init_na = init_com = ""

                    # ---------- KEYS ----------
                    k = row["id"]
                    dauer_key = f"{k}_dauer"
                    form_key = f"{k}_form"
                    dos_key = f"{k}_dos"
                    nue_key = f"{k}_nue"
                    morg_key = f"{k}_morg"
                    mitt_key = f"{k}_mitt"
                    ab_key = f"{k}_ab"
                    na_key = f"{k}_na"
                    com_key = f"{k}_com"

                    # ---------- INPUTS ----------
                    dauer_val = cols[1].number_input(
                        "", min_value=1, max_value=12, value=int(init_dauer),
                        key=dauer_key, label_visibility="collapsed"
                    )

                    forms = ["Kapseln", "Tabletten", "Pulver", "Tropfen", "Andere:"]
                    form_idx = forms.index(init_form) if init_form in forms else forms.index("Andere:")
                    form_val = cols[2].selectbox("", forms, index=form_idx, key=form_key, label_visibility="collapsed")

                    dos_opts = ["", "100mg", "200mg", "300mg", "400mg", "500mg"]
                    dos_val = cols[3].selectbox("", dos_opts, index=dos_opts.index(init_dos) if init_dos in dos_opts else 0,
                                                key=dos_key, label_visibility="collapsed")

                    dose_opts = ["", "1", "2", "3", "4", "5"]
                    nue = cols[4].selectbox("", dose_opts, index=dose_opts.index(init_nue) if init_nue in dose_opts else 0,
                                            key=nue_key, label_visibility="collapsed")
                    morg = cols[5].selectbox("", dose_opts, index=dose_opts.index(init_morg) if init_morg in dose_opts else 0,
                                            key=morg_key, label_visibility="collapsed")
                    mitt = cols[6].selectbox("", dose_opts, index=dose_opts.index(init_mitt) if init_mitt in dose_opts else 0,
                                            key=mitt_key, label_visibility="collapsed")
                    ab = cols[7].selectbox("", dose_opts, index=dose_opts.index(init_ab) if init_ab in dose_opts else 0,
                                        key=ab_key, label_visibility="collapsed")
                    na = cols[8].selectbox("", dose_opts, index=dose_opts.index(init_na) if init_na in dose_opts else 0,
                                        key=na_key, label_visibility="collapsed")

                    com = cols[9].text_input("", value=init_com, key=com_key,
                                            label_visibility="collapsed", placeholder="Kommentar")

                    # ---------- OVERRIDE SYNC ----------
                    st.session_state[override_key] = dauer_val if dauer_val != patient["dauer"] else None

                    # ---------- COLLECT ----------
                    all_supplements_data.append({
                        "name": supplement_name,
                        "Dauer": f"{dauer_val} M",
                        "Darreichungsform": form_val if form_val != "Andere:" else "",
                        "Dosierung": dos_val,
                        "Nüchtern": nue,
                        "Morgens": morg,
                        "Mittags": mitt,
                        "Abends": ab,
                        "Nachts": na,
                        "Kommentar": com,
                    })

                pdf_submitted = st.form_submit_button("📄 NEM PDF generieren")

            # --------------------------------------------------
            # 🔑 ALWAYS SAVE TABLE STATE (MAIN FIX)
            # --------------------------------------------------
            st.session_state.nem_prescriptions = all_supplements_data

            # --------------------------------------------------
            # PDF FILTER (ONLY PRESCRIBED)
            # --------------------------------------------------
            if pdf_submitted:

                def is_prescribed(p):
                    return any([
                        p["Dosierung"],
                        p["Kommentar"],
                        p["Nüchtern"], p["Morgens"], p["Mittags"], p["Abends"], p["Nachts"],
                        p["Dauer"] != f"{patient['dauer']} M",
                    ])

                pdf_data = [p for p in all_supplements_data if is_prescribed(p)]

                if not pdf_data:
                    st.warning("⚠️ Keine NEM-Supplemente ausgewählt.")
                else:
                    pdf_bytes = generate_pdf(patient, pdf_data, "NEM")
                    st.session_state.auto_download_pdf = {
                        "data": pdf_bytes,
                        "filename": f"RevitaClinic_NEM_{patient['patient']}.pdf",
                        "mime": "application/pdf",
                    }
                    st.success(f"✅ PDF mit {len(pdf_data)} Supplement(en) erstellt")
                    st.rerun()



    # TAB 2: Therapieplan
    with tabs[1]:
        therapieplan_data = st.session_state.therapieplan_data
        
        st.markdown("### Diagnostik & Überprüfung")
        zaehne = st.checkbox("Überprüfung der Zähne/Kieferknochen mittels OPG (Panoramaaufnahme mit lachendem Gebiss) / DVT", 
                           value=therapieplan_data.get("zaehne", False))
        zaehne_zu_pruefen = st.text_input("Zähne zu überprüfen:", 
                                        value=therapieplan_data.get("zaehne_zu_pruefen", ""))

        st.markdown("### Darm & Entgiftung")
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
        parasiten_bio = st.checkbox("Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)", 
                                  value=therapieplan_data.get("parasiten_bio", False))
        leberdetox = st.checkbox("Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5× alle 4–6 Wochen)", 
                               value=therapieplan_data.get("leberdetox", False))
        nierenprogramm = st.checkbox("Nierenprogramm nach Dr. Clark – 4 Wochen – bitte bei www.drclarkcenter.de beziehen", 
                                    value=therapieplan_data.get("nierenprogramm", False))

        st.markdown("### Infektionen & Ausleitung")
        infektion_bakt = st.text_input("Infektionsbehandlung für Bakterien (Borr./Helicob.):", 
                                     value=therapieplan_data.get("infektion_bakt", ""))
        infektion_virus = st.text_input("Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona):", 
                                      value=therapieplan_data.get("infektion_virus", ""))
        ausleitung_inf = st.checkbox("Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom mit Infusionen", 
                                    value=therapieplan_data.get("ausleitung_inf", False))
        ausleitung_oral = st.checkbox("Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom oral", 
                                     value=therapieplan_data.get("ausleitung_oral", False))

        st.markdown("### Therapieformen")
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
        bio_isopath = st.checkbox("Biologische / Isopathische Therapie", 
                                 value=therapieplan_data.get("bio_isopath", False))
        timewaver_analyse = st.checkbox("Timewaver Analyse", 
                                       value=therapieplan_data.get("timewaver_analyse", False))
        timewaver_freq = st.checkbox("Timewaver Frequency Behandlung", 
                                    value=therapieplan_data.get("timewaver_freq", False))
        weitere_labor = st.checkbox("Weitere Labordiagnostik (z. B. IMD, Dedimed, MMD, NextGen Onco)", 
                                   value=therapieplan_data.get("weitere_labor", False))

        st.markdown("### Ergänzende Therapieformen")
        ernaehrung = st.checkbox("Ernährungsänderung und -beratung", 
                               value=therapieplan_data.get("ernaehrung", False))
        hypnose = st.checkbox("Hypnosetherapie", 
                             value=therapieplan_data.get("hypnose", False))
        yager = st.checkbox("Yagertherapie", 
                           value=therapieplan_data.get("yager", False))
        energetisch = st.checkbox("Energetische Behandlung (Marie / Noreen / Martin / KU / Sandra)", 
                                 value=therapieplan_data.get("energetisch", False))

        # Collect data
        therapieplan_data = {
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

        # Update session state
        st.session_state.therapieplan_data = therapieplan_data

        # PDF button
        if st.button("Therapieplan PDF generieren"):
            pdf_bytes = generate_pdf(patient, therapieplan_data, "THERAPIEPLAN")
            filename = f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf"
            
            # Set auto-download
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": filename,
                "mime": "application/pdf"
            }
            st.rerun()

    # TAB 3: Ernährung
    with tabs[2]:
        ernaehrung_data = st.session_state.ernaehrung_data
        
        st.markdown("### Darmsanierung / Leberdetox")
        darmsanierung = st.checkbox("Darmsanierung nach Paracelsus Klinik", 
                                  value=ernaehrung_data.get("darmsanierung", False))
        leberdetox = st.radio("Leberdetox", ["Keine", "2 Tage Kurz-Intensiv", "5 Tage Standard"], 
                            index=["Keine", "2 Tage Kurz-Intensiv", "5 Tage Standard"].index(
                                ernaehrung_data.get("leberdetox", "Keine")))

        st.markdown("### Ernährungskonzepte")
        lowcarb = st.checkbox("Low Carb Ernährung (viel Protein und viel gesundes Fett/Öl)", 
                            value=ernaehrung_data.get("lowcarb", False))
        proteinmenge = st.text_input("Proteinmenge", placeholder="z. B. 1,5 g / kg KG", 
                                   value=ernaehrung_data.get("proteinmenge", ""))
        fasten = st.checkbox("Intermittierendes Fasten / 4-tägiges Fasten", 
                           value=ernaehrung_data.get("fasten", False))
        krebsdiaet = st.checkbox("Krebs-Diät nach Dr. Coy / Dr. Strunz / Budwig", 
                               value=ernaehrung_data.get("krebsdiaet", False))
        keto = st.checkbox("Ketogene Ernährung", 
                         value=ernaehrung_data.get("keto", False))
        oelziehen = st.checkbox("Ölziehen mit Kokosöl (2x10 Min. nach dem Zähneputzen)", 
                              value=ernaehrung_data.get("oelziehen", False))
        detox_vacc = st.checkbox("Detox vacc Protokoll (3–12 Monate, gelb markiert)", 
                               value=ernaehrung_data.get("detox_vacc", False))

        st.markdown("### Sonstige Empfehlungen")
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
        fluoridfrei = st.checkbox("Fluoridfreies Leben (Zahnpasta, Salz etc.)", 
                                value=ernaehrung_data.get("fluoridfrei", False))
        wasserfilter = st.checkbox("Wasserfilter (Umkehrosmose oder Tischfilter, z. B. Maunaway)", 
                                 value=ernaehrung_data.get("wasserfilter", False))
        atem = st.checkbox("Atemtherapie (z. B. Wim Hof oder Yoga)", 
                         value=ernaehrung_data.get("atem", False))
        beratung = st.checkbox("Ernährungsberatung", 
                             value=ernaehrung_data.get("beratung", False))

        st.markdown("### Bewegung")
        ruecken = st.checkbox("Rückentraining (z. B. Kieser Training)", 
                            value=ernaehrung_data.get("ruecken", False))
        cardio = st.checkbox("Cardio", 
                           value=ernaehrung_data.get("cardio", False))
        ausdauer = st.checkbox("Ausdauertraining", 
                             value=ernaehrung_data.get("ausdauer", False))
        trampolin = st.checkbox("Trampolin", 
                              value=ernaehrung_data.get("trampolin", False))
        barre = st.checkbox("Barre Mobility – Bewegungsapparat in Balance (150€)", 
                          value=ernaehrung_data.get("barre", False))

        # Collect data
        ernaehrung_data = {
            "darmsanierung": darmsanierung,
            "leberdetox": leberdetox,
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

        # Update session state
        st.session_state.ernaehrung_data = ernaehrung_data

        # PDF button
        if st.button("Ernährung & Lifestyle PDF generieren"):
            pdf_bytes = generate_pdf(patient, ernaehrung_data, "ERNÄHRUNG & LIFESTYLE")
            filename = f"RevitaClinic_Ernaehrung_{patient.get('patient', '')}.pdf"
            
            # Set auto-download
            st.session_state.auto_download_pdf = {
                "data": pdf_bytes,
                "filename": filename,
                "mime": "application/pdf"
            }
            st.rerun()

    # TAB 4: Infusion
    with tabs[3]:
        infusion_data = st.session_state.infusion_data
        
        st.markdown("### Infusionen")
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
        naehrstoffinfusion = st.multiselect("Nährstoffinfusion mit", 
                                          ["Glutathion", "Alpha Liponsäure"],
                                          default=infusion_data.get("naehrstoffinfusion", []))
        anti_aging = st.checkbox("Anti Aging Infusion komplett", 
                               value=infusion_data.get("anti_aging", False))
        nerven_aufbau = st.checkbox("Nerven Aufbau Infusion", 
                                  value=infusion_data.get("nerven_aufbau", False))
        leberentgiftung = st.checkbox("Leberentgiftungsinfusion", 
                                    value=infusion_data.get("leberentgiftung", False))
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

        st.markdown("### Zusätze")
        zusaetze = st.multiselect(
            "Zusätze auswählen",
            ["Vit.B Komplex", "Vit.B6/B12/Folsäure", "Vit.D 300 kIE", "Vit.B3", "Biotin", "Glycin",
             "Cholincitrat", "Zink inject", "Magnesium 400mg", "TAD (red.Glut.)", "Arginin", "Glutamin",
             "Taurin", "Ornithin", "Prolin/Lysin", "Lysin", "PC 1000mg"],
            default=infusion_data.get("zusaetze", [])
        )

        # Collect data
        infusion_data = {
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

        # Update session state
        st.session_state.infusion_data = infusion_data

        # PDF button
        if st.button("Infusionstherapie PDF generieren"):
            pdf_bytes = generate_pdf(patient, infusion_data, "INFUSIONSTHERAPIE")
            timestamp = time.strftime("%Y%m%d_%H%M%S")
            filename = f"RevitaClinic_Infusion_{patient.get('patient', '')}_{timestamp}.pdf"
            
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
