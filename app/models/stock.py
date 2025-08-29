# app/models/stock.py

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Text, Enum
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
import enum


class TypeMouvement(str, enum.Enum):
    """Types de mouvements de stock"""
    entree = "entree"
    sortie = "sortie"
    ajustement = "ajustement"
    retour = "retour"



"""
Modèles Stock : gestion des pièces détachées, mouvements de stock, et traçabilité d'utilisation.
Relations : 1:N entre PieceDetachee et MouvementStock, N:N via InterventionPiece.
Exemple : suivi inventaire, audit, alertes, reporting.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Numeric, Boolean, Text, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any
import enum

if TYPE_CHECKING:
    from .intervention import Intervention
    from .user import User

class TypeMouvement(str, enum.Enum):
    entree = "entree"
    sortie = "sortie"
    ajustement = "ajustement"
    retour = "retour"

class PieceDetachee(Base):
    """
    Modèle Pièce Détachée pour la gestion de l'inventaire.
    - Informations produit, gestion du stock, prix, relations mouvements/interventions
    - Préparé pour extension (audit, alertes, logs)
    """
    __tablename__ = "pieces_detachees"
    __table_args__ = (
        Index('idx_piece_reference', 'reference'),
        Index('idx_piece_stock', 'stock_actuel', 'stock_minimum'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    nom: str = Column(String(255), nullable=False, index=True)
    reference: str = Column(String(100), nullable=False, unique=True, index=True)
    description: Optional[str] = Column(Text, nullable=True)
    marque: Optional[str] = Column(String(100), nullable=True)
    modele: Optional[str] = Column(String(100), nullable=True)
    stock_actuel: int = Column(Integer, default=0, nullable=False, index=True)
    stock_minimum: int = Column(Integer, default=0, nullable=False)
    stock_maximum: Optional[int] = Column(Integer, nullable=True)
    prix_unitaire: Optional[float] = Column(Numeric(10, 2), nullable=True)
    cout_achat: Optional[float] = Column(Numeric(10, 2), nullable=True)
    devise: str = Column(String(3), default="EUR")
    fournisseur: Optional[str] = Column(String(255), nullable=True)
    reference_fournisseur: Optional[str] = Column(String(100), nullable=True)
    emplacement: Optional[str] = Column(String(100), nullable=True)
    rangee: Optional[str] = Column(String(50), nullable=True)
    etagere: Optional[str] = Column(String(50), nullable=True)
    is_active: bool = Column(Boolean, default=True, nullable=False, index=True)
    date_creation: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    date_modification: datetime = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    derniere_entree: Optional[datetime] = Column(DateTime, nullable=True)
    derniere_sortie: Optional[datetime] = Column(DateTime, nullable=True)

    mouvements = relationship(
        "MouvementStock",
        back_populates="piece_detachee",
        cascade="all, delete-orphan",
        order_by="MouvementStock.date_mouvement.desc()"
    )
    interventions_pieces = relationship(
        "InterventionPiece",
        back_populates="piece_detachee",
        cascade="all, delete-orphan"
    )

    def __repr__(self) -> str:
        return f"<PieceDetachee(id={self.id}, ref='{self.reference}', stock={self.stock_actuel})>"

    @property
    def est_en_rupture(self) -> bool:
        return self.stock_actuel <= 0

    @property
    def est_stock_bas(self) -> bool:
        return self.stock_actuel <= self.stock_minimum

    @property
    def valeur_stock(self) -> float:
        if self.prix_unitaire:
            return float(self.prix_unitaire) * self.stock_actuel
        return 0.0

    @property
    def pourcentage_stock(self) -> float:
        if self.stock_maximum and self.stock_maximum > 0:
            return (self.stock_actuel / self.stock_maximum) * 100
        return 0.0

    def peut_prelever(self, quantite: int) -> bool:
        return self.stock_actuel >= quantite

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "nom": self.nom,
            "reference": self.reference,
            "description": self.description,
            "marque": self.marque,
            "modele": self.modele,
            "stock_actuel": self.stock_actuel,
            "stock_minimum": self.stock_minimum,
            "stock_maximum": self.stock_maximum,
            "prix_unitaire": float(self.prix_unitaire) if self.prix_unitaire else None,
            "cout_achat": float(self.cout_achat) if self.cout_achat else None,
            "devise": self.devise,
            "fournisseur": self.fournisseur,
            "reference_fournisseur": self.reference_fournisseur,
            "emplacement": self.emplacement,
            "rangee": self.rangee,
            "etagere": self.etagere,
            "is_active": self.is_active,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "date_modification": self.date_modification.isoformat() if self.date_modification else None,
            "derniere_entree": self.derniere_entree.isoformat() if self.derniere_entree else None,
            "derniere_sortie": self.derniere_sortie.isoformat() if self.derniere_sortie else None,
            "est_en_rupture": self.est_en_rupture,
            "est_stock_bas": self.est_stock_bas,
            "valeur_stock": self.valeur_stock,
            "pourcentage_stock": self.pourcentage_stock,
        }
        if include_relations:
            data["mouvements"] = [m.to_dict() for m in self.mouvements] if self.mouvements else []
        return data

    # NOTE: Préparé pour extension future (audit, alertes, logs, etc.)



class MouvementStock(Base):
    """
    Modèle Mouvement de Stock pour tracer les entrées/sorties.
    - Type de mouvement, quantité, traçabilité, motif, intervention liée
    - Préparé pour extension (audit, logs, alertes)
    """
    __tablename__ = "mouvements_stock"
    __table_args__ = (
        Index('idx_mouvement_piece_date', 'piece_detachee_id', 'date_mouvement'),
        Index('idx_mouvement_type', 'type_mouvement'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    type_mouvement: TypeMouvement = Column(Enum(TypeMouvement), nullable=False, index=True)
    quantite: int = Column(Integer, nullable=False)
    stock_avant: int = Column(Integer, nullable=False)
    stock_apres: int = Column(Integer, nullable=False)
    motif: Optional[str] = Column(String(255), nullable=True)
    commentaire: Optional[str] = Column(Text, nullable=True)
    date_mouvement: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    piece_detachee_id: int = Column(Integer, ForeignKey("pieces_detachees.id", ondelete="CASCADE"), nullable=False, index=True)
    intervention_id: Optional[int] = Column(Integer, ForeignKey("interventions.id", ondelete="SET NULL"), nullable=True, index=True)
    user_id: Optional[int] = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True, index=True)
    piece_detachee = relationship("PieceDetachee", back_populates="mouvements", lazy="joined")
    intervention = relationship("Intervention", back_populates="mouvements_stock", lazy="select")
    user = relationship("User", back_populates="mouvements_stock", lazy="select")

    def __repr__(self) -> str:
        return f"<MouvementStock(id={self.id}, type='{self.type_mouvement.value}', qty={self.quantite})>"

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "id": self.id,
            "type_mouvement": self.type_mouvement.value,
            "quantite": self.quantite,
            "stock_avant": self.stock_avant,
            "stock_apres": self.stock_apres,
            "motif": self.motif,
            "commentaire": self.commentaire,
            "date_mouvement": self.date_mouvement.isoformat() if self.date_mouvement else None,
            "piece_detachee_id": self.piece_detachee_id,
            "intervention_id": self.intervention_id,
            "user_id": self.user_id,
        }
        if include_relations:
            data["piece_detachee"] = self.piece_detachee.to_dict() if self.piece_detachee else None
        return data

    # NOTE: Préparé pour extension future (audit, logs, alertes, etc.)



class InterventionPiece(Base):
    """
    Table d'association entre Interventions et Pièces Détachées.
    - Trace l'utilisation des pièces dans les interventions, quantité, date, commentaire
    - Préparé pour extension (audit, logs, RGPD)
    """
    __tablename__ = "interventions_pieces"
    __table_args__ = (
        Index('idx_intervention_piece', 'intervention_id', 'piece_detachee_id'),
    )

    intervention_id: int = Column(Integer, ForeignKey("interventions.id", ondelete="CASCADE"), primary_key=True, index=True)
    piece_detachee_id: int = Column(Integer, ForeignKey("pieces_detachees.id", ondelete="CASCADE"), primary_key=True, index=True)
    quantite_utilisee: int = Column(Integer, nullable=False, default=1)
    date_utilisation: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    commentaire: Optional[str] = Column(Text, nullable=True)
    intervention = relationship("Intervention", back_populates="pieces_utilisees", lazy="select")
    piece_detachee = relationship("PieceDetachee", back_populates="interventions_pieces", lazy="select")

    def __repr__(self) -> str:
        return f"<InterventionPiece(intervention={self.intervention_id}, piece={self.piece_detachee_id}, qty={self.quantite_utilisee})>"

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        data = {
            "intervention_id": self.intervention_id,
            "piece_detachee_id": self.piece_detachee_id,
            "quantite_utilisee": self.quantite_utilisee,
            "date_utilisation": self.date_utilisation.isoformat() if self.date_utilisation else None,
            "commentaire": self.commentaire,
        }
        if include_relations:
            data["piece_detachee"] = self.piece_detachee.to_dict() if self.piece_detachee else None
        return data

    # NOTE: Préparé pour extension future (audit, logs, RGPD, etc.)