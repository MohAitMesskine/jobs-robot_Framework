# MyJobs Maroc — Projet d'Automatisation de Tests (Robot Framework)

## 🎯 Objectif du Projet

Ce projet a pour objectif principal la mise en place d'une **stratégie complète d'automatisation des tests logiciels** avec **Robot Framework** pour une plateforme web de recrutement et de recherche d'emploi au Maroc (**MyJobs Maroc**), intégrant un moteur de recherche **Elasticsearch**, des rôles multiples (Administrateur, Employé, Candidat) et des flux de candidatures en ligne.

Le cœur de ce projet repose sur :
1. **La couverture fonctionnelle et de sécurité automatisée de bout en bout** via des suites de tests Robot Framework.
2. **L'isolation rigoureuse des environnements de test** (démarrage dynamique de serveurs et répertoires de données temporaires).
3. **La production et l'exploitation des rapports de tests détaillés** (`report.html`, `log.html`, `output.xml`) pour l'assurance qualité (QA) et l'intégration continue (CI/CD).

---

## 📊 Tableau de Bord des Tests (35 Tests / 100% Succès)

```text
==============================================================================
Robot                                                                 | PASS |
35 tests, 35 passed, 0 failed (100% de réussite)
==============================================================================
Suite 1 : tests/robot/job_search.robot                 | 19 tests passés |
Suite 2 : tests/robot/admin_and_elasticsearch.robot    | 16 tests passés |
==============================================================================
```

---

## 🏗️ Architecture et Stratégie d'Automatisation

### 1. Bibliothèques Robot Framework utilisées
- **`RequestsLibrary`** : Exécution de requêtes HTTP REST (`GET`, `POST`, `DELETE`), gestion des sessions d'authentification par cookies et validation fine des codes de statut HTTP et des payloads JSON.
- **`Process`** : Démarrage et arrêt automatisés du serveur d'application en arrière-plan pour chaque suite de tests (`Suite Setup` et `Suite Teardown`).
- **`Collections`** : Validation stricte des structures de données dictionnaires et listes renvoyées par l'API.
- **`OperatingSystem`** : Création et purge automatique des dossiers de stockage temporaires.

### 2. Isolation et Herméticité des Tests
Chaque suite Robot Framework applique le principe d'étanchéité des données :
- Dans le **`Suite Setup`**, un répertoire de données vierge est généré à la volée via `tempfile.mkdtemp()`.
- Le serveur Flask est lancé sur un port de test isolé (`5001` ou `5002`) avec la variable `DATA_DIR` pointant sur ce répertoire éphémère.
- Le mot-clé de synchronisation `Wait Until Keyword Succeeds` s'assure que le serveur répond sur `/health` avant de débuter les tests.
- Dans le **`Suite Teardown`**, le processus serveur est arrêté (`Terminate Process`) et le répertoire temporaire est détruit sans laisser de traces.

---

## 🧪 Périmètre des Suites de Tests Automatisés

### Suite 1 : `tests/robot/job_search.robot` (19 Tests)
*Vérification des parcours publics, de l'exposition des interfaces, de la recherche et de la robustesse de l'authentification.*

- **Contrôle d'exposition IHM & API** :
  - Exposition de la page d'accueil, du formulaire de recherche, des formulaires de compte et des liens d'espace.
  - Contrôle de santé de l'API (`GET /health`).
- **Moteur de recherche & Filtrage** :
  - Catalogue complet des offres marocaines et rémunérations en MAD.
  - Filtrage multicritère par ville (Casablanca, Rabat, Tanger, etc.).
  - Combinaison mot-clé + type de contrat (CDI, CDD, Stage, Freelance).
  - Gestion des recherches sans correspondance (retour d'une liste vide sans crash).
- **Sécurité & Authentification des candidats** :
  - Blocage des candidatures anonymes (`401 Unauthorized`).
  - Inscription valide avec création de compte et ouverture de session (`201 Created`).
  - Rejet des adresses email invalides (`400 Bad Request`).
  - Blocage de l'auto-attribution d'un rôle privilégié lors de l'inscription (protection contre l'élévation de privilèges).
  - Validation de la longueur minimale du mot de passe (au moins 8 caractères).
  - Validation de la présence de tous les champs obligatoires.
  - Rejet des inscriptions en doublon (`409 Conflict`).
  - Rejet des connexions avec mot de passe erroné (`401 Unauthorized`).
  - Cycle complet de connexion puis déconnexion avec expiration de session.
- **Gestion des candidatures candidat** :
  - Enregistrement de candidature authentifiée avec association automatique du compte.
  - Rejet de candidature sans message.
  - Rejet de candidature pour un identifiant d'offre inexistant (`404 Not Found`).

---

### Suite 2 : `tests/robot/admin_and_elasticsearch.robot` (16 Tests)
*Vérification de l'espace administrateur, du parcours employé, de la publication d'offres et du moteur Elasticsearch.*

