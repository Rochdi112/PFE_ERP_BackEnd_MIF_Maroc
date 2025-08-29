"""
Modèles SQLAlchemy pour la génération et gestion de rapports
"""
from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Text, JSON, BigInteger, Numeric, Enum
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base
import enum
import uuid
from typing import Optional


class ReportStatus(str, enum.Enum):
    """Statuts d'un rapport"""
    pending = "pending"
    generating = "generating"
    completed = "completed"
    failed = "failed"
    expired = "expired"


class ReportType(str, enum.Enum):
    """Types de rapports"""
    interventions = "interventions"
    equipements = "equipements"
    techniciens = "techniciens"
    clients = "clients"
    dashboard = "dashboard"
    planning = "planning"
    stock = "stock"
    financial = "financial"


class ReportFormat(str, enum.Enum):
    """Formats de rapport"""
    pdf = "pdf"
    excel = "excel"
    csv = "csv"
    json = "json"



class Report(Base):
    """
    Modèle Report pour la sauvegarde et traçabilité des rapports générés.
    - Sauvegarde, permissions, planification, audit, extension future
    """
    __tablename__ = "reports"
    __table_args__ = (
        # Index combinés pour recherche rapide
        # Index('idx_report_type_status', 'report_type', 'status'),
    )

    id: int = Column(Integer, primary_key=True, index=True)
    title: str = Column(String(255), nullable=False, index=True)
    description: str = Column(Text, nullable=True)
    report_type: ReportType = Column(Enum(ReportType), nullable=False, index=True)
    report_format: ReportFormat = Column(Enum(ReportFormat), nullable=False, index=True)
    status: ReportStatus = Column(Enum(ReportStatus), default=ReportStatus.pending, nullable=False, index=True)
    date_creation: datetime = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    date_generation_start: datetime = Column(DateTime, nullable=True)
    date_generation_end: datetime = Column(DateTime, nullable=True)
    date_expiration: datetime = Column(DateTime, nullable=True, index=True)
    last_downloaded_at: datetime = Column(DateTime, nullable=True)
    file_path: str = Column(String(500), nullable=True)
    file_name: str = Column(String(255), nullable=True)
    file_size: int = Column(BigInteger, nullable=True)
    mime_type: str = Column(String(100), nullable=True)
    filters_json: dict = Column(JSON, nullable=True)
    parameters: dict = Column(JSON, nullable=True)
    is_public: bool = Column(Boolean, default=False, nullable=False)
    is_downloadable: bool = Column(Boolean, default=True, nullable=False)
    access_token: str = Column(String(255), nullable=True, unique=True, index=True)
    download_count: int = Column(Integer, default=0, nullable=False)
    max_downloads: int = Column(Integer, nullable=True)
    generation_duration: int = Column(Integer, nullable=True)
    error_message: str = Column(Text, nullable=True)
    template_id: int = Column(Integer, ForeignKey("report_templates.id"), nullable=True)
    created_by_id: int = Column(Integer, ForeignKey("users.id"), nullable=False, index=True)
    created_by = relationship("User", back_populates="reports_created")
    template = relationship("ReportTemplate", back_populates="reports")

    @property
    def is_ready(self) -> bool:
        """Vérifie si le rapport est prêt à être téléchargé"""
        return self.status == ReportStatus.completed and self.file_path is not None

    @property
    def is_expired(self) -> bool:
        """Vérifie si le rapport a expiré"""
        if self.date_expiration:
            return datetime.utcnow() > self.date_expiration
        return False

    @property
    def file_size_mb(self) -> float:
        """Retourne la taille du fichier en MB"""
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0.0

    @property
    def can_download(self) -> bool:
        """Vérifie si le rapport peut être téléchargé"""
        return (
            self.is_ready and 
            not self.is_expired and 
            self.is_downloadable and
            (self.max_downloads is None or self.download_count < self.max_downloads)
        )

    @property
    def download_url(self) -> Optional[str]:
        """Génère l'URL de téléchargement"""
        if self.can_download:
            if self.access_token:
                return f"/api/v1/reports/{self.id}/download?token={self.access_token}"
            else:
                return f"/api/v1/reports/{self.id}/download"
        return None

    @property
    def generation_duration_formatted(self) -> Optional[str]:
        """Retourne la durée de génération formatée"""
        if self.generation_duration:
            if self.generation_duration < 60:
                return f"{self.generation_duration}s"
            else:
                minutes = self.generation_duration // 60
                seconds = self.generation_duration % 60
                return f"{minutes}m {seconds}s"
        return None

    def start_generation(self) -> None:
        """Marque le début de la génération"""
        self.status = "generating"
        self.date_generation_start = datetime.utcnow()
        self.error_message = None

    def complete_generation(self, file_path: str, file_size: int = None) -> None:
        """Marque la fin de la génération avec succès"""
        self.status = "completed"
        self.date_generation_end = datetime.utcnow()
        self.file_path = file_path
        if file_size:
            self.file_size = file_size
            
        # Calcul de la durée de génération
        if self.date_generation_start:
            duration = self.date_generation_end - self.date_generation_start
            self.generation_duration = int(duration.total_seconds())

    def fail_generation(self, error_message: str) -> None:
        """Marque l'échec de la génération"""
        self.status = "failed"
        self.date_generation_end = datetime.utcnow()
        self.error_message = error_message

    def increment_download(self) -> None:
        """Incrémente le compteur de téléchargement"""
        self.download_count += 1
        self.last_downloaded_at = datetime.utcnow()

    def extend_expiration(self, days: int = 7) -> None:
        """Prolonge la date d'expiration"""
        if self.date_expiration:
            self.date_expiration += timedelta(days=days)
        else:
            self.date_expiration = datetime.utcnow() + timedelta(days=days)

    def generate_access_token(self) -> str:
        """Génère un token d'accès unique"""
        self.access_token = str(uuid.uuid4())
        return self.access_token

    def __repr__(self) -> str:
        return f"<Report(id={self.id}, title='{self.title}', type='{self.report_type.value}', status='{self.status.value}')>"

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> dict:
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "report_type": self.report_type.value,
            "report_format": self.report_format.value,
            "status": self.status.value,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "date_generation_start": self.date_generation_start.isoformat() if self.date_generation_start else None,
            "date_generation_end": self.date_generation_end.isoformat() if self.date_generation_end else None,
            "date_expiration": self.date_expiration.isoformat() if self.date_expiration else None,
            "file_name": self.file_name,
            "file_size": self.file_size,
            "file_size_mb": self.file_size_mb,
            "mime_type": self.mime_type,
            "is_public": self.is_public,
            "is_downloadable": self.is_downloadable,
            "download_count": self.download_count,
            "max_downloads": self.max_downloads,
            "is_ready": self.is_ready,
            "is_expired": self.is_expired,
            "can_download": self.can_download,
            "generation_duration": self.generation_duration,
            "generation_duration_formatted": self.generation_duration_formatted,
            "created_by_id": self.created_by_id
        }
        if include_sensitive:
            data.update({
                "file_path": self.file_path,
                "access_token": self.access_token,
                "filters_json": self.filters_json,
                "parameters": self.parameters,
                "error_message": self.error_message,
                "download_url": self.download_url
            })
        if include_relations:
            data.update({
                "created_by": self.created_by.to_dict() if self.created_by else None,
                "template": self.template.to_dict() if self.template else None
            })
        return data


