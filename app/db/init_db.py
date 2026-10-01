from sqlalchemy import inspect, text
from sqlalchemy.engine import Engine

from app.db.base_class import Base
from app.db.session import engine
from app.models.application import Application
from app.models.company import CompanyProfile
from app.models.fct_log import FCTLog
from app.models.notification import Notification
from app.models.offer import Offer
from app.models.student import StudentProfile
from app.models.user import User


def init_db(bind_engine: Engine = engine) -> None:
	Base.metadata.create_all(bind=bind_engine)
	user_columns = {column["name"] for column in inspect(bind_engine).get_columns("users")}
	user_migrations = {
		"github_url": "VARCHAR",
		"linkedin_url": "VARCHAR",
		"portfolio_url": "VARCHAR",
		"cv_url": "VARCHAR",
		"tutor_id": "INTEGER REFERENCES users(id)",
		"full_name": "VARCHAR(100)",
		"technologies": "JSON NOT NULL DEFAULT '[]'",
		"suggested_technologies": "JSON NOT NULL DEFAULT '[]'",
		"location_city": "VARCHAR(100)",
		"location_province": "VARCHAR(100)",
		"education": "JSON NOT NULL DEFAULT '[]'",
		"experience_projects": "JSON NOT NULL DEFAULT '[]'",
		"availability": "VARCHAR(200)",
		"languages": "JSON NOT NULL DEFAULT '[]'",
		"soft_skills": "JSON NOT NULL DEFAULT '[]'",
		"profile_confirmed": "BOOLEAN NOT NULL DEFAULT FALSE",
	}
	with bind_engine.begin() as connection:
		for column, definition in user_migrations.items():
			if column not in user_columns:
				connection.execute(
					text(f"ALTER TABLE users ADD COLUMN {column} {definition}")
				)

	application_columns = {
		column["name"] for column in inspect(bind_engine).get_columns("applications")
	}
	application_migrations = {
		"status": "VARCHAR NOT NULL DEFAULT 'pendiente'",
		"feedback": "VARCHAR",
		"contact_shared": "BOOLEAN NOT NULL DEFAULT FALSE",
	}
	for column, definition in application_migrations.items():
		if column not in application_columns:
			with bind_engine.begin() as connection:
				connection.execute(
					text(f"ALTER TABLE applications ADD COLUMN {column} {definition}")
				)

	columns = {column["name"] for column in inspect(bind_engine).get_columns("fct_logs")}
	if "is_tutor_approved" not in columns:
		with bind_engine.begin() as connection:
			connection.execute(
				text(
					"ALTER TABLE fct_logs "
					"ADD COLUMN is_tutor_approved BOOLEAN NOT NULL DEFAULT FALSE"
				)
			)


if __name__ == "__main__":
	init_db()