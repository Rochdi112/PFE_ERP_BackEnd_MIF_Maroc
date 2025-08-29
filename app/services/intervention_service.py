from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.intervention import Intervention, StatutIntervention
from app.models.historique import HistoriqueIntervention
from app.models.technicien import Technicien
from app.models.equipement import Equipement
from app.models.user import User
from app.schemas.intervention import InterventionCreate
from app.models.planning import Planning

def create_intervention(db: Session, data: InterventionCreate, user_id: int) -> Intervention:
    # Vérification technicien si renseigné
    if data.technicien_id:
        if not db.query(Technicien).filter(Technicien.id == data.technicien_id).first():
            raise HTTPException(status_code=404, detail="Technicien assigné introuvable")
    equipement = db.query(Equipement).filter(Equipement.id == data.equipement_id).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement cible introuvable")
    intervention = Intervention(
        titre=data.titre,
        description=data.description,
        type_intervention=data.type_intervention,
        statut=data.statut,
        priorite=data.priorite,
        urgence=data.urgence,
        date_limite=data.date_limite,
        technicien_id=data.technicien_id,
        equipement_id=data.equipement_id,
        date_creation=datetime.utcnow()
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)
    # 👇 Historise avec l'utilisateur qui crée (user_id courant, pas technicien_id)
    add_historique(
        db,
        intervention_id=intervention.id,
        user_id=user_id,
        statut=data.statut,
        remarque="Création de l’intervention"
    )
    return intervention

def get_intervention_by_id(db: Session, intervention_id: int) -> Intervention:
    intervention = db.query(Intervention).filter(Intervention.id == intervention_id).first()
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention introuvable")
    return intervention

def get_all_interventions(db: Session) -> list[Intervention]:
    return db.query(Intervention).all()

def update_statut_intervention(
    db: Session,
    intervention_id: int,
    new_statut: StatutIntervention,
    user_id: int,
    remarque: str = ""
) -> Intervention:
    intervention = get_intervention_by_id(db, intervention_id)
    # Refuse modifications after closure
    if intervention.statut == StatutIntervention.cloturee:
        raise HTTPException(status_code=400, detail="Intervention déjà clôturée")
    # Interdire de passer directement à archivee sans clôture préalable
    if new_statut == StatutIntervention.archivee and intervention.statut != StatutIntervention.cloturee:
        raise HTTPException(status_code=409, detail="Transition vers 'archivee' interdite")
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    intervention.statut = new_statut
    if new_statut == StatutIntervention.cloturee:
        intervention.date_cloture = datetime.utcnow()
    db.commit()
    add_historique(db, intervention_id, user_id, new_statut, remarque)
    return intervention

def add_historique(
    db: Session,
    intervention_id: int,
    user_id: int,  # Doit être obligatoire/NOT NULL
    statut: StatutIntervention,
    remarque: str
):
    historique = HistoriqueIntervention(
        statut=statut,
        remarque=remarque,
        horodatage=datetime.utcnow(),
        user_id=user_id,
        intervention_id=intervention_id
    )
    db.add(historique)
    db.commit()

def create_intervention_from_planning(db: Session, planning: Planning) -> Intervention:
    """
    Crée une intervention préventive basée sur un objet Planning.
    Relie l'intervention à l'équipement du planning.
    Met à jour le planning (dernière/prochaine date).
    """
    equipement = db.query(Equipement).filter(Equipement.id == planning.equipement_id).first()
    if not equipement:
        raise HTTPException(status_code=404, detail="Équipement introuvable pour le planning")

    intervention = Intervention(
        titre=f"Maintenance préventive - {equipement.nom}",
        description=f"Intervention générée automatiquement depuis le planning #{planning.id}",
        type_intervention="preventive",
        statut=StatutIntervention.ouverte,
        priorite="normale",
        urgence=False,
        technicien_id=None,
        equipement_id=equipement.id,
        date_creation=datetime.utcnow(),
    )
    db.add(intervention)
    db.commit()
    db.refresh(intervention)

    # Historique système (user_id=0 convention pour système)
    add_historique(
        db,
        intervention_id=intervention.id,
        user_id=0,
        statut=StatutIntervention.ouverte,
        remarque="Intervention générée par le scheduler depuis le planning",
    )

    # Mettre à jour le planning
    planning.derniere_date = datetime.utcnow()
    planning.mettre_a_jour_prochaine_date()
    db.commit()
    return intervention
