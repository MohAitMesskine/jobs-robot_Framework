*** Settings ***
Documentation     Tests fonctionnels HTTP de MiniJob Maroc et de son authentification.
Library           RequestsLibrary
Library           Process
Library           Collections
Suite Setup       Start Test Server
Suite Teardown    Stop Test Server

*** Variables ***
${BASE_URL}       http://127.0.0.1:5001
${SERVER_ALIAS}   minijob-test-server

*** Test Cases ***
La page d'accueil expose la recherche et les formulaires de compte
    ${response}=    GET On Session    minijob    /
    Should Be Equal As Integers    ${response.status_code}    200
    Should Contain    ${response.text}    MiniJob Maroc
    Should Contain    ${response.text}    search-form
    Should Contain    ${response.text}    login-form
    Should Contain    ${response.text}    register-form

Le serveur répond au contrôle de santé
    ${response}=    GET On Session    minijob    /health
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    status    ok

Le catalogue contient des offres au Maroc et des salaires en dirhams
    ${response}=    GET On Session    minijob    /api/jobs
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    8
    Should Contain    ${response.text}    Casablanca
    Should Contain    ${response.text}    Rabat
    Should Contain    ${response.text}    MAD

La recherche filtre les offres par ville marocaine
    ${params}=    Create Dictionary    location=Casablanca
    ${response}=    GET On Session    minijob    /api/jobs    params=${params}
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    2
    Should Be Equal    ${jobs}[0][title]    Développeur Python
    Should Be Equal    ${jobs}[1][title]    Data Analyst

La recherche combine mot-clé et type de contrat
    ${params}=    Create Dictionary    q=Python    contract=CDI
    ${response}=    GET On Session    minijob    /api/jobs    params=${params}
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    1
    Dictionary Should Contain Item    ${jobs}[0]    title    Développeur Python

Une recherche sans résultat renvoie une liste vide
    ${params}=    Create Dictionary    q=métier inexistant
    ${response}=    GET On Session    minijob    /api/jobs    params=${params}
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    0

Une personne non connectée ne peut pas postuler
    Create Session    anonymous    ${BASE_URL}
    ${payload}=    Create Dictionary    job_id=${1}    message=Ma candidature.
    ${response}=    POST On Session    anonymous    /api/applications    json=${payload}    expected_status=401
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    Connectez-vous pour postuler.

Une inscription valide crée un compte et ouvre une session
    Create Session    registration    ${BASE_URL}
    ${payload}=    Create Dictionary    name=Sara Test    email=SARA.TEST@example.com    password=motdepasse-securise
    ${response}=    POST On Session    registration    /api/auth/register    json=${payload}    expected_status=201
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    message    Compte créé.
    Should Not Contain    ${response.text}    password_hash
    ${response}=    GET On Session    registration    /api/auth/me
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    ${user}=    Get From Dictionary    ${data}    user
    Dictionary Should Contain Item    ${user}    email    sara.test@example.com

Une inscription avec une adresse invalide est refusée
    Create Session    invalid-email    ${BASE_URL}
    ${payload}=    Create Dictionary    name=Sara Test    email=pas-une-adresse    password=motdepasse-securise
    ${response}=    POST On Session    invalid-email    /api/auth/register    json=${payload}    expected_status=400
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    L’adresse e-mail n’est pas valide.

Une inscription avec un mot de passe trop court est refusée
    Create Session    short-password    ${BASE_URL}
    ${payload}=    Create Dictionary    name=Sara Test    email=short.password@example.com    password=court
    ${response}=    POST On Session    short-password    /api/auth/register    json=${payload}    expected_status=400
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    Le mot de passe doit contenir au moins 8 caractères.

Une inscription sans tous les champs est refusée
    Create Session    missing-registration    ${BASE_URL}
    ${payload}=    Create Dictionary    name=Sara Test    email=missing@example.com
    ${response}=    POST On Session    missing-registration    /api/auth/register    json=${payload}    expected_status=400
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    Tous les champs sont obligatoires.

Une adresse e-mail déjà inscrite est refusée
    Create Session    duplicate-registration    ${BASE_URL}
    ${payload}=    Create Dictionary    name=Sara Test    email=duplicate@example.com    password=motdepasse-securise
    ${response}=    POST On Session    duplicate-registration    /api/auth/register    json=${payload}    expected_status=201
    ${response}=    POST On Session    duplicate-registration    /api/auth/register    json=${payload}    expected_status=409
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    Un compte utilise déjà cette adresse e-mail.

