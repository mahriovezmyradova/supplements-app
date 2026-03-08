import os
from supabase import create_client, Client
import streamlit as st
import json
from datetime import date
from typing import Optional, Dict, List, Any
import pandas as pd

class SupabaseDB:
    def __init__(self, use_streamlit_secrets=True):
        """Initialize Supabase client
        
        Args:
            use_streamlit_secrets: If True, use st.secrets, otherwise use environment variables
        """
        try:
            if use_streamlit_secrets:
                # Try to use Streamlit secrets first
                try:
                    import streamlit as st
                    url = st.secrets["SUPABASE_URL"]
                    key = st.secrets["SUPABASE_KEY"]
                except:
                    # Fall back to environment variables
                    url = os.environ.get("SUPABASE_URL")
                    key = os.environ.get("SUPABASE_KEY")
            else:
                # Use environment variables
                url = os.environ.get("SUPABASE_URL")
                key = os.environ.get("SUPABASE_KEY")
            
            if not url or not key:
                raise ValueError("Missing Supabase credentials. Please set SUPABASE_URL and SUPABASE_KEY in environment variables or .streamlit/secrets.toml")
            
            self.supabase: Client = create_client(url, key)
            print("✅ Successfully connected to Supabase")
            
        except Exception as e:
            print(f"❌ Failed to connect to Supabase: {e}")
            print("\nPlease set your Supabase credentials in one of these ways:")
            print("1. Create .streamlit/secrets.toml with:")
            print("   SUPABASE_URL = 'https://your-project.supabase.co'")
            print("   SUPABASE_KEY = 'your-anon-key'")
            print("2. Or set environment variables:")
            print("   export SUPABASE_URL='https://your-project.supabase.co'")
            print("   export SUPABASE_KEY='your-anon-key'")
            raise e
    
    def fetch_supplements(self) -> pd.DataFrame:
        """Get supplements with categories"""
        try:
            response = self.supabase.table('supplements').select('*').order('category').order('id').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error fetching supplements: {e}")
            return pd.DataFrame()
    
    def fetch_patient_names(self) -> pd.DataFrame:
        """Get all patient names for autocomplete"""
        try:
            response = self.supabase.table('patients').select('patient_name').order('patient_name').execute()
            return pd.DataFrame(response.data)
        except Exception as e:
            print(f"Error fetching patient names: {e}")
            return pd.DataFrame()
    
    def save_patient_data(self, patient_data: Dict, nem_prescriptions: List[Dict], 
                          therapieplan_data: Dict, ernaehrung_data: Dict, 
                          infusion_data: Dict) -> bool:
        """Save patient data and all prescriptions"""
        try:
            # Format dates as strings
            patient_data_formatted = patient_data.copy()
            for key in ['geburtsdatum', 'therapiebeginn']:
                if key in patient_data_formatted and hasattr(patient_data_formatted[key], 'isoformat'):
                    patient_data_formatted[key] = patient_data_formatted[key].isoformat()
            
            # Check if patient exists
            existing = self.supabase.table('patients')\
                .select('id')\
                .eq('patient_name', patient_data_formatted['patient'])\
                .execute()
            
            # Prepare patient data including Kontrolltermine
            patient_record = {
                'patient_name': patient_data_formatted['patient'],
                'geburtsdatum': patient_data_formatted['geburtsdatum'],
                'geschlecht': patient_data_formatted['geschlecht'],
                'groesse': patient_data_formatted['groesse'],
                'gewicht': patient_data_formatted['gewicht'],
                'therapiebeginn': patient_data_formatted['therapiebeginn'],
                'dauer': patient_data_formatted['dauer'],
                'tw_besprochen': patient_data_formatted['tw_besprochen'],
                'allergie': patient_data_formatted['allergie'],
                'diagnosen': patient_data_formatted['diagnosen'],
                # Add Kontrolltermine fields
                'kontrolltermin_4': patient_data_formatted.get('kontrolltermin_4', False),
                'kontrolltermin_12': patient_data_formatted.get('kontrolltermin_12', False),
                'kontrolltermin_kommentar': patient_data_formatted.get('kontrolltermin_kommentar', '')
            }
            
            if existing.data:
                # Update existing patient
                patient_id = existing.data[0]['id']
                self.supabase.table('patients').update(patient_record).eq('id', patient_id).execute()
            else:
                # Insert new patient
                response = self.supabase.table('patients').insert(patient_record).execute()
                patient_id = response.data[0]['id']
            
            # Delete existing prescriptions
            self.supabase.table('patient_prescriptions')\
                .delete()\
                .eq('patient_id', patient_id)\
                .execute()
            
            # Insert new prescriptions
            for prescription in nem_prescriptions:
                # Get supplement_id
                supp_response = self.supabase.table('supplements')\
                    .select('id')\
                    .eq('name', prescription['name'])\
                    .execute()
                
                if supp_response.data:
                    supplement_id = supp_response.data[0]['id']
                    
                    # Convert all values to strings
                    prescription_data = {
                        'patient_id': patient_id,
                        'supplement_id': supplement_id,
                        'dauer': str(prescription.get('Gesamt-dosierung', '')),
                        'darreichungsform': str(prescription.get('Darreichungsform', '')),
                        'dosierung': str(prescription.get('Pro Einnahme', '')),
                        'nuechtern': str(prescription.get('Nüchtern', '')),
                        'morgens': str(prescription.get('Morgens', '')),
                        'mittags': str(prescription.get('Mittags', '')),
                        'abends': str(prescription.get('Abends', '')),
                        'nachts': str(prescription.get('Nachts', '')),
                        'kommentar': str(prescription.get('Kommentar', ''))
                    }
                    
                    self.supabase.table('patient_prescriptions').insert(prescription_data).execute()
            
            # Save other tab data as JSON
            # Therapieplan
            self.supabase.table('patient_therapieplan')\
                .upsert({
                    'patient_id': patient_id,
                    'data': json.dumps(therapieplan_data, default=str)
                }, on_conflict='patient_id')\
                .execute()
            
            # Ernährung
            self.supabase.table('patient_ernaehrung')\
                .upsert({
                    'patient_id': patient_id,
                    'data': json.dumps(ernaehrung_data, default=str)
                }, on_conflict='patient_id')\
                .execute()
            
            # Infusion
            self.supabase.table('patient_infusion')\
                .upsert({
                    'patient_id': patient_id,
                    'data': json.dumps(infusion_data, default=str)
                }, on_conflict='patient_id')\
                .execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error in save_patient_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False
    
    def load_patient_data(self, patient_name: str) -> tuple:
        """Load patient data and all prescriptions"""
        try:
            # Get patient
            patient_response = self.supabase.table('patients')\
                .select('*')\
                .eq('patient_name', patient_name)\
                .execute()
            
            if not patient_response.data:
                return None, [], {}, {}, {}
            
            patient = patient_response.data[0]
            patient_id = patient['id']
            
            # Get prescriptions with supplement names
            prescriptions_response = self.supabase.table('patient_prescriptions')\
                .select('*, supplements(name)')\
                .eq('patient_id', patient_id)\
                .execute()
            
            nem_prescriptions = []
            for p in prescriptions_response.data:
                nem_prescriptions.append({
                    'name': p['supplements']['name'],
                    'Gesamt-dosierung': p.get('dauer', ''),
                    'Darreichungsform': p.get('darreichungsform', ''),
                    'Pro Einnahme': p.get('dosierung', ''),
                    'Nüchtern': p.get('nuechtern', ''),
                    'Morgens': p.get('morgens', ''),
                    'Mittags': p.get('mittags', ''),
                    'Abends': p.get('abends', ''),
                    'Nachts': p.get('nachts', ''),
                    'Kommentar': p.get('kommentar', '')
                })
            
            # Get other data
            therapieplan_response = self.supabase.table('patient_therapieplan')\
                .select('data')\
                .eq('patient_id', patient_id)\
                .execute()
            therapieplan_data = json.loads(therapieplan_response.data[0]['data']) if therapieplan_response.data else {}
            
            ernaehrung_response = self.supabase.table('patient_ernaehrung')\
                .select('data')\
                .eq('patient_id', patient_id)\
                .execute()
            ernaehrung_data = json.loads(ernaehrung_response.data[0]['data']) if ernaehrung_response.data else {}
            
            infusion_response = self.supabase.table('patient_infusion')\
                .select('data')\
                .eq('patient_id', patient_id)\
                .execute()
            infusion_data = json.loads(infusion_response.data[0]['data']) if infusion_response.data else {}
            
            # Format patient data to match the structure expected by the UI
            patient_data = {
                "patient": patient.get('patient_name', ''),
                "geburtsdatum": patient.get('geburtsdatum', ''),
                "geschlecht": patient.get('geschlecht', 'M'),
                "groesse": patient.get('groesse', 0),
                "gewicht": patient.get('gewicht', 0),
                "therapiebeginn": patient.get('therapiebeginn', ''),
                "dauer": patient.get('dauer', 6),
                "tw_besprochen": patient.get('tw_besprochen', 'Ja'),
                "allergie": patient.get('allergie', ''),
                "diagnosen": patient.get('diagnosen', ''),
                # Kontrolltermine - make sure these are included if they exist
                "kontrolltermin_4": patient.get('kontrolltermin_4', False),
                "kontrolltermin_12": patient.get('kontrolltermin_12', False),
                "kontrolltermin_kommentar": patient.get('kontrolltermin_kommentar', '')
            }
            
            # Return the formatted patient data, not the raw patient record
            return patient_data, nem_prescriptions, therapieplan_data, ernaehrung_data, infusion_data
            
        except Exception as e:
            print(f"❌ Error in load_patient_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return None, [], {}, {}, {}
    
    def delete_patient_data(self, patient_name: str) -> bool:
        """Delete patient and all their data"""
        try:
            # Get patient ID
            patient_response = self.supabase.table('patients')\
                .select('id')\
                .eq('patient_name', patient_name)\
                .execute()
            
            if not patient_response.data:
                print(f"Patient {patient_name} not found")
                return False
            
            patient_id = patient_response.data[0]['id']
            
            # Delete in correct order (foreign key constraints)
            # 1. Delete prescriptions
            self.supabase.table('patient_prescriptions')\
                .delete()\
                .eq('patient_id', patient_id)\
                .execute()
            
            # 2. Delete therapieplan
            self.supabase.table('patient_therapieplan')\
                .delete()\
                .eq('patient_id', patient_id)\
                .execute()
            
            # 3. Delete ernaehrung
            self.supabase.table('patient_ernaehrung')\
                .delete()\
                .eq('patient_id', patient_id)\
                .execute()
            
            # 4. Delete infusion
            self.supabase.table('patient_infusion')\
                .delete()\
                .eq('patient_id', patient_id)\
                .execute()
            
            # 5. Finally delete patient
            self.supabase.table('patients')\
                .delete()\
                .eq('id', patient_id)\
                .execute()
            
            return True
            
        except Exception as e:
            print(f"❌ Error in delete_patient_data: {str(e)}")
            import traceback
            traceback.print_exc()
            return False