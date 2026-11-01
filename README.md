# MiniJob Maroc

MiniJob est une mini-application de recherche d’emploi au Maroc réalisée avec Python et Flask. Elle permet de consulter des offres de démonstration à Casablanca, Rabat, Tanger, Marrakech, Agadir, Fès et en télétravail, de les filtrer par mot-clé, ville et contrat, de créer un compte et de postuler après connexion. Les rémunérations des offres sont indicatives.

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

L’interface propose l’inscription, la connexion et la déconnexion. Une adresse e-mail ne peut être inscrite qu’une fois et le mot de passe doit comporter au moins 8 caractères. Les mots de passe sont stockés sous forme hachée et les candidatures nécessitent une session authentifiée.

Cette version est une démonstration : les comptes, les offres et les candidatures sont conservés en mémoire et disparaissent au redémarrage. Pour un déploiement réel, configurez une valeur secrète persistante et privée dans `SECRET_KEY`, activez `COOKIE_SECURE=true` derrière HTTPS et remplacez les données en mémoire par une base de données. Le secret fourni par défaut est réservé au développement.

## Tests Robot Framework

Les tests lancent automatiquement une instance sur le port 5001, réalisent des requêtes HTTP, puis arrêtent le serveur.

```powershell
python -m robot --outputdir results tests/robot
```

Le rapport lisible se trouve dans `results\report.html` et le détail des étapes dans `results\log.html`. Pour exécuter un seul scénario :

```powershell
python -m robot --test "Une connexion valide puis une déconnexion fonctionnent" --outputdir results tests/robot
```

Robot Framework lit les scénarios dans `tests/robot/job_search.robot`. `RequestsLibrary` appelle l’API ; les mots-clés Robot vérifient les statuts HTTP et les données renvoyées. Les scénarios couvrent la recherche d’offres au Maroc, l’inscription et ses erreurs, la connexion, la déconnexion et les candidatures. Ces tests vérifient l’API HTTP : ils ne simulent pas les clics d’un navigateur.

## Routes API principales

| Méthode et route | Fonction |
| --- | --- |
| `GET /` | Affiche l’application. |
| `GET /api/jobs?q=...&location=...&contract=...` | Recherche des offres au Maroc. |
| `POST /api/auth/register` | Crée un compte et ouvre une session. |
| `POST /api/auth/login` | Connecte un compte existant. |
| `GET /api/auth/me` | Renvoie le profil de la session connectée. |
| `POST /api/auth/logout` | Ferme la session. |
| `POST /api/applications` | Enregistre une candidature pour la personne connectée. |
| `GET /health` | Vérifie que le serveur répond. |
# jobs-robot_Framework
