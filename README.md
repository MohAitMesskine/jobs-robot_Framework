# MiniJob Maroc

## Présentation du projet

**MiniJob Maroc** est une application web de démonstration destinée à faciliter la recherche d’emploi au Maroc et la gestion des candidatures. Elle met en relation des candidats qui consultent des offres et postulent en ligne avec des équipes de recrutement qui examinent les candidatures reçues.

Le projet fournit un parcours complet de démonstration : consultation et filtrage des offres, création de compte, connexion, envoi d’une candidature et consultation des candidatures selon le rôle de l’utilisateur. L’interface est en français et reprend les couleurs rouge et verte du Maroc.

> **Périmètre des données :** les offres et rémunérations affichées sont des exemples de démonstration. Elles ne constituent pas des offres d’emploi réelles ni une garantie de salaire.

## Objectifs

- Présenter un parcours de recherche d’emploi simple, lisible et utilisable sur ordinateur et mobile.
- Permettre de rechercher des offres par mot-clé, ville et type de contrat.
- Protéger les comptes et les candidatures avec une authentification par session.
- Séparer les espaces candidat et équipe de recrutement et appliquer les permissions côté serveur.
- Fournir des tests automatisés permettant de vérifier les principaux parcours et règles d’accès.

## Fonctionnalités disponibles

### Recherche d’offres

Le catalogue de démonstration propose huit offres associées à Casablanca, Rabat, Tanger, Marrakech, Agadir, Fès et au télétravail. La recherche peut combiner :

- un mot-clé portant sur le métier, l’entreprise, la description ou les compétences ;
- une ville ;
- un type de contrat : CDI, CDD, stage ou freelance.

Les résultats présentent le titre, l’entreprise, le lieu, le contrat, une description et une rémunération indicative lorsqu’elle est fournie.

### Comptes et authentification

- Inscription avec nom, adresse e-mail et mot de passe.
- Validation du format de l’adresse e-mail et d’une longueur minimale de huit caractères pour le mot de passe.
- Refus des adresses déjà inscrites.
- Connexion, déconnexion et vérification de la session en cours.
- Stockage des mots de passe sous forme de hachages ; le mot de passe en clair n’est pas écrit dans le fichier JSON.
- Attribution automatique du rôle `candidate` lors de l’inscription. Un utilisateur ne peut pas obtenir un rôle privilégié en ajoutant un champ au formulaire d’inscription.

### Candidatures et espaces par rôle

Les pages sont séparées afin que les candidatures ne soient pas affichées sur la page d’accueil :

| Rôle | Espace | Accès aux candidatures |
| --- | --- | --- |
| `candidate` | `/mes-candidatures` | Consulte uniquement ses propres candidatures et peut postuler aux offres. |
| `recruiter` | `/espace` | Consulte les candidatures reçues. Ne peut pas envoyer de candidature comme candidat. |
| `admin` | `/espace` | Consulte les candidatures reçues dans l’espace administrateur. |

Les liens vers ces espaces s’affichent après connexion et selon le rôle. Les pages et les API contrôlent également le rôle côté serveur : masquer un lien dans le navigateur ne constitue pas le contrôle d’accès.

### Ce qui n’est pas encore inclus

Cette version ne propose pas encore de gestion graphique des comptes et des rôles, de création/modification d’offres, de changement de statut des candidatures, de notifications, de dépôt de CV ni de déploiement en production. L’espace administrateur sert actuellement à consulter les candidatures, pas à administrer tous les éléments de la plateforme.

## Rôles et création d’un compte administrateur de démonstration

Pour des raisons de sécurité, l’inscription publique ne permet de créer que des comptes candidats. Il n’existe pas de compte administrateur ni de mot de passe administrateur prédéfini.

Pour tester l’espace administrateur localement :

1. Démarrez l’application et inscrivez un compte depuis le formulaire.
2. Arrêtez le serveur.
3. Ouvrez `data\users.json` dans un éditeur local et changez le champ `"role"` du compte souhaité de `"candidate"` à `"admin"`. Ne modifiez pas `password_hash`.
4. Redémarrez l’application et reconnectez-vous avec ce compte. Le lien **Espace admin** ouvre `/espace`.

