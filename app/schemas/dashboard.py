# app/schemas/dashboard.py

from pydantic import BaseModel, Field, ConfigDict
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class TimeRange(str, Enum):
    """Plages temporelles pour les statistiques"""
    jour = "jour"
    semaine = "semaine"
    mois = "mois"
    trimestre = "trimestre"
    annee = "annee"


class StatutSante(str, Enum):
    """Statuts de santé pour les équipements"""
    excellent = "excellent"
    bon = "bon"
    attention = "attention"
    critique = "critique"
    hors_service = "hors_service"


class KPIBase(BaseModel):
    """
    Schéma de base pour les indicateurs clés de performance (KPI).
    """
    # Interventions
    interventions_ouvertes: int = Field(0, description="Nombre d'interventions ouvertes")
    interventions_en_cours: int = Field(0, description="Nombre d'interventions en cours")
    interventions_en_retard: int = Field(0, description="Nombre d'interventions en retard")
    interventions_cloturees_mois: int = Field(0, description="Interventions clôturées ce mois")
    
    # Évolution
    evolution_interventions: float = Field(0.0, description="Évolution vs mois précédent (%)")
    
    # Performance
    temps_reponse_moyen: Optional[float] = Field(None, description="Temps de réponse moyen (heures)")
    taux_resolution_premier_passage: Optional[float] = Field(None, description="Taux de résolution au premier passage (%)")

    model_config = ConfigDict(from_attributes=True)


class KPIAdmin(KPIBase):
    """
    KPI étendus pour les administrateurs.
    Inclut les métriques de gestion et supervision.
    """
    # Utilisateurs
    nb_utilisateurs_actifs: int = Field(0, description="Nombre d'utilisateurs actifs")
    nb_techniciens_disponibles: int = Field(0, description="Nombre de techniciens disponibles")
    nb_clients_actifs: int = Field(0, description="Nombre de clients actifs")
    
    # Financier
    chiffre_affaires_mois: Optional[float] = Field(None, description="CA du mois en cours")
    cout_total_interventions: Optional[float] = Field(None, description="Coût total des interventions")
    marge_beneficiaire: Optional[float] = Field(None, description="Marge bénéficiaire (%)")
    
    # Qualité
    taux_satisfaction_client: Optional[float] = Field(None, description="Taux de satisfaction client (%)")
    nb_reclamations: int = Field(0, description="Nombre de réclamations")
    
    # Équipements
    nb_equipements_total: int = Field(0, description="Nombre total d'équipements")
    nb_equipements_critique: int = Field(0, description="Équipements en état critique")


class KPIResponsable(KPIBase):
    """
    KPI pour les responsables.
    Focus sur la gestion d'équipe et opérationnelle.
    """
    # Équipe
    nb_techniciens_equipe: int = Field(0, description="Nombre de techniciens dans l'équipe")
    charge_moyenne_techniciens: float = Field(0.0, description="Charge moyenne des techniciens (%)")
    
    # Planning
    interventions_planifiees_semaine: int = Field(0, description="Interventions planifiées cette semaine")
    conflits_planning: int = Field(0, description="Conflits de planning détectés")
    
    # Performance équipe
    productivite_equipe: Optional[float] = Field(None, description="Productivité de l'équipe")
    respect_delais: Optional[float] = Field(None, description="Taux de respect des délais (%)")


class KPITechnicien(BaseModel):
    """
    KPI personnalisés pour un technicien.
    """
    technicien_id: int
    
    # Interventions personnelles
    mes_interventions_ouvertes: int = Field(0, description="Mes interventions ouvertes")
    mes_interventions_en_cours: int = Field(0, description="Mes interventions en cours")
    mes_interventions_cloturees_mois: int = Field(0, description="Mes interventions clôturées ce mois")
    
    # Performance personnelle
    ma_charge_travail: float = Field(0.0, description="Ma charge de travail (%)")
    mon_temps_reponse_moyen: Optional[float] = Field(None, description="Mon temps de réponse moyen")
    ma_note_moyenne: Optional[float] = Field(None, description="Ma note moyenne de satisfaction")
    
    # Planning personnel
    prochaines_interventions: int = Field(0, description="Interventions prévues cette semaine")
    heures_travaillees_mois: Optional[float] = Field(None, description="Heures travaillées ce mois")
    
    model_config = ConfigDict(from_attributes=True)


