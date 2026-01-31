import os
from fb_parser_GPT_static import parse_source_with_includes

SININEN = '\033[94m'
VIHREA = '\033[92m'
HARMAA = '\033[90m'
KELTAINEN = '\033[93m'
LOPPU = '\033[0m'

def aja_testi():
    testitiedosto = os.path.join(os.path.dirname(__file__), "testikoodi.bas")
    
    try:
        with open(testitiedosto, "r", encoding="utf-8", errors='ignore') as f:
            testi_koodi = f.read()
    except Exception as e:
        print(f"Virhe: {e}")
        return

    ast, symbols = parse_source_with_includes(testi_koodi, testitiedosto)

    kaikki_tyypit = symbols.all_types_dict()
    muuttujat = symbols.var_to_type_dict()
    
    print(f"\n--- TESTI: {testitiedosto} ---")
    print("=" * 110)

    print(f"{KELTAINEN}LÖYDYT MUUTTUJAT:{LOPPU}")
    for var_name, var_type in muuttujat.items():
        print(f"  Muuttuja: {var_name:<15} | Tyyppi: {var_type}")
    print("-" * 110)

    for tyyppi_nimi, jasenet in kaikki_tyypit.items():
        print(f"\nTYYPPI: {tyyppi_nimi.upper()}")

        # --- LISÄTTY STATIC-KENTTIEN TULOSTUS ---
        ts = symbols.getType(tyyppi_nimi)
        for f in ts.static_fields:
            print(f"  {SININEN}label:{LOPPU} \"{f.name:<18}\" | "
                  f"{VIHREA}insertText:{LOPPU} \"{f.name:<15}\" | "
                  f"{HARMAA}detail:{LOPPU} \"(Static) {f.name} As {f.type_name}\"")
        # --- STATIC-KENTTIEN TULOSTUS LOPPU ---

        for m in jasenet:
            print(f"  {SININEN}label:{LOPPU} \"{m['label']:<18}\" | "
                  f"{VIHREA}insertText:{LOPPU} \"{m['insertText']:<15}\" | "
                  f"{HARMAA}detail:{LOPPU} \"{m['detail']}\"")
        print("-" * 110)

if __name__ == "__main__":
    aja_testi()
