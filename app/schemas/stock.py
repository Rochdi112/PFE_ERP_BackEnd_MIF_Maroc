# app/schemas/stock.py

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime
from decimal import Decimal
from enum import Enum


class TypeMouvement(str, Enum):
    """Types de mouvements de stock"""
    entree = "entree"
    sortie = "sortie"
    ajustement = "ajustement"
    retour = "retour"


class StatutStock(str, Enum):
    """Statuts calculés du stock"""
    normal = "normal"
    bas = "bas"
    critique = "critique"
    rupture = "rupture"


class PieceDetacheeBase(BaseModel):
    """
    Schéma de base pour une pièce détachée.
    """
    nom: str = Field(..., min_length=2, max_length=255, description="Nom de la pièce")
    reference: str = Field(..., min_length=1, max_length=100, description="Référence unique")
    description: Optional[str] = Field(None, description="Description détaillée")
    marque: Optional[str] = Field(None, max_length=100, description="Marque")
    modele: Optional[str] = Field(None, max_length=100, description="Modèle")
    
    # Gestion stock
    stock_minimum: int = Field(0, ge=0, description="Stock minimum")
    stock_maximum: Optional[int] = Field(None, ge=0, description="Stock maximum")
    
    # Prix et coûts
    prix_unitaire: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Prix unitaire")
    cout_achat: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Coût d'achat")
    devise: str = Field("EUR", max_length=3, description="Devise")
    
    # Fournisseur
    fournisseur: Optional[str] = Field(None, max_length=255, description="Nom du fournisseur")
    reference_fournisseur: Optional[str] = Field(None, max_length=100, description="Référence fournisseur")
    
    # Localisation
    emplacement: Optional[str] = Field(None, max_length=100, description="Emplacement de stockage")
    rangee: Optional[str] = Field(None, max_length=50, description="Rangée")
    etagere: Optional[str] = Field(None, max_length=50, description="Étagère")

    @field_validator('stock_maximum')
    @classmethod
    def validate_stock_maximum(cls, v, info):
        """Vérifie que le stock maximum est supérieur au minimum"""
        if v is not None and 'stock_minimum' in info.data:
            if v < info.data['stock_minimum']:
                raise ValueError('Le stock maximum doit être supérieur au stock minimum')
        return v

    @field_validator('reference')
    @classmethod
    def validate_reference(cls, v):
        """Vérifie le format de la référence"""
        if not v.replace('-', '').replace('_', '').isalnum():
            raise ValueError('La référence ne peut contenir que des lettres, chiffres, tirets et underscores')
        return v.upper()

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )


class PieceDetacheeCreate(PieceDetacheeBase):
    """
    Schéma pour la création d'une pièce détachée.
    """
    stock_initial: int = Field(0, ge=0, description="Stock initial")

    @field_validator('stock_initial')
    @classmethod
    def validate_stock_initial(cls, v):
        """Vérifie que le stock initial est positif"""
        if v < 0:
            raise ValueError('Le stock initial ne peut pas être négatif')
        return v


class PieceDetacheeUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'une pièce détachée.
    Tous les champs sont optionnels.
    """
    nom: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    marque: Optional[str] = Field(None, max_length=100)
    modele: Optional[str] = Field(None, max_length=100)
    
    stock_minimum: Optional[int] = Field(None, ge=0)
    stock_maximum: Optional[int] = Field(None, ge=0)
    
    prix_unitaire: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    cout_achat: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    
    fournisseur: Optional[str] = Field(None, max_length=255)
    reference_fournisseur: Optional[str] = Field(None, max_length=100)
    
    emplacement: Optional[str] = Field(None, max_length=100)
    rangee: Optional[str] = Field(None, max_length=50)
    etagere: Optional[str] = Field(None, max_length=50)
    
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class PieceDetacheeOut(PieceDetacheeBase):
    """
    Schéma de sortie pour une pièce détachée.
    """
    id: int
    stock_actuel: int
    is_active: bool
    date_creation: datetime
    date_modification: Optional[datetime] = None
    derniere_entree: Optional[datetime] = None
    derniere_sortie: Optional[datetime] = None
    
    # Propriétés calculées
    est_en_rupture: bool
    est_stock_bas: bool
    statut_stock: StatutStock
    valeur_stock: float
    pourcentage_stock: float

    model_config = ConfigDict(from_attributes=True)


class MouvementStockBase(BaseModel):
    """
    Schéma de base pour un mouvement de stock.
    """
    type_mouvement: TypeMouvement = Field(..., description="Type de mouvement")
    quantite: int = Field(..., gt=0, description="Quantité (toujours positive)")
    motif: Optional[str] = Field(None, max_length=255, description="Motif du mouvement")
    commentaire: Optional[str] = Field(None, description="Commentaire détaillé")

    @field_validator('quantite')
    @classmethod
    def validate_quantite(cls, v):
        """Vérifie que la quantité est positive"""
        if v <= 0:
            raise ValueError('La quantité doit être positive')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class MouvementStockCreate(MouvementStockBase):
    """
    Schéma pour la création d'un mouvement de stock.
    """
    piece_detachee_id: int = Field(..., gt=0, description="ID de la pièce détachée")
    intervention_id: Optional[int] = Field(None, gt=0, description="ID de l'intervention liée (optionnel)")


class MouvementStockOut(MouvementStockBase):
    """
    Schéma de sortie pour un mouvement de stock.
    """
    id: int
    piece_detachee_id: int
    intervention_id: Optional[int] = None
    user_id: Optional[int] = None
    
    stock_avant: int
    stock_apres: int
    date_mouvement: datetime
    
    # Relations incluses
    piece_detachee_nom: Optional[str] = None
    piece_detachee_reference: Optional[str] = None
    intervention_titre: Optional[str] = None
    user_nom: Optional[str] = None

    model_config = ConfigDict(from_attributes=True)


class InterventionPieceBase(BaseModel):
    """
    Schéma de base pour l'association intervention-pièce.
    """
    quantite_utilisee: int = Field(..., gt=0, description="Quantité utilisée")
    commentaire: Optional[str] = Field(None, description="Commentaire sur l'utilisation")

    @field_validator('quantite_utilisee')
    @classmethod
    def validate_quantite_utilisee(cls, v):
        """Vérifie que la quantité utilisée est positive"""
        if v <= 0:
            raise ValueError('La quantité utilisée doit être positive')
        return v

    model_config = ConfigDict(from_attributes=True)


class InterventionPieceCreate(InterventionPieceBase):
    """
    Schéma pour ajouter une pièce à une intervention.
    """
    piece_detachee_id: int = Field(..., gt=0, description="ID de la pièce détachée")


class InterventionPieceOut(InterventionPieceBase):
    """
    Schéma de sortie pour une pièce utilisée dans une intervention.
    """
    intervention_id: int
    piece_detachee_id: int
    date_utilisation: datetime
    
    # Informations de la pièce
    piece_nom: str
    piece_reference: str
    piece_prix_unitaire: Optional[Decimal] = None
    
    # Coût calculé
    cout_total: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class StockAlert(BaseModel):
    """
    Schéma pour les alertes de stock.
    """
    piece_detachee_id: int
    piece_nom: str
    piece_reference: str
    stock_actuel: int
    stock_minimum: int
    type_alerte: StatutStock
    message: str
    priorite: int = Field(..., ge=1, le=5, description="Priorité de l'alerte (1=max, 5=min)")
    
    # Actions suggérées
    action_recommandee: str
    quantite_recommandee: Optional[int] = None
    
    model_config = ConfigDict(from_attributes=True)


class StockValuation(BaseModel):
    """
    Schéma pour la valorisation du stock.
    """
    # Globale
    valeur_totale_stock: Decimal
    nb_references_total: int
    nb_references_actives: int
    
    # Par statut
    valeur_stock_normal: Decimal
    valeur_stock_bas: Decimal
    valeur_stock_critique: Decimal
    
    # Statistiques
    piece_plus_chere: Optional[str] = None
    piece_plus_utilisee: Optional[str] = None
    fournisseur_principal: Optional[str] = None
    
    # Évolution
    evolution_valeur_mois: Optional[float] = None
    evolution_mouvements_mois: Optional[int] = None
    
    date_calcul: datetime

    model_config = ConfigDict(from_attributes=True)


class StockSearch(BaseModel):
    """
    Schéma pour la recherche de pièces détachées.
    """
    query: Optional[str] = Field(None, description="Recherche textuelle (nom, référence)")
    marque: Optional[str] = Field(None, description="Filtrer par marque")
    fournisseur: Optional[str] = Field(None, description="Filtrer par fournisseur")
    statut_stock: Optional[StatutStock] = Field(None, description="Filtrer par statut de stock")
    emplacement: Optional[str] = Field(None, description="Filtrer par emplacement")
    
    # Filtres numériques
    prix_min: Optional[Decimal] = Field(None, ge=0, description="Prix unitaire minimum")
    prix_max: Optional[Decimal] = Field(None, ge=0, description="Prix unitaire maximum")
    stock_min: Optional[int] = Field(None, ge=0, description="Stock minimum")
    stock_max: Optional[int] = Field(None, ge=0, description="Stock maximum")
    
    # État
    is_active: Optional[bool] = Field(None, description="Filtrer par statut actif")
    
    # Pagination et tri
    page: int = Field(1, ge=1, description="Numéro de page")
    limit: int = Field(20, ge=1, le=100, description="Nombre d'éléments par page")
    sort_by: Optional[str] = Field("nom", description="Champ de tri")
    sort_order: Optional[str] = Field("asc", pattern="^(asc|desc)$", description="Ordre de tri")

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


class StockStats(BaseModel):
    """
    Schéma pour les statistiques de stock.
    """
    # Statistiques générales
    nb_pieces_total: int
    nb_pieces_actives: int
    nb_pieces_en_rupture: int
    nb_pieces_stock_bas: int
    
    # Valeurs
    valeur_totale: Decimal
    valeur_moyenne_piece: Decimal
    
    # Mouvements récents
    nb_mouvements_mois: int
    nb_entrees_mois: int
    nb_sorties_mois: int
    
    # Top listes
    pieces_plus_utilisees: List[dict] = Field(default_factory=list)
    pieces_plus_cheres: List[dict] = Field(default_factory=list)
    fournisseurs_principaux: List[dict] = Field(default_factory=list)
    
    # Alertes
    nb_alertes_critiques: int
    nb_alertes_normales: int
    
    date_calcul: datetime

    model_config = ConfigDict(from_attributes=True)