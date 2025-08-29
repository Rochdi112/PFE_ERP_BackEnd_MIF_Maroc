"""
Schémas Pydantic pour la génération de rapports
"""
from datetime import datetime, date
from typing import List, Optional, Dict, Any, Union
from pydantic import BaseModel, ConfigDict, Field
from enum import Enum

from app.schemas.intervention import InterventionOut
from app.schemas.equipement import EquipementOut
from app.schemas.technicien import TechnicienOut
from app.schemas.client import ClientOut


class ReportFormat(str, Enum):
    """Format de rapport disponible"""
    PDF = "pdf"
    EXCEL = "excel"
    CSV = "csv"
    JSON = "json"


class ReportType(str, Enum):
    """Types de rapports disponibles"""
    INTERVENTIONS = "interventions"
    EQUIPEMENTS = "equipements"
    TECHNICIENS = "techniciens"
    CLIENTS = "clients"
    DASHBOARD = "dashboard"
    PLANNING = "planning"
    STOCK = "stock"
    FINANCIAL = "financial"


class ReportPeriod(str, Enum):
    """Périodes prédéfinies pour les rapports"""
    TODAY = "today"
    YESTERDAY = "yesterday"
    LAST_7_DAYS = "last_7_days"
    LAST_30_DAYS = "last_30_days"
    THIS_MONTH = "this_month"
    LAST_MONTH = "last_month"
    THIS_QUARTER = "this_quarter"
    THIS_YEAR = "this_year"
    CUSTOM = "custom"


class ReportFilters(BaseModel):
    """Filtres pour la génération de rapports"""
    model_config = ConfigDict(from_attributes=True)
    
    # Filtres temporels
    date_debut: Optional[date] = Field(None, description="Date de début")
    date_fin: Optional[date] = Field(None, description="Date de fin")
    period: Optional[ReportPeriod] = Field(ReportPeriod.LAST_30_DAYS, description="Période prédéfinie")
    
    # Filtres par entités
    client_ids: Optional[List[int]] = Field(None, description="IDs des clients")
    technicien_ids: Optional[List[int]] = Field(None, description="IDs des techniciens")
    equipement_ids: Optional[List[int]] = Field(None, description="IDs des équipements")
    
    # Filtres métier
    statuts: Optional[List[str]] = Field(None, description="Statuts à inclure")
    types: Optional[List[str]] = Field(None, description="Types à inclure")
    priorites: Optional[List[int]] = Field(None, description="Priorités à inclure")
    
    # Options d'export
    include_details: bool = Field(True, description="Inclure les détails")
    include_charts: bool = Field(True, description="Inclure les graphiques")
    group_by: Optional[str] = Field(None, description="Grouper par champ")


class ReportRequest(BaseModel):
    """Requête de génération de rapport"""
    model_config = ConfigDict(from_attributes=True)
    
    type: ReportType = Field(..., description="Type de rapport")
    format: ReportFormat = Field(ReportFormat.PDF, description="Format de sortie")
    title: Optional[str] = Field(None, description="Titre personnalisé")
    description: Optional[str] = Field(None, description="Description du rapport")
    filters: Optional[ReportFilters] = Field(default_factory=ReportFilters, description="Filtres appliqués")
    
    # Options avancées
    template_id: Optional[int] = Field(None, description="ID du template personnalisé")
    language: str = Field("fr", description="Langue du rapport")
    send_email: bool = Field(False, description="Envoyer par email")
    email_recipients: Optional[List[str]] = Field(None, description="Destinataires email")


class ReportMetadata(BaseModel):
    """Métadonnées d'un rapport généré"""
    model_config = ConfigDict(from_attributes=True)
    
    id: int
    title: str
    type: ReportType
    format: ReportFormat
    file_path: str
    file_size: int
    created_at: datetime
    created_by_id: int
    expires_at: Optional[datetime] = Field(None, description="Date d'expiration")
    download_count: int = Field(0, description="Nombre de téléchargements")
    is_public: bool = Field(False, description="Rapport public")