class ReportTemplate(Base):
    """
    Modèle ReportTemplate pour les templates de rapports personnalisés.
    
    Permet de :
    - Créer des templates réutilisables pour différents types de rapports
    - Personnaliser la mise en forme et le contenu
    - Définir des filtres par défaut
    """
    __tablename__ = "report_templates"

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)

    # Informations de base
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    report_type = Column(String(50), nullable=False, index=True)
    
    # Contenu du template
    template_content = Column(Text, nullable=False)  # HTML/Jinja2 template
    css_styles = Column(Text, nullable=True)
    
    # Configuration
    default_filters = Column(JSON, nullable=True)
    default_parameters = Column(JSON, nullable=True)
    
    # Métadonnées
    is_active = Column(Boolean, default=True, nullable=False)
    is_system = Column(Boolean, default=False, nullable=False)  # Template système non modifiable
    version = Column(String(20), default="1.0", nullable=False)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relations
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_by = relationship("User", back_populates="report_templates_created")
    reports = relationship("Report", back_populates="template", cascade="all, delete-orphan")

    @property
    def usage_count(self):
        """Nombre de rapports générés avec ce template"""
        return len(self.reports)

    @property
    def last_used(self):
        """Date de dernière utilisation"""
        if self.reports:
            return max(report.date_creation for report in self.reports)
        return None

    def clone(self, new_name: str, created_by_id: int):
        """Clone le template avec un nouveau nom"""
        return ReportTemplate(
            name=new_name,
            description=f"Clone de {self.name}",
            report_type=self.report_type,
            template_content=self.template_content,
            css_styles=self.css_styles,
            default_filters=self.default_filters,
            default_parameters=self.default_parameters,
            created_by_id=created_by_id
        )

    def __repr__(self):
        return f"<ReportTemplate(id={self.id}, name='{self.name}', type='{self.report_type}')>"

    def to_dict(self, include_sensitive=False, include_relations=False):
        """Sérialisation en dictionnaire"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "report_type": self.report_type,
            "is_active": self.is_active,
            "is_system": self.is_system,
            "version": self.version,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "usage_count": self.usage_count,
            "last_used": self.last_used.isoformat() if self.last_used else None,
            "created_by_id": self.created_by_id
        }

        if include_sensitive:
            data.update({
                "template_content": self.template_content,
                "css_styles": self.css_styles,
                "default_filters": self.default_filters,
                "default_parameters": self.default_parameters
            })

        if include_relations:
            data.update({
                "created_by": self.created_by.to_dict() if self.created_by else None
            })

        return data


class ReportSchedule(Base):
    """
    Modèle ReportSchedule pour la planification automatique de rapports.
    
    Permet de :
    - Programmer des rapports récurrents (quotidiens, hebdomadaires, mensuels)
    - Envoyer automatiquement par email
    - Garder un historique des exécutions
    """
    __tablename__ = "report_schedules"

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)

    # Configuration
    name = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    
    # Configuration du rapport à générer
    report_type = Column(String(50), nullable=False, index=True)
    report_format = Column(String(10), nullable=False)
    report_title_template = Column(String(255), nullable=True)  # Template avec variables
    
    # Planification (expression cron)
    cron_expression = Column(String(100), nullable=False)  # Ex: "0 9 * * 1" pour tous les lundis à 9h
    timezone = Column(String(50), default="UTC", nullable=False)
    
    # Configuration des filtres et paramètres
    filters_json = Column(JSON, nullable=True)
    parameters_json = Column(JSON, nullable=True)
    
    # Configuration email
    email_enabled = Column(Boolean, default=True, nullable=False)
    email_recipients = Column(JSON, nullable=False)  # Liste des emails
    email_subject_template = Column(String(255), nullable=True)
    email_body_template = Column(Text, nullable=True)
    
    # Statut et métadonnées
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    last_run_at = Column(DateTime, nullable=True, index=True)
    next_run_at = Column(DateTime, nullable=True, index=True)
    run_count = Column(Integer, default=0, nullable=False)
    success_count = Column(Integer, default=0, nullable=False)
    error_count = Column(Integer, default=0, nullable=False)
    last_error_message = Column(Text, nullable=True)
    
    # Dates
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    # Relations
    created_by_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    template_id = Column(Integer, ForeignKey("report_templates.id"), nullable=True)
    created_by = relationship("User", back_populates="report_schedules_created")
    template = relationship("ReportTemplate")

    @property
    def success_rate(self):
        """Taux de succès des exécutions"""
        if self.run_count == 0:
            return 0.0
        return round((self.success_count / self.run_count) * 100, 2)

    @property
    def is_due(self):
        """Vérifie si la planification est due pour exécution"""
        if not self.is_active or not self.next_run_at:
            return False
        return datetime.utcnow() >= self.next_run_at

    @property
    def last_run_status(self):
        """Statut de la dernière exécution"""
        if self.run_count == 0:
            return "never_run"
        elif self.last_error_message:
            return "failed"
        else:
            return "success"

    def record_run_start(self):
        """Enregistre le début d'une exécution"""
        self.last_run_at = datetime.utcnow()
        self.run_count += 1
        self.last_error_message = None

    def record_run_success(self, next_run_at: datetime = None):
        """Enregistre le succès d'une exécution"""
        self.success_count += 1
        if next_run_at:
            self.next_run_at = next_run_at

    def record_run_error(self, error_message: str, next_run_at: datetime = None):
        """Enregistre l'échec d'une exécution"""
        self.error_count += 1
        self.last_error_message = error_message
        if next_run_at:
            self.next_run_at = next_run_at

    def get_report_title(self, **variables):
        """Génère le titre du rapport avec les variables"""
        if self.report_title_template:
            try:
                return self.report_title_template.format(**variables)
            except:
                return self.report_title_template
        return f"{self.name} - {datetime.now().strftime('%Y-%m-%d')}"

    def get_email_subject(self, **variables):
        """Génère le sujet de l'email avec les variables"""
        if self.email_subject_template:
            try:
                return self.email_subject_template.format(**variables)
            except:
                return self.email_subject_template
        return f"Rapport automatique : {self.name}"

    def __repr__(self):
        return f"<ReportSchedule(id={self.id}, name='{self.name}', active={self.is_active})>"

    def to_dict(self, include_sensitive=False, include_relations=False):
        """Sérialisation en dictionnaire"""
        data = {
            "id": self.id,
            "name": self.name,
            "description": self.description,
            "report_type": self.report_type,
            "report_format": self.report_format,
            "cron_expression": self.cron_expression,
            "timezone": self.timezone,
            "is_active": self.is_active,
            "last_run_at": self.last_run_at.isoformat() if self.last_run_at else None,
            "next_run_at": self.next_run_at.isoformat() if self.next_run_at else None,
            "success_rate": self.success_rate,
            "run_count": self.run_count,
            "success_count": self.success_count,
            "error_count": self.error_count,
            "last_run_status": self.last_run_status,
            "email_enabled": self.email_enabled,
            "is_due": self.is_due,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "created_by_id": self.created_by_id
        }

        if include_sensitive:
            data.update({
                "filters_json": self.filters_json,
                "parameters_json": self.parameters_json,
                "email_recipients": self.email_recipients,
                "email_subject_template": self.email_subject_template,
                "email_body_template": self.email_body_template,
                "report_title_template": self.report_title_template,
                "last_error_message": self.last_error_message
            })

        if include_relations:
            data.update({
                "created_by": self.created_by.to_dict() if self.created_by else None,
                "template": self.template.to_dict() if self.template else None
            })

        return data


# Mise à jour du modèle User pour ajouter les relations avec les rapports
def update_user_model():
    """
    Fonction pour mettre à jour le modèle User avec les relations reports.
    À appeler après l'import du modèle User.
    """
    from app.models.user import User
    
    # Ajout des relations dans le modèle User
    User.reports_created = relationship("Report", back_populates="created_by")
    User.report_templates_created = relationship("ReportTemplate", back_populates="created_by")
    User.report_schedules_created = relationship("ReportSchedule", back_populates="created_by")