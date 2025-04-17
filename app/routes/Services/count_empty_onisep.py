import json

def count_empty_onisep_links(file_path="parcoursup_updated.json"):
    with open(file_path, "r", encoding="utf-8") as f:
        data = json.load(f)

    total = len(data)
    empty_count = 0

    for formation in data:
        lien = formation.get("lien_onisep", "").strip().lower()
        if not lien or "aucun lien" in lien:
            empty_count += 1

    print(f"📊 Total de formations : {total}")
    print(f"❌ Formations sans lien Onisep valide : {empty_count}")
    print(f"✅ Formations avec lien Onisep valide : {total - empty_count}")

if __name__ == "__main__":
    count_empty_onisep_links()
