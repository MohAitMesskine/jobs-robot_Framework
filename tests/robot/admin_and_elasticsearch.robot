*** Settings ***
Documentation     Tests automatisés Robot Framework : Espace administrateur, publication d'offres et intégration Elasticsearch.
Library           RequestsLibrary
Library           Process
Library           Collections
Library           OperatingSystem
Suite Setup       Start Test Server
Suite Teardown    Stop Test Server

*** Variables ***
${BASE_URL}       http://127.0.0.1:5002
${SERVER_ALIAS}   admin-test-server

*** Test Cases ***
Connexion réussie du compte administrateur avec admin@gmail.com et mot de passe admin
    Create Session    admin_sess    ${BASE_URL}
    ${credentials}=    Create Dictionary    email=admin@gmail.com    password=admin
    ${response}=    POST On Session    admin_sess    /api/auth/login    json=${credentials}
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    message    Connexion réussie.
    ${user}=    Get From Dictionary    ${data}    user
    Dictionary Should Contain Item    ${user}    email    admin@gmail.com
    Dictionary Should Contain Item    ${user}    role    admin

L'espace administrateur est accessible et contient les formulaires de gestion
    ${response}=    GET On Session    admin_sess    /espace
    Should Be Equal As Integers    ${response.status_code}    200
    Should Contain    ${response.text}    Espace administrateur
    Should Contain    ${response.text}    Publier une offre d'emploi
    Should Contain    ${response.text}    id="create-job-form"
    Should Contain    ${response.text}    id="job-title"
    Should Contain    ${response.text}    id="job-company"

Le point de contrôle de statut Elasticsearch répond correctement
    ${response}=    GET On Session    admin_sess    /api/es/status
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Key    ${data}    status
    Dictionary Should Contain Key    ${data}    url
    Dictionary Should Contain Key    ${data}    index

L'administrateur peut publier une nouvelle offre d'emploi
    ${payload}=    Create Dictionary
    ...    title=Lead Architecte IA
    ...    company=Atlas AI Maroc
    ...    location=Casablanca
    ...    contract=CDI
    ...    salary=35 000 MAD / mois
    ...    description=Expert en solutions NLP et moteur de recherche Elasticsearch.
    ...    tags=AI, Elasticsearch, Python
    ${response}=    POST On Session    admin_sess    /api/jobs    json=${payload}    expected_status=201
    ${data}=    Evaluate    $response.json()
    Dictionary Should Contain Item    ${data}    message    Offre créée avec succès.
    ${job}=    Get From Dictionary    ${data}    job
    Dictionary Should Contain Item    ${job}    title    Lead Architecte IA
    Dictionary Should Contain Item    ${job}    company    Atlas AI Maroc
    Set Suite Variable    ${NEW_JOB_ID}    ${job}[id]

La nouvelle offre publiée apparaît dans la recherche
    ${params}=    Create Dictionary    q=Architecte
    ${response}=    GET On Session    admin_sess    /api/jobs    params=${params}
    Should Be Equal As Integers    ${response.status_code}    200
    ${data}=    Evaluate    $response.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    1
    Should Be Equal    ${jobs}[0][title]    Lead Architecte IA

Un candidat normal ne peut pas publier d'offre d'emploi
    Create Session    cand_sess    ${BASE_URL}
    ${cand_reg}=    Create Dictionary    name=Yassine Test    email=yassine.candidat@example.com    password=motdepasse123
    ${reg_res}=    POST On Session    cand_sess    /api/auth/register    json=${cand_reg}    expected_status=201
    ${job_payload}=    Create Dictionary    title=Job Pirate    company=Hacker Corp    location=Rabat    contract=CDI
    ${res}=    POST On Session    cand_sess    /api/jobs    json=${job_payload}    expected_status=403
    ${data}=    Evaluate    $res.json()
    Dictionary Should Contain Item    ${data}    error    Action réservée aux administrateurs.

Un visiteur non connecté ne peut pas publier d'offre
    Create Session    anon_sess    ${BASE_URL}
    ${job_payload}=    Create Dictionary    title=Job Anonyme    company=Inconnu    location=Tanger    contract=CDD
    ${res}=    POST On Session    anon_sess    /api/jobs    json=${job_payload}    expected_status=401
    ${data}=    Evaluate    $res.json()
    Dictionary Should Contain Item    ${data}    error    Authentification requise.

Un candidat peut postuler à la nouvelle offre d'emploi
    ${app_payload}=    Create Dictionary    job_id=${NEW_JOB_ID}    message=Je souhaite postuler au poste de Lead Architecte IA.
    ${res}=    POST On Session    cand_sess    /api/applications    json=${app_payload}    expected_status=201
    ${data}=    Evaluate    $res.json()
    Dictionary Should Contain Item    ${data}    message    Candidature envoyée.
    ${app}=    Get From Dictionary    ${data}    application
    Dictionary Should Contain Item    ${app}    job_title    Lead Architecte IA
    Dictionary Should Contain Item    ${app}    email    yassine.candidat@example.com
    Set Suite Variable    ${NEW_APP_ID}    ${app}[id]

L'administrateur peut visualiser la candidature dans l'espace de gestion
    ${res}=    GET On Session    admin_sess    /api/management/applications
    Should Be Equal As Integers    ${res.status_code}    200
    Should Contain    ${res.text}    Lead Architecte IA
    Should Contain    ${res.text}    yassine.candidat@example.com

