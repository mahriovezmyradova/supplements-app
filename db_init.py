import sqlite3, csv, os

DB_PATH = "app.db"
CSV_PATH = "supplements.csv"

schema = """
-- Drop existing tables to ensure clean schema
DROP TABLE IF EXISTS patient_prescriptions;
DROP TABLE IF EXISTS patients;
DROP TABLE IF EXISTS supplements;

CREATE TABLE supplements (
  id TEXT PRIMARY KEY,
  name TEXT
);

CREATE TABLE patients (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_name TEXT UNIQUE,
  geburtsdatum DATE,
  geschlecht TEXT,
  groesse INTEGER,
  gewicht REAL,
  therapiebeginn DATE,
  dauer INTEGER,
  tw_besprochen TEXT,
  allergie TEXT,
  diagnosen TEXT,
  created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE patient_prescriptions (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  patient_id INTEGER,
  supplement_id TEXT,
  dauer INTEGER,
  darreichungsform TEXT,
  dosierung TEXT,
  nuechtern TEXT DEFAULT '',
  morgens TEXT DEFAULT '',
  mittags TEXT DEFAULT '',
  abends TEXT DEFAULT '',
  nachts TEXT DEFAULT '',
  kommentar TEXT DEFAULT '',
  FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE,
  FOREIGN KEY (supplement_id) REFERENCES supplements (id)
);

-- Create tables for other tab data
CREATE TABLE IF NOT EXISTS patient_therapieplan (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER UNIQUE,
    data TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS patient_ernaehrung (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER UNIQUE,
    data TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
);

CREATE TABLE IF NOT EXISTS patient_infusion (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    patient_id INTEGER UNIQUE,
    data TEXT,
    FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
);
"""

def main():
    # Remove existing database to start fresh
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("Removed existing database")
    
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(schema)
    con.commit()

    # Seed supplements data
    if os.path.exists(CSV_PATH):
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            rows = [(r["id"], r["name"]) for r in csv.DictReader(f)]
        cur.executemany("INSERT INTO supplements (id, name) VALUES (?,?)", rows)
        con.commit()
        print(f"Seeded {len(rows)} supplements.")
    else:
        print(f"Warning: {CSV_PATH} not found. Creating empty supplements table.")
    
    # Verify tables were created
    cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
    tables = cur.fetchall()
    print("Created tables:", [table[0] for table in tables])
    
    # Verify patient_prescriptions table structure
    cur.execute("PRAGMA table_info(patient_prescriptions)")
    columns = cur.fetchall()
    print("\npatient_prescriptions table columns:")
    for col in columns:
        print(f"  {col[1]} ({col[2]})")
    
    con.close()
    print("\nDatabase initialization completed successfully!")

if __name__ == "__main__":
    main()