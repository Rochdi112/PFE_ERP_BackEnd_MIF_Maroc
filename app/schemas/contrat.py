# app/schemas/contrat.py

from pydantic import BaseModel, Field, ConfigDict, field_validator
from typing import Optional, List
from datetime import datetime, date
from decimal import Decimal
from enum import Enum


class TypeContrat(str, Enum):
    """Types de contrats de maintenance"""
    maintenance_preventive = "maintenance_preventive"
    maintenance_corrective = "maintenance_corrective"
    maintenance_complete = "maintenance_complete"
    support_technique = "support_technique"
    contrat_cadre = "contrat_cadre"


class StatutContrat(str, Enum):
    """Statuts d'un contrat"""
    brouillon = "brouillon"
    en_cours = "en_cours"
    expire = "expire"
    resilie = "resilie"
    suspendu = "suspendu"


class ModePaiement(str, Enum):
    """Modes de paiement/facturation"""
    mensuel = "mensuel"
    trimestriel = "trimestriel"
    semestriel = "semestriel"
    annuel = "annuel"


class ContratBase(BaseModel):
    """
    Schéma de base pour un contrat.
    Champs communs entre création, mise à jour et affichage.
    """
    nom_contrat: str = Field(..., min_length=2, max_length=255, description="Nom du contrat")
    description: Optional[str] = Field(None, description="Description détaillée du contrat")
    type_contrat: TypeContrat = Field(..., description="Type de contrat")
    
    # Dates
    date_debut: date = Field(..., description="Date de début du contrat")
    date_fin: date = Field(..., description="Date de fin du contrat")
    date_renouvellement: Optional[date] = Field(None, description="Date de renouvellement automatique")
    
    # Conditions financières
    montant_annuel: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2, description="Montant annuel")
    montant_mensuel: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Montant mensuel")
    devise: str = Field("EUR", max_length=3, description="Devise")
    mode_facturation: ModePaiement = Field(ModePaiement.mensuel, description="Mode de facturation")
    
    # SLA (Service Level Agreement)
    temps_reponse_urgence: Optional[int] = Field(None, ge=1, le=168, description="Temps de réponse urgence (heures)")
    temps_reponse_normal: Optional[int] = Field(None, ge=1, le=720, description="Temps de réponse normal (heures)")
    taux_disponibilite: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2, description="Taux de disponibilité (%)")
    penalites_retard: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Pénalités de retard")
    
    # Limites et conditions
    nb_interventions_incluses: Optional[int] = Field(None, ge=0, description="Nombre d'interventions incluses")
    heures_maintenance_incluses: Optional[int] = Field(None, ge=0, description="Heures de maintenance incluses")
    
    # Équipements et contacts
    equipements_couverts: Optional[str] = Field(None, description="Description des équipements couverts")
    contact_client: Optional[str] = Field(None, max_length=255, description="Contact client")
    contact_responsable: Optional[str] = Field(None, max_length=255, description="Contact responsable")

    @field_validator('date_fin')
    @classmethod
    def validate_date_fin(cls, v, info):
        """Vérifie que la date de fin est après la date de début"""
        if 'date_debut' in info.data and v <= info.data['date_debut']:
            raise ValueError('La date de fin doit être postérieure à la date de début')
        return v

    @field_validator('temps_reponse_urgence', 'temps_reponse_normal')
    @classmethod
    def validate_temps_reponse(cls, v, info):
        """Vérifie la cohérence des temps de réponse"""
        if v is not None:
            if 'temps_reponse_urgence' in info.data and 'temps_reponse_normal' in info.data:
                urgence = info.data.get('temps_reponse_urgence')
                normal = info.data.get('temps_reponse_normal')
                if urgence and normal and urgence >= normal:
                    raise ValueError('Le temps de réponse urgence doit être inférieur au temps normal')
        return v

    @field_validator('montant_mensuel', 'montant_annuel')
    @classmethod
    def validate_montants(cls, v, info):
        """Vérifie la cohérence des montants"""
        if v is not None and v <= 0:
            raise ValueError('Les montants doivent être positifs')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True,
        validate_assignment=True
    )


