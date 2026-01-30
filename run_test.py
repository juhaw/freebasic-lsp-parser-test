from fb_parser import get_type_members

# Testikoodi, jossa on sotkua (kommentteja, tyhjiä rivejä ja eri kirjainkokoja)
testi_koodi = """
' --- TESTI ALKAA ---
Type Sankari
    HP As Integer
    Voima As Integer ' Kommentti tässä
    
    Declare Sub Hyokkaa(kohde As String)
    Declare Function GetNimi() As String
End Type
"""

def aja_testi():
    # Parseri palauttaa nyt CaseInsensitiveDictin, joka hoitaa haut automaattisesti
    kaikki_tyypit, _ = get_type_members(testi_koodi)
    
    # Kokeillaan hakea "Sankari" (isolla), vaikka se on sisäisesti "sankari"
    tunnistettu_tyyppi = "Sankari" 
    
    print(f"--- TESTI: {tunnistettu_tyyppi} ---")
    
    # Tämä haku toimii nyt suoraan, koska parserin palauttama 
    # sanakirja osaa pienentää hakusanan itse!
    if tunnistettu_tyyppi in kaikki_tyypit:
        print(f"LÖYTYI: Tyyppi '{tunnistettu_tyyppi}' tunnistettu onnistuneesti.\n")
        
        jasenet = kaikki_tyypit[tunnistettu_tyyppi]
        for jasen in jasenet:
            print(f"  NÄKYY LISTASSA: {jasen['label']}")
            print(f"  LISÄÄ KOODIIN:  {jasen['insertText']}")
            print(f"  LISÄTIETO:      {jasen['detail']}")
            print("-" * 40)
    else:
        print(f"VIRHE: Tyyppiä '{tunnistettu_tyyppi}' ei löytynyt.")
        print(f"Parserin löytämät avaimet: {list(kaikki_tyypit.keys())}")

if __name__ == "__main__":
    aja_testi()