
"""
Modèle HistoriqueIntervention : traçabilité des changements de statut d'une intervention.
Relations : N:1 avec Intervention, N:1 avec User.
Exemple : audit, suivi RGPD, analyse de délais, reporting.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any
from .intervention import StatutIntervention

if TYPE_CHECKING:
    from .intervention import Intervention
    from .user import User

class HistoriqueIntervention(Base):
    """
    Modèle HistoriqueIntervention - Traçabilité des changements de statut d'une intervention.
    - Trace tous les changements de statut
    - Enregistre l'auteur du changement et une remarque facultative
    - Utile pour audit, suivi RGPD, analyse de délais
    - Préparé pour extension (audit, suppression logique, RGPD)
    """
    __tablename__ = "historiques_interventions"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True
    __table_args__ = (
        Index('idx_historique_intervention', 'intervention_id', 'user_id', 'horodatage'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    statut: StatutIntervention = Column(Enum(StatutIntervention), nullable=False, index=True, doc="Statut enregistré")
    remarque: Optional[str] = Column(String, nullable=True, doc="Remarque libre")
    horodatage: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, doc="Horodatage du changement")

    # Liens vers intervention et utilisateur
    intervention_id: int = Column(Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    intervention: "Intervention" = relationship("Intervention", back_populates="historiques", lazy="select")
    user: "User" = relationship("User", back_populates="historiques", lazy="select")

    def __repr__(self) -> str:
        return f"<HistoriqueIntervention(id={self.id}, statut='{self.statut.value}', intervention_id={self.intervention_id}, user_id={self.user_id})>"

    @property
    def statut_label(self) -> str:
        """Label lisible du statut."""
        return self.statut.value.capitalize()

    @property
    def resume(self) -> str:
        """Résumé court de l'événement historique."""
        return f"{self.horodatage.strftime('%d/%m/%Y %H:%M')} - {self.statut_label} par user {self.user_id}"

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "statut": self.statut.value,
            "statut_label": self.statut_label,
            "remarque": self.remarque,
            "horodatage": self.horodatage.isoformat() if self.horodatage else None,
            "intervention_id": self.intervention_id,
            "user_id": self.user_id,
            "resume": self.resume,
        }
        if include_relations:
            data["user"] = self.user.to_dict() if self.user else None
            data["intervention"] = self.intervention.to_dict() if self.intervention else None
        return data

    # NOTE: Préparé pour extension future (audit, suppression logique, RGPD, etc.)
