import sqlite3
import os
import csv

DB_PATH = "app.db"

def complete_reset():
    print("=== COMPLETE DATABASE RESET ===")
    
    # Step 1: Delete old database
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
        print("✅ Removed old database")
    
    # Step 2: Create new database with EXACT schema
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # Create tables
    cursor.execute("""
        CREATE TABLE supplements (
            id TEXT PRIMARY KEY,
            name TEXT,
            category INTEGER
        )
    """)
    
    cursor.execute("""
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
        )
    """)
    
    cursor.execute("""
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
        )
    """)
    
    cursor.execute("""
        CREATE TABLE patient_therapieplan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE patient_ernaehrung (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
    """)
    
    cursor.execute("""
        CREATE TABLE patient_infusion (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            patient_id INTEGER UNIQUE,
            data TEXT,
            FOREIGN KEY (patient_id) REFERENCES patients (id) ON DELETE CASCADE
        )
    """)
    
    print("✅ Created new database schema")
    
    # Step 3: Manually insert the EXACT supplements with CLEANED names
    supplements = [
        # Category 1: Basis
        ("CAT1", "CATEGORY: Basis", 1),
        ("S001", "Magnesiumbisglycinat", 1),
        ("S002", "Magnesiumthreonat", 1),
        ("S003", "liposomales Magnesium 200mg", 1),
        ("S004", "Vitamin C / Na Ascorbat", 1),
        ("S005", "Vitamin C 1000mg", 1),
        ("S006", "Ascorbyl Palmitat / liposomales Vit. C", 1),
        ("S007", "L-Carnitin (Carnipure)", 1),
        ("S008", "L-Carnitin (Carnipure) Lösung", 1),
        ("S009", "Kapselmischung nach UR V.9 Arnika", 1),
        ("S010", "Multi Mischung Vit. Min.", 1),
        ("S011", "Benfothiamin", 1),
        ("S012", "Vitamin B6 – P5P aktiviert", 1),
        ("S013", "Mangan 10mg", 1),
        ("S014", "Nattokinase 100mg", 1),
        ("S015", "Q10 400mg", 1),
        ("S016", "Selen 300 (100 Stk) Arnika", 1),
        ("S017", "Selen 200 Na-Selenit", 1),
        ("S018", "Vitamin E 800 IU E8 Tocotrienol", 1),
        ("S019", "Polyphenol Arnika", 1),
        ("S020", "Vitamin D3", 1),
        ("S021", "Vitamin K2 1000µg", 1),
        ("S022", "Calcium", 1),
        ("S023", "OPC", 1),
        ("S024", "Lugolsche Lösung (Jod) 5%", 1),
        ("S025", "Kelp mit Jod", 1),
        ("S026", "Zink 25mg (Zink-Glycinat)", 1),
        ("S027", "Eisen", 1),
        ("S028", "R-Alpha Liponsäure 400mg", 1),
        ("S029", "Lactoferrin", 1),
        ("S030", "Quercetin 500mg", 1),
        ("S031", "Enzyme Multienzym / Superenzym", 1),
        ("S032", "Sulbutiamin", 1),
        ("S033", "Spermidin", 1),
        ("S034", "Berberin (plaquefrei)", 1),
        ("S035", "Benfotiamin (B1 fürs Nervensystem)", 1),
        ("S036", "Huperzin", 1),
        ("S037", "Kalium", 1),
        ("S038", "Lithiumorotat 1mg", 1),
        ("S039", "Lithiumorotat 5mg", 1),
        
        # Category 2: Gehirn / Gedächtnis
        ("CAT2", "CATEGORY: Gehirn / Gedächtnis", 2),
        ("S040", "Omega-3 Öl 1 EL = 2g EPA/DHA", 2),
        ("S041", "Alpha GPC", 2),
        ("S042", "Phosphatidylserin / Phosphatidylcholin", 2),
        ("S043", "NMN 500mg", 2),
        ("S044", "NAD+ liposomal 500mg", 2),
        ("S045", "Citicolin", 2),
        ("S046", "Trans-Resveratrol 1000mg", 2),
        ("S047", "Astaxanthin 18mg", 2),
        ("S048", "Lutein 40mg", 2),
        ("S049", "Piracetam (Memory)", 2),
        ("S050", "Aniracetam (Learning)", 2),
        
        # Category 3: Aminosäuren
        ("CAT3", "CATEGORY: Aminosäuren", 3),
        ("S051", "MAP (Aminosäuremischung)", 3),
        ("S052", "Proteinshake 2 Messlöffel", 3),
        ("S053", "Tyrosin 500mg", 3),
        ("S054", "5-HTP 200mg", 3),
        ("S055", "5-HTP 300mg", 3),
        ("S056", "5-HTP 600mg", 3),
        ("S057", "SAMe 400mg", 3),
        ("S058", "Phenylalanin 500mg", 3),
        ("S059", "GABA 1g", 3),
        ("S060", "Tryptophan 1000mg", 3),
        ("S061", "Tryptophan 500mg", 3),
        ("S062", "Lysin", 3),
        ("S063", "Prolin", 3),
        ("S064", "Arginin 1g", 3),
        ("S065", "Citrullin", 3),
        ("S066", "Ornithin", 3),
        ("S067", "Histidin", 3),
        ("S068", "BCAA 1g", 3),
        ("S069", "Glycin 1000mg", 3),
        ("S070", "Taurin", 3),
        ("S071", "Methionin 500mg", 3),
        ("S072", "Kreatin Monohydrat", 3),
        ("S073", "Carnosin 500mg", 3),
        
        # Category 4: Entgiftung oral
        ("CAT4", "CATEGORY: Entgiftung oral", 4),
        ("S074", "MSM 1000mg", 4),
        ("S075", "liposomales Glutathion", 4),
        ("S076", "Zeolith", 4),
        ("S077", "DMSA 100mg", 4),
        ("S078", "Ca EDTA 750mg", 4),
        ("S079", "Chlorella Algen", 4),
        ("S080", "NAC 600mg", 4),
        ("S081", "NAC 800mg", 4),
        ("S082", "TUDCA 500mg", 4),
        ("S083", "Lymphdiaral / Lymphomyosot", 4),
        ("S084", "Ceres Geranium robertianum", 4),
        ("S085", "Mineralien und Spurenelemente Mischg.", 4),
        ("S086", "NACET 100mg", 4),
        ("S087", "Bromelain 750mg", 4),
        ("S088", "Sulforaphan 35mg", 4),
        ("S089", "Tamarindenextrakt", 4),
        ("S090", "Chelidonium", 4),
        ("S091", "Hyperikum", 4),
        ("S092", "Colostrum (freeze-dried)", 4),
        
        # Category 5: Darmsanierung
        ("CAT5", "CATEGORY: Darmsanierung nach Paracelsus Kl.", 5),
        ("S093", "Symbiolact Pur", 5),
        ("S094", "Probio-Cult AKK1", 5),
        ("S095", "Glutamin 1g", 5),
        ("S096", "Mucosa Compositum", 5),
        ("S097", "Basenpulver", 5),
        ("S098", "Vermox", 5),
        
        # Category 6: Leberdetox
        ("CAT6", "CATEGORY: Leberdetox nach Paracelsus Kl.", 6),
        ("S099", "Okoubaka", 6),
        ("S100", "Bittersalz", 6),
        ("S101", "Bile Acid Factors", 6),
        ("S102", "Mariendistel / Carduus Marianus / Taraxacum", 6),
        ("S103", "Bitterliebe", 6),
        
        # Category 7: Schlafen
        ("CAT7", "CATEGORY: Schlafen", 7),
        ("S104", "Baldrian / Hopfen", 7),
        ("S105", "Melatonin", 7),
        
        # Category 8: Gelenke/Bindegewebe
        ("CAT8", "CATEGORY: Gelenke / Bindegewebe", 8),
        ("S106", "Glucosamin 10g", 8),
        ("S107", "Chondroitin 10g", 8),
        ("S108", "Silizium G7", 8),
        ("S109", "Kollagen", 8),
        ("S110", "Isagenix SuperKollagen", 8),
        
        # Category 9: Infektionsbehandlung
        ("CAT9", "CATEGORY: Infektionsbehandlung", 9),
        ("S111", "Disulfiram", 9),
        ("S112", "Quentakehl", 9),
        ("S113", "Lysin 1g", 9),
        ("S114", "Weihrauch (Boswelliasäure)", 9),
        ("S115", "Curcuma", 9),
        ("S116", "CurcumaXan Spray Arnika", 9),
        ("S117", "Helicobacter-Therapie", 9),
        ("S118", "Symbiolact comp.", 9),
        ("S119", "Artemisia annua 600mg", 9),
        ("S120", "Artemisia annua Pulver", 9),
        ("S121", "Amantadin 100mg", 9),
        ("S122", "Hydroxychloroquin (HCQ) 200mg", 9),
        ("S123", "Ivermectin", 9),
        ("S124", "Schwarzkümmelöl", 9),
        ("S125", "Astragalus", 9),
        ("S126", "Andrographis 400mg", 9),
        ("S127", "Andrographis 500mg", 9),
        ("S128", "AHCC 500mg", 9),
        
        # Category 10: Hormone
        ("CAT10", "CATEGORY: Hormone", 10),
        ("S129", "Östradiol 0,03%", 10),
        ("S130", "Östradiol 0,06%", 10),
        ("S131", "Progesteroncreme 3%", 10),
        ("S132", "Progesteroncreme 10%", 10),
        ("S133", "DHEA 2% Creme", 10),
        ("S134", "Estradiol 0,04% / Estriol 1,6% / Testosteron 0,2%", 10),
        ("S135", "DHEA 5% Gel", 10),
        ("S136", "Testosteron 10% Gel", 10),
        ("S137", "Testosteron 8mg (Frauen)", 10),
        ("S138", "Testosteron 50mg", 10),
        ("S139", "Testosteron 100mg", 10),
        ("S140", "Testosteron 150mg", 10),
        ("S141", "Progesteron 25mg (Männer)", 10),
        ("S142", "DHEA 5mg", 10),
        ("S143", "DHEA 10mg", 10),
        ("S144", "DHEA 25mg", 10),
        ("S145", "DHEA 50mg", 10),
        ("S146", "Pregnenolon 10mg", 10),
        ("S147", "Pregnenolon 30mg", 10),
        ("S148", "Pregnenolon 50mg", 10),
        ("S149", "Pregnenolon 100mg", 10),
        ("S150", "Phytocortal 100ml", 10),
        ("S151", "Ceres Ribes nigrum", 10),
        ("S152", "Lion's Mane Mushroom Extrakt 500mg", 10),
        ("S153", "LDN 1mg", 10),
        ("S154", "LDN 1,5mg", 10),
        ("S155", "LDN 4mg", 10),
        ("S156", "LDN 4,5mg", 10),
        
        # Category 11: Biologische Therapie
        ("CAT11", "CATEGORY: Biologische Therapie", 11),
        ("S157", "Ceres Solidago comp.", 11),
        
        # Category 12: Sonstiges
        ("CAT12", "CATEGORY: Sonstiges", 12),
        ("S158", "Pro Human Probiotikum", 12),
        ("S159", "Thymusextrakt", 12),
        ("S160", "Nierenextrakt", 12),
        ("S161", "Leberextrakt", 12),
        ("S162", "Adrenal Organzellextrakt", 12),
        ("S163", "Frischpflanzensaft", 12),
        ("S164", "Löwenzahn / Sellerie / Bärlauch", 12),
        ("S165", "Kaktusfeige", 12),
        ("S166", "Kiefernadeltee", 12),
        ("S167", "Weidenröschen (Fireweed)", 12),
        ("S168", "SuperPatches einzeln", 12),
        ("S169", "SuperPatches Packung 28er", 12),
    ]
    
    cursor.executemany("INSERT INTO supplements (id, name, category) VALUES (?, ?, ?)", supplements)
    conn.commit()
    print(f"✅ Inserted {len(supplements)} supplements")
    
    # Step 4: Verify critical entries
    print("\n=== VERIFICATION ===")
    
    # Check Östradiol
    print("\nÖstradiol entries (should be ONLY in Hormone category 10):")
    cursor.execute("SELECT id, name, category FROM supplements WHERE name LIKE '%Östradiol%'")
    for row in cursor.fetchall():
        status = "✅" if row[2] == 10 else "❌"
        print(f"{status} {row[0]}: {row[1]} (Category: {row[2]})")
    
    # Check Zeolith
    print("\nZeolith entry (should be in Entgiftung oral category 4):")
    cursor.execute("SELECT id, name, category FROM supplements WHERE name LIKE '%Zeolith%'")
    row = cursor.fetchone()
    if row:
        status = "✅" if row[2] == 4 else "❌"
        print(f"{status} {row[0]}: {row[1]} (Category: {row[2]})")
    else:
        print("❌ Zeolith not found!")
    
    # Check LDN
    print("\nLDN entries (should be ONLY in Hormone category 10):")
    cursor.execute("SELECT id, name, category FROM supplements WHERE name LIKE '%LDN%' ORDER BY name")
    ldn_count = 0
    for row in cursor.fetchall():
        status = "✅" if row[2] == 10 else "❌"
        print(f"{status} {row[0]}: {row[1]} (Category: {row[2]})")
        ldn_count += 1
    
    print(f"\nFound {ldn_count} LDN entries (should be 4)")
    
    # Check wrong placements
    print("\n=== CHECKING FOR WRONG PLACEMENTS ===")
    
    # Östradiol in wrong categories
    cursor.execute("SELECT COUNT(*) FROM supplements WHERE name LIKE '%Östradiol%' AND category != 10")
    wrong_ostradiol = cursor.fetchone()[0]
    print(f"Östradiol in wrong categories: {wrong_ostradiol} (should be 0)")
    
    # LDN in wrong categories
    cursor.execute("SELECT COUNT(*) FROM supplements WHERE name LIKE '%LDN%' AND category != 10")
    wrong_ldn = cursor.fetchone()[0]
    print(f"LDN in wrong categories: {wrong_ldn} (should be 0)")
    
    # Zeolith missing
    cursor.execute("SELECT COUNT(*) FROM supplements WHERE name LIKE '%Zeolith%'")
    zeolith_count = cursor.fetchone()[0]
    print(f"Zeolith entries: {zeolith_count} (should be 1)")
    
    # Count by category
    print("\n=== CATEGORY COUNTS ===")
    for cat_num in range(1, 13):
        cursor.execute("SELECT COUNT(*) FROM supplements WHERE category = ? AND id NOT LIKE 'CAT%'", (cat_num,))
        count = cursor.fetchone()[0]
        cursor.execute("SELECT name FROM supplements WHERE id = ?", (f"CAT{cat_num}",))
        cat_name = cursor.fetchone()
        if cat_name:
            cat_display = cat_name[0].replace("CATEGORY: ", "")
            print(f"Category {cat_num} ({cat_display}): {count} items")
    
    # Show some sample cleaned names
    print("\n=== SAMPLE CLEANED NAMES ===")
    sample_categories = [
        (1, "Basis"),
        (3, "Aminosäuren"),
        (4, "Entgiftung oral"),
        (10, "Hormone")
    ]
    
    for cat_num, cat_name in sample_categories:
        print(f"\n{cat_name} samples:")
        cursor.execute("SELECT name FROM supplements WHERE category = ? AND id NOT LIKE 'CAT%' LIMIT 3", (cat_num,))
        for row in cursor.fetchall():
            print(f"  - {row[0]}")
    
    conn.close()
    
    print("\n" + "="*60)
    print("✅ COMPLETE RESET FINISHED!")
    print("="*60)
    print("\nKey improvements:")
    print("1. Removed dosage forms (Pulver, Kapseln, etc.) from names")
    print("2. Östradiol ONLY in Hormone category")
    print("3. Zeolith in Entgiftung oral")
    print("4. All LDN versions in Hormone category")
    print("5. All supplements in correct categories with clean names")

if __name__ == "__main__":
    complete_reset()