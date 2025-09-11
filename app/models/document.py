"""
Modèle Document : gestion des fichiers liés aux interventions (photos, rapports, etc.).
Relations : N:1 avec Intervention.
Exemple : utilisé pour stocker et référencer les documents opérationnels dans le SI.
"""

from datetime import datetime
from typing import TYPE_CHECKING, Any, Dict

from sqlalchemy import Column, DateTime, ForeignKey, Index, Integer, String
from sqlalchemy.orm import relationship

from app.db.database import Base

if TYPE_CHECKING:
    from .intervention import Intervention


class Document(Base):
    """
    Modèle Document - Gestion des fichiers liés à une intervention.
    - Peut être une photo, un rapport PDF ou tout fichier joint
    - Stocké dans le dossier /static/uploads/
    - Chaque document est obligatoirement lié à une intervention
    - Préparé pour extension (audit, typage, versioning)
    """

    __tablename__ = "documents"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True
    __table_args__ = (
        Index("idx_document_intervention_upload", "intervention_id", "date_upload"),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    nom_fichier: str = Column(
        String(255), nullable=False, index=True, doc="Nom du fichier (ex: rapport.pdf)"
    )
    chemin: str = Column(
        String(255),
        nullable=False,
        doc="Chemin relatif (ex: static/uploads/<uuid>.<ext>)",
    )
    date_upload: datetime = Column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
        index=True,
        doc="Date d'upload",
    )

    # Clé étrangère vers une intervention
    intervention_id: int = Column(
        Integer,
        ForeignKey("interventions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )
    intervention: "Intervention" = relationship(
        "Intervention", back_populates="documents", lazy="select"
    )

    def __repr__(self) -> str:
        return (
            f"<Document(id={self.id}, nom_fichier='{self.nom_fichier}', "
            f"intervention_id={self.intervention_id})>"
        )

    @property
    def url(self) -> str:
        # URL d'accès public au document (pour l'API ou le front).
        # Les fichiers sont servis depuis /static, et `chemin` est relatif
        # (ex: "static/uploads/<uuid>.ext").
        # Normalise pour éviter les doubles slash/backslashes.
        rel = (self.chemin or "").lstrip("/\\")
        return f"/{rel}" if rel else "/static/uploads"

    def to_dict(
        self, include_sensitive: bool = False, include_relations: bool = False
    ) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "nom_fichier": self.nom_fichier,
            "chemin": self.chemin if include_sensitive else None,
            "date_upload": self.date_upload.isoformat() if self.date_upload else None,
            "url": self.url,
            "intervention_id": self.intervention_id,
        }
        if include_relations:
            data["intervention"] = (
                self.intervention.to_dict() if self.intervention else None
            )
        return data

    # NOTE: Préparé pour extension future (audit, versioning, typage MIME, etc.)
