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
    
    i = 0
    while i < len(lines):
        line = lines[i].strip()
        if line.startswith(':FUNCTION:') or line.startswith(':CLASS:'):
            if current_block:
                blocks.append('\n'.join(current_block))
            current_block = [line]
            if i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                if next_line.startswith(':FUNCTION:') or next_line.startswith(':CLASS:'):
                    current_block.append(next_line)
                    i += 1
            i += 1
            while i < len(lines) and not lines[i].strip().startswith(':FUNCTION:') and not lines[i].strip().startswith(':CLASS:'):
                current_block.append(lines[i])
                i += 1
            continue
        i += 1
    if current_block:
        blocks.append('\n'.join(current_block))

    if not blocks:
        print("❌ Ei löytynyt koodilohkoja AI-vastauksesta.")
        return None

    print(f"\n📁 Kohdetiedosto: {TARGET_FILE}")
    print(f"📦 Löytyi {len(blocks)} päivityskohdetta")
    
    modified_content = file_content

    for i, block in enumerate(blocks, 1):
        try:
            lines = block.strip().split('\n')
            match_start = -1
            target_name = ""

            # Tunnista onko kyseessä Luokka, Metodi vai Funktio
            if lines[0].startswith(':CLASS:'):
                class_name = lines[0].split(':CLASS:')[1].strip()
                if len(lines) > 1 and lines[1].startswith(':FUNCTION:'):
                    func_name = lines[1].split(':FUNCTION:')[1].strip()
                    target_name = f"{class_name}.{func_name}"
                    code_to_insert = '\n'.join(lines[2:])
                else:
                    target_name = f"Class: {class_name}"
                    code_to_insert = '\n'.join(lines[1:])
            else:
                func_name = lines[0].split(':FUNCTION:')[1].strip()
                target_name = f"Function: {func_name}"
                code_to_insert = '\n'.join(lines[1:])

            print(f"\n{'='*60}")
            print(f"KÄSITTELLÄÄN {i}/{len(blocks)}: {CYAN}{target_name}{RESET}")

            # Etsi sijainti tiedostosta
            if '.' in target_name:
                c_name, m_name = target_name.split('.')
                class_pattern = rf'class\s+{re.escape(c_name)}\s*[:\(]'
                class_match = re.search(class_pattern, modified_content)
                if class_match:
                    class_start = class_match.start()
                    after_class = modified_content[class_start:]
                    method_pattern = rf'\n([ \t]+)def\s+{re.escape(m_name)}\s*\('
                    m_match = re.search(method_pattern, after_class)
                    if m_match:
                        match_start = class_start + m_match.start() + 1 # +1 ohittaa \n
            elif 'Class:' in target_name:
                c_name = target_name.replace('Class: ', '')
                pattern = rf'class\s+{re.escape(c_name)}\s*[:\(]'
                m = re.search(pattern, modified_content)
                if m: match_start = m.start()
            else:
                f_name = target_name.replace('Function: ', '')
                pattern = rf'def\s+{re.escape(f_name)}\s*\('
                m = re.search(pattern, modified_content)
                if m: match_start = m.start()

            if match_start == -1:
                print(f"❌ Kohdetta '{target_name}' ei löytynyt koodista.")
                continue

            # ETSI LOPPU SISENNYKSEN PERUSTEELLA
            content_from_start = modified_content[match_start:].split('\n')
            indent_level = -1
            end_line_idx = 0
            
            for j, line in enumerate(content_from_start):
                if j == 0: continue
                if not line.strip(): continue # Hypätään tyhjien yli pääteltäessä tasoa
                
                curr_indent = len(line) - len(line.lstrip())
                if indent_level == -1: indent_level = curr_indent
                
                if curr_indent < indent_level and line.strip():
                    end_line_idx = j
                    break
            else:
                end_line_idx = len(content_from_start)

            # --- KORJAUS: POISTETAAN TYHJÄT RIVIT LOPUSTA ---
            raw_lines = content_from_start[:end_line_idx]
            while raw_lines and not raw_lines[-1].strip():
                raw_lines.pop()
                end_line_idx -= 1
            
            old_code = '\n'.join(raw_lines)
            match_end = match_start + len('\n'.join(content_from_start[:end_line_idx]))

            # RIVINUMERO (1-perusteinen)
            alku_rivi = len(modified_content[:match_start].split('\n'))

            print(f"✅ Löytyi: {target_name} (Rivit {alku_rivi} - {alku_rivi + len(raw_lines) - 1})")
            
            print(f"\n{RED}POISTETAAN:{RESET}")
            for idx, line in enumerate(old_code.split('\n')):
                print(f"{RED}{alku_rivi + idx:4}: {line}{RESET}")

            print(f"\n{YELLOW}UUSI KOODI:{RESET}")
            new_code_clean = code_to_insert.rstrip()
            for idx, line in enumerate(new_code_clean.split('\n')):
                print(f"{YELLOW}{alku_rivi + idx:4}: {line}{RESET}")

            modified_content = modified_content[:match_start] + new_code_clean + modified_content[match_end:]

        except Exception as e:
            print(f"❌ Virhe lohkon käsittelyssä: {e}")
    
    return modified_content

if __name__ == "__main__":
    if os.name == 'nt': os.system('')
    
    paivitetty_sisalto = nayta_muutos()
    
    if paivitetty_sisalto:
        vastaus = input("\n💾 Tallennetaanko muutokset? (k/e): ")
        if vastaus.lower() == 'k':
            tallenna_muutokset(paivitetty_sisalto)
        else:
            print("Tallennus peruttu.")
    else:
        print("Ei muutoksia tehtäväksi.")