class KPIClient(BaseModel):
    """
    KPI pour les clients.
    Vue sur leurs interventions et services.
    """
    client_id: int
    
    # Interventions client
    mes_interventions_ouvertes: int = Field(0, description="Mes interventions ouvertes")
    mes_interventions_en_cours: int = Field(0, description="Mes interventions en cours")
    mes_interventions_terminees_mois: int = Field(0, description="Interventions terminées ce mois")
    
    # Satisfaction
    mon_taux_satisfaction: Optional[float] = Field(None, description="Mon taux de satisfaction")
    temps_reponse_moyen_recu: Optional[float] = Field(None, description="Temps de réponse moyen reçu")
    
    # Contrats
    contrats_actifs: int = Field(0, description="Nombre de contrats actifs")
    interventions_incluses_restantes: Optional[int] = Field(None, description="Interventions restantes dans les contrats")
    
    model_config = ConfigDict(from_attributes=True)


class EquipementHealth(BaseModel):
    """
    Schéma pour l'état de santé d'un équipement.
    """
    equipement_id: int
    equipement_nom: str
    equipement_type: str
    localisation: str
    
    # Métriques de santé
    nb_pannes_mois: int = Field(0, description="Nombre de pannes ce mois")
    nb_interventions_total: int = Field(0, description="Nombre total d'interventions")
    
    # Maintenance
    derniere_maintenance: Optional[datetime] = Field(None, description="Date de dernière maintenance")
    prochaine_maintenance: Optional[datetime] = Field(None, description="Date de prochaine maintenance")
    jours_depuis_derniere_maintenance: Optional[int] = Field(None, description="Jours depuis dernière maintenance")
    
    # État calculé
    statut_sante: StatutSante = Field(StatutSante.bon, description="État de santé calculé")
    score_fiabilite: Optional[float] = Field(None, description="Score de fiabilité (0-100)")
    
    # Coûts
    cout_maintenance_mois: Optional[float] = Field(None, description="Coût maintenance ce mois")
    cout_total_maintenance: Optional[float] = Field(None, description="Coût total maintenance")
    
    # Temps d'arrêt
    temps_arret_mois: Optional[float] = Field(None, description="Temps d'arrêt ce mois (heures)")
    disponibilite: Optional[float] = Field(None, description="Taux de disponibilité (%)")

    model_config = ConfigDict(from_attributes=True)


class TechnicienWorkload(BaseModel):
    """
    Schéma pour la charge de travail d'un technicien.
    """
    technicien_id: int
    nom_complet: str
    equipe: Optional[str] = None
    
    # Charge de travail
    interventions_assignees: int = Field(0, description="Interventions assignées")
    interventions_en_cours: int = Field(0, description="Interventions en cours")
    interventions_planifiees_semaine: int = Field(0, description="Interventions planifiées cette semaine")
    
    # Pourcentages
    pourcentage_charge: float = Field(0.0, ge=0, le=100, description="Pourcentage de charge (0-100)")
    pourcentage_disponibilite: float = Field(100.0, ge=0, le=100, description="Pourcentage de disponibilité")
    
    # Compétences
    nb_competences: int = Field(0, description="Nombre de compétences")
    competences_principales: List[str] = Field(default_factory=list, description="Compétences principales")
    
    # Performance
    note_moyenne: Optional[float] = Field(None, description="Note moyenne de performance")
    temps_reponse_moyen: Optional[float] = Field(None, description="Temps de réponse moyen")
    
    # Statut
    disponibilite: str = Field("Disponible", description="Statut de disponibilité")
    derniere_intervention: Optional[datetime] = Field(None, description="Date de dernière intervention")

    model_config = ConfigDict(from_attributes=True)


class ChartData(BaseModel):
    """
    Schéma générique pour les données de graphiques.
    """
    labels: List[str] = Field(default_factory=list, description="Labels des données")
    datasets: List[Dict[str, Any]] = Field(default_factory=list, description="Jeux de données")
    type_chart: str = Field("line", description="Type de graphique (line, bar, pie, doughnut)")
    title: Optional[str] = Field(None, description="Titre du graphique")
    
    model_config = ConfigDict(from_attributes=True)


