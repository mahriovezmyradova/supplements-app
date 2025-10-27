import sqlite3, csv, os

DB_PATH = "app.db"
CSV_PATH = "supplements.csv"

schema = """
CREATE TABLE IF NOT EXISTS supplements (
  id TEXT PRIMARY KEY,
  name TEXT
);
"""

def main():
    con = sqlite3.connect(DB_PATH)
    cur = con.cursor()
    cur.executescript(schema)
    con.commit()

    # Check if already seeded
    cur.execute("SELECT COUNT(*) FROM supplements")
    if cur.fetchone()[0] == 0:
        with open(CSV_PATH, newline='', encoding='utf-8') as f:
            rows = [(r["id"], r["name"]) for r in csv.DictReader(f)]
        cur.executemany("INSERT INTO supplements (id, name) VALUES (?,?)", rows)
        con.commit()
        print(f"Seeded {len(rows)} supplements.")
    else:
        print("Supplements table already has data. Skipping seeding.")

if __name__ == "__main__":
    main()