Un mauvais mot de passe ne permet pas de se connecter
    Create Session    failed-login    ${BASE_URL}
    ${register}=    Create Dictionary    name=Sara Test    email=failed.login@example.com    password=motdepasse-securise
    ${response}=    POST On Session    failed-login    /api/auth/register    json=${register}    expected_status=201
    ${logout}=    POST On Session    failed-login    /api/auth/logout
    ${payload}=    Create Dictionary    email=failed.login@example.com    password=mauvais-mot-de-passe
    ${response}=    POST On Session    failed-login    /api/auth/login    json=${payload}    expected_status=401
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    Adresse e-mail ou mot de passe incorrect.
    ${response}=    GET On Session    failed-login    /api/auth/me    expected_status=401

Une connexion valide puis une déconnexion fonctionnent
    Create Session    login-flow    ${BASE_URL}
    ${register}=    Create Dictionary    name=Sara Test    email=login.flow@example.com    password=motdepasse-securise
    ${response}=    POST On Session    login-flow    /api/auth/register    json=${register}    expected_status=201
    ${logout}=    POST On Session    login-flow    /api/auth/logout
    ${payload}=    Create Dictionary    email=login.flow@example.com    password=motdepasse-securise
    ${response}=    POST On Session    login-flow    /api/auth/login    json=${payload}
    Should Be Equal As Integers    ${response.status_code}    200
    ${response}=    GET On Session    login-flow    /api/auth/me
    Should Be Equal As Integers    ${response.status_code}    200
    ${response}=    POST On Session    login-flow    /api/auth/logout
    Should Be Equal As Integers    ${response.status_code}    200
    ${response}=    GET On Session    login-flow    /api/auth/me    expected_status=401

Une candidature authentifiée est enregistrée avec le compte connecté
    Create Session    authenticated-application    ${BASE_URL}
    ${credentials}=    Create Dictionary    name=Sara Candidate    email=apply@example.com    password=motdepasse-securise
    ${response}=    POST On Session    authenticated-application    /api/auth/register    json=${credentials}    expected_status=201
    ${payload}=    Create Dictionary    job_id=${1}    message=Je souhaite rejoindre votre équipe.
    ${response}=    POST On Session    authenticated-application    /api/applications    json=${payload}    expected_status=201
    ${data}=    Evaluate    $response.json()
    ${application}=    Get From Dictionary    ${data}    application
    Dictionary Should Contain Item    ${application}    job_title    Développeur Python
    Dictionary Should Contain Item    ${application}    email    apply@example.com
    Dictionary Should Contain Item    ${application}    name    Sara Candidate

Une candidature authentifiée sans message est refusée
    Create Session    incomplete-application    ${BASE_URL}
    ${credentials}=    Create Dictionary    name=Sara Candidate    email=incomplete@example.com    password=motdepasse-securise
    ${response}=    POST On Session    incomplete-application    /api/auth/register    json=${credentials}    expected_status=201
    ${payload}=    Create Dictionary    job_id=${1}    message=${EMPTY}
    ${response}=    POST On Session    incomplete-application    /api/applications    json=${payload}    expected_status=400
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    L’offre et le message sont obligatoires.

Une candidature pour une offre inexistante est refusée
    Create Session    unknown-job    ${BASE_URL}
    ${credentials}=    Create Dictionary    name=Sara Candidate    email=unknown.job@example.com    password=motdepasse-securise
    ${response}=    POST On Session    unknown-job    /api/auth/register    json=${credentials}    expected_status=201
    ${payload}=    Create Dictionary    job_id=${999}    message=Bonjour.
    ${response}=    POST On Session    unknown-job    /api/applications    json=${payload}    expected_status=404
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    error    Cette offre n’existe pas.

*** Keywords ***
Start Test Server
    Start Process    python    app.py    alias=${SERVER_ALIAS}    env:PORT=5001
    Create Session    minijob    ${BASE_URL}
    Wait Until Keyword Succeeds    15x    1s    Server Should Be Ready

Server Should Be Ready
    ${response}=    GET On Session    minijob    /health
    Should Be Equal As Integers    ${response.status_code}    200

Stop Test Server
    Terminate Process    ${SERVER_ALIAS}    kill=True
