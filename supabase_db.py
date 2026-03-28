import os
import json
from datetime import date
from typing import Optional, Dict, List, Any, Tuple
import pandas as pd

class SupabaseDB:
    def __init__(self, use_streamlit_secrets=True):
        try:
            if use_streamlit_secrets:
                try:
                    import streamlit as st
                    url = st.secrets["SUPABASE_URL"]
                    key = st.secrets["SUPABASE_KEY"]
                except Exception:
                    url = os.environ.get("SUPABASE_URL")
                    key = os.environ.get("SUPABASE_KEY")
            else:
                url = os.environ.get("SUPABASE_URL")
                key = os.environ.get("SUPABASE_KEY")

            if not url or not key:
                raise ValueError(
                    "Missing Supabase credentials. Set SUPABASE_URL and SUPABASE_KEY "
                    "in .streamlit/secrets.toml or as environment variables."
                )

            from supabase import create_client
            self.supabase = create_client(url, key)
            print("✅ Connected to Supabase")

        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            raise

    # ──────────────────────────────────────────────────────────
    # HELPERS
    # ──────────────────────────────────────────────────────────

    @staticmethod
    def _to_str(v) -> str:
        """Safely convert value to string for DB storage."""
        if v is None:
            return ""
        if isinstance(v, date):
            return v.isoformat()
        return str(v)

    @staticmethod
    def _serialize(obj) -> str:
        """JSON-serialize a dict, converting date objects to ISO strings."""
        def _default(o):
            if isinstance(o, date):
                return o.isoformat()
            raise TypeError(f"Object of type {type(o)} is not JSON serializable")
        return json.dumps(obj, default=_default)

    @staticmethod
    def _deserialize(s: str) -> dict:
        """JSON-deserialize a string, returning {} on failure."""
        if not s:
            return {}
        try:
            return json.loads(s)
        except Exception:
            return {}

    # ──────────────────────────────────────────────────────────
    # SUPPLEMENTS
    # ──────────────────────────────────────────────────────────

    def fetch_supplements(self) -> pd.DataFrame:
        try:
            resp = self.supabase.table('supplements').select('*').order('category').order('id').execute()
            return pd.DataFrame(resp.data)
        except Exception as e:
            print(f"Error fetching supplements: {e}")
            return pd.DataFrame()

    # ──────────────────────────────────────────────────────────
    # PATIENT NAMES
    # ──────────────────────────────────────────────────────────

    def fetch_patient_names(self) -> pd.DataFrame:
        try:
            resp = self.supabase.table('patients').select('patient_name').order('patient_name').execute()
            return pd.DataFrame(resp.data)
        except Exception as e:
            print(f"Error fetching patient names: {e}")
            return pd.DataFrame()

    # ──────────────────────────────────────────────────────────
    # SAVE
    # ──────────────────────────────────────────────────────────

    def save_patient_data(
        self,
        patient_data: Dict,
        nem_prescriptions: List[Dict],
        therapieplan_data: Dict,
        ernaehrung_data: Dict,
        infusion_data: Dict,
    ) -> bool:
        try:
            # ── 1. Upsert patient record ──────────────────────
            patient_record = {
                'patient_name':             str(patient_data.get('patient', '')),
                'geburtsdatum':             self._to_str(patient_data.get('geburtsdatum')),
                'geschlecht':               str(patient_data.get('geschlecht', 'M')),
                'groesse':                  int(patient_data.get('groesse', 0) or 0),
                'gewicht':                  int(patient_data.get('gewicht', 0) or 0),
                'therapiebeginn':           self._to_str(patient_data.get('therapiebeginn')),
                'dauer':                    int(patient_data.get('dauer', 6) or 6),
                'tw_besprochen':            str(patient_data.get('tw_besprochen', 'Ja')),
                'allergie':                 str(patient_data.get('allergie', '')),
                'diagnosen':                str(patient_data.get('diagnosen', '')),
                'kontrolltermin_4':         bool(patient_data.get('kontrolltermin_4', False)),
                'kontrolltermin_12':        bool(patient_data.get('kontrolltermin_12', False)),
                'kontrolltermin_24':        bool(patient_data.get('kontrolltermin_24', False)),
                'kontrolltermin_kommentar': str(patient_data.get('kontrolltermin_kommentar', '')),
                'kt4_date':                 self._to_str(patient_data.get('kt4_date')) or None,
                'kt12_date':                self._to_str(patient_data.get('kt12_date')) or None,
                'kt24_date':                self._to_str(patient_data.get('kt24_date')) or None,
            }

            existing = self.supabase.table('patients') \
                .select('id') \
                .eq('patient_name', patient_record['patient_name']) \
                .execute()

            if existing.data:
                patient_id = existing.data[0]['id']
                # Try full update; if columns missing, retry with base columns only
                try:
                    self.supabase.table('patients').update(patient_record).eq('id', patient_id).execute()
                except Exception as col_err:
                    print(f"Full update failed ({col_err}), trying base columns...")
                    base = {k: v for k, v in patient_record.items()
                            if k in ('patient_name','geburtsdatum','geschlecht','groesse',
                                     'gewicht','therapiebeginn','dauer','tw_besprochen',
                                     'allergie','diagnosen','kontrolltermin_4',
                                     'kontrolltermin_12','kontrolltermin_kommentar')}
                    self.supabase.table('patients').update(base).eq('id', patient_id).execute()
            else:
                try:
                    resp = self.supabase.table('patients').insert(patient_record).execute()
                except Exception as col_err:
                    print(f"Full insert failed ({col_err}), trying base columns...")
                    base = {k: v for k, v in patient_record.items()
                            if k in ('patient_name','geburtsdatum','geschlecht','groesse',
                                     'gewicht','therapiebeginn','dauer','tw_besprochen',
                                     'allergie','diagnosen','kontrolltermin_4',
                                     'kontrolltermin_12','kontrolltermin_kommentar')}
                    resp = self.supabase.table('patients').insert(base).execute()
                patient_id = resp.data[0]['id']

            # ── 2. NEM prescriptions ─────────────────────────
            self.supabase.table('patient_prescriptions').delete().eq('patient_id', patient_id).execute()

            for prescription in (nem_prescriptions or []):
                supp_resp = self.supabase.table('supplements') \
                    .select('id') \
                    .eq('name', prescription.get('name', '')) \
                    .execute()
                if not supp_resp.data:
                    continue
                self.supabase.table('patient_prescriptions').insert({
                    'patient_id':      patient_id,
                    'supplement_id':   supp_resp.data[0]['id'],
                    'dauer':           self._to_str(prescription.get('Gesamt-dosierung', '')),
                    'darreichungsform': self._to_str(prescription.get('Darreichungsform', '')),
                    'dosierung':       self._to_str(prescription.get('Pro Einnahme', '')),
                    'nuechtern':       self._to_str(prescription.get('Nüchtern', '')),
                    'morgens':         self._to_str(prescription.get('Morgens', '')),
                    'mittags':         self._to_str(prescription.get('Mittags', '')),
                    'abends':          self._to_str(prescription.get('Abends', '')),
                    'nachts':          self._to_str(prescription.get('Nachts', '')),
                    'kommentar':       self._to_str(prescription.get('Kommentar', '')),
                }).execute()

            # ── 3. JSON blobs ────────────────────────────────
            for table, data in [
                ('patient_therapieplan', therapieplan_data),
                ('patient_ernaehrung',   ernaehrung_data),
                ('patient_infusion',     infusion_data),
            ]:
                self.supabase.table(table).upsert(
                    {'patient_id': patient_id, 'data': self._serialize(data or {})},
                    on_conflict='patient_id',
                ).execute()

            print(f"✅ Saved patient '{patient_record['patient_name']}' (id={patient_id})")
            return True

        except Exception as e:
            print(f"❌ save_patient_data error: {e}")
            import traceback; traceback.print_exc()
            return False

    # ──────────────────────────────────────────────────────────
    # LOAD
    # ──────────────────────────────────────────────────────────

    def load_patient_data(self, patient_name: str) -> Tuple:
        """Returns (patient_data, nem_prescriptions, therapieplan, ernaehrung, infusion)
        or (None, [], {}, {}, {}) on failure."""
        try:
            # ── Patient ──────────────────────────────────────
            p_resp = self.supabase.table('patients') \
                .select('*') \
                .eq('patient_name', patient_name) \
                .execute()
            if not p_resp.data:
                return None, [], {}, {}, {}

            p = p_resp.data[0]
            patient_id = p['id']

            patient_data = {
                'patient':                  p.get('patient_name', ''),
                'geburtsdatum':             p.get('geburtsdatum', ''),
                'geschlecht':               p.get('geschlecht', 'M'),
                'groesse':                  p.get('groesse', 0) or 0,
                'gewicht':                  p.get('gewicht', 0) or 0,
                'therapiebeginn':           p.get('therapiebeginn', ''),
                'dauer':                    p.get('dauer', 6) or 6,
                'tw_besprochen':            p.get('tw_besprochen', 'Ja'),
                'allergie':                 p.get('allergie', ''),
                'diagnosen':                p.get('diagnosen', ''),
                'kontrolltermin_4':         bool(p.get('kontrolltermin_4', False)),
                'kontrolltermin_12':        bool(p.get('kontrolltermin_12', False)),
                'kontrolltermin_24':        bool(p.get('kontrolltermin_24', False)),
                'kontrolltermin_kommentar': p.get('kontrolltermin_kommentar', ''),
                'kt4_date':                 p.get('kt4_date'),
                'kt12_date':                p.get('kt12_date'),
                'kt24_date':                p.get('kt24_date'),
            }

            # ── NEM prescriptions ─────────────────────────────
            pr_resp = self.supabase.table('patient_prescriptions') \
                .select('*, supplements(name)') \
                .eq('patient_id', patient_id) \
                .execute()

            nem_prescriptions = []
            for row in (pr_resp.data or []):
                nem_prescriptions.append({
                    'name':              row['supplements']['name'],
                    'Gesamt-dosierung':  row.get('dauer', ''),
                    'Darreichungsform':  row.get('darreichungsform', ''),
                    'Pro Einnahme':      row.get('dosierung', ''),
                    'Nüchtern':          row.get('nuechtern', ''),
                    'Morgens':           row.get('morgens', ''),
                    'Mittags':           row.get('mittags', ''),
                    'Abends':            row.get('abends', ''),
                    'Nachts':            row.get('nachts', ''),
                    'Kommentar':         row.get('kommentar', ''),
                })

            # ── JSON blobs ────────────────────────────────────
            def _load_blob(table: str) -> dict:
                resp = self.supabase.table(table).select('data').eq('patient_id', patient_id).execute()
                return self._deserialize(resp.data[0]['data']) if resp.data else {}

            therapieplan_data = _load_blob('patient_therapieplan')
            ernaehrung_data   = _load_blob('patient_ernaehrung')
            infusion_data     = _load_blob('patient_infusion')

            print(f"✅ Loaded patient '{patient_name}'")
            return patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data

        except Exception as e:
            print(f"❌ load_patient_data error: {e}")
            import traceback; traceback.print_exc()
            return None, [], {}, {}, {}

    # ──────────────────────────────────────────────────────────
    # DELETE
    # ──────────────────────────────────────────────────────────

    def delete_patient_data(self, patient_name: str) -> bool:
        try:
            p_resp = self.supabase.table('patients') \
                .select('id') \
                .eq('patient_name', patient_name) \
                .execute()
            if not p_resp.data:
                print(f"Patient '{patient_name}' not found")
                return False

            patient_id = p_resp.data[0]['id']

            for table in ['patient_prescriptions', 'patient_therapieplan',
                          'patient_ernaehrung', 'patient_infusion']:
                self.supabase.table(table).delete().eq('patient_id', patient_id).execute()

            self.supabase.table('patients').delete().eq('id', patient_id).execute()
            print(f"✅ Deleted patient '{patient_name}'")
            return True

        except Exception as e:
            print(f"❌ delete_patient_data error: {e}")
            import traceback; traceback.print_exc()
            return False