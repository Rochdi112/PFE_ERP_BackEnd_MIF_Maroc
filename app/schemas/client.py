# app/schemas/client.py

from datetime import datetime
from typing import List, Optional

from pydantic import BaseModel, ConfigDict, EmailStr, Field, field_validator


class ClientBase(BaseModel):
    """
    Schéma de base pour un client.
    Champs communs entre création, mise à jour et affichage.
    """

    nom_entreprise: str = Field(
        ..., min_length=2, max_length=255, description="Nom de l'entreprise"
    )
    secteur_activite: Optional[str] = Field(
        None, max_length=100, description="Secteur d'activité"
    )
    numero_siret: Optional[str] = Field(
        None, min_length=14, max_length=14, description="Numéro SIRET"
    )

    contact_principal: str = Field(
        ..., min_length=2, max_length=255, description="Nom du contact principal"
    )
    email: EmailStr = Field(..., description="Email de contact")
    telephone: Optional[str] = Field(
        None, max_length=20, description="Téléphone principal"
    )
    telephone_mobile: Optional[str] = Field(
        None, max_length=20, description="Téléphone mobile"
    )

    adresse: Optional[str] = Field(None, description="Adresse complète")
    code_postal: Optional[str] = Field(None, max_length=10, description="Code postal")
    ville: Optional[str] = Field(None, max_length=100, description="Ville")
    pays: str = Field(default="France", max_length=100, description="Pays")

    @field_validator("numero_siret")
    @classmethod
    def validate_siret(cls, v):
        """Validation du numéro SIRET"""
        if v and not v.isdigit():
            raise ValueError("Le numéro SIRET doit contenir uniquement des chiffres")
        return v

    @field_validator("telephone", "telephone_mobile")
    @classmethod
    def validate_phone(cls, v):
        """Validation basique des numéros de téléphone"""
        if v:
            # Supprimer les espaces et caractères spéciaux
            cleaned = "".join(
                filter(
                    str.isdigit, v.replace("+", "").replace(" ", "").replace(".", "")
                )
            )
            if len(cleaned) < 8:
                raise ValueError("Numéro de téléphone trop court")
        return v

    model_config = ConfigDict(
        from_attributes=True, str_strip_whitespace=True, validate_assignment=True
    )


class ClientCreate(ClientBase):
    """
    Schéma pour la création d'un client.
    Nécessite l'ID de l'utilisateur lié.
    """

    user_id: int = Field(..., gt=0, description="ID de l'utilisateur lié (rôle client)")

    @field_validator("user_id")
    @classmethod
    def validate_user_id(cls, v):
        """Validation de l'ID utilisateur"""
        if v <= 0:
            raise ValueError("L'ID utilisateur doit être positif")
        return v


class ClientUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un client.
    Tous les champs sont optionnels.
    """

    nom_entreprise: Optional[str] = Field(None, min_length=2, max_length=255)
    secteur_activite: Optional[str] = Field(None, max_length=100)
    numero_siret: Optional[str] = Field(None, min_length=14, max_length=14)

    contact_principal: Optional[str] = Field(None, min_length=2, max_length=255)
    email: Optional[EmailStr] = None
    telephone: Optional[str] = Field(None, max_length=20)
    telephone_mobile: Optional[str] = Field(None, max_length=20)

    adresse: Optional[str] = None
    code_postal: Optional[str] = Field(None, max_length=10)
    ville: Optional[str] = Field(None, max_length=100)
    pays: Optional[str] = Field(None, max_length=100)

    is_active: Optional[bool] = None

    model_config = ConfigDict(from_attributes=True, str_strip_whitespace=True)


class ClientOut(ClientBase):
    """
    Schéma de sortie pour un client.
    Inclut les métadonnées et statistiques.
    """

    id: int
    user_id: int
    is_active: bool
    date_creation: datetime
    date_modification: Optional[datetime] = None

    # Statistiques calculées
    nb_interventions_total: Optional[int] = 0
    derniere_intervention_date: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)


class ClientStats(BaseModel):
    """
    Schéma pour les statistiques détaillées d'un client.
    """

    client_id: int
    nom_entreprise: str

    # Statistiques interventions
    total_interventions: int
    interventions_ouvertes: int
    interventions_en_cours: int
    interventions_terminees: int
    interventions_en_retard: int

    # Statistiques temporelles
    duree_moyenne_intervention: Optional[float] = None  # en heures
    temps_reponse_moyen: Optional[float] = None  # en heures

    # Statistiques financières
    cout_total_interventions: Optional[float] = None
    cout_moyen_intervention: Optional[float] = None

    # Satisfaction et performance
    taux_respect_sla: Optional[float] = None  # pourcentage
    note_satisfaction: Optional[float] = None  # sur 5

    # Dates importantes
    premiere_intervention: Optional[datetime] = None
    derniere_intervention: Optional[datetime] = None

    # Contrats actifs
    nb_contrats_actifs: int = 0
    montant_contrats_annuel: Optional[float] = None

    model_config = ConfigDict(from_attributes=True)


class ClientSearch(BaseModel):
    """
    Schéma pour la recherche de clients avec filtres.
    """

    query: Optional[str] = Field(
        None, description="Recherche textuelle (nom, email, contact)"
    )
    secteur_activite: Optional[str] = Field(None, description="Filtrer par secteur")
    ville: Optional[str] = Field(None, description="Filtrer par ville")
    is_active: Optional[bool] = Field(None, description="Filtrer par statut actif")

    # Pagination
    page: int = Field(1, ge=1, description="Numéro de page")
    limit: int = Field(10, ge=1, le=100, description="Nombre d'éléments par page")

    # Tri
    sort_by: Optional[str] = Field("nom_entreprise", description="Champ de tri")
    sort_order: Optional[str] = Field(
        "asc", pattern="^(asc|desc)$", description="Ordre de tri"
    )

    model_config = ConfigDict(str_strip_whitespace=True)


class ClientContactInfo(BaseModel):
    """
    Schéma simplifié pour les informations de contact d'un client.
    Utilisé dans les listes et sélections.
    """

    id: int
    nom_entreprise: str
    contact_principal: str
    email: EmailStr
    telephone: Optional[str] = None
    ville: Optional[str] = None
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class ClientInterventionSummary(BaseModel):
    """
    Schéma pour le résumé des interventions d'un client.
    """

    client_id: int
    interventions_ouvertes: List[dict] = []
    interventions_en_cours: List[dict] = []
    dernières_interventions: List[dict] = []
    prochaines_maintenances: List[dict] = []

    model_config = ConfigDict(from_attributes=True)