Pour créer un recruteur de démonstration, la même procédure s’applique avec le rôle `"recruiter"`. Ne modifiez les rôles que dans un environnement local de confiance. La modification manuelle des fichiers JSON est une procédure de démonstration, pas un mécanisme d’administration adapté à une mise en production.

## Architecture et données

- **Serveur :** Python et Flask (`app.py`).
- **Interface :** modèles HTML/Jinja dans `templates\`, JavaScript et styles dans `static\`.
- **Persistance de démonstration :** `data\users.json` pour les comptes et `data\applications.json` pour les candidatures.
- **Stockage des sessions :** session Flask protégée par la clé configurée dans `SECRET_KEY`.
- **Tests :** tests unitaires Python dans `tests\test_app.py` et tests d’API HTTP Robot Framework dans `tests\robot\job_search.robot`.

Le dossier `data\` et ses fichiers sont créés au premier enregistrement. Ils sont ignorés par Git afin de ne pas versionner les comptes ou les candidatures. La variable d’environnement `DATA_DIR` permet de choisir un autre dossier de données.

Les fichiers JSON sont prévus pour une démonstration locale avec une seule instance. Ils ne conviennent pas comme stockage de production ou pour plusieurs instances concurrentes. Pour un déploiement réel, il faudra notamment les remplacer par une base de données, définir une clé secrète privée et persistante, utiliser HTTPS avec `COOKIE_SECURE=true`, protéger les données personnelles et prévoir les procédures de sauvegarde et de contrôle d’accès adaptées.

## Installation et lancement local

Depuis la racine du dépôt, dans PowerShell :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Ouvrez ensuite <http://127.0.0.1:5000>. Pour arrêter le serveur, utilisez `Ctrl+C` dans la fenêtre PowerShell où il tourne.

Le serveur Flask intégré est destiné au développement et à la démonstration locale, pas à l’hébergement en production.

## Vérification et tests

### Tests unitaires

```powershell
python -m unittest discover -s tests -v
```

Ils couvrent notamment le hachage du mot de passe, la persistance JSON, la séparation des candidatures par utilisateur et les permissions des rôles.

### Tests Robot Framework

```powershell
python -m robot --outputdir results tests/robot
```

La suite démarre une instance de test sur le port 5001, utilise un dossier temporaire pour les données, puis arrête le serveur. Elle vérifie les routes HTTP, la recherche, l’authentification, les candidatures, les rôles et les pages séparées. Elle contrôle l’API et le balisage HTML ; elle ne simule pas les interactions dans un vrai navigateur.

Les rapports Robot sont générés dans `results\report.html`, `results\log.html` et `results\output.xml`.

## Routes principales

| Méthode | Route | Description | Accès |
| --- | --- | --- | --- |
| `GET` | `/` | Page d’accueil et catalogue d’offres. | Public |
| `GET` | `/api/jobs?q=...&location=...&contract=...` | Recherche les offres selon les filtres fournis. | Public |
| `POST` | `/api/auth/register` | Crée un compte candidat et ouvre une session. | Public |
| `POST` | `/api/auth/login` | Authentifie un compte existant. | Public |
| `GET` | `/api/auth/me` | Renvoie le profil de la session active. | Connecté |
| `POST` | `/api/auth/logout` | Ferme la session active. | Connecté |
| `GET` | `/mes-candidatures` | Page des candidatures personnelles. | `candidate` |
| `GET` | `/espace` | Page de suivi des candidatures reçues. | `recruiter`, `admin` |
| `GET` | `/api/applications` | Liste les candidatures de l’utilisateur connecté. | `candidate` |
| `POST` | `/api/applications` | Envoie une candidature pour une offre existante. | `candidate` |
| `GET` | `/api/management/applications` | Liste les candidatures reçues. | `recruiter`, `admin` |
| `GET` | `/health` | Vérifie que le serveur répond. | Public |

## Organisation des principaux fichiers

```text
app.py                         Routes Flask, authentification, rôles et stockage JSON
templates\index.html           Page d’accueil et recherche d’offres
templates\applications.html   Modèle commun des espaces de candidatures
static\app.js                  Interactions de la page d’accueil
static\applications.js         Chargement et affichage des candidatures
static\style.css               Style responsive et thème marocain
tests\test_app.py              Tests unitaires
tests\robot\job_search.robot   Tests HTTP Robot Framework
```
