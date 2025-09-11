# app/db/init_db.py

from app.db.database import Base, engine


def init_db():
    # Crée toutes les tables définies dans les modèles
    Base.metadata.create_all(bind=engine)