class ContratCreate(ContratBase):
    """
    Schéma pour la création d'un contrat.
    Nécessite l'ID du client.
    """
    client_id: int = Field(..., gt=0, description="ID du client")
    numero_contrat: Optional[str] = Field(None, max_length=50, description="Numéro de contrat (auto-généré si non fourni)")
    date_signature: Optional[date] = Field(None, description="Date de signature")

    @field_validator('client_id')
    @classmethod
    def validate_client_id(cls, v):
        """Validation de l'ID client"""
        if v <= 0:
            raise ValueError('L\'ID client doit être positif')
        return v


class ContratUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'un contrat.
    Tous les champs sont optionnels.
    """
    nom_contrat: Optional[str] = Field(None, min_length=2, max_length=255)
    description: Optional[str] = None
    type_contrat: Optional[TypeContrat] = None
    statut: Optional[StatutContrat] = None
    
    # Dates
    date_signature: Optional[date] = None
    date_debut: Optional[date] = None
    date_fin: Optional[date] = None
    date_renouvellement: Optional[date] = None
    
    # Conditions financières
    montant_annuel: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2)
    montant_mensuel: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    mode_facturation: Optional[ModePaiement] = None
    
    # SLA
    temps_reponse_urgence: Optional[int] = Field(None, ge=1, le=168)
    temps_reponse_normal: Optional[int] = Field(None, ge=1, le=720)
    taux_disponibilite: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    penalites_retard: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    
    # Limites
    nb_interventions_incluses: Optional[int] = Field(None, ge=0)
    heures_maintenance_incluses: Optional[int] = Field(None, ge=0)
    
    # Autres
    equipements_couverts: Optional[str] = None
    contact_client: Optional[str] = Field(None, max_length=255)
    contact_responsable: Optional[str] = Field(None, max_length=255)
    
    is_active: Optional[bool] = None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class ContratOut(ContratBase):
    """
    Schéma de sortie pour un contrat.
    Inclut les métadonnées et statistiques calculées.
    """
    id: int
    numero_contrat: str
    client_id: int
    statut: StatutContrat
    date_signature: Optional[date] = None
    
    # Utilisation
    nb_interventions_utilisees: int = 0
    heures_maintenance_utilisees: int = 0
    
    # État et métadonnées
    is_active: bool
    date_creation: datetime
    date_modification: Optional[datetime] = None
    
    # Propriétés calculées
    est_actif: bool
    est_expire: bool
    jours_restants: int
    pourcentage_interventions_utilisees: float
    pourcentage_heures_utilisees: float
    interventions_restantes: Optional[int] = None
    heures_restantes: Optional[int] = None

    model_config = ConfigDict(from_attributes=True)


class ContratSummary(BaseModel):
    """
    Schéma résumé pour un contrat.
    Version allégée pour les listes et sélections.
    """
    id: int
    numero_contrat: str
    nom_contrat: str
    type_contrat: TypeContrat
    statut: StatutContrat
    client_id: int
    date_debut: date
    date_fin: date
    est_actif: bool
    jours_restants: int
    montant_annuel: Optional[Decimal] = None

    model_config = ConfigDict(from_attributes=True)


class ContratStats(BaseModel):
    """
    Schéma pour les statistiques détaillées d'un contrat.
    """
    contrat_id: int
    numero_contrat: str
    nom_contrat: str
    
    # Statistiques d'utilisation
    total_interventions: int
    interventions_restantes: Optional[int] = None
    pourcentage_utilisation_interventions: float
    
    heures_utilisees: int
    heures_restantes: Optional[int] = None
    pourcentage_utilisation_heures: float
    
    # Performance SLA
    temps_reponse_moyen: Optional[float] = None
    taux_respect_sla: Optional[float] = None
    penalites_appliquees: Optional[Decimal] = None
    
    # Financier
    montant_facture_total: Optional[Decimal] = None
    montant_paye: Optional[Decimal] = None
    montant_en_attente: Optional[Decimal] = None
    
    # Satisfaction
    note_satisfaction: Optional[float] = None
    nb_reclamations: int = 0
    
    # Dates importantes
    derniere_intervention: Optional[datetime] = None
    prochaine_facture: Optional[date] = None
    
    model_config = ConfigDict(from_attributes=True)


class ContratSearch(BaseModel):
    """
    Schéma pour la recherche de contrats avec filtres.
    """
    query: Optional[str] = Field(None, description="Recherche textuelle (numéro, nom)")
    type_contrat: Optional[TypeContrat] = Field(None, description="Filtrer par type")
    statut: Optional[StatutContrat] = Field(None, description="Filtrer par statut")
    client_id: Optional[int] = Field(None, description="Filtrer par client")
    
    # Filtres temporels
    date_debut_min: Optional[date] = Field(None, description="Date de début minimum")
    date_debut_max: Optional[date] = Field(None, description="Date de début maximum")
    date_fin_min: Optional[date] = Field(None, description="Date de fin minimum")
    date_fin_max: Optional[date] = Field(None, description="Date de fin maximum")
    
    # Filtres financiers
    montant_min: Optional[Decimal] = Field(None, ge=0, description="Montant annuel minimum")
    montant_max: Optional[Decimal] = Field(None, ge=0, description="Montant annuel maximum")
    
    # Filtres d'état
    est_actif: Optional[bool] = Field(None, description="Filtrer par statut actif")
    expire_dans_jours: Optional[int] = Field(None, ge=0, description="Expire dans X jours")
    
    # Pagination et tri
    page: int = Field(1, ge=1, description="Numéro de page")
    limit: int = Field(20, ge=1, le=100, description="Nombre d'éléments par page")
    sort_by: Optional[str] = Field("date_creation", description="Champ de tri")
    sort_order: Optional[str] = Field("desc", pattern="^(asc|desc)$", description="Ordre de tri")

    model_config = ConfigDict(
        str_strip_whitespace=True
    )


# Schémas pour les factures

class StatutFacture(str, Enum):
    """Statuts d'une facture"""
    brouillon = "brouillon"
    emise = "emise"
    envoyee = "envoyee"
    payee = "payee"
    en_retard = "en_retard"
    annulee = "annulee"


