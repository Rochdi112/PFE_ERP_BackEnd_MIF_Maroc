# app/db/init_db.py

from app.db.database import Base, engine
from app.models import user, technicien, equipement, intervention, notification, document, historique

def init_db():
    # Crée toutes les tables définies dans les modèles
    Base.metadata.create_all(bind=engine)
