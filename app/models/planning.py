
"""
Modèle Planning : gestion des cycles de maintenance préventive et planification opérationnelle.
Relations : 1:N avec Equipement, liens potentiels avec Interventions futures.
Exemple : utilisé pour générer automatiquement les interventions préventives, détecter les retards, optimiser la charge.
"""

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Enum, Index, Boolean
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any
import enum

if TYPE_CHECKING:
    from .equipement import Equipement
    from .intervention import Intervention

class FrequencePlanning(str, enum.Enum):
    """Fréquence de maintenance planifiée."""
    journalier = "journalier"
    hebdomadaire = "hebdomadaire"
    mensuel = "mensuel"
    trimestriel = "trimestriel"
    semestriel = "semestriel"
    annuel = "annuel"

class StatutPlanning(str, enum.Enum):
    """Statut du planning de maintenance."""
    actif = "actif"
    suspendu = "suspendu"
    termine = "termine"
    en_retard = "en_retard"

class Planning(Base):
    """
    Modèle Planning - Orchestration de la maintenance préventive.
    
    - Définit la fréquence, les dates clés, le statut du cycle de maintenance
    - Lié à un équipement industriel (1:N)
    - Permet la génération automatique d'interventions préventives
    - Sert à détecter les retards et optimiser la planification
    
    Relations :
    - N:1 avec Equipement (patrimoine technique)
    - (Futur) 1:N avec Interventions générées
    """
    __tablename__ = "plannings"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True
    __table_args__ = (
        Index('idx_planning_equipement_frequence', 'equipement_id', 'frequence'),
        Index('idx_planning_statut_prochaine', 'statut', 'prochaine_date'),
    )

    id = Column(Integer, primary_key=True, index=True)
    frequence = Column(Enum(FrequencePlanning), nullable=False, index=True)
    prochaine_date = Column(DateTime, nullable=True, index=True)
    derniere_date = Column(DateTime, nullable=True)
    statut = Column(Enum(StatutPlanning), default=StatutPlanning.actif, nullable=False, index=True)
    commentaire = Column(String(255), nullable=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    date_modification = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    equipement_id = Column(Integer, ForeignKey("equipements.id", ondelete="CASCADE"), nullable=False, index=True)
    equipement: "Equipement" = relationship("Equipement", back_populates="plannings", lazy="select")

    # NOTE: Préparé pour extension future (lien direct avec interventions générées)
    # interventions = relationship("Intervention", back_populates="planning", lazy="dynamic")

    def __repr__(self) -> str:
        return f"<Planning(id={self.id}, equipement_id={self.equipement_id}, frequence='{self.frequence.value}', statut='{self.statut.value}')>"

    # Propriétés calculées
    @property
    def est_en_retard(self) -> bool:
        """Vérifie si la prochaine intervention planifiée est dépassée."""
        if not self.prochaine_date or self.statut != StatutPlanning.actif:
            return False
        return datetime.utcnow() > self.prochaine_date

    @property
    def jours_retard(self) -> Optional[int]:
        """Nombre de jours de retard si en retard."""
        if self.est_en_retard:
            return (datetime.utcnow() - self.prochaine_date).days
        return None

    @property
    def prochaine_frequence_label(self) -> str:
        """Label lisible de la prochaine échéance."""
        if not self.prochaine_date:
            return "Non planifiée"
        return self.prochaine_date.strftime("%d/%m/%Y")

    @property
    def equipement_nom(self) -> Optional[str]:
        """Nom de l'équipement lié."""
        return self.equipement.nom if self.equipement else None

    # Méthodes métier
    def calculer_prochaine_date(self) -> Optional[datetime]:
        """Calcule la prochaine date planifiée selon la fréquence."""
        if not self.derniere_date:
            return None
        freq = self.frequence
        if freq == FrequencePlanning.journalier:
            return self.derniere_date + timedelta(days=1)
        elif freq == FrequencePlanning.hebdomadaire:
            return self.derniere_date + timedelta(weeks=1)
        elif freq == FrequencePlanning.mensuel:
            return self.derniere_date + timedelta(days=30)
        elif freq == FrequencePlanning.trimestriel:
            return self.derniere_date + timedelta(days=90)
        elif freq == FrequencePlanning.semestriel:
            return self.derniere_date + timedelta(days=182)
        elif freq == FrequencePlanning.annuel:
            return self.derniere_date + timedelta(days=365)
        return None

    def mettre_a_jour_prochaine_date(self) -> None:
        """Met à jour la prochaine date planifiée automatiquement."""
        self.prochaine_date = self.calculer_prochaine_date()
        self.date_modification = datetime.utcnow()

    def suspendre(self, raison: Optional[str] = None) -> None:
        """Suspend le planning (maintenance non planifiée)."""
        self.statut = StatutPlanning.suspendu
        if raison:
            self.commentaire = raison
        self.date_modification = datetime.utcnow()

    def reactiver(self) -> None:
        """Réactive le planning."""
        self.statut = StatutPlanning.actif
        self.date_modification = datetime.utcnow()

    def terminer(self) -> None:
        """Marque le planning comme terminé définitivement."""
        self.statut = StatutPlanning.termine
        self.date_modification = datetime.utcnow()

    # Sérialisation harmonisée
    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "frequence": self.frequence.value,
            "statut": self.statut.value,
            "prochaine_date": self.prochaine_date.isoformat() if self.prochaine_date else None,
            "derniere_date": self.derniere_date.isoformat() if self.derniere_date else None,
            "equipement_id": self.equipement_id,
            "equipement_nom": self.equipement_nom,
            "est_en_retard": self.est_en_retard,
            "jours_retard": self.jours_retard,
            "prochaine_frequence_label": self.prochaine_frequence_label,
            "is_active": self.is_active,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
        }
        if include_sensitive:
            data.update({
                "date_modification": self.date_modification.isoformat() if self.date_modification else None,
                "commentaire": self.commentaire,
            })
        if include_relations:
            data.update({
                "equipement": self.equipement.to_dict() if self.equipement else None,
            })
        return data