class FactureBase(BaseModel):
    """
    Schéma de base pour une facture.
    """
    date_echeance: date = Field(..., description="Date d'échéance")
    montant_ht: Decimal = Field(..., ge=0, max_digits=10, decimal_places=2, description="Montant HT")
    taux_tva: Decimal = Field(20.0, ge=0, le=100, max_digits=5, decimal_places=2, description="Taux de TVA")
    description: Optional[str] = Field(None, description="Description de la facture")
    periode_debut: Optional[date] = Field(None, description="Début de période facturée")
    periode_fin: Optional[date] = Field(None, description="Fin de période facturée")

    @field_validator('montant_ht')
    @classmethod
    def validate_montant_ht(cls, v):
        """Vérifie que le montant HT est positif"""
        if v <= 0:
            raise ValueError('Le montant HT doit être positif')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class FactureCreate(FactureBase):
    """
    Schéma pour la création d'une facture.
    """
    contrat_id: int = Field(..., gt=0, description="ID du contrat")
    numero_facture: Optional[str] = Field(None, max_length=50, description="Numéro de facture (auto-généré si non fourni)")
    date_emission: Optional[date] = Field(None, description="Date d'émission (aujourd'hui si non fournie)")

    @field_validator('contrat_id')
    @classmethod
    def validate_contrat_id(cls, v):
        """Validation de l'ID contrat"""
        if v <= 0:
            raise ValueError('L\'ID contrat doit être positif')
        return v


class FactureUpdate(BaseModel):
    """
    Schéma pour la mise à jour d'une facture.
    """
    date_echeance: Optional[date] = None
    montant_ht: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2)
    taux_tva: Optional[Decimal] = Field(None, ge=0, le=100, max_digits=5, decimal_places=2)
    description: Optional[str] = None
    periode_debut: Optional[date] = None
    periode_fin: Optional[date] = None
    statut_paiement: Optional[StatutFacture] = None
    date_paiement: Optional[date] = None

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class FactureOut(FactureBase):
    """
    Schéma de sortie pour une facture.
    """
    id: int
    numero_facture: str
    contrat_id: int
    date_emission: date
    montant_ttc: Decimal
    statut_paiement: StatutFacture
    date_paiement: Optional[date] = None
    date_creation: datetime
    
    # Propriétés calculées
    est_en_retard: bool
    jours_retard: int

    model_config = ConfigDict(from_attributes=True)


