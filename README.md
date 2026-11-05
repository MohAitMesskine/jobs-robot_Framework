# MiniJob Maroc

MiniJob est une plateforme de recherche d’emploi au Maroc réalisée avec Python et Flask. Elle propose un catalogue d’offres de démonstration à Casablanca, Rabat, Tanger, Marrakech, Agadir, Fès et en télétravail, une recherche multicritère, des comptes à rôles et le suivi des candidatures. Son identité visuelle reprend les couleurs rouge et verte du Maroc. Les rémunérations des offres sont indicatives.

## Démarrer le site

Depuis le dossier du projet, créez un environnement virtuel et installez les dépendances :

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python app.py
```

Ouvrez ensuite <http://127.0.0.1:5000>.

## Authentification

L’interface propose l’inscription, la connexion et la déconnexion. Une adresse e-mail ne peut être inscrite qu’une fois et le mot de passe doit comporter au moins 8 caractères. Les mots de passe sont stockés sous forme hachée dans `data\users.json`; les candidatures sont enregistrées dans `data\applications.json`. Ces fichiers sont créés au premier enregistrement, conservés après redémarrage et exclus de Git. Les nouvelles inscriptions reçoivent toujours le rôle `candidate` : le rôle envoyé par le navigateur n’est jamais accepté.

Les rôles disponibles sont `candidate`, `recruiter` et `admin`. Après connexion, l’espace du compte est disponible sur une page dédiée : `/espace` pour les administrateurs et recruteurs, `/mes-candidatures` pour les candidats. Les listes de candidatures ne s’affichent donc pas sur la page d’accueil. Les administrateurs et recruteurs voient toutes les candidatures reçues; chaque candidat ne voit que les siennes. Pour promouvoir un compte dans cette version de démonstration, modifiez son champ `role` dans `data\users.json` depuis un environnement de confiance (par exemple, `candidate` vers `admin`). Les recruteurs et administrateurs peuvent consulter toutes les candidatures avec `GET /api/management/applications`; les candidats ne peuvent consulter que leurs propres candidatures avec `GET /api/applications` et sont les seuls à pouvoir en envoyer.

Les fichiers JSON conviennent à une démonstration locale mono-instance, mais ne remplacent pas une base de données pour un déploiement multi-processus ou une plateforme de production. Pour un déploiement réel, configurez une valeur secrète persistante et privée dans `SECRET_KEY`, activez `COOKIE_SECURE=true` derrière HTTPS, protégez les fichiers de données et migrez le stockage vers une base de données. Le secret fourni par défaut est réservé au développement. `DATA_DIR` permet de choisir un autre dossier de stockage.

## Vérifications

Les tests unitaires couvrent la persistance JSON, le hachage des mots de passe et les permissions par rôle :

```powershell
python -m unittest discover -s tests -v
```

## Tests Robot Framework

Les tests lancent automatiquement une instance sur le port 5001, réalisent des requêtes HTTP, puis arrêtent le serveur.

```powershell
python -m robot --outputdir results tests/robot
```

Le rapport lisible se trouve dans `results\report.html` et le détail des étapes dans `results\log.html`. Pour exécuter un seul scénario :

```powershell
python -m robot --test "Une connexion valide puis une déconnexion fonctionnent" --outputdir results tests/robot
```

Robot Framework lit les scénarios dans `tests/robot/job_search.robot`. `RequestsLibrary` appelle l’API ; les mots-clés Robot vérifient les statuts HTTP et les données renvoyées. Les scénarios couvrent la recherche d’offres au Maroc, l’inscription et ses erreurs, la protection des rôles, la connexion, la déconnexion et les candidatures. Ils vérifient aussi que la page d’accueil ne mélange pas les espaces de candidatures. Chaque exécution utilise un dossier de données temporaire. Ces tests vérifient l’API HTTP et le balisage de la page : ils ne simulent pas les clics d’un navigateur.

## Routes API principales

| Méthode et route | Fonction |
| --- | --- |
| `GET /` | Affiche l’application. |
| `GET /api/jobs?q=...&location=...&contract=...` | Recherche des offres au Maroc. |
| `POST /api/auth/register` | Crée un compte et ouvre une session. |
| `POST /api/auth/login` | Connecte un compte existant. |
| `GET /api/auth/me` | Renvoie le profil de la session connectée. |
| `POST /api/auth/logout` | Ferme la session. |
| `GET /espace` | Page dédiée aux rôles `admin` et `recruiter`. |
| `GET /mes-candidatures` | Page dédiée aux candidatures du compte `candidate`. |
| `GET /api/applications` | Renvoie les candidatures de la personne connectée. |
| `POST /api/applications` | Enregistre une candidature pour un compte candidat connecté. |
| `GET /api/management/applications` | Liste les candidatures (rôles `recruiter` et `admin`). |
| `GET /health` | Vérifie que le serveur répond. |
# jobs-robot_Framework
