import os
from pathlib import Path
from tempfile import TemporaryDirectory
import unittest
from types import SimpleNamespace

os.environ.setdefault("SECRET_KEY", "test-secret-key-that-is-at-least-32-chars")

import httpx
from sqlalchemy import create_engine
from sqlalchemy.orm import Session
from sqlalchemy.pool import StaticPool

from app.api.v1 import deps
from app.api.v1.endpoints import applications as application_routes
from app.api.v1.endpoints import users as user_routes
from app.db.base_class import Base
from app.db.session import engine as application_engine
from app.main import app
from app.models.application import Application
from app.models.company import CompanyProfile
from app.models.offer import Offer
from app.models.user import User


class MVPApiTests(unittest.IsolatedAsyncioTestCase):
    async def asyncSetUp(self):
        self.engine = create_engine(
            "sqlite://",
            connect_args={"check_same_thread": False},
            poolclass=StaticPool,
        )
        Base.metadata.create_all(self.engine)
        with Session(self.engine) as db:
            company = User(email="company@example.com", hashed_password="hash", role="empresa")
            student = User(
                email="student@example.com",
                hashed_password="hash",
                role="alumno",
                full_name="Ada Alumna",
                technologies=[{"name": "Python", "context": "Proyecto API"}],
                location_city="Valencia",
                profile_confirmed=True,
            )
            other_company = User(
                email="other@example.com", hashed_password="hash", role="empresa"
            )
            db.add_all([company, student, other_company])
            db.flush()
            offer = Offer(
                title="Prácticas backend",
                description="Desarrollo de API",
                company_id=company.id,
            )
            db.add(offer)
            db.flush()
            application = Application(
                user_id=student.id, offer_id=offer.id, status="pendiente"
            )
            db.add(application)
            db.commit()
            self.company_id = company.id
            self.student_id = student.id
            self.other_company_id = other_company.id
            self.offer_id = offer.id
            self.application_id = application.id

        self.active_user = SimpleNamespace(id=self.company_id, role="empresa")

        def override_db():
            with Session(self.engine) as db:
                yield db

        app.dependency_overrides[deps.get_db] = override_db
        app.dependency_overrides[deps.get_current_company_user] = lambda: self.active_user
        app.dependency_overrides[deps.get_current_user] = lambda: self.active_user
        self.cv_directory = TemporaryDirectory()
        self.original_cv_directory = application_routes.CV_UPLOAD_DIR
        self.original_user_upload_directory = user_routes.UPLOAD_DIR
        application_routes.CV_UPLOAD_DIR = Path(self.cv_directory.name)
        user_routes.UPLOAD_DIR = self.cv_directory.name
        cv_path = application_routes.CV_UPLOAD_DIR / f"user_{self.student_id}_test.pdf"
        cv_path.write_bytes(b"%PDF-1.7 test CV")
        with Session(self.engine) as db:
            student = db.get(User, self.student_id)
            student.cv_url = f"/uploads/cvs/{cv_path.name}"
            db.add(
                CompanyProfile(
                    user_id=self.company_id,
                    company_name="Empresa de prueba",
                    cif="B12345678",
                )
            )
            db.commit()

        self.client = httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        )

    async def asyncTearDown(self):
        await self.client.aclose()
        app.dependency_overrides.clear()
        application_routes.CV_UPLOAD_DIR = self.original_cv_directory
        user_routes.UPLOAD_DIR = self.original_user_upload_directory
        self.cv_directory.cleanup()
        self.engine.dispose()
        application_engine.dispose()

    async def test_company_profile_and_public_offer_name(self):
        profile = await self.client.get("/api/v1/users/company-profile")
        self.assertEqual(profile.status_code, 200)
        self.assertEqual(profile.json()["company_name"], "Empresa de prueba")

        update = await self.client.put(
            "/api/v1/users/company-profile",
            json={
                "company_name": "Empresa actualizada",
                "cif": "b12345678",
                "website": "https://example.com",
            },
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["cif"], "B12345678")

        offers = await self.client.get("/api/v1/offers/")
        self.assertEqual(offers.status_code, 200)
        self.assertEqual(offers.json()[0]["company_name"], "Empresa actualizada")

    async def test_candidate_privacy_cv_access_and_contact_release(self):
        applications = await self.client.get(f"/api/v1/applications/offer/{self.offer_id}")
        self.assertEqual(applications.status_code, 200)
        candidate = applications.json()[0]["student"]
        self.assertIsNone(candidate["email"])
        self.assertEqual(candidate["technologies"][0]["name"], "Python")

        cv = await self.client.get(
            f"/api/v1/applications/{self.application_id}/cv"
        )
        self.assertEqual(cv.status_code, 200)
        self.assertEqual(cv.headers["content-type"], "application/pdf")

        self.active_user = SimpleNamespace(
            id=self.student_id,
            role="alumno",
            cv_url=f"/uploads/cvs/user_{self.student_id}_test.pdf",
        )
        own_cv = await self.client.get("/api/v1/users/cv")
        self.assertEqual(own_cv.status_code, 200)

        self.active_user = SimpleNamespace(id=self.company_id, role="empresa")
        update = await self.client.put(
            f"/api/v1/applications/{self.application_id}/status",
            json={"status": "entrevista"},
        )
        self.assertEqual(update.status_code, 200)
        self.assertEqual(update.json()["student"]["email"], "student@example.com")

        self.active_user = SimpleNamespace(id=self.other_company_id, role="empresa")
        forbidden = await self.client.get(
            f"/api/v1/applications/{self.application_id}/cv"
        )
        self.assertEqual(forbidden.status_code, 403)

    async def test_public_registration_cannot_choose_privileged_role(self):
        response = await self.client.post(
            "/api/v1/users/",
            json={
                "email": "attacker@example.com",
                "password": "a-long-test-password",
                "role": "admin",
            },
        )
        self.assertEqual(response.status_code, 422)

    async def test_frontend_origin_is_allowed_by_cors(self):
        response = await self.client.options(
            "/api/v1/offers/",
            headers={
                "Origin": "http://localhost:5173",
                "Access-Control-Request-Method": "GET",
            },
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(
            response.headers["access-control-allow-origin"], "http://localhost:5173"
        )


if __name__ == "__main__":
    unittest.main()