class FactureSummary(BaseModel):
    """
    Schéma résumé pour une facture.
    """
    id: int
    numero_facture: str
    contrat_id: int
    date_emission: date
    date_echeance: date
    montant_ttc: Decimal
    statut_paiement: StatutFacture
    est_en_retard: bool

    model_config = ConfigDict(from_attributes=True)


class ContratRenouvellement(BaseModel):
    """
    Schéma pour le renouvellement d'un contrat.
    """
    nouvelle_date_fin: date = Field(..., description="Nouvelle date de fin")
    nouveau_montant_annuel: Optional[Decimal] = Field(None, ge=0, max_digits=12, decimal_places=2, description="Nouveau montant annuel")
    nouveau_montant_mensuel: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Nouveau montant mensuel")
    nouvelles_conditions: Optional[str] = Field(None, description="Nouvelles conditions spécifiques")
    
    # Réinitialiser les compteurs
    reset_interventions: bool = Field(True, description="Réinitialiser le compteur d'interventions")
    reset_heures: bool = Field(True, description="Réinitialiser le compteur d'heures")

    @field_validator('nouvelle_date_fin')
    @classmethod
    def validate_nouvelle_date_fin(cls, v):
        """Vérifie que la nouvelle date de fin est dans le futur"""
        if v <= date.today():
            raise ValueError('La nouvelle date de fin doit être dans le futur')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class ContratResiliation(BaseModel):
    """
    Schéma pour la résiliation d'un contrat.
    """
    date_resiliation: date = Field(..., description="Date de résiliation")
    motif: str = Field(..., min_length=10, max_length=500, description="Motif de résiliation")
    compensation: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Compensation financière")
    penalite: Optional[Decimal] = Field(None, ge=0, max_digits=10, decimal_places=2, description="Pénalité de résiliation")

    @field_validator('date_resiliation')
    @classmethod
    def validate_date_resiliation(cls, v):
        """Vérifie que la date de résiliation n'est pas dans le passé"""
        if v < date.today():
            raise ValueError('La date de résiliation ne peut pas être dans le passé')
        return v

    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )


class ContratAnalytics(BaseModel):
    """
    Schéma pour l'analyse avancée des contrats.
    """
    # Métriques générales
    total_contrats: int
    contrats_actifs: int
    contrats_expires: int
    contrats_bientot_expires: int  # Dans les 30 jours
    
    # Répartition par type
    repartition_types: dict[TypeContrat, int]
    repartition_statuts: dict[StatutContrat, int]
    
    # Métriques financières
    chiffre_affaires_total: Decimal
    chiffre_affaires_mois: Decimal
    montant_moyen_contrat: Decimal
    
    # Performance
    taux_renouvellement: float  # Pourcentage
    duree_moyenne_contrat: float  # En mois
    satisfaction_moyenne: Optional[float] = None
    
    # Tendances
    evolution_ca_mois: float  # Pourcentage d'évolution
    nouveaux_contrats_mois: int
    resiliations_mois: int
    
    # Top listes
    top_clients_ca: List[dict]
    contrats_les_plus_rentables: List[dict]
    
    # Alertes
    contrats_attention: int  # Contrats nécessitant une attention
    facturation_en_retard: int
    
    date_calcul: datetime

    model_config = ConfigDict(from_attributes=True)


class ContratValidation(BaseModel):
    """
    Schéma pour la validation des règles métier d'un contrat.
    """
    contrat_id: int
    is_valid: bool
    errors: List[str] = Field(default_factory=list)
    warnings: List[str] = Field(default_factory=list)
    
    # Vérifications spécifiques
    dates_coherentes: bool
    sla_defini: bool
    conditions_financieres_completes: bool
    client_actif: bool
    
    # Recommandations
    recommandations: List[str] = Field(default_factory=list)

    model_config = ConfigDict(from_attributes=True)


class ContratExport(BaseModel):
    """
    Schéma pour l'export de données de contrat.
    """
    format: str = Field("excel", description="Format d'export (excel, csv, pdf)")
    include_factures: bool = Field(True, description="Inclure les factures")
    include_interventions: bool = Field(True, description="Inclure les interventions")
    include_stats: bool = Field(True, description="Inclure les statistiques")
    date_debut: Optional[date] = Field(None, description="Filtrer à partir de cette date")
    date_fin: Optional[date] = Field(None, description="Filtrer jusqu'à cette date")

    model_config = ConfigDict(from_attributes=True)
