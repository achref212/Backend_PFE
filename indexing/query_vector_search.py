from sentence_transformers import SentenceTransformer
import faiss
import json
import numpy as np
import os

# Charger modèle
model = SentenceTransformer('all-MiniLM-L6-v2')

# Charger index FAISS et métadonnées
index = faiss.read_index("data/formations_index.faiss")
with open("data/formations_metadata.json", "r", encoding="utf-8") as f:
    metadata = json.load(f)

# Fonction de recherche
def search(question, k=5):
    query_vector = model.encode([question])
    query_vector = np.array(query_vector).astype("float32")
    distances, indices = index.search(query_vector, k)

    results = []
    for idx in indices[0]:
        if idx < len(metadata):
            results.append(metadata[idx])
    return results
