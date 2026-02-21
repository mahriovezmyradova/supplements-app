import os
from supabase_db import SupabaseDB

def migrate_supplements():
    print("Starting supplements migration...")
    
    # Initialize without Streamlit secrets
    db = SupabaseDB(use_streamlit_secrets=False)
    
    # Your supplements data from init_db.py (keep the same long list)
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
        ("S074", "Amin (artgerecht)", 3),
        
        # Category 4: Entgiftung oral
        ("CAT4", "CATEGORY: Entgiftung oral", 4),
        ("S075", "MSM 1000mg", 4),
        ("S076", "liposomales Glutathion", 4),
        ("S077", "Zeolith", 4),
        ("S078", "DMSA 100mg", 4),
        ("S079", "Ca EDTA 750mg", 4),
        ("S080", "Chlorella Algen", 4),
        ("S081", "NAC 600mg", 4),
        ("S082", "NAC 800mg", 4),
        ("S083", "TUDCA 500mg", 4),
        ("S084", "Lymphdiaral / Lymphomyosot", 4),
        ("S085", "Ceres Geranium robertianum", 4),
        ("S086", "Mineralien und Spurenelemente Mischg.", 4),
        ("S087", "NACET 100mg", 4),
        ("S088", "Bromelain 750mg", 4),
        ("S089", "Sulforaphan 35mg", 4),
        ("S090", "Tamarindenextrakt", 4),
        ("S091", "Chelidonium", 4),
        ("S092", "Hyperikum", 4),
        ("S093", "Colostrum (freeze-dried)", 4),
        
        # Category 5: Darmsanierung
        ("CAT5", "CATEGORY: Darmsanierung nach Revita Kl.", 5),
        ("S094", "Symbiolact Pur", 5),
        ("S095", "Probio-Cult AKK1", 5),
        ("S096", "Glutamin 1g", 5),
        ("S097", "Mucosa Compositum", 5),
        ("S098", "Basenpulver", 5),
        ("S099", "Vermox", 5),
        
        # Category 6: Leberdetox
        ("CAT6", "CATEGORY: Leberdetox nach Revita Kl.", 6),
        ("S100", "Okoubaka", 6),
        ("S101", "Bittersalz", 6),
        ("S102", "Bile Acid Factors", 6),
        ("S103", "Mariendistel / Carduus Marianus / Taraxacum", 6),
        ("S104", "Bitterliebe", 6),
        
        # Category 7: Schlafen
        ("CAT7", "CATEGORY: Schlafen", 7),
        ("S105", "Baldrian / Hopfen", 7),
        ("S106", "Melatonin", 7),
        
        # Category 8: Gelenke/Bindegewebe
        ("CAT8", "CATEGORY: Gelenke / Bindegewebe", 8),
        ("S107", "Glucosamin 10g", 8),
        ("S108", "Chondroitin 10g", 8),
        ("S109", "Silizium G7", 8),
        ("S110", "Kollagen", 8),
        ("S111", "Isagenix SuperKollagen", 8),
        
        # Category 9: Infektionsbehandlung
        ("CAT9", "CATEGORY: Infektionsbehandlung", 9),
        ("S112", "Disulfiram", 9),
        ("S113", "Quentakehl", 9),
        ("S114", "Lysin 1g", 9),
        ("S115", "Weihrauch (Boswelliasäure)", 9),
        ("S116", "Curcuma", 9),
        ("S117", "CurcumaXan Spray Arnika", 9),
        ("S118", "Helicobacter-Therapie", 9),
        ("S119", "Symbiolact comp.", 9),
        ("S120", "Artemisia annua 600mg", 9),
        ("S121", "Artemisia annua Pulver", 9),
        ("S122", "Amantadin 100mg", 9),
        ("S123", "Hydroxychloroquin (HCQ) 200mg", 9),
        ("S124", "Ivermectin", 9),
        ("S125", "Schwarzkümmelöl", 9),
        ("S126", "Astragalus", 9),
        ("S127", "Andrographis 400mg", 9),
        ("S128", "Andrographis 500mg", 9),
        ("S129", "AHCC 500mg", 9),
        
        # Category 10: Hormone
        ("CAT10", "CATEGORY: Hormone", 10),
        ("S130", "Östradiol 0,03%", 10),
        ("S131", "Östradiol 0,06%", 10),
        ("S132", "Progesteroncreme 3%", 10),
        ("S133", "Progesteroncreme 10%", 10),
        ("S134", "DHEA 2% Creme", 10),
        ("S135", "Estradiol 0,04% / Estriol 1,6% / Testosteron 0,2%", 10),
        ("S136", "DHEA 5% Gel", 10),
        ("S137", "Testosteron 10% Gel", 10),
        ("S138", "Testosteron 8mg (Frauen)", 10),
        ("S139", "Testosteron 50mg", 10),
        ("S140", "Testosteron 100mg", 10),
        ("S141", "Testosteron 150mg", 10),
        ("S142", "Progesteron 25mg (Männer)", 10),
        ("S143", "DHEA 5mg", 10),
        ("S144", "DHEA 10mg", 10),
        ("S145", "DHEA 25mg", 10),
        ("S146", "DHEA 50mg", 10),
        ("S147", "Pregnenolon 10mg", 10),
        ("S148", "Pregnenolon 30mg", 10),
        ("S149", "Pregnenolon 50mg", 10),
        ("S150", "Pregnenolon 100mg", 10),
        ("S151", "Phytocortal 100ml", 10),
        ("S152", "Ceres Ribes nigrum", 10),
        ("S153", "Lion's Mane Mushroom Extrakt 500mg", 10),
        ("S154", "LDN 1mg", 10),
        ("S155", "LDN 1,5mg", 10),
        ("S156", "LDN 4mg", 10),
        ("S157", "LDN 4,5mg", 10),
        
        # Category 11: Biologische Therapie
        ("CAT11", "CATEGORY: Biologische Therapie", 11),
        ("S158", "Ceres Solidago comp.", 11),
        
        # Category 12: Sonstiges
        ("CAT12", "CATEGORY: Sonstiges", 12),
        ("S159", "Pro Human Probiotikum", 12),
        ("S160", "Thymusextrakt", 12),
        ("S161", "Nierenextrakt", 12),
        ("S162", "Leberextrakt", 12),
        ("S163", "Adrenal Organzellextrakt", 12),
        ("S164", "Frischpflanzensaft", 12),
        ("S165", "Löwenzahn / Sellerie / Bärlauch", 12),
        ("S166", "Kaktusfeige", 12),
        ("S167", "Kiefernadeltee", 12),
        ("S168", "Weidenröschen (Fireweed)", 12),
        ("S169", "SuperPatches einzeln", 12),
        ("S170", "SuperPatches Packung 28er", 12),
    ]
    
    print(f"Migrating {len(supplements)} supplements to Supabase...")
    
    success_count = 0
    error_count = 0
    
    for supp_id, name, category in supplements:
        try:
            # Check if supplement already exists
            existing = db.supabase.table('supplements')\
                .select('id')\
                .eq('id', supp_id)\
                .execute()
            
            if existing.data:
                # Update existing
                db.supabase.table('supplements')\
                    .update({'name': name, 'category': category})\
                    .eq('id', supp_id)\
                    .execute()
                print(f"🔄 Updated: {name}")
            else:
                # Insert new
                db.supabase.table('supplements')\
                    .insert({'id': supp_id, 'name': name, 'category': category})\
                    .execute()
                print(f"✅ Added: {name}")
            
            success_count += 1
            
        except Exception as e:
            print(f"❌ Error with {name}: {e}")
            error_count += 1
    
    print(f"\n📊 Migration complete!")
    print(f"   Successfully processed: {success_count}")
    print(f"   Errors: {error_count}")
    
    # Verify counts
    print("\n🔍 Verifying categories:")
    for cat_num in range(1, 13):
        response = db.supabase.table('supplements')\
            .select('*')\
            .eq('category', cat_num)\
            .execute()
        count = len([s for s in response.data if not s['id'].startswith('CAT')])
        cat_response = db.supabase.table('supplements')\
            .select('name')\
            .eq('id', f'CAT{cat_num}')\
            .execute()
        cat_name = cat_response.data[0]['name'].replace('CATEGORY: ', '') if cat_response.data else f'Category {cat_num}'
        print(f"   Category {cat_num} ({cat_name}): {count} supplements")

if __name__ == "__main__":
    migrate_supplements()