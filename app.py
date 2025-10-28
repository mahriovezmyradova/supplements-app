import os
import sqlite3
import pandas as pd
import streamlit as st
from fpdf import FPDF
from datetime import date
from PIL import Image

st.set_page_config("THERAPIEKONZEPT", layout="wide")

# --- Header ---
c1, c2 = st.columns([1, 3])
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


# --- Patient inputs ---
def patient_inputs():
    name = st.text_input("Patient", placeholder="Vor- und Nachname")

    c1, c2, c3, c4, c5, c6, c7 = st.columns([1, 1, 1, 1, 1, 1, 1])
    with c1:
        geburtsdatum = st.date_input("Geburtsdatum", format="DD.MM.YYYY", min_value=date(1960, 1, 1), value=date.today())
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

    bekannte_allergie = st.text_input("Bekannte Allergie?")
    diagnosen = st.text_area("Diagnosen", placeholder="Relevante Diagnosen...", height=100)

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

        self.set_font("Helvetica", "", 10)
        self.set_xy(230, 10)
        self.multi_cell(60, 5,
                        "Clausewitzstr. 2\n10629 Berlin-Charlottenburg\n+49 30 6633110\ninfo@revitaclinic.de",
                        0, "R")
        self.ln(12)

    def footer(self):
        self.set_y(-15)
        self.set_font("Helvetica", "", 9)
        self.set_text_color(100)
        self.cell(0, 10, "www.revitaclinic.de", 0, 0, "C")


# --- PDF generation ---
def generate_pdf(patient, supplements):
    pdf = PDF("L", "mm", "A4")
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)

    pdf.set_font("Helvetica", "B", 16)
    pdf.cell(0, 8, "THERAPIEKONZEPT", 0, 1, "L")
    pdf.ln(3)

    # --- Patient info ---
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
    pdf.cell(col_w[5], 6, f"{patient.get('groesse', '')} cm", 0, 0)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[6], 6, "Gewicht:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[7], 6, f"{patient.get('gewicht', '')} kg", 0, 1)
    pdf.ln(2)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[0], 6, "Therapiebeginn:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[1], 6, _fmt_dt(patient.get("therapiebeginn")), 0, 0)

    pdf.set_font("Helvetica", "B", 10)
    pdf.cell(col_w[2], 6, "Dauer:", 0, 0)
    pdf.set_font("Helvetica", "", 10)
    pdf.cell(col_w[3], 6, f"{patient.get('dauer', '')} Monate", 0, 0)

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

    return bytes(pdf.output(dest="S"))