- **Espace Administrateur & Intégration Elasticsearch** :
  - Connexion du compte administrateur et validation du rôle `admin`.
  - Contrôle d'accès et présence des formulaires de gestion dans `/espace`.
  - Contrôle de l'endpoint d'état Elasticsearch (`GET /api/es/status`).
  - Réindexation manuelle Elasticsearch (`POST /api/admin/reindex`).
- **Publication et Cycle de Vie des Offres (Administrateur)** :
  - Publication d'une nouvelle offre d'emploi (`POST /api/jobs`).
  - Validation de la découvrabilité immédiate de l'offre publiée dans le moteur de recherche (`/api/jobs?q=...`).
  - Consultation des candidatures reçues dans l'espace de gestion staff.
  - Suppression définitive d'une offre d'emploi (`DELETE /api/jobs/<id>`) et vérification de son retrait de la recherche.
- **Publication d'Offres par les Employés** :
  - Connexion avec un compte employé et accès à son espace dédié.
  - Création et publication avec succès d'une offre par un employé (`POST /api/jobs`).
  - Découvrabilité immédiate dans la recherche de l'offre créée par l'employé.
  - Inscription publique d'un nouvel employé (`role=employee`) et publication directe d'annonces.
- **Contrôles de Sécurité & Permissions RBAC** :
  - Interdiction formelle pour un candidat classique de publier une offre (`403 Forbidden`).
  - Interdiction pour un visiteur non connecté de publier une offre (`401 Unauthorized`).
  - Possibilité pour le candidat de consulter ses candidatures puis de retirer sa propre candidature (`DELETE /api/applications/<id>`).

---

## 🚀 Exécution des Tests Automatisés

### Exécuter l'ensemble des suites Robot Framework
Depuis le terminal PowerShell à la racine du projet :

```powershell
python -m robot --outputdir results tests/robot/
```

### Exécuter une suite de test spécifique
```powershell
# Exécuter uniquement la suite de recherche et authentification
python -m robot --outputdir results tests/robot/job_search.robot

# Exécuter uniquement la suite administration, employés et Elasticsearch
python -m robot --outputdir results tests/robot/admin_and_elasticsearch.robot
```

### Exécuter les tests unitaires Python (complémentaires)
```powershell
python -m unittest discover -s tests -v
```

---

## 📑 Exploitation des Rapports de Test

Après chaque exécution, Robot Framework génère automatiquement trois artefacts d'analyse dans le dossier `results/` :

### 1. `results/report.html` — Le Rapport de Synthèse Interactif
- **Vue d'ensemble managériale** : diagramme circulaire et barre de statut visuelle indiquant le taux de réussite global (100% PASS).
- **Statistiques d'exécution** : durée totale, temps d'exécution par suite et par scénario de test.
- **Détail par scénario** : liste ordonnée de tous les cas de tests avec leur état (`PASS`/`FAIL`) et leurs métadonnées.

### 2. `results/log.html` — Le Journal Technique Détaillé
- **Traçabilité pas-à-pas** : arborescence dépliable montrant chaque mot-clé exécuté (`Keyword`).
- **Données d'appels HTTP** : requêtes exactes envoyées, URLs cibles, headers HTTP, payloads JSON transmis, codes de réponse HTTP et corps des réponses JSON.
- **Diagnostic instantané** : identification immédiate des causes d'erreur en cas d'échec d'une assertion.

### 3. `results/output.xml` — Les Résultats Bruts pour la CI/CD
- Fichier structuré standard XML permettant l'intégration avec des outils tiers :
  - Tableaux de bord **Jenkins** (via le plugin Robot Framework).
  - **GitHub Actions** / **GitLab CI** pour la publication de métriques de test et le blocage automatique des déploiements en cas de régression.

---

## 🛠️ Structure des Fichiers de Test

```text
projet-robot-framework/
├── tests/
│   ├── robot/
│   │   ├── job_search.robot                 # 19 tests fonctionnels (recherche, auth, candidatures)
│   │   └── admin_and_elasticsearch.robot    # 16 tests avancés (admin, employés, ES, sécurité)
│   └── test_app.py                          # 8 tests unitaires Python
├── results/                                 # Dossier de génération des rapports
│   ├── report.html                          # Rapport visuel de synthèse
│   ├── log.html                             # Journal technique détaillé
│   └── output.xml                           # Rapport XML pour CI/CD
├── app.py                                   # Application sous test (SUT)
└── elasticsearch_service.py                 # Module client Elasticsearch sous test
```

---

## 📋 Prérequis et Installation pour l'Exécution

```powershell
# 1. Création et activation de l'environnement virtuel
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# 2. Installation des dépendances de test
python -m pip install -r requirements.txt

# 3. Lancement de la campagne de test
python -m robot --outputdir results tests/robot/
```
