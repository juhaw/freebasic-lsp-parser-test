import re
import os
import ast

# === KONFIGURAATIO ===
TARGET_FILE = 'fb_parser_GPT_static.py'
AI_RESPONSE_FILE = 'AI code.txt'

RED = '\033[91m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def lue_tiedosto(tiedosto):
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, tiedosto)
    try:
        with open(path, 'r', encoding='utf-8', newline='') as f:
            return f.read()
    except Exception as e:
        print(f"❌ Virhe luvussa ({tiedosto}): {e}")
        return None

def tallenna_tiedosto(tiedosto, sisalto):
    base_path = os.path.dirname(os.path.abspath(__file__))
    path = os.path.join(base_path, tiedosto)
    try:
        with open(path, 'w', encoding='utf-8', newline='') as f:
            f.write(sisalto)
        print(f"✅ Muutokset tallennettu: {tiedosto}")
        return True
    except Exception as e:
        print(f"❌ Virhe tallennuksessa: {e}")
        return False



def nayta_muutos_raportti(tyyppi, kohde, v_alku, v_loppu, u_alku, u_loppu, vanha_koodi, uusi_koodi):
    """
    Tulostaa koodit ensin ja raportin viimeiseksi.
    Muutos ja Tyyppi on sijoitettu samalle riville tiiviyden vuoksi.
    """
    # 1. TULOSTETAAN KOODIT ENSIN
    if v_alku != -1 and vanha_koodi.strip():
        print(f"\n{RED}--- ALKUPERÄINEN KOODI ---{RESET}")
        print(f"{RED}{vanha_koodi}{RESET}")
    
    print(f"\n{YELLOW}--- UUSI KOODI ---{RESET}")
    print(f"{YELLOW}{uusi_koodi}{RESET}")

    # 2. LASKETAAN RIVIT JA PÄÄTELLÄÄN TYYPPI
    v_lkm = len(vanha_koodi.splitlines()) if vanha_koodi else 0
    u_lkm = len(uusi_koodi.splitlines()) if uusi_koodi else 0
    
    if "." in kohde:
        k_tyyppi = "LUOKAN METODI"
    elif any(x in kohde.lower() for x in ["variable", "dict", "lista", "data"]):
        k_tyyppi = "MUUTTUJA / DATA"
    elif kohde and kohde[0].isupper():
        k_tyyppi = "LUOKKA"
    else:
        k_tyyppi = "FUNKTIO"

    # 3. TULOSTETAAN RAPORTTI VIIMEISENÄ
    print(f"\n{'='*65}")
    print(f"📊 {CYAN}YHTEENVETO MUUTOKSESTA{RESET}")
    print(f"   Kohde:    {CYAN}{kohde}{RESET}")
    
    # TÄSSÄ MUUTOS: Muutos ja Tyyppi samalla rivillä
    print(f"   Muutos:   {YELLOW}{tyyppi}{RESET}  |  Tyyppi: {YELLOW}{k_tyyppi}{RESET}")
    
    print(f"{'-'*65}")
    
    # Faktat: ALKUPERÄINEN (Aloitus/Lopetusrivi + Kokonaismäärä)
    if v_alku != -1:
        print(f"   {RED}VANHA:{RESET} Rivit {v_alku}-{v_loppu} ({v_lkm} riviä)")
    else:
        print(f"   {RED}VANHA:{RESET} (Uusi kohde)")
        
    # Faktat: UUSI (Aloitus/Lopetusrivi + Kokonaismäärä)
    print(f"   {YELLOW}UUSI: {RESET} Rivit {u_alku}-{u_loppu} ({u_lkm} riviä)")
    print(f"{'='*65}\n")

