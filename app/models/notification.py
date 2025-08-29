
"""
Modèle Notification : gestion des alertes et messages liés aux interventions.
Relations : N:1 avec Intervention, N:1 avec User.
Exemple : notification d'affectation, clôture, rappel, etc.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any
import enum

if TYPE_CHECKING:
    from .intervention import Intervention
    from .user import User

class TypeNotification(str, enum.Enum):
    affectation = "affectation"
    cloture = "cloture"
    rappel = "rappel"
    retard = "retard"
    information = "information"

class CanalNotification(str, enum.Enum):
    email = "email"
    log = "log"
    sms = "sms"
    push = "push"

class Notification(Base):
    """
    Modèle Notification - Gestion des alertes/messages liés à une intervention.
    - Peut être envoyée par email, log, SMS, etc.
    - Concerne un utilisateur et une intervention
    - Contient le type, le canal, le contenu, et la date d’envoi
    - Préparé pour extension (statut, lecture, audit)
    """
    __tablename__ = "notifications"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True
    __table_args__ = (
        Index('idx_notification_user_intervention', 'user_id', 'intervention_id'),
        Index('idx_notification_date', 'date_envoi'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    type_notification: TypeNotification = Column("type", Enum(TypeNotification), nullable=False, index=True, doc="Type de notification")
    canal: CanalNotification = Column(Enum(CanalNotification), nullable=False, index=True, doc="Canal d'envoi")
    contenu: Optional[str] = Column(String(1000), nullable=True, doc="Sujet/message")
    date_envoi: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True, doc="Date d'envoi")

    # Foreign Keys
    intervention_id: int = Column(Integer, ForeignKey("interventions.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id: int = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)

    # ORM relationships
    intervention: "Intervention" = relationship("Intervention", back_populates="notifications", lazy="select")
    user: "User" = relationship("User", back_populates="notifications", lazy="select")

    def __repr__(self) -> str:
        return f"<Notification(id={self.id}, type='{self.type_notification.value}', canal='{self.canal.value}', user_id={self.user_id}, intervention_id={self.intervention_id})>"

    @property
    def resume(self) -> str:
        """Résumé court de la notification."""
        return f"[{self.type_notification.value.upper()}] {self.contenu[:40] if self.contenu else ''}..."

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "type_notification": self.type_notification.value,
            "canal": self.canal.value,
            "contenu": self.contenu,
            "date_envoi": self.date_envoi.isoformat() if self.date_envoi else None,
            "user_id": self.user_id,
            "intervention_id": self.intervention_id,
            "resume": self.resume,
        }
        if include_relations:
            data["user"] = self.user.to_dict() if self.user else None
            data["intervention"] = self.intervention.to_dict() if self.intervention else None
        return data

    # NOTE: Préparé pour extension future (statut de lecture, audit, suppression logique, etc.)