Le candidat peut consulter puis retirer sa candidature
    ${res}=    GET On Session    cand_sess    /api/applications
    Should Be Equal As Integers    ${res.status_code}    200
    Should Contain    ${res.text}    Lead Architecte IA
    ${del_res}=    DELETE On Session    cand_sess    /api/applications/${NEW_APP_ID}
    Should Be Equal As Integers    ${del_res.status_code}    200
    ${res_after}=    GET On Session    cand_sess    /api/applications
    Should Not Contain    ${res_after.text}    Lead Architecte IA

L'administrateur peut supprimer l'offre d'emploi
    ${res}=    DELETE On Session    admin_sess    /api/jobs/${NEW_JOB_ID}
    Should Be Equal As Integers    ${res.status_code}    200
    ${params}=    Create Dictionary    q=Architecte
    ${search_res}=    GET On Session    admin_sess    /api/jobs    params=${params}
    ${data}=    Evaluate    $search_res.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    0

L'administrateur peut exécuter la réindexation Elasticsearch
    ${res}=    POST On Session    admin_sess    /api/admin/reindex
    Should Be Equal As Integers    ${res.status_code}    200
    ${data}=    Evaluate    $res.json()
    Dictionary Should Contain Key    ${data}    message
    Dictionary Should Contain Key    ${data}    count

Un employé peut se connecter et accéder à son espace pour publier des offres
    Create Session    emp_sess    ${BASE_URL}
    ${emp_login}=    Create Dictionary    email=employee@gmail.com    password=employee
    ${res}=    POST On Session    emp_sess    /api/auth/login    json=${emp_login}
    Should Be Equal As Integers    ${res.status_code}    200
    ${data}=    Evaluate    $res.json()
    ${user}=    Get From Dictionary    ${data}    user
    Dictionary Should Contain Item    ${user}    role    employee
    ${page}=    GET On Session    emp_sess    /espace
    Should Be Equal As Integers    ${page.status_code}    200
    Should Contain    ${page.text}    Publier une offre d'emploi
    Should Contain    ${page.text}    id="create-job-form"

Un employé peut créer et publier avec succès une offre d'emploi
    ${payload}=    Create Dictionary
    ...    title=Expert Sécurité Cloud
    ...    company=Bank Al-Maghribia Digital
    ...    location=Rabat
    ...    contract=CDI
    ...    salary=28 000 MAD / mois
    ...    description=Sécurisation des architectures cloud et réseaux bancaires.
    ...    tags=Sécurité, Cloud, Azure
    ${res}=    POST On Session    emp_sess    /api/jobs    json=${payload}    expected_status=201
    ${data}=    Evaluate    $res.json()
    Dictionary Should Contain Item    ${data}    message    Offre créée avec succès.
    ${job}=    Get From Dictionary    ${data}    job
    Dictionary Should Contain Item    ${job}    title    Expert Sécurité Cloud
    Dictionary Should Contain Item    ${job}    company    Bank Al-Maghribia Digital
    Set Suite Variable    ${EMP_JOB_ID}    ${job}[id]

L'offre publiée par l'employé apparaît dans la recherche
    ${params}=    Create Dictionary    q=Sécurité
    ${res}=    GET On Session    emp_sess    /api/jobs    params=${params}
    Should Be Equal As Integers    ${res.status_code}    200
    ${data}=    Evaluate    $res.json()
    ${jobs}=    Get From Dictionary    ${data}    jobs
    Length Should Be    ${jobs}    1
    Should Be Equal    ${jobs}[0][title]    Expert Sécurité Cloud

Un nouvel employé peut s'inscrire et publier des offres
    Create Session    new_emp_sess    ${BASE_URL}
    ${reg_payload}=    Create Dictionary    name=Salma Recruteuse    email=salma.recruteuse@example.ma    password=motdepasseSecurise1    role=employee
    ${reg_res}=    POST On Session    new_emp_sess    /api/auth/register    json=${reg_payload}    expected_status=201
    ${data}=    Evaluate    $reg_res.json()
    ${user}=    Get From Dictionary    ${data}    user
    Dictionary Should Contain Item    ${user}    role    employee
    ${job_payload}=    Create Dictionary    title=Consultante SAP    company=Consulting Casablanca    location=Casablanca    contract=CDI
    ${job_res}=    POST On Session    new_emp_sess    /api/jobs    json=${job_payload}    expected_status=201
    ${job_data}=    Evaluate    $job_res.json()
    Dictionary Should Contain Item    ${job_data}    message    Offre créée avec succès.

*** Keywords ***
Start Test Server
    ${test_data_dir}=    Evaluate    __import__('tempfile').mkdtemp(prefix='admin-robot-')
    Set Suite Variable    ${TEST_DATA_DIR}    ${test_data_dir}
    Start Process    python    app.py    alias=${SERVER_ALIAS}    env:PORT=5002    env:DATA_DIR=${TEST_DATA_DIR}
    Create Session    minijob_admin    ${BASE_URL}
    Wait Until Keyword Succeeds    15x    1s    Server Should Be Ready

Server Should Be Ready
    ${response}=    GET On Session    minijob_admin    /health
    Should Be Equal As Integers    ${response.status_code}    200

Stop Test Server
    Terminate Process    ${SERVER_ALIAS}    kill=True
    Remove Directory    ${TEST_DATA_DIR}    recursive=True

