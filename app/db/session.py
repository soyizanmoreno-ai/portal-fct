from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

url_db = "sqlite:///./sql_app.db"

engine = create_engine(url_db, connect_args={"check_same_thread" : False})

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)