# app/seed/seed_data.py

from faker import Faker
from sqlalchemy.orm import Session
from app.models.user import User, UserRole
from app.models.technicien import Technicien, Competence, DisponibiliteTechnicien
from app.models.equipement import Equipement
from app.models.intervention import Intervention, StatutIntervention, InterventionType, PrioriteIntervention
from app.models.planning import Planning
from app.models.notification import Notification, TypeNotification, CanalNotification
from app.models.historique import HistoriqueIntervention
from app.core.security import get_password_hash
from datetime import datetime, timedelta
import random

fake = Faker()

def seed_all(db: Session):
    # --- USERS ---
    # helper: reuse existing user if present to make seed idempotent
    def get_or_create_user(email, **kwargs):
        existing = db.query(User).filter_by(email=email).first()
        if existing:
            return existing
        u = User(email=email, **kwargs)
        db.add(u)
        return u

    admin = get_or_create_user(
        "admin@mif.ma",
        username="admin",
        full_name="Admin MIF",
        role=UserRole.admin,
        hashed_password=get_password_hash("admin123"),
        is_active=True
    )

    # ensure a fixed responsable account for tests
    responsable_fixed = get_or_create_user(
        "responsable@mif.ma",
        username="responsable",
        full_name="Responsable MIF",
        role=UserRole.responsable,
        hashed_password=get_password_hash("responsable123"),
        is_active=True
    )

    responsables = []
    for _ in range(2):
        email = fake.unique.email()
        user = get_or_create_user(
            email,
            username=email.split('@')[0],
            full_name=fake.name(),
            role=UserRole.responsable,
            hashed_password=get_password_hash("responsable123"),
            is_active=True
        )
        responsables.append(user)

    techniciens = []
    for _ in range(3):
        email = fake.unique.email()
        user = get_or_create_user(
            email,
            username=email.split('@')[0],
            full_name=fake.name(),
            role=UserRole.technicien,
            hashed_password=get_password_hash("tech123"),
            is_active=True
        )
        # ensure a Technicien row exists for this user
        existing_tech = db.query(Technicien).filter_by(user_id=user.id).first()
        if not existing_tech:
            db.flush()  # pour obtenir l'ID
            tech = Technicien(user_id=user.id, equipe="A", disponibilite=DisponibiliteTechnicien.disponible)
            db.add(tech)
            techniciens.append(tech)
        else:
            techniciens.append(existing_tech)

    clients = []
    for _ in range(2):
        email = fake.unique.email()
        user = User(
            username=email.split('@')[0],
            full_name=fake.name(),
            email=email,
            role=UserRole.client,
            hashed_password=get_password_hash("client123"),
            is_active=True
        )
        db.add(user)
        clients.append(user)

    # --- COMPÉTENCES ---
    competence_labels = ["mécanique", "électrique", "hydraulique"]
    for nom in competence_labels:
        # avoid duplicate insertion on re-seed
        existing_comp = db.query(Competence).filter_by(nom=nom).first()
        if not existing_comp:
            db.add(Competence(nom=nom))

    # --- ÉQUIPEMENTS ---
    equipements = []
    for _ in range(5):
        equip = Equipement(
            nom=fake.word().capitalize() + " Machine",
            type=random.choice(["électrique", "hydraulique"]),
            localisation=fake.city(),
            frequence_entretien=random.choice(["mensuel", "hebdomadaire", "trimestriel"])
        )
        db.add(equip)
        equipements.append(equip)

    db.flush()

    # --- INTERVENTIONS ---
    # Use only API-supported InterventionType values (corrective/preventive)
    allowed_types = [InterventionType.corrective, InterventionType.preventive]
    allowed_statuts = [
        StatutIntervention.ouverte,
        StatutIntervention.affectee,
        StatutIntervention.en_cours,
        StatutIntervention.en_attente,
        StatutIntervention.cloturee,
        StatutIntervention.archivee,
    ]
    for _ in range(10):
        i = Intervention(
            titre=fake.sentence(nb_words=3),
            description=fake.text(),
            type=random.choice(allowed_types),
            statut=random.choice(allowed_statuts),
            priorite=random.choice(list(PrioriteIntervention)),
            urgence=random.choice([True, False]),
            date_creation=datetime.utcnow() - timedelta(days=random.randint(0, 30)),
            date_limite=datetime.utcnow() + timedelta(days=random.randint(1, 10)),
            date_cloture=None,
            technicien_id=random.choice(techniciens).id,
            equipement_id=random.choice(equipements).id
        )
        db.add(i)
    db.flush()  # ensure interventions have ids for FK references

    # --- PLANNING ---
    for equip in equipements[:2]:
        planning = Planning(
            frequence="mensuel",
            prochaine_date=datetime.utcnow() + timedelta(days=30),
            derniere_date=datetime.utcnow() - timedelta(days=30),
            date_creation=datetime.utcnow(),
            equipement_id=equip.id
        )
        db.add(planning)

    # --- NOTIFICATIONS SIMULÉES ---
    for _ in range(5):
        intervention_choice = random.choice(techniciens)
        # choose a real intervention id
        inter = random.choice(list(db.query(Intervention).all()))
        notif = Notification(
            type_notification=TypeNotification.affectation,
            canal=CanalNotification.email,
            contenu="Intervention affectée à un technicien.",
            date_envoi=datetime.utcnow(),
            user_id=random.choice(techniciens).user_id,
            intervention_id=inter.id
        )
        db.add(notif)

    # --- HISTORIQUE ---
    # attach historique to an existing intervention
    inter_for_hist = random.choice(list(db.query(Intervention).all()))
    historique = HistoriqueIntervention(
        statut=StatutIntervention.en_cours,
        remarque="Intervention démarrée automatiquement.",
        horodatage=datetime.utcnow(),
        user_id=admin.id,
        intervention_id=inter_for_hist.id
    )
    db.add(historique)

    db.commit()
# app/seed/seed_data.py