import os, sqlite3, pandas as pd, streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image

st.set_page_config("THERAPIEKONZEPT","💊",layout="wide")

# --- Header ---
c1, c2 = st.columns([1,3])
with c1:
    if os.path.exists("clinic_logo.png"):
        st.image("clinic_logo.png", width=200)
with c2:
    st.markdown("""
    <div style="text-align:right; font-size:14px; line-height:1.4;">
    Clausewitz str. 2<br>
    10629 Berlin-Charlottenburg<br>
    +49 30 6633110<br>
    info@revitaclinic.de<br>
    www.revitaclinic.de
    </div>
    """, unsafe_allow_html=True)

st.markdown("<hr>", unsafe_allow_html=True)



# --- Database ---
DB_PATH = "app.db"
TIMES = ["Nüchtern", "Morgens", "Mittags", "Abends", "Nachts"]

def get_conn():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def fetch_supplements(conn):
    return pd.read_sql("SELECT * FROM supplements ORDER BY id", conn)

# --- Patient inputs ---
def patient_inputs():
    #st.subheader("Patientendaten")

    c1, c2 = st.columns([3, 2])
    with c1:
        patient_name = st.text_input("Patient", placeholder="Vor- und Nachname")
    with c2:
        geburtsdatum = st.date_input(
            "Geburtsdatum",
            format="DD.MM.YYYY",
            min_value=date(1960, 1, 1),
            max_value=date.today()
)


# All 5 fields in one row
    c3, c4, c5, c6, c7 = st.columns([1, 1, 2, 2, 2])
    with c3:
        groesse = st.number_input("Grösse (cm)", min_value=0, max_value=300, step=1)
    with c4:
        gewicht = st.number_input("Gewicht (kg)", min_value=0, max_value=500, step=1)
    with c5:
        therapiebeginn = st.date_input("Therapiebeginn", value=date.today(), format="DD.MM.YYYY")
    with c6:
        dauer = st.selectbox("Voraussichtliche Dauer (Monate)", options=list(range(1,7)), index=5)
    with c7:
        tw_besprochen = st.radio("TW besprochen?", options=["Ja","Nein"], horizontal=True)

    bekannte_allergie = st.text_input("Bekannte Allergie?")
    diagnosen = st.text_area("Diagnosen", height=100, placeholder="Relevante Diagnosen...", label_visibility="visible")

    return {
        "patient": patient_name.strip(),
        "geburtsdatum": geburtsdatum,
        "therapiebeginn": therapiebeginn,
        "dauer": dauer,
        "groesse": groesse,
        "gewicht": gewicht,
        "tw_besprochen": tw_besprochen,
        "allergie": bekannte_allergie.strip(),
        "diagnosen": diagnosen.strip(),
    }


# --- Helpers ---
def _fmt_dt(d):
    try:
        return d.strftime("%d.%m.%Y")
    except Exception:
        return ""

from fpdf import FPDF
import os

class PDF(FPDF):
    def header(self):
        # Logo (left)
        if os.path.exists("clinic_logo.png"):
            try:
                self.image("clinic_logo.png", 10, 8, 40)  # x, y, width
            except:
                pass

        # Address (right)
        self.set_font("Helvetica", "", 10)
        self.set_xy(230, 10)  # adjust for landscape
        self.multi_cell(60, 5,
            "Clausewitz str. 2\n10629 Berlin-Charlottenburg\n+49 30 6633110\ninfo@revitaclinic.de",
            0, "R"
        )

        self.ln(12)  # small gap after header

    def footer(self):
        self.set_y(-15)  # 15mm from bottom
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100)
        self.cell(0, 10, "www.revitaclinic.de", 0, 0, "C")


