import re

# Tämä luokka pitää olla mukana, jotta haku on automaattista
class CaseInsensitiveDict(dict):
    """Sanakirja, joka ei välitä kirjainkoosta haettaessa."""
    def __getitem__(self, key):
        return super().__getitem__(key.lower())
    def __contains__(self, key):
        return super().__contains__(key.lower())
    def get(self, key, default=None):
        return super().get(key.lower(), default)

def get_type_members(source, var_name=None):
    """
    Tämä on se siirrettävä funktio. Se käyttää yllä olevaa luokkaa 
    varmistaakseen, ettei kirjainkoosta tarvitse välittää missään vaiheessa.
    """
    types = CaseInsensitiveDict()
    current_type = None
    lines = source.splitlines()
    
    for line in lines:
        clean_line = line.split("'")[0].strip()
        if not clean_line:
            continue
            
        lower_line = clean_line.lower()
        
        # Tunnistetaan Tyypin alku
        m_type = re.match(r"^type\s+(\w+)", lower_line)
        if m_type and not lower_line.endswith("end type"):
            current_type = m_type.group(1) 
            types[current_type] = []
            continue
            
        # Tunnistetaan Tyypin loppu
        if lower_line == "end type":
            current_type = None
            continue
            
        if current_type:
            # Jäsenten haku
            if lower_line.startswith("declare"):
                is_sub = "sub" in lower_line
                prefix = "Sub: " if is_sub else "Func: "
                temp = lower_line.replace("declare", "").replace("sub", "").replace("function", "").strip()
                member_name = re.split(r'\(|\s+as\s+', temp)[0].strip()
            else:
                prefix = "Var: "
                member_name = re.split(r'\(|\s+as\s+', lower_line)[0].strip()

            if member_name:
                types[current_type].append({
                    "label": f"{prefix}{member_name}",
                    "insertText": member_name,
                    "detail": clean_line
                })

    # Muuttujan tyypin haku (LSP:tä varten)
    var_type = None
    if var_name:
        search_target = var_name.lower()
        for line in lines:
            clean = line.split("'")[0].strip().lower()
            if re.search(r"\b" + re.escape(search_target) + r"\b", clean):
                m_var = re.search(r"as\s+(\w+)", clean)
                if m_var:
                    var_type = m_var.group(1)
                    break
                
    return types, var_type