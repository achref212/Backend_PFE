import json
import re

def sanitize_json_fields(obj):
    """
    Corrige les champs texte mal formés dans un JSON : caractères spéciaux, guillemets non échappés, retours ligne.
    """
    if isinstance(obj, dict):
        return {k: sanitize_json_fields(v) for k, v in obj.items()}
    elif isinstance(obj, list):
        return [sanitize_json_fields(v) for v in obj]
    elif isinstance(obj, str):
        obj = obj.replace('\n', ' ').replace('\r', '')
        obj = obj.replace('"', '\\"')  # échappe les guillemets
        return obj.strip()
    return obj
def fix_malformed_json(input_path="parcoursup_updated.json", output_path="parcoursup_sanitized.json"):
    with open(input_path, "r", encoding="utf-8") as f:
        try:
            data = json.load(f)
        except json.JSONDecodeError as e:
            print(f"[❌ Erreur JSON initial] : {e}")
            return

    fixed_data = []
    for formation in data:
        for key in formation:
            if isinstance(formation[key], str):
                formation[key] = sanitize_json_fields(formation[key])
            elif isinstance(formation[key], dict):
                for subkey in formation[key]:
                    formation[key][subkey] = sanitize_json_fields(formation[key][subkey])
        fixed_data.append(formation)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(fixed_data, f, indent=2, ensure_ascii=False)

    print(f"✅ Données nettoyées sauvegardées dans {output_path}")

# === Point d’entrée principal ===
if __name__ == "__main__":
    fix_malformed_json()
