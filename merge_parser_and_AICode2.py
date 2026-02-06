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


def kasittele_lohko(block, nykyinen_sisalto):
    raw_lines = block.split('\n')
    header_lines = []
    code_start_idx = 0
    tunnisteet = (':FUNCTION:', ':CLASS:', ':VARIABLE:')

    for idx, line in enumerate(raw_lines):
        clean = line.strip()
        # Käytetään stripattuja tunnisteita vertailuun
        if any(clean.startswith(t) for t in tunnisteet):
            header_lines.append(clean)
            code_start_idx = idx + 1
        elif not clean and code_start_idx == idx:
            code_start_idx = idx + 1
        elif header_lines:
            code_start_idx = idx
            break

    # Puhdistetaan nimet huolellisesti
    class_name = next((l.split(':CLASS:')[1].strip() for l in header_lines if ':CLASS:' in l), None)
    func_name = next((l.split(':FUNCTION:')[1].strip() for l in header_lines if ':FUNCTION:' in l), None)
    var_name = next((l.split(':VARIABLE:')[1].strip() for l in header_lines if ':VARIABLE:' in l), None)
    
    is_variable = var_name is not None
    item_name = var_name if is_variable else func_name
    code_to_insert = '\n'.join(raw_lines[code_start_idx:]).rstrip()

    if not item_name and not class_name:
        return nykyinen_sisalto

    try:
        tree = ast.parse(nykyinen_sisalto)
    except Exception as e:
        print(f"❌ AST-VIRHE: Tiedostossa on syntaksivirhe, ei voida analysoida: {e}")
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
        # Etsitään ensimmäinen ei-tyhjä rivi sisennyksen laskemiseksi
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

        old_code_snippet = '\n'.join(target_lines[start_line_idx:end_line_idx])

        print(f"\n🔄 KORVATAAN (AST): {CYAN}{class_name if class_name else ''}{'.' + item_name if item_name else ''}{RESET}")
        print(f"{RED}--- POISTETTAVA (Rivit {start_line_idx+1}-{end_line_idx}) ---{RESET}")
        print(f"{RED}{old_code_snippet}{RESET}")
        print(f"{YELLOW}--- UUSI KOODI ---{RESET}")
        print(f"{YELLOW}{indented_code_str}{RESET}")

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
        print(f"\n➕ LISÄTÄÄN LUOKKAAN {CYAN}{class_name}{RESET}: {item_name}")
        print(f"{YELLOW}--- UUSI KOODI ---{RESET}")
        print(f"{YELLOW}{indented_code_str}{RESET}")
        
        return '\n'.join(target_lines[:insert_pos]) + '\n' + indented_code_str + '\n' + '\n'.join(target_lines[insert_pos:])

    else:
        target_name = f"{class_name}.{item_name}" if class_name and item_name else (item_name or class_name)
        print(f"⚠️ {YELLOW}Kohdetta {target_name} ei löytynyt. Lisätään loppuun.{RESET}")
        print(f"{YELLOW}--- UUSI KOODI ---{RESET}")
        print(f"{YELLOW}{code_to_insert}{RESET}")
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