class InterventionTrend(BaseModel):
    """
    Schéma pour les tendances d'interventions.
    """
    periode: str = Field(..., description="Période (YYYY-MM ou YYYY-MM-DD)")
    nb_interventions: int = Field(0, description="Nombre d'interventions")
    nb_correctives: int = Field(0, description="Interventions correctives")
    nb_preventives: int = Field(0, description="Interventions préventives")
    temps_reponse_moyen: Optional[float] = Field(None, description="Temps de réponse moyen")
    cout_total: Optional[float] = Field(None, description="Coût total")
    
    model_config = ConfigDict(from_attributes=True)


class AlerteTableauBord(BaseModel):
    """
    Schéma pour les alertes du tableau de bord.
    """
    id: str = Field(..., description="ID unique de l'alerte")
    type_alerte: str = Field(..., description="Type d'alerte (equipement, intervention, stock, etc.)")
    niveau: str = Field(..., description="Niveau (info, warning, error, critical)")
    titre: str = Field(..., description="Titre de l'alerte")
    message: str = Field(..., description="Message détaillé")
    
    # Données liées
    entite_id: Optional[int] = Field(None, description="ID de l'entité concernée")
    entite_type: Optional[str] = Field(None, description="Type d'entité (equipement, intervention, etc.)")
    
    # Actions
    action_url: Optional[str] = Field(None, description="URL d'action pour résoudre l'alerte")
    action_label: Optional[str] = Field(None, description="Label du bouton d'action")
    
    # Métadonnées
    date_creation: datetime = Field(default_factory=datetime.utcnow, description="Date de création")
    est_lue: bool = Field(False, description="Alerte lue ou non")
    
    model_config = ConfigDict(from_attributes=True)


class DashboardResponse(BaseModel):
    """
    Schéma principal de réponse du tableau de bord.
    Adapté selon le rôle de l'utilisateur.
    """
    user_role: str = Field(..., description="Rôle de l'utilisateur")
    
    # KPIs selon le rôle
    kpis: Dict[str, Any] = Field(default_factory=dict, description="KPIs selon le rôle")
    
    # Données principales
    equipements_sante: List[EquipementHealth] = Field(default_factory=list, description="État de santé des équipements")
    techniciens_charge: List[TechnicienWorkload] = Field(default_factory=list, description="Charge de travail des techniciens")
    
    # Tendances et graphiques
    tendances_interventions: List[InterventionTrend] = Field(default_factory=list, description="Tendances des interventions")
    graphiques: List[ChartData] = Field(default_factory=list, description="Données des graphiques")
    
    # Alertes
    alertes: List[AlerteTableauBord] = Field(default_factory=list, description="Alertes actives")
    nb_alertes_non_lues: int = Field(0, description="Nombre d'alertes non lues")
    
    # Métadonnées
    derniere_maj: datetime = Field(default_factory=datetime.utcnow, description="Dernière mise à jour")
    periode_analyse: str = Field("mois", description="Période d'analyse des données")
    
    model_config = ConfigDict(from_attributes=True)


class DashboardFilters(BaseModel):
    """
    Schéma pour les filtres du tableau de bord.
    """
    periode: TimeRange = Field(TimeRange.mois, description="Période d'analyse")
    date_debut: Optional[datetime] = Field(None, description="Date de début personnalisée")
    date_fin: Optional[datetime] = Field(None, description="Date de fin personnalisée")
    
    # Filtres spécifiques
    equipement_ids: Optional[List[int]] = Field(None, description="IDs des équipements à inclure")
    technicien_ids: Optional[List[int]] = Field(None, description="IDs des techniciens à inclure")
    client_ids: Optional[List[int]] = Field(None, description="IDs des clients à inclure")
    
    # Types d'interventions
    types_intervention: Optional[List[str]] = Field(None, description="Types d'intervention à inclure")
    statuts_intervention: Optional[List[str]] = Field(None, description="Statuts d'intervention à inclure")
    
    # Options d'affichage
    inclure_graphiques: bool = Field(True, description="Inclure les données des graphiques")
    inclure_alertes: bool = Field(True, description="Inclure les alertes")
    inclure_tendances: bool = Field(True, description="Inclure les tendances")
    
    model_config = ConfigDict(
        from_attributes=True,
        str_strip_whitespace=True
    )