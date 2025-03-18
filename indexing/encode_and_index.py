from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np
import os

# Charger le modèle d'encodage sémantique
model = SentenceTransformer('all-MiniLM-L6-v2')

# Chemins
json_path = "data/formations.json"
index_path = "data/formations_index.faiss"
meta_path = "data/formations_metadata.json"

# Lecture intelligente du fichier JSON
data = []
try:
    with open(json_path, "r", encoding="utf-8") as f:
        try:
            # Essai lecture JSON classique (array [])
            data = json.load(f)
        except json.JSONDecodeError:
            print("⚠ Format JSON classique échoué, tentative en JSON Lines (ligne par ligne)...")
            f.seek(0)
            data = [json.loads(line) for line in f if line.strip() != '']
except FileNotFoundError:
    raise FileNotFoundError(f"[❌] Le fichier {json_path} est introuvable.")

if not data:
    raise ValueError("[❌] Le fichier formations.json est vide ou invalide.")

# Création des documents à encoder
documents = [
    f"{f.get('nom_formation', '')} - {f.get('etablissement', '')} - {', '.join(f.get('attendus', []))}"
    for f in data
]

# Encodage des documents
vectors = model.encode(documents)
vectors = np.array(vectors).astype("float32")

# Création de l'index FAISS
dimension = vectors.shape[1]
index = faiss.IndexFlatL2(dimension)
index.add(vectors)

# Sauvegarde de l'index
faiss.write_index(index, index_path)

# Sauvegarde des métadonnées
with open(meta_path, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print("✅ Encodage + indexation FAISS terminés avec succès.")
