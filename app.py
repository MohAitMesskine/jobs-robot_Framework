import json
import os
import re
import tempfile
from pathlib import Path
from threading import RLock

from flask import Flask, abort, jsonify, redirect, render_template, request, session
from werkzeug.security import check_password_hash, generate_password_hash

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("SECRET_KEY", "local-development-key-change-before-deploy"),
    DATA_DIR=os.environ.get("DATA_DIR", str(Path(__file__).parent / "data")),
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

DATA_LOCK = RLock()


def load_records(filename):
    path = Path(app.config["DATA_DIR"]) / filename
    if not path.exists():
        return []
    with path.open(encoding="utf-8") as data_file:
        records = json.load(data_file)
    if not isinstance(records, list) or not all(isinstance(item, dict) for item in records):
        raise ValueError(f"Le fichier de données {filename} doit contenir une liste d’objets JSON.")
    return records


def save_records(filename, records):
    directory = Path(app.config["DATA_DIR"])
    directory.mkdir(parents=True, exist_ok=True)
    temporary_path = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directory,
            delete=False,
        ) as data_file:
            temporary_path = Path(data_file.name)
            json.dump(records, data_file, ensure_ascii=False, indent=2)
            data_file.write("\n")
        temporary_path.replace(directory / filename)
    finally:
        if temporary_path is not None and temporary_path.exists():
            temporary_path.unlink()


def public_user(user):
    return {"name": user["name"], "email": user["email"], "role": user["role"]}


def request_data():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        return None
    return data


def authenticated_user():
    email = session.get("user_email")
    if not email:
        return None
    with DATA_LOCK:
        return next((user for user in load_records("users.json") if user["email"] == email), None)


def has_role(user, *roles):
    return user["role"] in roles


@app.get("/")
def home():
    return render_template("index.html")


@app.get("/espace")
def staff_workspace():
    user = authenticated_user()
    if user is None:
        return redirect("/")
    if not has_role(user, "admin", "recruiter"):
        abort(403)
    return render_template(
        "applications.html",
        user=public_user(user),
        title="Espace administrateur" if user["role"] == "admin" else "Espace recruteur",
        description="Consultez et suivez les candidatures reçues.",
        applications_endpoint="/api/management/applications",
        is_staff=True,
    )


@app.get("/mes-candidatures")
def candidate_workspace():
    user = authenticated_user()
    if user is None:
        return redirect("/")
    if not has_role(user, "candidate"):
        abort(403)
    return render_template(
        "applications.html",
        user=public_user(user),
        title="Mes candidatures",
        description="Retrouvez les candidatures envoyées depuis votre compte.",
        applications_endpoint="/api/applications",
        is_staff=False,
    )


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
    with DATA_LOCK:
        users = load_records("users.json")
        if any(user["email"] == email for user in users):
            return jsonify({"error": "Un compte utilise déjà cette adresse e-mail."}), 409
        user = {
            "name": name,
            "email": email,
            "password_hash": generate_password_hash(password),
            "role": "candidate",
        }
        users.append(user)
        save_records("users.json", users)
    session.clear()
    session["user_email"] = email
    return jsonify({"message": "Compte créé.", "user": public_user(user)}), 201


@app.post("/api/auth/login")
def login():
    data = request_data()
    if data is None:
        return jsonify({"error": "Le formulaire doit contenir des données JSON."}), 400

    email = data.get("email", "").strip().casefold() if isinstance(data.get("email"), str) else ""
    password = data.get("password", "") if isinstance(data.get("password"), str) else ""

    session.clear()
    with DATA_LOCK:
        user = next((item for item in load_records("users.json") if item["email"] == email), None)
    if user is None or not check_password_hash(user["password_hash"], password):
        return jsonify({"error": "Adresse e-mail ou mot de passe incorrect."}), 401


    session["user_email"] = email
    return jsonify({"message": "Connexion réussie.", "user": public_user(user)})


@app.get("/api/auth/me")
def current_user():
    user = authenticated_user()
    if user is None:
        return jsonify({"error": "Authentification requise."}), 401
    return jsonify({"user": public_user(user)})


@app.post("/api/auth/logout")
def logout():
    session.clear()
    return jsonify({"message": "Déconnexion réussie."})


@app.route("/api/applications", methods=["GET", "POST"])
def applications():
    user = authenticated_user()
    if user is None:
        message = (
            "Authentification requise."
            if request.method == "GET"
            else "Connectez-vous pour postuler."
        )
        return jsonify({"error": message}), 401

    if request.method == "GET":
        if has_role(user, "admin", "recruiter"):
            with DATA_LOCK:
                records = load_records("applications.json")
        else:
            with DATA_LOCK:
                records = [
                    record
                    for record in load_records("applications.json")
                    if record["email"] == user["email"]
                ]
        return jsonify({"applications": records})

    if not has_role(user, "candidate"):
        return jsonify({"error": "Seuls les candidats peuvent postuler."}), 403

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

    with DATA_LOCK:
        records = load_records("applications.json")
        application = {
            "id": max((record["id"] for record in records), default=0) + 1,
            "job_id": job_id,
            "job_title": job["title"],
            "name": user["name"],
            "email": user["email"],
            "message": message,
        }
        records.append(application)
        save_records("applications.json", records)
    return jsonify({"message": "Candidature envoyée.", "application": application}), 201


@app.get("/api/management/applications")
def management_applications():
    user = authenticated_user()
    if user is None:
        return jsonify({"error": "Authentification requise."}), 401
    if not has_role(user, "admin", "recruiter"):
        return jsonify({"error": "Rôle insuffisant."}), 403
    with DATA_LOCK:
        records = load_records("applications.json")
    return jsonify({"applications": records})


if __name__ == "__main__":
    app.run(
        host="127.0.0.1",
        port=int(os.environ.get("PORT", "5000")),
        debug=False,
    )