# --- PDF generation ---
def generate_pdf(patient, supplements):
    pdf = PDF("L", "mm", "A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    # Title
    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, "THERAPIEKONZEPT", 0, 1, "L")
    pdf.ln(3)

    # --- Patient info ---
    pdf.set_font("Helvetica", "B", 10); pdf.cell(22,6,"Patient:",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(88,6, patient.get("patient",""),0,0)
    pdf.set_font("Helvetica", "B", 10); pdf.cell(30,6,"Geburtsdatum:",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(0,6, _fmt_dt(patient.get("geburtsdatum")),0,1)

    # One line with all 5 fields
    pdf.set_font("Helvetica", "B", 10); pdf.cell(22,6,"Grösse:",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(20,6,f"{patient.get('groesse','')} cm",0,0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(22,6,"Gewicht:",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(25,6,f"{patient.get('gewicht','')} kg",0,0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(30,6,"Therapiebeginn:",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(35,6,_fmt_dt(patient.get("therapiebeginn")),0,0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(45,6,"Voraussichtliche Dauer:",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(25,6,f"{patient.get('dauer','')} Monate",0,0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(30,6,"TW besprochen?",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(0,6,patient.get("tw_besprochen",""),0,1)

    pdf.ln(2)

    # New row for allergies
    pdf.set_font("Helvetica", "B", 10); pdf.cell(40,6,"Bekannte Allergie?",0,0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(0,6,patient.get("allergien",""),0,1)

    pdf.ln(2)

    pdf.set_font("Helvetica","B",10); pdf.cell(0,6,"Diagnosen",0,1)
    pdf.set_font("Helvetica","",10)
    diagnosen = patient.get("diagnosen","") or "-"
    pdf.multi_cell(0,5, diagnosen,0,"L")
    pdf.ln(3)

    # --- Supplements Table ---
    table_width = 277  # A4 landscape width (297) - margins (10+10)
    pdf.set_fill_color(38,96,65)
    pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",12)
    pdf.cell(table_width,8,"NAHRUNGSERGÄNZUNGSMITTEL (NEM) VO",0,1,"L",True)

    headers = ["Supplement","Nüchtern","Morgens","Mittags","Abends","Nachts","Kommentare"]
    base_widths = [70,20,20,20,20,20]   # fixed widths for first 6
    used_width = sum(base_widths)
    comment_width = table_width - used_width
    widths = base_widths + [comment_width]

    pdf.set_font("Helvetica","B",10)
    for w,h in zip(widths,headers):
        pdf.cell(w,8,h,1,0,"C",True)
    pdf.ln()

    pdf.set_text_color(0,0,0)
    pdf.set_font("Helvetica","",9)

    for s in supplements:
        row = [s["name"], s["Nüchtern"], s["Morgens"], s["Mittags"], s["Abends"], s["Nachts"], s["Kommentar"]]
        comment_text = row[-1] or ""
        line_height = 8
        comment_lines = int(pdf.get_string_width(comment_text) / (widths[-1] - 2)) + 1 if comment_text else 1
        row_height = max(line_height, line_height * comment_lines)

        # Print first 6
        for w,text in zip(widths[:-1],row[:-1]):
            pdf.cell(w,row_height,(text or ""),1,0)

        # Print Kommentar
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(widths[-1], line_height, comment_text, 1)
        pdf.set_xy(x + widths[-1], y)
        pdf.ln(row_height)

    return bytes(pdf.output(dest="S"))



# --- Main app ---
def main():
    st.title("THERAPIEKONZEPT")

    conn = get_conn()
    df = fetch_supplements(conn)

    # Patient info
    patient = patient_inputs()

    # Supplements form
    st.subheader("Nahrungsergänzungsmittel (NEM) VO")
    selected = []
    with st.form("plan"):
        for _,row in df.iterrows():
            with st.expander(row["name"], expanded=False):
                prescribe = st.checkbox("Verschreiben", key=row["id"])
                inputs = {t: st.text_input(t, key=f"{row['id']}_{t}") for t in TIMES}
                comment = st.text_input("Kommentar", key=f"{row['id']}_comment")
                if prescribe:
                    selected.append({"name": row["name"], **inputs, "Kommentar": comment})
        submitted = st.form_submit_button("PDF generieren")

    if submitted:
        if not selected:
            st.error("Bitte mindestens ein Supplement auswählen!")
            return
        pdf_bytes = generate_pdf(patient, selected)
        st.download_button(
            "⬇️ Download Patient PDF",
            data=pdf_bytes,
            file_name=f"Supplements_{patient.get('patient','')}.pdf",
            mime="application/pdf"
        )

if __name__ == "__main__":
    main() 