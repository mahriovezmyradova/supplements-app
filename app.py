import os
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image
import time

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
                prescription_values = (
                    patient_id,
                    supplement_id,
                    int(prescription["Dauer"].replace(" M", "")),
                    prescription["Darreichungsform"],
                    prescription["Dosierung"],
                    prescription["Nüchtern"],
                    prescription["Morgens"],
                    prescription["Mittags"],
                    prescription["Abends"],
                    prescription["Nachts"],
                    prescription["Kommentar"]
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
            return None, {}, {}, {}, {}
        
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
        for _, row in nem_df.iterrows():
            nem_prescriptions.append({
                "name": row["name"],
                "Dauer": f"{row['dauer']} M",
                "Darreichungsform": row["darreichungsform"],
                "Dosierung": row["dosierung"],
                "Nüchtern": row["nuechtern"],
                "Morgens": row["morgens"],
                "Mittags": row["mittags"],
                "Abends": row["abends"],
                "Nachts": row["nachts"],
                "Kommentar": row["kommentar"]
            })
        
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
        return None, {}, {}, {}, {}

# --- Improved Header with better centering ---
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
    "Lactoferrin": "Kapsel",
    "Alpha GPC": "Kapseln",
    "NMN 500mg": "Kapsel",
    "Citicoline": "Kapseln",
    "TransResveratol 1000mg": "Kapseln",
    "Astaxanthin 18mg": "Kapseln",
    "Lutein 40 mg": "Kapseln",
    "MAP (Aminosäuremischung)": "Pulver",
    "Tyrosin 500mg": "Kapseln",
    "Lysin": "Pulver",
    "Prolin": "Pulver"
}

# --- Patient inputs with proper autocomplete ---
def patient_inputs(conn):
    # Get patient names for autocomplete
    patient_names_df = fetch_patient_names(conn)
    patient_names = patient_names_df['patient_name'].tolist() if not patient_names_df.empty else []
    

    # Initialize session state
    if 'patient_data' not in st.session_state:
        st.session_state.patient_data = {}
    if 'nem_prescriptions' not in st.session_state:
        st.session_state.nem_prescriptions = []
    if 'therapieplan_data' not in st.session_state:
        st.session_state.therapieplan_data = {}
    if 'ernaehrung_data' not in st.session_state:
        st.session_state.ernaehrung_data = {}
    if 'infusion_data' not in st.session_state:
        st.session_state.infusion_data = {}
    if 'last_loaded_patient' not in st.session_state:
        st.session_state.last_loaded_patient = None

    # Header controls (save, delete) - placed at the top
    st.markdown("#### Patientendaten")
    
    # --- Free text input with optional suggestions ---
    typed = st.text_input(
        "Vor- und Nachname",
        value=st.session_state.patient_data.get("patient_name", ""),
        placeholder="Geben Sie den Namen ein und drücken Sie die Eingabetaste, um Vorschläge zu suchen."
    )

    # Suggestions (filtered)
    suggestions = [name for name in patient_names if typed.lower() in name.lower()]

    if typed and suggestions:
        st.write("**Vorschläge:**")

        for name in suggestions[:7]:
            if st.button(f"{name}", key=f"suggest_{name}"):
                # Load patient immediately
                result = load_patient_data(conn, name)
                if result[0]:
                    patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data = result
                    st.session_state.patient_data = patient_data
                    st.session_state.nem_prescriptions = nem_prescriptions
                    st.session_state.therapieplan_data = therapieplan_data
                    st.session_state.ernaehrung_data = ernaehrung_data
                    st.session_state.infusion_data = infusion_data
                    st.session_state.last_loaded_patient = name
                    st.rerun()

    # Use typed name as patient name
    patient_name_input = typed


    # Compact Row with 7 fields
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1, 1, 1])

    with c1:
        geburtsdatum = st.date_input(
            "Geburtsdatum",
            format="DD.MM.YYYY",
            value=st.session_state.patient_data.get("geburtsdatum", date.today())
        )

    with c2:
        geschlecht_options = ["M", "W"]
        geschlecht_default = st.session_state.patient_data.get("geschlecht", "M")
        geschlecht = st.radio(
            "Geschlecht",
            geschlecht_options,
            horizontal=True,
            index=geschlecht_options.index(geschlecht_default)
            if geschlecht_default in geschlecht_options else 0
        )

    with c3:
        groesse = st.number_input(
            "Grösse (cm)",
            min_value=0,
            step=1,
            value=int(st.session_state.patient_data.get("groesse", 0))
        )

    with c4:
        gewicht = st.number_input(
            "Gewicht (kg)",
            min_value=0,
            step=1,
            value=int(st.session_state.patient_data.get("gewicht", 0))
        )

    with c5:
        therapiebeginn = st.date_input(
            "Therapiebeginn",
            format="DD.MM.YYYY",
            value=st.session_state.patient_data.get("therapiebeginn", date.today())
        )

    with c6:
        dauer_value = st.session_state.patient_data.get("dauer", 6)
        dauer = st.selectbox(
            "Dauer (Monate)",
            options=list(range(1, 13)),
            index=dauer_value - 1 if isinstance(dauer_value, int) and 1 <= dauer_value <= 12 else 5
        )

    with c7:
        tw_options = ["Ja", "Nein"]
        tw_default = st.session_state.patient_data.get("tw_besprochen", "Ja")
        tw_besprochen = st.radio(
            "TW besprochen?",
            tw_options,
            horizontal=True,
            index=tw_options.index(tw_default) if tw_default in tw_options else 0
        )

    # Allergie
    bekannte_allergie = st.text_input(
        "Bekannte Allergie?",
        value=st.session_state.patient_data.get("allergie", "")
    )

    # Diagnosen
    diagnosen = st.text_area(
        "Diagnosen",
        placeholder="Relevante Diagnosen...",
        height=100,
        value=st.session_state.patient_data.get("diagnosen", "")
    )

    # Final data object returned to main
    data = {
        "patient": patient_name_input or st.session_state.patient_data.get("patient_name", ""),
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

# PDF class and generate_pdf function
class PDF(FPDF):
    def header(self):
        if os.path.exists("clinic_logo.png"):
            try:
                self.image("clinic_logo.png", 10, 8, 40)
            except:
                pass
        self.set_font("Helvetica", "", 10)
        self.set_xy(230, 10)
        self.multi_cell(60, 5,
            "Clausewitzstr. 2\n10629 Berlin-Charlottenburg\n+49 30 6633110\ninfo@revitaclinic.de",
            0, "R"
        )
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100)
        self.cell(0, 10, "www.revitaclinic.de", 0, 0, "C")

