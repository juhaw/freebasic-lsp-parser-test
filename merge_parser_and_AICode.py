import re
import os

# === MUOKKAA NÄITÄ ===
TARGET_FILE = 'fb_parser_GPT_static.py'
AI_RESPONSE_FILE = 'AI code.txt'
# =====================

RED = '\033[91m'
GREEN = '\033[92m'
YELLOW = '\033[93m'
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
        print(f"Virhe: {e}")
        return None

    blocks = re.findall(r'(.*?<<<< VANHA start \[.*?\].*?>>>> UUSI end)', ai_text, re.DOTALL)
    if not blocks: blocks = [ai_text]

    modified_content = file_content

    for i, block in enumerate(blocks, 1):
        if '<<<< VANHA start' not in block: continue

        try:
            parts = block.split('<<<< VANHA start')
            top_ctx = parts[0].strip('\n')
            mid_parts = parts[1].split('>>>> VANHA end')
            header = mid_parts[0].split(']', 1)[0] + "]"
            old_code = mid_parts[0].split(']', 1)[1].strip('\n')
            bottom_parts = mid_parts[1].split('<<<< UUSI start')
            bottom_ctx = bottom_parts[0].strip('\n')
            new_code = bottom_parts[1].split('>>>> UUSI end')[0].strip('\n')

            def to_regex(text):
                if not text.strip(): return r'\s*'
                return re.sub(r'\\\s+', r'\\s+', re.escape(text.strip()))

            # LUO PATTERNI JOKA KATSOO KOKO KONTEKSTIN
            full_pattern = rf"({to_regex(top_ctx)})\s+({to_regex(old_code)})\s+({to_regex(bottom_ctx)})"
            match = re.search(full_pattern, file_content, re.DOTALL)
            
            print(f"\nKOHDE: {header}")
            
            if match:
                # LASKETAAN OIKEAT INDEKSIT
                start_index = match.start(2)  # Vanhan koodin alku
                end_index = match.end(2)      # Vanhan koodin loppu
                
                # Lasketaan rivinumerot
                rivit = file_content.split('\n')
                korvaus_alku_rivi = file_content[:start_index].count('\n') + 1
                korvaus_loppu_rivi = file_content[:end_index].count('\n') + 1
                vanhan_koodin_rivimäärä = korvaus_loppu_rivi - korvaus_alku_rivi + 1
                uusi_koodi_rivit = new_code.split('\n')

                print(f"Löytyi tiedostosta (Vihreä = Säilyy, Punainen = Poistetaan):")
                print("-" * 60)

                # Lasketaan näytettävän alueen alku (top_ctx alkaa)
                naytto_alku_rivi = file_content[:match.start(1)].count('\n') + 1
                naytto_loppu_rivi = file_content[:match.end(3)].count('\n') + 1
                
                for idx in range(naytto_alku_rivi - 1, naytto_loppu_rivi):
                    rivi_nro = idx + 1
                    rivi = rivit[idx]
                    
                    if korvaus_alku_rivi <= rivi_nro <= korvaus_loppu_rivi:
                        print(f"{RED}{rivi_nro:4}: {rivi} <--- POISTETAAN{RESET}")
                    else:
                        print(f"{GREEN}{rivi_nro:4}: {rivi}{RESET}")

                print("-" * 60)
                print("UUSI KOODI JOKA TULEE TILALLE:")
                for idx, rivi in enumerate(uusi_koodi_rivit):
                    print(f"{YELLOW}{korvaus_alku_rivi + idx:4}: {rivi}{RESET}")
                print("-" * 60)

                # KORJATTU KORVAUSLOGIJIKKA
                # Yläosa: kaikki rivit ennen korvausaluetta
                ylaosa = rivit[:korvaus_alku_rivi - 1]
                
                # Alaosa: kaikki rivit korvausalueen jälkeen
                alaosa = rivit[korvaus_loppu_rivi:]
                
                # Luodaan uusi sisältö
                modified_content = '\n'.join(ylaosa + uusi_koodi_rivit + alaosa)
                
                # Päivitetään rivit-muuttuja seuraavaa vertailua varten
                rivit = modified_content.split('\n')
                file_content = modified_content  # Päivitetään hakemista varten
                
            else:
                print("Kohtaa ei löytynyt tiedostosta.")
                print(f"Haku: {old_code[:100]}...")
                print(f"Pattern: {full_pattern[:200]}...")

        except Exception as e:
            print(f"Lohkon {i} käsittelyvirhe: {e}")
            import traceback
            traceback.print_exc()

    return modified_content

if __name__ == "__main__":
    if os.name == 'nt':
        os.system('')

    paivitetty_sisalto = nayta_muutos()
    
    if paivitetty_sisalto:
        # Varmistus ennen tallennusta
        vastaus = input("\n💾 Tallennetaanko muutokset? (k/e): ")
        if vastaus.lower() == 'k':
            tallenna_muutokset(paivitetty_sisalto)
        else:
            print("Tallennus peruttu.")
    else:
        print("Ei muutoksia tallennettavaksi.")