def kasittele_lohko(block, nykyinen_sisalto):
    raw_lines = block.split('\n')
    header_lines = []
    code_start_idx = 0
    tunnisteet = (':FUNCTION:', ':CLASS:', ':VARIABLE:')

    for idx, line in enumerate(raw_lines):
        clean = line.strip()
        if any(clean.startswith(t) for t in tunnisteet):
            header_lines.append(clean)
            code_start_idx = idx + 1
        elif not clean and code_start_idx == idx:
            code_start_idx = idx + 1
        elif header_lines:
            code_start_idx = idx
            break

    class_name = next((l.split(':CLASS:')[1].strip() for l in header_lines if ':CLASS:' in l), None)
    func_name = next((l.split(':FUNCTION:')[1].strip() for l in header_lines if ':FUNCTION:' in l), None)
    var_name = next((l.split(':VARIABLE:')[1].strip() for l in header_lines if ':VARIABLE:' in l), None)
    
    is_variable = var_name is not None
    item_name = var_name if is_variable else func_name
    code_to_insert = '\n'.join(raw_lines[code_start_idx:]).rstrip()
    kohde_str = f"{class_name + '.' if class_name else ''}{item_name or ''}"

    if not item_name and not class_name:
        return nykyinen_sisalto

    try:
        tree = ast.parse(nykyinen_sisalto)
    except Exception as e:
        print(f"❌ AST-VIRHE: {e}")
        return nykyinen_sisalto

    found_node = None
    parent_class_node = None
    target_lines = nykyinen_sisalto.split('\n')

    for node in ast.walk(tree):
        if class_name:
            if isinstance(node, ast.ClassDef) and node.name == class_name:
                parent_class_node = node
                if item_name:
                    for sub in node.body:
                        if not is_variable and isinstance(sub, (ast.FunctionDef, ast.AsyncFunctionDef)) and sub.name == item_name:
                            found_node = sub
                            break
                        elif is_variable and isinstance(sub, ast.Assign):
                            for t in sub.targets:
                                if (isinstance(t, ast.Name) and t.id == item_name) or (isinstance(t, ast.Attribute) and t.attr == item_name):
                                    found_node = sub
                                    break
                    if found_node: break
                else:
                    found_node = node
                    break
        elif item_name:
            if not is_variable and isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name == item_name:
                found_node = node
                break
            elif is_variable and isinstance(node, ast.Assign):
                for t in node.targets:
                    if isinstance(t, ast.Name) and t.id == item_name:
                        found_node = node
                        break
        if found_node: break

    if found_node:
        start_line_idx = found_node.lineno - 1
        end_line_idx = found_node.end_lineno
        first_old_line = target_lines[start_line_idx]
        base_indent_str = first_old_line[:len(first_old_line) - len(first_old_line.lstrip())]
        
        ai_lines = code_to_insert.split('\n')
        first_non_empty_ai = next((l for l in ai_lines if l.strip()), "")
        ai_indent_len = len(first_non_empty_ai) - len(first_non_empty_ai.lstrip())
        
        new_lines = []
        for line in ai_lines:
            if line.strip():
                clean_line = line[ai_indent_len:] if len(line) >= ai_indent_len else line.lstrip()
                new_lines.append(base_indent_str + clean_line)
            else:
                new_lines.append('')
        indented_code_str = '\n'.join(new_lines)

        uusi_lkm = len(indented_code_str.splitlines())
        nayta_muutos_raportti("KORVAUS", kohde_str, start_line_idx + 1, end_line_idx, 
                             start_line_idx + 1, start_line_idx + uusi_lkm, 
                             '\n'.join(target_lines[start_line_idx:end_line_idx]), indented_code_str)

        return '\n'.join(target_lines[:start_line_idx]) + '\n' + indented_code_str + '\n' + '\n'.join(target_lines[end_line_idx:])
    
    elif parent_class_node and item_name:
        insert_pos = parent_class_node.end_lineno
        class_line = target_lines[parent_class_node.lineno - 1]
        class_indent = class_line[:len(class_line) - len(class_line.lstrip())]
        method_indent = class_indent + "    "
        
        ai_lines = code_to_insert.split('\n')
        first_non_empty_ai = next((l for l in ai_lines if l.strip()), "")
        ai_indent_len = len(first_non_empty_ai) - len(first_non_empty_ai.lstrip())
        
        new_lines = []
        for line in ai_lines:
            if line.strip():
                clean_line = line[ai_indent_len:] if len(line) >= ai_indent_len else line.lstrip()
                new_lines.append(method_indent + clean_line)
            else:
                new_lines.append('')
        
        indented_code_str = '\n'.join(new_lines)
        uusi_lkm = len(indented_code_str.splitlines())
        
        nayta_muutos_raportti("LISÄYS LUOKKAAN", kohde_str, -1, -1, 
                             insert_pos + 1, insert_pos + uusi_lkm, 
                             "", indented_code_str)
        
        return '\n'.join(target_lines[:insert_pos]) + '\n' + indented_code_str + '\n' + '\n'.join(target_lines[insert_pos:])

    else:
        uusi_lkm = len(code_to_insert.splitlines())
        nayta_muutos_raportti("LISÄYS LOPPUUN", kohde_str, -1, -1, 
                             len(target_lines) + 2, len(target_lines) + 2 + uusi_lkm, 
                             "", code_to_insert)
        return nykyinen_sisalto.rstrip() + '\n\n' + code_to_insert + '\n'

if __name__ == "__main__":
    if os.name == 'nt': os.system('')
    ai_text = lue_tiedosto(AI_RESPONSE_FILE)
    if not ai_text: exit()

    blocks = []
    current_lines = []
    lines = ai_text.split('\n')

    for line in lines:
        clean = line.strip()
        is_tag = any(clean.startswith(t) for t in (':FUNCTION:', ':VARIABLE:', ':CLASS:'))
        if is_tag:
            if current_lines:
                last_line = current_lines[-1].strip()
                if (clean.startswith(':FUNCTION:') or clean.startswith(':VARIABLE:')) and last_line.startswith(':CLASS:'):
                    current_lines.append(line)
                elif clean.startswith(':CLASS:') or not any(l.strip().startswith(':CLASS:') for l in current_lines):
                    blocks.append('\n'.join(current_lines))
                    current_lines = [line]
                else:
                    current_lines.append(line)
            else:
                current_lines = [line]
        else:
            current_lines.append(line)
    
    if current_lines:
        blocks.append('\n'.join(current_lines))

    for i, block in enumerate(blocks, 1):
        if not any(t in block for t in (':CLASS:', ':FUNCTION:', ':VARIABLE:')): continue
        
        sisalto = lue_tiedosto(TARGET_FILE)
        if sisalto is None: continue
        
        uusi_sisalto = kasittele_lohko(block, sisalto)
        
        if uusi_sisalto != sisalto:
            if input(f"\n💾 Tallennetaanko lohko {i}/{len(blocks)}? (k/e): ").lower() == 'k':
                tallenna_tiedosto(TARGET_FILE, uusi_sisalto)

    print("\n✨ Valmis.")