# MiniJob Maroc

## Présentation du projet

**MiniJob Maroc** est une application web destinée à faciliter la recherche d’emploi au Maroc et la gestion des candidatures. Elle met en relation des candidats qui consultent des offres et postulent en ligne avec des équipes de recrutement et des administrateurs.

Le projet intègre :
- La recherche avancée d'offres via un moteur **Elasticsearch** (avec bascule automatique en recherche locale si Elasticsearch est hors ligne).
- Un **espace administrateur** préconfiguré avec publication d'offres d'emploi, suivi des candidatures et gestion de l'index Elasticsearch.
- Un **espace candidat** complet avec suivi des candidatures et possibilité de retrait.
- Une suite complète de **tests automatisés Robot Framework** (31 tests passants).

---

## Comptes de démonstration préconfigurés

| Profil | Email | Mot de passe | Rôle & Permissions |
| --- | --- | --- | --- |
| **Administrateur** | `admin@gmail.com` | `admin` | Accès `/espace`, publication et suppression d'offres, examen des candidatures, réindexation Elasticsearch. |
| **Employé / Recruteur** | `employee@gmail.com` | `employee` | Accès `/espace`, création et publication d'offres d'emploi, suivi des candidatures. |
| **Candidat** | `aitmeskine.mohamed@gmail.com` | `password` (ou créer un compte via le formulaire) | Accès `/mes-candidatures`, recherche d'offres, postuler et retirer ses candidatures. |

---

## Moteur de Recherche Elasticsearch

L'application intègre le service [`elasticsearch_service.py`](elasticsearch_service.py) :
- **Index utilisé** : `jobs`
- **Recherche plein texte** : titre (`title^3`), entreprise (`company^2`), tags/compétences (`tags^2`), description avec tolérance aux fautes (`fuzziness: AUTO`).
- **Filtres combinés** : filtrage par ville (Casablanca, Rabat, Tanger, etc.) et contrat (CDI, CDD, Stage, Freelance).
- **Mode Haute Disponibilité** : si le cluster Elasticsearch n'est pas joignable (ex: port 9200 fermé), l'application bascule automatiquement et de manière transparente sur la recherche locale sans erreur.
- **Synchronisation automatique** : chaque offre publiée par l'administrateur est immédiatement enregistrée et indexée dans Elasticsearch.

### Pour lancer Elasticsearch localement (optionnel avec Docker) :
```powershell
docker run -d --name elasticsearch -p 9200:9200 -e "discovery.type=single-node" -e "xpack.security.enabled=false" docker.elastic.co/elasticsearch/elasticsearch:8.11.0
```

---

## Architecture et fichiers principaux

```text
app.py                                       Routes Flask, authentification, gestion des offres & candidatures
elasticsearch_service.py                     Client REST Elasticsearch, mapping, indexation et requêtes booléennes
templates\index.html                         Page d'accueil et recherche d'offres
templates\applications.html                  Espace administrateur & tableau de bord candidat
static\app.js                                Logique de la page d'accueil (recherche, formulaire de compte, candidature)
static\applications.js                       Logique des tableaux de bord (tabs admin, publication, statut ES, candidatures)
static\style.css                             Styles responsive (thème marocain, métriques, badges, formulaires admin)
data\jobs.json                               Persistance des offres d'emploi
data\users.json                              Persistance des comptes utilisateurs
data\applications.json                       Persistance des candidatures
tests\test_app.py                            Tests unitaires Python
tests\robot\job_search.robot                 Tests Robot Framework : parcours recherche et authentification (19 tests)
tests\robot\admin_and_elasticsearch.robot    Tests Robot Framework : admin, publication d'offres et Elasticsearch (12 tests)
```

---

## Routes API

| Méthode | Route | Description | Accès requis |
| --- | --- | --- | --- |
| `GET` | `/` | Page d’accueil et recherche des offres. | Public |
| `GET` | `/api/jobs?q=...&location=...&contract=...` | Recherche des offres (Elasticsearch ou local). | Public |
| `POST` | `/api/jobs` | Publie une nouvelle offre d'emploi et l'indexe dans Elasticsearch. | `admin`, `recruiter` |
| `DELETE` | `/api/jobs/<int:job_id>` | Supprime une offre du catalogue et d'Elasticsearch. | `admin` |
| `GET` | `/api/es/status` | Indique l'état du moteur Elasticsearch (en ligne / hors ligne). | Public |
| `POST` | `/api/admin/reindex` | Réindexe toutes les offres dans Elasticsearch. | `admin` |
| `POST` | `/api/auth/register` | Inscription d'un nouveau candidat. | Public |
| `POST` | `/api/auth/login` | Connexion à un compte existant. | Public |
| `GET` | `/api/auth/me` | Profil de l'utilisateur connecté. | Connecté |
| `POST` | `/api/auth/logout` | Déconnexion. | Connecté |
| `GET` | `/mes-candidatures` | Dashboard personnel du candidat. | `candidate` |
| `GET` | `/espace` | Dashboard de l'administrateur / recruteur. | `admin`, `recruiter` |
| `GET` | `/api/applications` | Liste des candidatures de l'utilisateur. | `candidate`, `admin`, `recruiter` |
| `POST` | `/api/applications` | Envoie une candidature pour une offre. | `candidate`, `admin` |
| `DELETE` | `/api/applications/<int:app_id>` | Retire/supprime une candidature. | Propriétaire ou `admin` |
| `GET` | `/api/management/applications` | Liste toutes les candidatures reçues. | `admin`, `recruiter` |
| `GET` | `/health` | Contrôle de santé de l'API. | Public |

---

## Lancement local de l'application

Dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

L'application est disponible sur **<http://127.0.0.1:5000>**.

---

## Exécution des Tests

### 1. Tests Automatisés Robot Framework (31 tests au total)

```powershell
python -m robot --outputdir results tests/robot/
```

Les rapports et journaux interactifs sont générés dans :
- `results\report.html`
- `results\log.html`
- `results\output.xml`

### 2. Tests Unitaires Python

```powershell
python -m unittest discover -s tests -v
```