# --- Main app ---
def main():
    st.title("THERAPIEKONZEPT")

    conn = get_conn()
    df = fetch_supplements(conn)
    patient = patient_inputs()

    for _, row in df.iterrows():
        override_key = f"dauer_override_{row['id']}"
        if override_key not in st.session_state:
            st.session_state[override_key] = None

    tabs = st.tabs([
        "Nahrungsergänzungsmittel (NEM) VO",
        "Therapieplan – Übersicht & Maßnahmen",
        "Ernährungstherapie – Lifestyleänderung",
        "Infusionstherapie"
    ])

    selected = []

    with tabs[0]:
        #st.subheader("Nahrungsergänzungsmittel (NEM) VO")
        with st.form("plan"):
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

            header_cols = st.columns([2.2, 0.7, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])
            headers = ["Supplement", "Dauer (M)", "Darreichungsform", "Dosierung",
                       "Nüchtern", "Morgens", "Mittags", "Abends", "Nachts", "Kommentar"]

            for col, text in zip(header_cols, headers):
                col.markdown(f"**{text}**")

            st.markdown("---")

            for _, row in df.iterrows():
                cols = st.columns([2.2, 0.7, 1.2, 1, 0.7, 0.7, 0.7, 0.7, 0.7, 2.3])
                cols[0].markdown(row["name"])

                override_key = f"dauer_override_{row['id']}"
                initial_dauer = st.session_state[override_key] if st.session_state[override_key] is not None else patient["dauer"]

                dauer_input = cols[1].number_input(
                    "", key=f"{row['id']}_dauer", min_value=1, max_value=12, value=initial_dauer,
                    label_visibility="collapsed"
                )

                dosage_presets = ["Kapseln", "Tabletten", "Pulver", "Tropfen", "Sachet", "TL", "EL", "ML", "Andere:"]
                default_form = DEFAULT_FORMS.get(row["name"], dosage_presets[0])
                darreichungsform_key = f"{row['id']}_darreichungsform"
                selected_form = cols[2].selectbox(
                    "", dosage_presets,
                    index=dosage_presets.index(default_form) if default_form in dosage_presets else 0,
                    key=darreichungsform_key, label_visibility="collapsed"
                )

                dosierung_options = ["", "100mg", "200mg", "300mg", "400mg", "500mg"]
                dosierung_val = cols[3].selectbox(
                    "", dosierung_options, key=f"{row['id']}_dosierung", label_visibility="collapsed"
                )

                custom_form = ""
                if selected_form == "Andere:":
                    custom_form = cols[2].text_input(
                        " ", key=f"{row['id']}_custom_dosage", placeholder="z. B. Pulver"
                    )

                if dauer_input != patient["dauer"]:
                    st.session_state[override_key] = dauer_input
                else:
                    st.session_state[override_key] = None

                dose_options = ["", "1", "2", "3", "4", "5"]
                nue_val = cols[4].selectbox("", dose_options, key=f"{row['id']}_Nuechtern", label_visibility="collapsed")
                morg_val = cols[5].selectbox("", dose_options, key=f"{row['id']}_Morgens", label_visibility="collapsed")
                mitt_val = cols[6].selectbox("", dose_options, key=f"{row['id']}_Mittags", label_visibility="collapsed")
                abend_val = cols[7].selectbox("", dose_options, key=f"{row['id']}_Abends", label_visibility="collapsed")
                nacht_val = cols[8].selectbox("", dose_options, key=f"{row['id']}_Nachts", label_visibility="collapsed")

                comment = cols[9].text_input("", key=f"{row['id']}_comment", placeholder="Kommentar", label_visibility="collapsed")

                if any([nue_val, morg_val, mitt_val, abend_val, nacht_val]):
                    selected.append({
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

            submitted = st.form_submit_button("PDF generieren")

   
    with tabs[1]:
        #st.subheader("Therapieplan – Übersicht & Maßnahmen")

        st.markdown("### Diagnostik & Überprüfung")
        zaehne = st.checkbox("Überprüfung der Zähne/Kieferknochen mittels OPG (Panoramaaufnahme mit lachendem Gebiss) / DVT")
        zaehne_zu_pruefen = st.text_input("Zähne zu überprüfen:")

        st.markdown("### Darm & Entgiftung")
        darm_biofilm = st.checkbox("Darm - Biofilmentfernung nach www.regenbogenkreis.de (Express-Darmkur 4 Tageskur)")
        darmsanierung = st.checkbox("Darmsanierung nach Paracelsus Klinik (Rezept von Praxis)")
        darmsanierung_dauer = st.multiselect("Darmsanierung Dauer:", ["4 Wo", "6 Wo", "8 Wo"])
        hydrocolon = st.checkbox("mit Hydrocolon (Darmspülung) 2x insgesamt, Abstand 14 Tage mit Rekolonisierungs-Shot")
        parasiten = st.checkbox("Parasitenbehandlung mit Vermox (3 Tage)")
        parasiten_bio = st.checkbox("Biologisches Parasitenprogramm (z. B. www.drclarkcenter.de)")
        leberdetox = st.checkbox("Leberdetox Behandlung nach Paracelsus Klinik (2-Tageskur, 4–5× alle 4–6 Wochen)")
        nierenprogramm = st.checkbox("Nierenprogramm nach Dr. Clark – 4 Wochen – bitte bei www.drclarkcenter.de beziehen")

        st.markdown("### Infektionen & Ausleitung")
        infektion_bakt = st.text_input("Infektionsbehandlung für Bakterien (Borr./Helicob.):")
        infektion_virus = st.text_input("Infektionsbehandlung für Viren (EBV, HPV, Herpes, Corona):")
        ausleitung_inf = st.checkbox("Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom mit Infusionen")
        ausleitung_oral = st.checkbox("Ausleitung von Schwermetallen/Umweltgiften/PostVacSyndrom oral")

        st.markdown("### Therapieformen")
        mikronaehrstoffe = st.checkbox("Einnahme von Mikronährstoffen (NEM-Verordnung)")
        infusionsbehandlung = st.checkbox("Infusionsbehandlung")
        neuraltherapie = st.checkbox("Neuraltherapie")
        eigenblut = st.checkbox("Eigenbluttherapie")
        medikamente = st.checkbox("Medikamentenverordnung")
        bio_isopath = st.checkbox("Biologische / Isopathische Therapie")
        timewaver_analyse = st.checkbox("Timewaver Analyse")
        timewaver_freq = st.checkbox("Timewaver Frequency Behandlung")
        weitere_labor = st.checkbox("Weitere Labordiagnostik (z. B. IMD, Dedimed, MMD, NextGen Onco)")

        st.markdown("### Ergänzende Therapieformen")
        ernaehrung = st.checkbox("Ernährungsänderung und -beratung")
        hypnose = st.checkbox("Hypnosetherapie")
        yager = st.checkbox("Yagertherapie")
        energetisch = st.checkbox("Energetische Behandlung (Marie / Noreen / Martin / KU / Sandra)")

        if st.button("📄 Therapieplan PDF generieren"):
            pdf = PDF("L", "mm", "A4")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 8, "THERAPIEKONZEPT – THERAPIEPLAN", 0, 1, "L")
            pdf.ln(3)

            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"Patient: {patient.get('patient', '')}\n", 0, "L")
            pdf.multi_cell(0, 6, "Empfohlene Maßnahmen:", 0, "L")

            for label, val in {
                "Überprüfung der Zähne/Kieferknochen mittels OPG / DVT": zaehne,
                f"Zähne zu überprüfen: {zaehne_zu_pruefen}": bool(zaehne_zu_pruefen),
                "Darm - Biofilmentfernung (Express-Darmkur)": darm_biofilm,
                "Darmsanierung nach Paracelsus Klinik": darmsanierung,
                f"Darmsanierung Dauer: {', '.join(darmsanierung_dauer)}": bool(darmsanierung_dauer),
                "Hydrocolon (Darmspülung) 2x, Abstand 14 Tage mit Rekolonisierungs-Shot": hydrocolon,
                "Parasitenbehandlung mit Vermox (3 Tage)": parasiten,
                "Biologisches Parasitenprogramm": parasiten_bio,
                "Leberdetox nach Paracelsus Klinik (2-Tageskur)": leberdetox,
                "Nierenprogramm nach Dr. Clark": nierenprogramm,
                f"Infektionsbehandlung für Bakterien: {infektion_bakt}": bool(infektion_bakt),
                f"Infektionsbehandlung für Viren: {infektion_virus}": bool(infektion_virus),
                "Ausleitung mit Infusionen": ausleitung_inf,
                "Ausleitung oral": ausleitung_oral,
                "Einnahme von Mikronährstoffen (NEM-Verordnung)": mikronaehrstoffe,
                "Infusionsbehandlung": infusionsbehandlung,
                "Neuraltherapie": neuraltherapie,
                "Eigenbluttherapie": eigenblut,
                "Medikamentenverordnung": medikamente,
                "Biologische / Isopathische Therapie": bio_isopath,
                "Timewaver Analyse": timewaver_analyse,
                "Timewaver Frequency Behandlung": timewaver_freq,
                "Weitere Labordiagnostik (IMD, Dedimed, MMD, NextGen Onco)": weitere_labor,
                "Ernährungsänderung und -beratung": ernaehrung,
                "Hypnosetherapie": hypnose,
                "Yagertherapie": yager,
                "Energetische Behandlung (Marie / Noreen / Martin / KU / Sandra)": energetisch,
            }.items():
                if val:
                    pdf.multi_cell(0, 6, f"• {label}", 0, "L")

            pdf_bytes = bytes(pdf.output(dest="S"))
            st.download_button(
                "⬇️ Therapieplan-PDF herunterladen",
                data=pdf_bytes,
                file_name=f"RevitaClinic_Therapieplan_{patient.get('patient','')}.pdf",
                mime="application/pdf"
            )


    # --- Ernährungstherapie – Lifestyleänderung ---
    with tabs[2]:
        #st.subheader("Ernährungstherapie – Lifestyleänderung")
        st.markdown("Hier können Ernährungs- und Lifestyleempfehlungen dokumentiert werden.")

        st.markdown("### Darmsanierung / Leberdetox")
        darmsanierung = st.checkbox("Darmsanierung nach Paracelsus Klinik")
        leberdetox = st.radio("Leberdetox", ["Keine", "2 Tage Kurz-Intensiv", "5 Tage Standard"])

        st.markdown("### Ernährungskonzepte")
        lowcarb = st.checkbox("Low Carb Ernährung (viel Protein und viel gesundes Fett/Öl)")
        proteinmenge = st.text_input("Proteinmenge", placeholder="z. B. 1,5 g / kg KG")
        fasten = st.checkbox("Intermittierendes Fasten / 4-tägiges Fasten")
        krebsdiaet = st.checkbox("Krebs-Diät nach Dr. Coy / Dr. Strunz / Budwig")
        keto = st.checkbox("Ketogene Ernährung")
        oelziehen = st.checkbox("Ölziehen mit Kokosöl (2x10 Min. nach dem Zähneputzen)")
        detox_vacc = st.checkbox("Detox vacc Protokoll (3–12 Monate, gelb markiert)")

        st.markdown("### Sonstige Empfehlungen")
        abnehmen = st.checkbox("Abnehmen mit Akupunktur nach Uwe Richter")
        salz = st.checkbox("Gut gesalzene Kost mit Himalaya- oder Meersalz (fluoridfrei)")
        phosphat = st.checkbox("Phosphatreiche Nahrungsmittel")
        kalium = st.checkbox("Kaliumreiche Nahrungsmittel")
        basisch = st.checkbox("Basische Ernährung (pflanzlich)")
        fluoridfrei = st.checkbox("Fluoridfreies Leben (Zahnpasta, Salz etc.)")
        wasserfilter = st.checkbox("Wasserfilter (Umkehrosmose oder Tischfilter, z. B. Maunaway)")
        atem = st.checkbox("Atemtherapie (z. B. Wim Hof oder Yoga)")
        beratung = st.checkbox("Ernährungsberatung")

        st.markdown("### Bewegung")
        ruecken = st.checkbox("Rückentraining (z. B. Kieser Training)")
        cardio = st.checkbox("Cardio")
        ausdauer = st.checkbox("Ausdauertraining")
        trampolin = st.checkbox("Trampolin")
        barre = st.checkbox("Barre Mobility – Bewegungsapparat in Balance (150€)")
        barre_info = st.markdown("Terminvereinbarung: Nadine – 0178 2093975")

        if st.button("📄 Ernährung & Lifestyle PDF generieren"):
            pdf = PDF("L", "mm", "A4")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 8, "THERAPIEKONZEPT – ERNÄHRUNG & LIFESTYLE", 0, 1, "L")
            pdf.ln(3)

            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"Patient: {patient.get('patient', '')}\n", 0, "L")
            pdf.multi_cell(0, 6, "Empfehlungen:", 0, "L")

            for label, val in {
                "Darmsanierung nach Paracelsus Klinik": darmsanierung,
                f"Leberdetox: {leberdetox}": leberdetox != "Keine",
                "Low Carb Ernährung": lowcarb,
                f"Proteinmenge: {proteinmenge}": bool(proteinmenge),
                "Intermittierendes Fasten / 4 Tage Fasten": fasten,
                "Krebs-Diät (Coy/Strunz/Budwig)": krebsdiaet,
                "Ketogene Ernährung": keto,
                "Ölziehen mit Kokosöl": oelziehen,
                "Detox vacc Protokoll": detox_vacc,
                "Abnehmen mit Akupunktur": abnehmen,
                "Salz (Himalaya/Meersalz)": salz,
                "Phosphatreiche Nahrungsmittel": phosphat,
                "Kaliumreiche Nahrungsmittel": kalium,
                "Basische Ernährung": basisch,
                "Fluoridfreies Leben": fluoridfrei,
                "Wasserfilter": wasserfilter,
                "Atemtherapie": atem,
                "Ernährungsberatung": beratung,
                "Rückentraining (Kieser)": ruecken,
                "Cardio": cardio,
                "Ausdauer": ausdauer,
                "Trampolin": trampolin,
                "Barre Mobility": barre,
            }.items():
                if val:
                    pdf.multi_cell(0, 6, f"• {label}", 0, "L")

            pdf_bytes = bytes(pdf.output(dest="S"))
            st.download_button(
                "⬇️ Ernährung & Lifestyle PDF herunterladen",
                data=pdf_bytes,
                file_name=f"RevitaClinic_Ernaehrung_{patient.get('patient', '')}.pdf",
                mime="application/pdf"
            )

    # --- Infusionstherapie ---
    with tabs[3]:
        #st.subheader("Infusionstherapie")
        st.markdown("Hier können Infusionsbehandlungen dokumentiert werden.")

        infusionen = {
            "Mito-Energy Behandlung (Mito-Gerät, Wirkbooster)": st.checkbox("Mito-Energy Behandlung"),
            "Schwermetalltest mit DMSA und Ca EDTA": st.checkbox("Schwermetalltest"),
            "Procain Baseninfusion mit Magnesium": st.checkbox("Procain Baseninfusion mit Magnesium"),
            "Procain 2%": st.text_input("Procain 2% (ml)"),
            "Artemisinin Infusion mit 2x Lysin": st.checkbox("Artemisinin Infusion (mit 2x Lysin)"),
            "Perioperative Infusion (3 Infusionen)": st.checkbox("Perioperative Infusion"),
            "Detox-Infusion Standard": st.checkbox("Detox-Infusion Standard"),
            "Detox-Infusion Maxi": st.checkbox("Detox-Infusion Maxi"),
            "Aufbauinfusion nach Detox": st.checkbox("Aufbauinfusion nach Detox"),
            "Infektions-Infusion / H2O2": st.text_input("Infektions-Infusion (Anzahl / ml)"),
            "Immun-Boosterung": st.selectbox("Immun-Boosterung Typ", ["", "Typ 1", "Typ 2", "Typ 3"]),
            "Oxyvenierung (10–40 ml, 10er Serie)": st.checkbox("Oxyvenierung"),
            "Energetisierungsinfusion": st.multiselect("Energetisierungsinfusion mit", ["Vitamin B Shot", "Q10 Boostershot"]),
            "Nährstoffinfusion Maxi": st.multiselect("Nährstoffinfusion mit", ["Glutathion", "Alpha Liponsäure"]),
            "Anti Aging Infusion komplett": st.checkbox("Anti Aging Infusion komplett"),
            "Nerven Aufbau Infusion": st.checkbox("Nerven Aufbau Infusion"),
            "Leberentgiftungsinfusion": st.checkbox("Leberentgiftungsinfusion"),
            "Anti-Oxidantien Infusion": st.checkbox("Anti-Oxidantien Infusion"),
            "Aminoinfusion leaky gut (5–10)": st.checkbox("Aminoinfusion leaky gut"),
            "Relax Infusion": st.checkbox("Relax Infusion"),
            "Eisen Infusion (Ferinject)": st.text_input("Eisen Infusion mg / Anzahl"),
            "Vitamin C Hochdosistherapie": st.text_input("Vitamin C Hochdosis (g)"),
        }

        st.markdown("### Zusätze")
        zusaetze = st.multiselect(
            "Zusätze auswählen",
            ["Vit.B Komplex", "Vit.B6/B12/Folsäure", "Vit.D 300 kIE", "Vit.B3", "Biotin", "Glycin",
             "Cholincitrat", "Zink inject", "Magnesium 400mg", "TAD (red.Glut.)", "Arginin", "Glutamin",
             "Taurin", "Ornithin", "Prolin/Lysin", "Lysin", "PC 1000mg"]
        )

        if st.button("📄 Infusionstherapie PDF generieren"):
            pdf = PDF("L", "mm", "A4")
            pdf.add_page()
            pdf.set_font("Helvetica", "B", 16)
            pdf.cell(0, 8, "THERAPIEKONZEPT – INFUSIONSTHERAPIE", 0, 1, "L")
            pdf.ln(3)

            pdf.set_font("Helvetica", "", 10)
            pdf.multi_cell(0, 6, f"Patient: {patient.get('patient', '')}\n", 0, "L")
            pdf.multi_cell(0, 6, "Infusionen / Maßnahmen:", 0, "L")

            for label, val in infusionen.items():
                if val:
                    if isinstance(val, list):
                        for v in val:
                            pdf.multi_cell(0, 6, f"• {label}: {v}", 0, "L")
                    elif isinstance(val, str) and val.strip():
                        pdf.multi_cell(0, 6, f"• {label}: {val}", 0, "L")
                    elif isinstance(val, bool) and val:
                        pdf.multi_cell(0, 6, f"• {label}", 0, "L")

            if zusaetze:
                pdf.ln(3)
                pdf.multi_cell(0, 6, "Zusätze:", 0, "L")
                for z in zusaetze:
                    pdf.multi_cell(0, 6, f"• {z}", 0, "L")

            pdf_bytes = bytes(pdf.output(dest="S"))
            st.download_button(
                "⬇️ Infusionstherapie PDF herunterladen",
                data=pdf_bytes,
                file_name=f"RevitaClinic_Infusion_{patient.get('patient', '')}.pdf",
                mime="application/pdf"
            )

    if submitted:
        if not selected:
            st.error("Bitte mindestens ein Supplement auswählen!")
            return
        pdf_bytes = generate_pdf(patient, selected)
        st.download_button(
            "⬇️ PDF für Patienten herunterladen",
            data=pdf_bytes,
            file_name=f"RevitaClinic_Therapieplan_{patient.get('patient', '')}.pdf",
            mime="application/pdf"
        )


if __name__ == "__main__":
    main()
