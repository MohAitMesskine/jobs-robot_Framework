import os
import re

from flask import Flask, jsonify, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key-change-before-deploy"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
    SESSION_COOKIE_SECURE=os.environ.get("COOKIE_SECURE", "").casefold() == "true",
)

JOBS = [
    {
        "id": 1,
        "title": "Développeur Python",
        "company": "Atlas Digital",
        "location": "Casablanca",
        "contract": "CDI",
        "salary": "15 000–22 000 MAD / mois",
        "description": "Concevez des API utiles au sein d’une équipe produit basée à Casablanca.",
        "tags": ["Python", "Flask", "PostgreSQL"],
    },
    {
        "id": 2,
        "title": "Développeuse Front-end",
        "company": "Studio Jasmin",
        "location": "Rabat",
        "contract": "CDI",
        "salary": "12 000–18 000 MAD / mois",
        "description": "Créez des interfaces accessibles avec une équipe design à Rabat.",
        "tags": ["JavaScript", "React", "Accessibilité"],
    },
    {
        "id": 3,
        "title": "Data Analyst",
        "company": "Maroc Insights",
        "location": "Casablanca",
        "contract": "CDD",
        "salary": "11 000–16 000 MAD / mois",
        "description": "Transformez les données en décisions claires pour nos clients.",
        "tags": ["SQL", "Python", "Tableau"],
    },
    {
        "id": 4,
        "title": "Ingénieur DevOps",
        "company": "Atlas Cloud",
        "location": "Tanger",
        "contract": "CDI",
        "salary": "16 000–24 000 MAD / mois",
        "description": "Fiabilisez les déploiements et faites évoluer une plateforme cloud.",
        "tags": ["Docker", "AWS", "CI/CD"],
    },
    {
        "id": 5,
        "title": "Chargée de recrutement",
        "company": "Collectif Humain",
        "location": "Marrakech",
        "contract": "Stage",
        "salary": "Indemnité de stage",
        "description": "Accompagnez les équipes dans leurs recrutements et l’expérience candidat.",
        "tags": ["Recrutement", "RH", "Communication"],
    },
    {
        "id": 6,
        "title": "Product Designer",
        "company": "Studio Jasmin",
        "location": "Télétravail",
        "contract": "Freelance",
        "salary": "Selon profil",
        "description": "Imaginez des parcours simples, inclusifs et agréables à utiliser.",
        "tags": ["Figma", "UX", "UI"],
    },
    {
        "id": 7,
        "title": "Technicienne support informatique",
        "company": "Agadir Services",
        "location": "Agadir",
        "contract": "CDI",
        "salary": "7 000–10 000 MAD / mois",
        "description": "Aidez nos équipes à résoudre leurs questions techniques au quotidien.",
        "tags": ["Support", "Réseau", "Informatique"],
    },
    {
        "id": 8,
        "title": "Comptable junior",
        "company": "Fès Conseil",
        "location": "Fès",
        "contract": "CDD",
        "salary": "6 500–9 000 MAD / mois",
        "description": "Participez au suivi comptable et administratif de nos clients.",
        "tags": ["Comptabilité", "Excel", "Gestion"],
    },
]

USERS = {}
APPLICATIONS = []


def request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def authenticated_user():
    email = session.get("user_email")
    return USERS.get(email) if email else None


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/health")
def health():
    return jsonify({"status": "ok"})


@app.get("/api/jobs")
def search_jobs():
    query = request.args.get("q", "").strip().casefold()
    location = request.args.get("location", "").strip().casefold()
    contract = request.args.get("contract", "").strip().casefold()

    matches = []
    for job in JOBS:
        searchable_text = " ".join(
            [job["title"], job["company"], job["description"], *job["tags"]]
        ).casefold()
        if query and query not in searchable_text:
            continue
        if location and location not in job["location"].casefold():
            continue
        if contract and contract != job["contract"].casefold():
            continue
        matches.append(job)

    return jsonify({"jobs": matches})


@app.post("/api/auth/register")
def register():
    data = request_data()
    if data is None:
        return jsonify({"error": "Le formulaire doit contenir des données JSON."}), 400

    name = data.get("name", "").strip() if isinstance(data.get("name"), str) else ""
    email = data.get("email", "").strip().casefold() if isinstance(data.get("email"), str) else ""
    password = data.get("password", "") if isinstance(data.get("password"), str) else ""

    if not name or not email or not password:
        return jsonify({"error": "Tous les champs sont obligatoires."}), 400
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", email):
        return jsonify({"error": "L’adresse e-mail n’est pas valide."}), 400
    if len(password) < 8:
        return jsonify({"error": "Le mot de passe doit contenir au moins 8 caractères."}), 400
    if email in USERS:
        return jsonify({"error": "Un compte utilise déjà cette adresse e-mail."}), 409

    USERS[email] = {
        "name": name,
        "email": email,
        "password_hash": generate_password_hash(password),
    }
    session.clear()
    session["user_email"] = email
    return jsonify({"message": "Compte créé.", "user": {"name": name, "email": email}}), 201


@app.post("/api/auth/login")
def login():
    data = request_data()
    if data is None:
        return jsonify({"error": "Le formulaire doit contenir des données JSON."}), 400

    email = data.get("email", "").strip().casefold() if isinstance(data.get("email"), str) else ""
    password = data.get("password", "") if isinstance(data.get("password"), str) else ""
    session.clear()
    user = USERS.get(email)
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Adresse e-mail ou mot de passe incorrect."}), 401

    session.clear()
    session["user_email"] = email
    return jsonify({"message": "Connexion réussie.", "user": {"name": user["name"], "email": email}})


@app.get("/api/auth/me")
def current_user():
    user = authenticated_user()
    if user is None:
        return jsonify({"error": "Authentification requise."}), 401
    return jsonify({"user": {"name": user["name"], "email": user["email"]}})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Déconnexion réussie."})


@app.post("/api/applications")
def submit_application():
    user = authenticated_user()
    if user is None:
        return jsonify({"error": "Connectez-vous pour postuler."}), 401

    data = request_data()
    if data is None:
        return jsonify({"error": "Le formulaire doit contenir des données JSON."}), 400

    job_id = data.get("job_id")
    if isinstance(job_id, str) and job_id.isdecimal():
        job_id = int(job_id)
    message = (
        data.get("message", "").strip()
        if isinstance(data.get("message"), str)
        else ""
    )

    if not message or not isinstance(job_id, int) or isinstance(job_id, bool):
        return jsonify({"error": "L’offre et le message sont obligatoires."}), 400

    job = next((item for item in JOBS if item["id"] == job_id), None)
    if job is None:
        return jsonify({"error": "Cette offre n’existe pas."}), 404

    application = {
        "id": len(APPLICATIONS) + 1,
        "job_id": job_id,
        "job_title": job["title"],
        "name": user["name"],
        "email": user["email"],
        "message": message,
    }
    APPLICATIONS.append(application)
    return jsonify({"message": "Candidature envoyée.", "application": application}), 201


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
