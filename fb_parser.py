import re
import os

class CaseInsensitiveDict(dict):
    """Sanakirja, joka ei välitä kirjainkoosta avaimissa."""
    def __setitem__(self, key, value):
        super().__setitem__(key.lower(), value)
    def __getitem__(self, key):
        return super().__getitem__(key.lower())
    def get(self, key, default=None):
        return super().get(key.lower(), default)
    def __contains__(self, key):
        return super().__contains__(key.lower())

def get_type_members(source_code, current_file_path=""):
    """
    Skannaa koodin ja palauttaa (all_types, var_to_type).
    """
    all_types = CaseInsensitiveDict()
    var_to_type = CaseInsensitiveDict()
    base_path = os.path.dirname(current_file_path) if current_file_path else ""

    # 1. Käsitellään #include
    include_matches = re.findall(r'(?i)#include\s+"([^"]+)"', source_code)
    for inc_file in include_matches:
        full_path = os.path.join(base_path, inc_file)
        if os.path.exists(full_path):
            try:
                with open(full_path, "r", encoding="utf-8", errors="ignore") as f:
                    inc_code = f.read()
                    inc_types, inc_vars = get_type_members(inc_code, full_path)
                    all_types.update(inc_types)
                    var_to_type.update(inc_vars)
            except Exception: pass

    # 2. Etsitään tyyppimäärittelyt
    type_blocks = re.findall(r"(?i)type\s+(\w+)\s+(.*?)\s+end\s+type", source_code, re.DOTALL)
    for type_name, body in type_blocks:
        members = []
        for line in body.splitlines():
            line = line.strip()
            if not line or line.startswith("'"): continue
            
            # Metodit: Nappaa nimen, sulut JA kaiken niiden jälkeen (paluutyypin)
            method_match = re.search(r"(?i)declare\s+(?:sub|function)\s+(\w+)\s*(\(.*\)\s*.*)", line)
            if method_match:
                m_name, rest = method_match.groups()
                members.append({
                    'label': m_name.strip(),
                    'insertText': f"{m_name.strip()}($1)",
                    'detail': f"(Method) {m_name.strip()} {rest.strip()}"
                })
                continue

            # Jäsenmuuttujat
            member_match = re.search(r"(?i)^(\w+)\s+as\s+(\w+)", line)
            if member_match:
                m_name, m_type = member_match.groups()
                members.append({
                    'label': m_name.strip(),
                    'insertText': m_name.strip(),
                    'detail': f"(Member) {m_name.strip()} As {m_type.strip()}"
                })
        all_types[type_name] = members

    # 3. Muuttujamäärittelyt (Dim)
    for line in source_code.splitlines():
        line = line.strip()
        if not line or line.lower().startswith("'"): continue

        match_a = re.match(r"(?i)dim\s+as\s+(\w+)\s+(.+)", line)
        if match_a:
            t_name, names_str = match_a.groups()
            for n in names_str.split(','):
                name = n.strip()
                if name: var_to_type[name] = t_name
            continue

        match_b = re.match(r"(?i)dim\s+(.+)\s+as\s+(\w+)", line)
        if match_b:
            names_str, t_name = match_b.groups()
            for n in names_str.split(','):
                name = n.strip()
                if name: var_to_type[name] = t_name

    return all_types, var_to_type