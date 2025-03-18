# 📚 Projet PFE — Orientation Post-Bac Assistée par IA

## 📝 Sujet du Projet
Collecte et structuration des données des 24 000 formations Parcoursup, et développement d’un Chatbot Q&A basé sur un LLM (Mistral) avec une architecture RAG (Retrieval-Augmented Generation), ainsi qu’un système de prédiction intelligent des taux d’acceptation pour améliorer l’orientation des lycéens.

## 🎯 Objectifs
- Collecte et structuration des données des formations via scraping ou API publiques (ONISEP, Parcoursup, Data.gouv.fr).
- Construction de bases de données relationnelle (SQL) et vectorielle (FAISS).
- Mise en place d’un Chatbot intelligent basé sur un LLM (Mistral) + RAG.
- Personnalisation des réponses du Chatbot selon le profil utilisateur.
- Développement d’un modèle de prédiction du taux d’acceptation.
- Amélioration continue via feedback utilisateurs.

## 🔍 Fonctionnalités Clés
### ✅ Web Scraping & Structuration des Formations
- Extraction des données (noms, spécialités, attendus, débouchés, taux de remplissage...).
- Nettoyage et structuration des données.
- Enregistrement en base SQL et vectorielle.

### 🤖 Chatbot LLM + RAG
- Intégration d’un modèle Mistral.
- Génération de réponses contextualisées via une base vectorielle (FAISS).
- Prise en compte des étapes du parcours utilisateur pour personnaliser les réponses.

### 📈 Prédiction de Taux d’Acceptation
- Scraping des critères d’évaluation : notes moyennes, quotas, spécialités, etc.
- Modélisation statistique ou ML pour calculer les chances d’admission.
- Visualisation des résultats avec des scores de probabilité par voeu.

### 📊 Tableau de Bord Utilisateur
- Suivi de progression (QCM, statistiques).
- Interface de feedback utilisateurs.
- Historique des interactions avec le LLM.

## 🛠️ Technologies Utilisées
| Côté | Technologies |
|------|----------------|
| Backend | Python, Flask |
| Frontend | Flutter ou React.js |
| Scraping | BeautifulSoup, Scrapy |
| Base de données | PostgreSQL / MySQL, FAISS |
| IA & LLM | Mistral, OpenAI/HuggingFace API, Transformers |
| Modélisation | Scikit-learn, PyTorch, TensorFlow |
| Déploiement | GitHub, CI/CD (GitHub Actions), Docker |
