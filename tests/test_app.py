import json
import tempfile
import unittest
from pathlib import Path

from werkzeug.security import generate_password_hash

import app as minijob


class AuthenticationAndRoleTests(unittest.TestCase):
    def setUp(self):
        self.data_dir = tempfile.TemporaryDirectory()
        minijob.app.config.update(TESTING=True, DATA_DIR=self.data_dir.name)
        self.client = minijob.app.test_client()

    def tearDown(self):
        self.data_dir.cleanup()

    def register_candidate(self, email="candidate@example.com"):
        return self.client.post(
            "/api/auth/register",
            json={
                "name": "Sara Candidate",
                "email": email,
                "password": "Password123!",
            },
        )

    def test_registration_persists_hashed_password_and_ignores_submitted_role(self):
        response = self.client.post(
            "/api/auth/register",
            json={
                "name": "Sara Candidate",
                "email": "candidate@example.com",
                "password": "Password123!",
                "role": "admin",
            },
        )

        self.assertEqual(response.status_code, 201)
        self.assertEqual(response.json["user"]["role"], "candidate")
        users = json.loads((Path(self.data_dir.name) / "users.json").read_text(encoding="utf-8"))
        self.assertNotEqual(users[0]["password_hash"], "Password123!")
        self.assertNotIn("password_hash", response.get_data(as_text=True))

        self.client.post("/api/auth/logout")
        login = self.client.post(
            "/api/auth/login",
            json={"email": "candidate@example.com", "password": "Password123!"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json["user"]["role"], "candidate")

    def test_candidate_application_is_saved_and_visible_to_its_owner(self):
        self.assertEqual(self.register_candidate().status_code, 201)
        submitted = self.client.post(
            "/api/applications",
            json={"job_id": 1, "message": "Je souhaite rejoindre votre équipe."},
        )
        self.assertEqual(submitted.status_code, 201)

        response = self.client.get("/api/applications")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json["applications"][0]["email"], "candidate@example.com")
        persisted = json.loads(
            (Path(self.data_dir.name) / "applications.json").read_text(encoding="utf-8")
        )
        self.assertEqual(persisted, response.json["applications"])

    def test_recruiter_can_review_applications_but_cannot_apply(self):
        self.assertEqual(self.register_candidate().status_code, 201)
        self.client.post(
            "/api/applications",
            json={"job_id": 1, "message": "Candidature de test."},
        )
        users_path = Path(self.data_dir.name) / "users.json"
        users = json.loads(users_path.read_text(encoding="utf-8"))
        users.append(
            {
                "name": "Recruteur",
                "email": "recruiter@example.com",
                "password_hash": generate_password_hash("Password123!"),
                "role": "recruiter",
            }
        )
        users_path.write_text(json.dumps(users), encoding="utf-8")

        recruiter = minijob.app.test_client()
        login = recruiter.post(
            "/api/auth/login",
            json={"email": "recruiter@example.com", "password": "Password123!"},
        )
        self.assertEqual(login.status_code, 200)
        self.assertEqual(login.json["user"]["role"], "recruiter")
        applications = recruiter.get("/api/management/applications")
        self.assertEqual(applications.status_code, 200)
        self.assertEqual(len(applications.json["applications"]), 1)
        forbidden = recruiter.post(
            "/api/applications",
            json={"job_id": 1, "message": "Un recruteur ne postule pas."},
        )
        self.assertEqual(forbidden.status_code, 403)

    def test_candidate_is_forbidden_from_management_endpoint(self):
        self.assertEqual(self.register_candidate().status_code, 201)

        response = self.client.get("/api/management/applications")

        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json["error"], "Rôle insuffisant.")

    def test_admin_can_review_all_applications(self):
        self.assertEqual(self.register_candidate().status_code, 201)
        self.client.post(
            "/api/applications",
            json={"job_id": 1, "message": "Candidature visible par l’administration."},
        )
        users_path = Path(self.data_dir.name) / "users.json"
        users = json.loads(users_path.read_text(encoding="utf-8"))
        users[0]["role"] = "admin"
        users_path.write_text(json.dumps(users), encoding="utf-8")

        response = self.client.get("/api/management/applications")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.json["applications"]), 1)
        self.assertEqual(
            response.json["applications"][0]["message"],
            "Candidature visible par l’administration.",
        )

    def test_candidate_applications_have_a_separate_page(self):
        self.assertEqual(self.register_candidate().status_code, 201)

        home = self.client.get("/")
        applications_page = self.client.get("/mes-candidatures")

        self.assertEqual(home.status_code, 200)
        self.assertNotIn(b"Retrouvez les candidatures envoy\xc3\xa9es depuis votre compte.", home.data)
        self.assertEqual(applications_page.status_code, 200)
        self.assertIn("Mes candidatures".encode(), applications_page.data)
        self.assertIn("Retrouvez les candidatures envoyées depuis votre compte.".encode(), applications_page.data)
        self.assertIn(b"/api/applications", applications_page.data)

    def test_admin_applications_have_a_separate_protected_page(self):
        self.assertEqual(self.register_candidate().status_code, 201)
        users_path = Path(self.data_dir.name) / "users.json"
        users = json.loads(users_path.read_text(encoding="utf-8"))
        users[0]["role"] = "admin"
        users_path.write_text(json.dumps(users), encoding="utf-8")

        home = self.client.get("/")
        admin_page = self.client.get("/espace")

        self.assertEqual(home.status_code, 200)
        self.assertNotIn(b'id="application-list"', home.data)
        self.assertEqual(admin_page.status_code, 200)
        self.assertIn("Espace administrateur".encode(), admin_page.data)
        self.assertIn(b"/api/management/applications", admin_page.data)

    def test_candidates_cannot_open_admin_page_and_admins_cannot_open_candidate_page(self):
        self.assertEqual(self.register_candidate().status_code, 201)
        self.assertEqual(self.client.get("/espace").status_code, 403)

        users_path = Path(self.data_dir.name) / "users.json"
        users = json.loads(users_path.read_text(encoding="utf-8"))
        users[0]["role"] = "admin"
        users_path.write_text(json.dumps(users), encoding="utf-8")
        self.assertEqual(self.client.get("/mes-candidatures").status_code, 403)


if __name__ == "__main__":
    unittest.main()
