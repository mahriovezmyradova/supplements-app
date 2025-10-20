import os
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image


st.set_page_config("THERAPIEKONZEPT",layout="wide")

# --- Header ---
c1, c2 = st.columns([1,3])
with c1:
    if os.path.exists("clinic_logo.png"):
        st.image("clinic_logo.png", width=200)
with c2:
    st.markdown("""
    <div style="text-align:right; font-size:14px; line-height:1.4;">
    Clausewitzstr. 2<br>
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
    #st.markdown("Patient")

    # --- Name (full width) ---
    name = st.text_input("Patient", placeholder="Vor- und Nachname")

    # --- Compact Row with 7 fields ---
    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1, 1, 1])
    with c1:
        geburtsdatum = st.date_input("Geburtsdatum", format="DD.MM.YYYY", value=date.today())
    with c2:
        geschlecht = st.radio("Geschlecht", ["M", "W"], horizontal=True)
    with c3:
        groesse = st.number_input("Grösse (cm)", min_value=0, step=1)
    with c4:
        gewicht = st.number_input("Gewicht (kg)", min_value=0, step=1)
    with c5:
        therapiebeginn = st.date_input("Therapiebeginn", format="DD.MM.YYYY", value=date.today())
    with c6:
        dauer = st.selectbox("Dauer (Monate)", options=list(range(1, 13)), index=5)
    with c7:
        tw_besprochen = st.radio("TW besprochen?", ["Ja", "Nein"], horizontal=True)

    # --- Allergie (full width) ---
    bekannte_allergie = st.text_input("Bekannte Allergie?")

    # --- Diagnosen (full width) ---
    diagnosen = st.text_area("Diagnosen", placeholder="Relevante Diagnosen...", height=100)

    # --- Return collected data ---
    data = {
        "patient": name,
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
            "Clausewitzstr. 2\n10629 Berlin-Charlottenburg\n+49 30 6633110\ninfo@revitaclinic.de",
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
        # --- Patient info (grid layout) ---
        # --- Patient info (aligned grid layout) ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(35, 6, "Vor- und Nachname:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(0, 6, patient.get("patient", ""), 0, 1)
    pdf.ln(2)

    # Define consistent column widths
    col_w = [38, 38, 30, 30, 42, 28, 35, 70]  
    # total ~311mm → fits well in A4 landscape margins

    # --- Line 2: Geburtsdatum, Geschlecht, Grösse, Gewicht ---
    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[0], 6, "Geburtsdatum:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[1], 6, _fmt_dt(patient.get("geburtsdatum")), 0, 0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[2], 6, "Geschlecht:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[3], 6, patient.get("geschlecht", ""), 0, 0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[4], 6, "Grösse:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[5], 6, f"{patient.get('groesse','')} cm", 0, 0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[6], 6, "Gewicht:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[7], 6, f"{patient.get('gewicht','')} kg", 0, 1)
    pdf.ln(2)

    # --- Line 3: Therapiebeginn, Dauer, TW besprochen?, Bekannte Allergie ---
    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[0], 6, "Therapiebeginn:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[1], 6, _fmt_dt(patient.get("therapiebeginn")), 0, 0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[2], 6, "Dauer:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[3], 6, f"{patient.get('dauer','')} Monate", 0, 0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[4], 6, "TW besprochen?:", 0, 0)
    pdf.set_font("Helvetica", "", 10);  pdf.cell(col_w[5], 6, patient.get("tw_besprochen", ""), 0, 0)

    pdf.set_font("Helvetica", "B", 10); pdf.cell(col_w[6], 6, "Bekannte Allergie:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    allergie_text = patient.get("allergie", "")
    if len(allergie_text) > 45:
        allergie_text = allergie_text[:42] + "..."
    pdf.cell(col_w[7], 6, allergie_text, 0, 1)
    pdf.ln(3)

    # --- Diagnosen ---
    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(0, 6, "Diagnosen:", 0, 1)
    pdf.set_font("Helvetica", "", 10)
    diagnosen = patient.get("diagnosen", "") or "-"
    pdf.multi_cell(0, 5, diagnosen, 0, "L")
    pdf.ln(3)


    # --- Supplements Table ---
    table_width = 277  # A4 landscape width (297) - margins (10+10)
    pdf.set_fill_color(38,96,65)
    pdf.set_text_color(255,255,255)
    pdf.set_font("Helvetica","B",12)
    pdf.cell(table_width,8,"NAHRUNGSERGÄNZUNGSMITTEL (NEM) VO",0,1,"L",True)

    headers = ["Supplement", "Dauer", "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentare"]
    base_widths = [60, 18, 20, 20, 20, 20, 20]  # Supplement, Dauer, 5 checkboxes
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
        row = [
            s.get("name", ""),
            s.get("Dauer", ""),
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

    # Print first 7 columns (excluding comment)
        for i, (w, text) in enumerate(zip(widths[:-1], row[:-1])):
            align = "L" if i == 0 else "C"  # First column = supplement name (left aligned), rest centered
            pdf.cell(w, row_height, (text or ""), 1, 0, align)

    # Print Kommentar column (last column)
        x = pdf.get_x()
        y = pdf.get_y()
        pdf.multi_cell(widths[-1], line_height, comment_text, 1)
        pdf.set_xy(x + widths[-1], y)
        pdf.ln(row_height)


    return bytes(pdf.output(dest="S"))




# --- Main app ---
def main():
    #st.set_page_config("THERAPIEKONZEPT", layout="wide")
    st.title("THERAPIEKONZEPT")

    conn = get_conn()
    df = fetch_supplements(conn)

    # --- Patient Info ---
    patient = patient_inputs()

    # --- Supplements Form ---
    st.subheader("Nahrungsergänzungsmittel (NEM) VO")
    selected = []

    with st.form("plan"):

        # Inject compact CSS
        st.markdown("""
            <style>
            div[data-testid="stVerticalBlock"] > div {
                margin-bottom: -6px;
            }
            [data-testid="stCheckbox"] {
                margin-top: -6px;
                margin-bottom: -6px;
            }
            .custom-input input {
                height: 30px !important;
                font-size: 14px !important;
                padding: 4px 6px;
            }
            </style>
        """, unsafe_allow_html=True)

        # Header row
        header_cols = st.columns([2, 1, 1, 1, 1, 1, 1, 2])
        headers = ["Supplement", "Dauer (M)", "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]
        for col, text in zip(header_cols, headers):
            col.markdown(f"**{text}**")
        st.markdown("---")

        # Each supplement row
        for _, row in df.iterrows():
            cols = st.columns([2, 1, 1, 1, 1, 1, 1, 2])

            # Supplement name
            cols[0].markdown(row["name"])
            dauer_input = cols[1].number_input(
                "", key=f"{row['id']}_dauer", min_value=1, max_value=12, value=patient["dauer"],
                label_visibility="collapsed"
            )

            # Checkboxes
            cb_nue = cols[2].checkbox("", key=f"{row['id']}_Nuechtern")
            cb_morg = cols[3].checkbox("", key=f"{row['id']}_Morgens")
            cb_mitt = cols[4].checkbox("", key=f"{row['id']}_Mittags")
            cb_abend = cols[5].checkbox("", key=f"{row['id']}_Abends")
            cb_nacht = cols[6].checkbox("", key=f"{row['id']}_Nachts")

            # Kommentar field
            comment = cols[7].text_input(
                "", key=f"{row['id']}_comment", placeholder="Kommentar",
                label_visibility="collapsed"
            )

            # Add to selected list if any box ticked
            if any([cb_nue, cb_morg, cb_mitt, cb_abend, cb_nacht]):
                selected.append({
                    "name": row["name"],
                    "Dauer": f"{dauer_input} M",
                    "Nüchtern": "X" if cb_nue else "",
                    "Morgens": "X" if cb_morg else "",
                    "Mittags": "X" if cb_mitt else "",
                    "Abends": "X" if cb_abend else "",
                    "Nachts": "X" if cb_nacht else "",
                    "Kommentar": comment
                })

        submitted = st.form_submit_button("PDF generieren")

    # PDF generation
    if submitted:
        if not selected:
            st.error("Bitte mindestens ein Supplement auswählen!")
            return
        pdf_bytes = generate_pdf(patient, selected)
        st.download_button(
            "⬇️ PDF für Patienten herunterladen",
            data=pdf_bytes,
            file_name=f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf",
            mime="application/pdf"
        )


if __name__ == "__main__":
    main()
