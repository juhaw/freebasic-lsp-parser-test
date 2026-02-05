import re
import os

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
        if any(clean.startswith(t) for t in tunnisteet):
            header_lines.append(clean)
            code_start_idx = idx + 1
        elif not clean and code_start_idx == idx:
            code_start_idx = idx + 1
        elif header_lines:
            code_start_idx = idx
            break

    class_name = next((l.split(':CLASS:')[1].strip() for l in header_lines if ':CLASS:' in l), None)
    var_name = next((l.split(':VARIABLE:')[1].strip() for l in header_lines if ':VARIABLE:' in l), None)
    func_name = next((l.split(':FUNCTION:')[1].strip() for l in header_lines if ':FUNCTION:' in l), None)
    
    is_variable = var_name is not None
    item_name = var_name if is_variable else func_name

    if not item_name:
        return nykyinen_sisalto

    code_to_insert = '\n'.join(raw_lines[code_start_idx:]).rstrip()
    target_name = f"{class_name}.{item_name}" if class_name and item_name else (item_name or class_name)

    match_start = -1
    if class_name:
        c_match = re.search(rf'class\s+{re.escape(class_name)}\s*[:\(]', nykyinen_sisalto)
        if c_match:
            after_c = nykyinen_sisalto[c_match.start():]
            p = rf'\n([ \t]+){re.escape(item_name)}\s*=' if is_variable else rf'\n([ \t]+)def\s+{re.escape(item_name)}\s*\('
            m = re.search(p, after_c)
            if m: match_start = c_match.start() + m.start() + 1
    else:
        p = rf'^{re.escape(item_name)}\s*=' if is_variable else rf'^def\s+{re.escape(item_name)}\s*\('
        m = re.search(p, nykyinen_sisalto, re.MULTILINE)
        if m: match_start = m.start()

    if match_start != -1:
        start_line_no = nykyinen_sisalto[:match_start].count('\n') + 1
        raw_after = nykyinen_sisalto[match_start:]
        c_lines = raw_after.split('\n')
        
        # --- PARANNETTU LOPUN TUNNISTUS ---
        e_idx = 1
        first_line = c_lines[0]
        base_indent = len(first_line) - len(first_line.lstrip())
        
        # Tarkistetaan onko kyseessä sanakirja/lista
        is_multiline_container = '{' in first_line or '[' in first_line or '(' in first_line

        for j, line in enumerate(c_lines):
            if j == 0: continue
            if not line.strip():
                continue
            
            curr_indent = len(line) - len(line.lstrip())
            
            # Jos ollaan sisennetty syvemmälle, koodi jatkuu varmasti
            if curr_indent > base_indent:
                e_idx = j + 1
                continue
            
            # Jos ollaan samalla tasolla:
            if curr_indent == base_indent:
                # Jos rivi alkaa sulkevalla merkillä, se on viimeinen rivi
                if line.strip().startswith(('}', ']', ')')):
                    e_idx = j + 1
                    break
                # Jos muuttuja on jo saanut sisältöä ja tulee uusi muuttuja/funktio samalla tasolla
                if any(line.strip().startswith(prefix) for prefix in ('def ', 'class ', 'self.')) or '=' in line:
                    break
                e_idx = j + 1
            else:
                # Sisennys pieneni -> lohko loppui
                break
        
        match_end = match_start + len('\n'.join(c_lines[:e_idx]))
        end_line_no = start_line_no + e_idx - 1
        old_code = nykyinen_sisalto[match_start:match_end]

        print(f"\n🔄 KORVATAAN: {CYAN}{target_name}{RESET} (Rivit {start_line_no}-{end_line_no})")
        print(f"{RED}--- POISTETTAVA ALKAA ---{RESET}")
        print(f"{RED}{old_code}{RESET}")
        print(f"{RED}--- POISTETTAVA LOPPUU ---{RESET}")
        
        # === MUUTOS: uuden koodin rivinumerot ===
        new_line_count = code_to_insert.count('\n') + 1
        new_start_line_no = start_line_no
        new_end_line_no = new_start_line_no + new_line_count - 1

        print(
            f"{YELLOW}--- UUSI ALKAA "
            f"(Rivit {new_start_line_no}-{new_end_line_no}, "
            f"Yhteensä {new_line_count} riviä) ---{RESET}"
        )
        print(f"{YELLOW}{code_to_insert}{RESET}")
        print(f"{YELLOW}--- UUSI LOPPUU ---{RESET}")
        
        return nykyinen_sisalto[:match_start] + code_to_insert + nykyinen_sisalto[match_end:]
    else:
        print(f"\n✨ LISÄTÄÄN UUSI: {CYAN}{target_name}{RESET}")
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
                last_was_class = current_lines[-1].strip().startswith(':CLASS:')
                if (clean.startswith(':FUNCTION:') or clean.startswith(':VARIABLE:')) and last_was_class:
                    current_lines.append(line)
                elif clean.startswith(':CLASS:') or not last_was_class:
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
        if not any(t in block for t in (':FUNCTION:', ':VARIABLE:')): continue
        
        print(f"\n--- KÄSITTELLÄÄN LOHKO {i}/{len(blocks)} ---")
        sisalto = lue_tiedosto(TARGET_FILE)
        uusi_sisalto = kasittele_lohko(block, sisalto)
        
        if uusi_sisalto != sisalto:
            if input(f"\n💾 Tallennetaanko? (k/e): ").lower() == 'k':
                tallenna_tiedosto(TARGET_FILE, uusi_sisalto)
                pass

    print("\n✨ Valmis.")
