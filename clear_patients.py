import sqlite3
import os

DB_PATH = "app.db"

def clear_all_patient_data():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    print("Clearing all patient data...")
    
    # Delete all patient-related data
    cursor.execute("DELETE FROM patient_prescriptions")
    cursor.execute("DELETE FROM patients")
    cursor.execute("DELETE FROM patient_therapieplan")
    cursor.execute("DELETE FROM patient_ernaehrung")
    cursor.execute("DELETE FROM patient_infusion")
    
    # Verify the supplements table is correct
    print("\nVerifying supplements are in correct categories:")
    
    # Check Östradiol
    cursor.execute("SELECT id, name, category FROM supplements WHERE name LIKE '%Östradiol%'")
    ostradiol_entries = cursor.fetchall()
    print("Östradiol entries:")
    for entry in ostradiol_entries:
        print(f"  {entry[0]}: {entry[1]} (Category: {entry[2]})")
    
    # Check Zeolith
    cursor.execute("SELECT id, name, category FROM supplements WHERE name LIKE '%Zeolith%'")
    zeolith = cursor.fetchone()
    print(f"\nZeolith entry: {'Found' if zeolith else 'Missing'}")
    if zeolith:
        print(f"  {zeolith[0]}: {zeolith[1]} (Category: {zeolith[2]})")
    
    # Check LDN
    cursor.execute("SELECT id, name, category FROM supplements WHERE name LIKE '%LDN%' ORDER BY name")
    ldn_entries = cursor.fetchall()
    print(f"\nLDN entries: {len(ldn_entries)}")
    for entry in ldn_entries:
        print(f"  {entry[0]}: {entry[1]} (Category: {entry[2]})")
    
    conn.commit()
    conn.close()
    
    print("\n✅ All patient data has been cleared!")
    print("Now when you start fresh, supplements will appear in their correct categories.")

if __name__ == "__main__":
    clear_all_patient_data()