def generate_pdf(patient, supplements, tab_name="NEM"):
    pdf = PDF("L", "mm", "A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, f"THERAPIEKONZEPT - {tab_name.upper()}", 0, 1, "L")
    pdf.ln(3)

    # Patient info
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Vor- und Nachname:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, patient.get("patient", ""), 0, 1)
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

        for s in supplements:
            row = [
                s.get("name", ""),
                s.get("Dauer", ""),
                s.get("Darreichungsform", ""),
                s.get("Dosierung", ""), 
                s.get("Nüchtern", ""),
                s.get("Morgens", ""),
                s.get("Mittags", ""),
                s.get("Abends", ""),
                s.get("Nachts", ""),
                s.get("Kommentar", "")
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

    # Save and Delete buttons at the top
    col1, col2, col3 = st.columns([1, 1, 1])
    with col1:
        save_button = st.button("💾 Alle Daten speichern", use_container_width=True, type="primary")
    with col2:
        # Delete button - only show if patient exists in database
        patient_names = fetch_patient_names(conn)['patient_name'].tolist()
        if patient["patient"] and patient["patient"] in patient_names:
            if st.button("🗑️ Patient löschen", use_container_width=True, type="secondary"):
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
            if st.button("❌ Ja, endgültig löschen", use_container_width=True, key="confirm_delete"):
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
            if st.button("✅ Abbrechen", use_container_width=True, key="cancel_delete"):
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

    # TAB 1: NEM
    with tabs[0]:
        # Store NEM prescriptions in a container to access outside the form
        nem_container = st.container()
        
        with nem_container:
            with st.form("nem_form", clear_on_submit=False):
                if "last_main_dauer" not in st.session_state:
                    st.session_state.last_main_dauer = patient["dauer"]

                if st.session_state.last_main_dauer != patient["dauer"]:
                    for _, row in df.iterrows():
                        override_key = f"dauer_override_{row['id']}"
                        widget_key = f"{row['id']}_dauer"
                        if st.session_state[override_key] is None:
                            current_val = st.session_state.get(widget_key)
                            if current_val != patient["dauer"]:
                                st.session_state.update({widget_key: patient["dauer"]})
                    st.session_state.last_main_dauer = patient["dauer"]

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
                    </style>
                """, unsafe_allow_html=True)

                # Header row
                header_cols = st.columns([2.2, 0.7, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])
                headers = ["Supplement", "Dauer (M)", "Darreichungsform", "Dosierung",
                           "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]

                for col, text in zip(header_cols, headers):
                    col.markdown(f"**{text}**")

                st.markdown("---")

                # Reset selected list for this form submission
                form_selected = []

                # Each supplement row
                for _, row in df.iterrows():
                    cols = st.columns([2.2, 0.7, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])

                    # Supplement name
                    cols[0].markdown(row["name"])

                    override_key = f"dauer_override_{row['id']}"

                    # Check if we have loaded prescriptions for this supplement
                    loaded_prescription = None
                    for prescription in st.session_state.nem_prescriptions:
                        if prescription["name"] == row["name"]:
                            loaded_prescription = prescription
                            break

                    # Determine initial values
                    if loaded_prescription:
                        initial_dauer = int(loaded_prescription["Dauer"].replace(" M", ""))
                        initial_form = loaded_prescription["Darreichungsform"]
                        initial_dosierung = loaded_prescription["Dosierung"]
                        initial_nue = loaded_prescription["Nüchtern"]
                        initial_morg = loaded_prescription["Morgens"]
                        initial_mitt = loaded_prescription["Mittags"]
                        initial_abend = loaded_prescription["Abends"]
                        initial_nacht = loaded_prescription["Nachts"]
                        initial_comment = loaded_prescription["Kommentar"]
                    else:
                        initial_dauer = st.session_state[override_key] if st.session_state[override_key] is not None else patient["dauer"]
                        initial_form = DEFAULT_FORMS.get(row["name"], "Kapseln")
                        initial_dosierung = ""
                        initial_nue = ""
                        initial_morg = ""
                        initial_mitt = ""
                        initial_abend = ""
                        initial_nacht = ""
                        initial_comment = ""

                    # Dauer input
                    dauer_input = cols[1].number_input(
                        "", key=f"{row['id']}_dauer", min_value=1, max_value=12, 
                        value=int(initial_dauer),
                        label_visibility="collapsed"
                    )

                    # Darreichungsform dropdown
                    dosage_presets = ["Kapseln", "Tabletten", "Pulver", "Tropfen", "Sachet", "TL", "EL", "ML","Andere:"]
                    
                    # Find index for initial form
                    form_index = dosage_presets.index(initial_form) if initial_form in dosage_presets else 0
                    
                    selected_form = cols[2].selectbox(
                        "", dosage_presets, index=form_index,
                        key=f"{row['id']}_darreichungsform", label_visibility="collapsed"
                    )

                    # Dosierung dropdown
                    dosierung_options = ["", "100mg", "200mg", "300mg", "400mg", "500mg"]
                    dosierung_index = dosierung_options.index(initial_dosierung) if initial_dosierung in dosierung_options else 0
                    dosierung_val = cols[3].selectbox(
                        "", dosierung_options, index=dosierung_index,
                        key=f"{row['id']}_dosierung", label_visibility="collapsed"
                    )

                    # Custom dosage text input
                    custom_form = ""
                    if selected_form == "Andere:":
                        custom_form = cols[2].text_input(
                            " ", key=f"{row['id']}_custom_dosage", placeholder="z. B. Pulver",
                            value=initial_form if initial_form not in dosage_presets else ""
                        )

                    # Sync override state
                    if dauer_input != patient["dauer"]:
                        st.session_state[override_key] = dauer_input
                    else:
                        st.session_state[override_key] = None

                    # Intake dropdowns
                    dose_options = ["", "1", "2", "3", "4", "5"]
                    
                    nue_val = cols[4].selectbox("", dose_options, 
                                              index=dose_options.index(initial_nue) if initial_nue in dose_options else 0,
                                              key=f"{row['id']}_Nuechtern", label_visibility="collapsed")
                    morg_val = cols[5].selectbox("", dose_options,
                                               index=dose_options.index(initial_morg) if initial_morg in dose_options else 0,
                                               key=f"{row['id']}_Morgens", label_visibility="collapsed")
                    mitt_val = cols[6].selectbox("", dose_options,
                                               index=dose_options.index(initial_mitt) if initial_mitt in dose_options else 0,
                                               key=f"{row['id']}_Mittags", label_visibility="collapsed")
                    abend_val = cols[7].selectbox("", dose_options,
                                                index=dose_options.index(initial_abend) if initial_abend in dose_options else 0,
                                                key=f"{row['id']}_Abends", label_visibility="collapsed")
                    nacht_val = cols[8].selectbox("", dose_options,
                                                index=dose_options.index(initial_nacht) if initial_nacht in dose_options else 0,
                                                key=f"{row['id']}_Nachts", label_visibility="collapsed")

                    # Kommentar field
                    comment = cols[9].text_input(
                        "", key=f"{row['id']}_comment", placeholder="Kommentar",
                        value=initial_comment, label_visibility="collapsed"
                    )

                    # Add supplement if any intake dropdown is selected
                    if any([nue_val, morg_val, mitt_val, abend_val, nacht_val]):
                        form_selected.append({
                            "name": row["name"],
                            "Dauer": f"{dauer_input} M",
                            "Darreichungsform": custom_form or selected_form,
                            "Dosierung": dosierung_val,
                            "Nüchtern": nue_val,
                            "Morgens": morg_val,
                            "Mittags": mitt_val,
                            "Abends": abend_val,
                            "Nachts": nacht_val,
                            "Kommentar": comment
                        })

                # Form submit button for PDF generation (without download button inside)
                pdf_submitted = st.form_submit_button("📄 NEM PDF generieren")
                
                # Handle form submission for PDF
                if pdf_submitted:
                    if not form_selected:
                        st.error("Bitte mindestens ein Supplement auswählen!")
                    else:
                        # Update the global selected list
                        selected.clear()
                        selected.extend(form_selected)
                        
                        # Update session state
                        st.session_state.nem_prescriptions = form_selected
                        
                        # Generate PDF and store in session state
                        st.session_state.nem_pdf_bytes = generate_pdf(patient, form_selected, "NEM")
                        st.success("PDF wurde generiert! Download-Button erscheint unten.")
                else:
                    # Update the global selected list even when form is not submitted for PDF
                    # This ensures the data is available for the save button
                    selected.clear()
                    selected.extend(form_selected)
                    st.session_state.nem_prescriptions = form_selected
        
        # Show PDF download button outside the form if PDF was generated
        if st.session_state.get("nem_pdf_bytes"):
            st.download_button(
                "⬇️ NEM PDF herunterladen",
                data=st.session_state.nem_pdf_bytes,
                file_name=f"RevitaClinic_NEM_{patient.get('patient','')}.pdf",
                mime="application/pdf",
                key="nem_pdf_download"
            )

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

        # PDF button
        if st.button("📄 Therapieplan PDF generieren"):
            pdf_bytes = generate_pdf(patient, therapieplan_data, "THERAPIEPLAN")
            st.download_button(
                "⬇️ Therapieplan-PDF herunterladen",
                data=pdf_bytes,
                file_name=f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf",
                mime="application/pdf"
            )

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

        # PDF button
        if st.button("📄 Ernährung & Lifestyle PDF generieren"):
            pdf_bytes = generate_pdf(patient, ernaehrung_data, "ERNÄHRUNG & LIFESTYLE")
            st.download_button(
                "⬇️ Ernährung & Lifestyle PDF herunterladen",
                data=pdf_bytes,
                file_name=f"RevitaClinic_Ernaehrung_{patient.get('patient', '')}.pdf",
                mime="application/pdf"
            )

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

        # PDF button
        if st.button("📄 Infusionstherapie PDF generieren"):
            pdf_bytes = generate_pdf(patient, infusion_data, "INFUSIONSTHERAPIE")
            st.download_button(
                "⬇️ Infusionstherapie PDF herunterladen",
                data=pdf_bytes,
                file_name=f"RevitaClinic_Infusion_{patient.get('patient', '')}.pdf",
                mime="application/pdf"
            )

    # Handle save button (saves all tabs)
    if save_button:
        if not patient["patient"]:
            st.error("Bitte Patientennamen eingeben!")
        else:
            # Update session state with current data from all tabs
            st.session_state.nem_prescriptions = selected
            st.session_state.therapieplan_data = therapieplan_data
            st.session_state.ernaehrung_data = ernaehrung_data
            st.session_state.infusion_data = infusion_data
            
            # Save all data
            if save_patient_data(conn, patient, selected, therapieplan_data, ernaehrung_data, infusion_data):
                # Set success flag and trigger rerun
                st.session_state.show_save_success = True
                st.session_state.last_loaded_patient = patient["patient"]
                # Force immediate rerun
                st.rerun()

if __name__ == "__main__":
    main()