class ReportData(BaseModel):
    """Données structurées d'un rapport"""
    model_config = ConfigDict(from_attributes=True)
    
    # Métadonnées
    title: str
    subtitle: Optional[str] = None
    generated_at: datetime
    period: str
    filters_applied: Dict[str, Any]
    
    # Données principales
    summary: Dict[str, Any]
    data: List[Dict[str, Any]]
    totals: Dict[str, Union[int, float]]
    
    # Statistiques
    count: int
    charts: Optional[List[Dict[str, Any]]] = None
    
    # Options d'affichage
    columns: List[Dict[str, str]]
    formatting: Dict[str, Any]


class InterventionReportData(ReportData):
    """Rapport spécialisé pour les interventions"""
    interventions: List[InterventionOut]
    stats_by_status: Dict[str, int]
    stats_by_type: Dict[str, int]
    stats_by_priority: Dict[str, int]
    average_duration: Optional[float] = None
    top_equipements: List[Dict[str, Any]]
    top_techniciens: List[Dict[str, Any]]


class EquipementReportData(ReportData):
    """Rapport spécialisé pour les équipements"""
    equipements: List[EquipementOut]
    stats_by_type: Dict[str, int]
    maintenance_schedule: List[Dict[str, Any]]
    breakdown_frequency: Dict[str, int]
    availability_rate: float
    mtbf: Optional[float] = None  # Mean Time Between Failures
    mttr: Optional[float] = None  # Mean Time To Repair


class TechnicienReportData(ReportData):
    """Rapport spécialisé pour les techniciens"""
    techniciens: List[TechnicienOut]
    workload_by_technicien: Dict[str, Dict[str, Any]]
    performance_metrics: Dict[str, float]
    competences_distribution: Dict[str, int]
    availability_schedule: List[Dict[str, Any]]


class ClientReportData(ReportData):
    """Rapport spécialisé pour les clients"""
    clients: List[ClientOut]
    revenue_by_client: Dict[str, float]
    interventions_by_client: Dict[str, int]
    satisfaction_scores: Dict[str, float]
    contract_renewals: List[Dict[str, Any]]


class DashboardReportData(ReportData):
    """Rapport tableau de bord global"""
    kpi_summary: Dict[str, Union[int, float]]
    trends: Dict[str, List[Dict[str, Any]]]
    alerts: List[Dict[str, Any]]
    performance_indicators: Dict[str, float]
    charts_data: List[Dict[str, Any]]


class ReportOut(BaseModel):
    """Schéma de sortie pour un rapport"""
    model_config = ConfigDict(from_attributes=True)
    
    metadata: ReportMetadata
    data: Optional[ReportData] = None
    download_url: str
    preview_url: Optional[str] = None
    
    
class ReportList(BaseModel):
    """Liste paginée de rapports"""
    model_config = ConfigDict(from_attributes=True)
    
    reports: List[ReportMetadata]
    total: int
    page: int
    per_page: int
    has_next: bool
    has_prev: bool


class ReportTemplate(BaseModel):
    """Template de rapport personnalisé"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    name: str
    type: ReportType
    template_content: str  # HTML/Jinja2 template
    css_styles: Optional[str] = None
    default_filters: Optional[ReportFilters] = None
    is_active: bool = True
    created_by_id: int
    created_at: Optional[datetime] = None


class ReportSchedule(BaseModel):
    """Planification automatique de rapports"""
    model_config = ConfigDict(from_attributes=True)
    
    id: Optional[int] = None
    name: str
    report_request: ReportRequest
    cron_expression: str  # Expression cron pour la planification
    email_recipients: List[str]
    is_active: bool = True
    last_run: Optional[datetime] = None
    next_run: Optional[datetime] = None
    created_by_id: int


# Schémas pour l'API
class ReportCreate(BaseModel):
    """Création de rapport via API"""
    model_config = ConfigDict(from_attributes=True)
    
    request: ReportRequest


class ReportResponse(BaseModel):
    """Réponse de génération de rapport"""
    model_config = ConfigDict(from_attributes=True)
    
    success: bool
    message: str
    report_id: Optional[int] = None
    download_url: Optional[str] = None
    estimated_time: Optional[int] = None  # en secondes


class ReportError(BaseModel):
    """Erreur de génération de rapport"""
    model_config = ConfigDict(from_attributes=True)
    
    error_code: str
    error_message: str
    details: Optional[Dict[str, Any]] = None
    timestamp: datetime