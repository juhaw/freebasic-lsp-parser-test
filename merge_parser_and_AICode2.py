import re
import os

# === MUOKKAA NÄITÄ ===
TARGET_FILE = 'fb_parser_GPT_static.py'
AI_RESPONSE_FILE = 'AI code.txt'
# =====================

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
CYAN = '\033[96m'
RESET = '\033[0m'

def tallenna_muutokset(uusi_sisalto):
    if uusi_sisalto is None: return
    base_path = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_path, TARGET_FILE)
    try:
        with open(target_path, 'w', encoding='utf-8', newline='') as f:
            f.write(uusi_sisalto)
        print(f"\n✅ Muutokset tallennettu tiedostoon: {TARGET_FILE}")
    except Exception as e:
        print(f"\n❌ Virhe tallennettaessa: {e}")

def nayta_muutos():
    base_path = os.path.dirname(os.path.abspath(__file__))
    target_path = os.path.join(base_path, TARGET_FILE)
    ai_path = os.path.join(base_path, AI_RESPONSE_FILE)

    try:
        with open(target_path, 'r', encoding='utf-8', newline='') as f:
            file_content = f.read()
        with open(ai_path, 'r', encoding='utf-8') as f:
            ai_text = f.read()
    except Exception as e:
        print(f"Virhe tiedostojen luvussa: {e}")
        return None

    # Lohkojen parsiminen AI-vastauksesta
    blocks = []
    current_block = []
    lines = ai_text.strip().split('\n')
    tunnisteet = (':FUNCTION:', ':CLASS:', ':VARIABLE:')
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if any(line.startswith(t) for t in tunnisteet):
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = [line]
            
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if any(next_line.startswith(t) for t in tunnisteet):
                    current_block.append(next_line)
                    i += 1
            i += 1
            while i < len(lines) and not any(lines[i].strip().startswith(t) for t in tunnisteet):
                current_block.append(lines[i])
                i += 1
            continue
        i += 1
    if current_block:
        blocks.append('\n'.join(current_block))

    if not blocks:
        print("❌ Ei löytynyt koodilohkoja (:FUNCTION:, :CLASS:, :VARIABLE:) AI-vastauksesta.")
        return None

    print(f"\n📁 Kohdetiedosto: {TARGET_FILE}")
    print(f"📦 Löytyi {len(blocks)} päivityskohdetta")
    
    modified_content = file_content

    for i, block in enumerate(blocks, 1):
        try:
            raw_lines = block.split('\n')
            
            # --- KORJATTU KOODIN ALUN ETSINTÄ (SÄILYTTÄÄ @STATICMETHOD) ---
            header_lines = []
            code_start_idx = 0
            for idx, line in enumerate(raw_lines):
                clean = line.strip()
                if any(clean.startswith(t) for t in tunnisteet):
                    header_lines.append(clean)
                    code_start_idx = idx + 1
                elif not clean:
                    if code_start_idx == idx:
                        code_start_idx = idx + 1
                else:
                    code_start_idx = idx
                    break
            # -------------------------------------------------------------

            class_name = next((l.split(':CLASS:')[1].strip() for l in header_lines if ':CLASS:' in l), None)
            var_name = next((l.split(':VARIABLE:')[1].strip() for l in header_lines if ':VARIABLE:' in l), None)
            func_name = next((l.split(':FUNCTION:')[1].strip() for l in header_lines if ':FUNCTION:' in l), None)
            
            is_variable = var_name is not None
            item_name = var_name if is_variable else func_name
            code_to_insert = '\n'.join(raw_lines[code_start_idx:]).rstrip()

            match_start = -1
            target_name = f"{class_name}.{item_name}" if class_name and item_name else (item_name or class_name)

            # Sijainnin haku
            if class_name:
                c_match = re.search(rf'class\s+{re.escape(class_name)}\s*[:\(]', modified_content)
                if c_match:
                    after_c = modified_content[c_match.start():]
                    p = rf'\n([ \t]+){re.escape(item_name)}\s*=' if is_variable else rf'\n([ \t]+)def\s+{re.escape(item_name)}\s*\('
                    m = re.search(p, after_c)
                    if m: match_start = c_match.start() + m.start() + 1
            else:
                p = rf'^{re.escape(item_name)}\s*=' if is_variable else rf'def\s+{re.escape(item_name)}\s*\('
                m = re.search(p, modified_content, re.MULTILINE)
                if m: match_start = m.start()

            if match_start == -1:
                print(f"❌ Kohdetta '{target_name}' ei löytynyt koodista.")
                continue

            # Lopun tunnistus
            raw_after = modified_content[match_start:]
            match_end = -1
            first_line = raw_after.split('\n')[0]
            
            if '{' in first_line:
                bc, found = 0, False
                for idx, char in enumerate(raw_after):
                    if char == '{': bc += 1; found = True
                    elif char == '}': bc -= 1
                    if found and bc == 0:
                        tail = raw_after[idx:].split('\n')[0]
                        match_end = match_start + idx + len(tail)
                        break
            
            if match_end == -1:
                c_lines = raw_after.split('\n')
                indent = -1
                e_idx = 0
                for j, line in enumerate(c_lines):
                    if j == 0: continue
                    if not line.strip(): continue
                    curr_indent = len(line) - len(line.lstrip())
                    if indent == -1: indent = curr_indent
                    if curr_indent < indent and line.strip():
                        e_idx = j; break
                else: e_idx = len(c_lines)
                
                final_b = c_lines[:e_idx]
                while final_b and not final_b[-1].strip():
                    final_b.pop()
                    e_idx -= 1
                match_end = match_start + len('\n'.join(c_lines[:e_idx]))

            old_code = modified_content[match_start:match_end]
            alku_rivi = len(modified_content[:match_start].split('\n'))

            # --- TULOSTUS PUNAISELLA JA KELTAISELLA ---
            print(f"\n{'='*60}")
            print(f"KÄSITTELLÄÄN {i}/{len(blocks)}: {CYAN}{target_name}{RESET}")
            print(f"✅ Löytyi kohde (Rivit {alku_rivi} - {alku_rivi + len(old_code.split('\n')) - 1})")
            
            print(f"\n{RED}POISTETAAN:{RESET}")
            for idx, line in enumerate(old_code.split('\n')):
                print(f"{RED}{alku_rivi + idx:4}: {line}{RESET}")

            print(f"\n{YELLOW}UUSI KOODI:{RESET}")
            for idx, line in enumerate(code_to_insert.split('\n')):
                print(f"{YELLOW}{alku_rivi + idx:4}: {line}{RESET}")

            modified_content = modified_content[:match_start] + code_to_insert + modified_content[match_end:]

        except Exception as e:
            print(f"❌ Virhe lohkon käsittelyssä: {e}")
    
    return modified_content

if __name__ == "__main__":
    if os.name == 'nt': os.system('')
    paivitetty = nayta_muutos()
    if paivitetty:
        if input("\n💾 Tallennetaanko muutokset? (k/e): ").lower() == 'k':
            tallenna_muutokset(paivitetty)