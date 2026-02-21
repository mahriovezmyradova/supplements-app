from supabase_db import SupabaseDB

def test_connection():
    print("Testing Supabase connection...")
    
    # Test with environment variables
    db = SupabaseDB(use_streamlit_secrets=False)
    
    # Test fetching supplements
    print("\nTesting fetch_supplements...")
    df = db.fetch_supplements()
    print(f"Found {len(df)} supplements")
    if not df.empty:
        print("First 5 supplements:")
        print(df.head())
    
    # Test patient names
    print("\nTesting fetch_patient_names...")
    names_df = db.fetch_patient_names()
    print(f"Found {len(names_df)} patients")

if __name__ == "__main__":
    test_connection()