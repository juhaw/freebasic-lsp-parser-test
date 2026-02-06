#```

import os
from fb_parser_GPT_static import tokenize_source, Parser, SymbolTable, FieldNode, MethodNode, TypeNode, DimNode

try:
    import pyperclip
except ImportError:
    pyperclip = None

SININEN = '\033[94m'
VIHREA = '\033[92m'
HARMAA = '\033[90m'
KELTAINEN = '\033[93m'
LOPPU = '\033[0m'

def aja_testi():
    file = "dim.bas"
    filepath = "Freebasic_statements"
    testitiedosto = os.path.join(os.path.dirname(__file__), filepath, file)
    try:
        with open(testitiedosto, "r", encoding="utf-8", errors="ignore") as f:
            koodi = f.read()
    except Exception as e:
        print(f"Virhe: {e}")
        return

    output_lines = []

    # --- TOKENISOINTI ---
    tokenizer = tokenize_source(koodi, testitiedosto)
    tokens = tokenizer.get_tokens()

    output_lines.append("--- TOKENS ---")
    for t in tokens:
        output_lines.append(f"{t.line:03}:{t.column:02} {t.type:<10} '{t.value}'")
    output_lines.append("--- END TOKENS ---\n")

    # --- PARSING ---
    symtab = SymbolTable()
    parser = Parser(tokens, symtab, os.path.dirname(testitiedosto))
    output_lines.append("--- PARSING BLOCK ---")

    # *** KORJATTU KOHTA ***
    nodes = parser.parseBlock()
    for node in nodes:
        output_lines.append(f"Parsed node: {type(node).__name__}")
    # *** KORJAUS PÄÄTTYY ***

    output_lines.append("--- PARSING DONE ---\n")

    # --- SYMBOLIT ---
    kaikki_tyypit = symtab.all_types_dict()
    muuttujat = symtab.var_to_type_dict()

    output_lines.append("Variables:")
    for var_name, var_type in muuttujat.items():
        output_lines.append(f"  {var_name:<15} : {var_type}")

    output_lines.append("Types:")
    for tyyppi_nimi, jasenet in kaikki_tyypit.items():
        output_lines.append(f"TYPE: {tyyppi_nimi}")
        for m in jasenet:
            output_lines.append(f"  label: {m['label']:<15} insertText: {m['insertText']:<15} detail: {m['detail']}")
        output_lines.append("-" * 60)

    # --- AST (Type, Field, Method) ---
    output_lines.append("\n--- AST ---")
    for t in symtab.types.values():
        output_lines.append(f"TYPE {t.name}")
        for f in t.fields:
            vis = getattr(f, "visibility", "public")
            stat = getattr(f, "is_static", False)
            output_lines.append(f"  FIELD {f.name} : {f.type_name} (vis={vis}, static={stat})")
        for m in t.methods:
            output_lines.append(f"  METHOD {m.name} : returns {m.return_type} params {m.params}")

    # --- Tulostus ja leikepöytä ---
    output_text = "\n".join(output_lines)
    print(output_text)

    if pyperclip:
        pyperclip.copy(output_text)
        print("\nTuloste kopioitu leikepöydälle!")
    else:
        try:
            import subprocess
            subprocess.run("clip", input=output_text.encode('utf-8'), check=True)
            print("\nTuloste kopioitu leikepöydälle!")
        except Exception:
            print("\nHuom! Leikepöydälle kopiointi epäonnistui. Asenna pyperclip.")

if __name__ == "__main__":
    aja_testi()

#```