import re
import os

def load_ai_snippets(snippet_file):
    """
    Lataa AI:n koodipalasten tiedoston ja ryhmittelee palaset paikkamerkkien mukaan.
    Palaset ovat muotoa:
    # ### AI_INSERT_POINT: <marker> ###
    """
    snippets = {}
    current_marker = None
    current_lines = []

    with open(snippet_file, "r", encoding="utf-8") as f:
        for line in f:
            m = re.match(r"#\s*### AI_INSERT_POINT: (.+) ###", line.strip())
            if m:
                # Tallenna edellinen palanen
                if current_marker is not None and current_lines:
                    snippets.setdefault(current_marker, []).extend(current_lines)
                current_marker = m.group(1)
                current_lines = []
            else:
                if current_marker is not None:
                    current_lines.append(line)
        # Tallenna viimeinen palanen
        if current_marker is not None and current_lines:
            snippets.setdefault(current_marker, []).extend(current_lines)
    return snippets

def insert_snippets_into_parser(parser_file, snippets, backup=True):
    """
    Lukee parserin, lisää snippetit paikkamerkkien kohdille ja tallentaa tiedoston.
    """
    with open(parser_file, "r", encoding="utf-8") as f:
        lines = f.readlines()

    new_lines = []
    for line in lines:
        new_lines.append(line)
        m = re.match(r"#\s*### AI_INSERT_POINT: (.+) ###", line.strip())
        if m:
            marker = m.group(1)
            if marker in snippets:
                new_lines.extend(snippets[marker])
                # Poistetaan tallennettu snippet, ettei lisätä uudestaan
                del snippets[marker]

    if backup:
        backup_file = parser_file + ".bak"
        os.rename(parser_file, backup_file)
        print(f"Backup saved to {backup_file}")

    with open(parser_file, "w", encoding="utf-8") as f:
        f.writelines(new_lines)

    print(f"Snippets inserted into {parser_file}")

if __name__ == "__main__":
    snippet_file = "ai_snippets.txt"       # Tiedosto johon kopioit leikepöydältä AI-palasen
    parser_file = "fb_parser_copilot_3_static.py"

    snippets = load_ai_snippets(snippet_file)
    insert_snippets_into_parser(parser_file, snippets)
