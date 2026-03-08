# test_supabase.py
import os
import toml
from supabase_db import SupabaseDB

def test_connection():
    print("Testing Supabase connection...")
    try:
        # Try to load from .streamlit/secrets.toml
        secrets_path = os.path.join('.streamlit', 'secrets.toml')
        if os.path.exists(secrets_path):
            secrets = toml.load(secrets_path)
            os.environ['SUPABASE_URL'] = secrets['SUPABASE_URL']
            os.environ['SUPABASE_KEY'] = secrets['SUPABASE_KEY']
            print("✅ Loaded credentials from .streamlit/secrets.toml")
        
        # Now initialize the database
        db = SupabaseDB(use_streamlit_secrets=False)
        print("✅ Successfully connected to Supabase")
        
        # Test fetch
        df = db.fetch_patient_names()
        print(f"Found {len(df)} patients")
        
    except Exception as e:
        print(f"❌ Failed: {e}")

if __name__ == "__main__":
    # Install toml if not already installed
    try:
        import toml
    except ImportError:
        print("Installing toml package...")
        os.system("pip install toml")
        import toml
    
    test_connection()