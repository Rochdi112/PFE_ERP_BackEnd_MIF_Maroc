# app/models/user.py
"""
Modèle User - Gestion des utilisateurs et authentification.

Ce module contient la gestion complète des utilisateurs du système ERP :
- Authentification et autorisation (JWT + RBAC)
- Rôles métier avec permissions granulaires
- Relations avec entités spécialisées (technicien, client)
- Audit et traçabilité des actions utilisateur
- Gestion des sessions et notifications

Architecture:
- Base SQLAlchemy avec contraintes d'intégrité
- Enum typé pour les rôles (extensible)
- Relations ORM optimisées avec cascade appropriée
- Propriétés calculées pour permissions métier
- Interface harmonisée to_dict() pour sérialisation
"""

from sqlalchemy import Column, Integer, String, Enum, Boolean, DateTime, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base
import enum
from typing import TYPE_CHECKING, Optional, Dict, Any

# NOTE: Import conditionnel pour éviter les imports circulaires
if TYPE_CHECKING:
    from .technicien import Technicien
    from .client import Client
    from .notification import Notification
    from .historique import HistoriqueIntervention
    from .stock import MouvementStock


class UserRole(str, enum.Enum):
    """
    Énumération des rôles utilisateur dans l'ERP.
    
    Hiérarchie des permissions (décroissante) :
    - admin : contrôle total du système, gestion utilisateurs
    - responsable : supervise interventions, équipes, planification
    - technicien : exécute interventions, saisie données terrain
    - client : consultation interventions, équipements personnels
    
    NOTE: Extensible pour futurs rôles (auditeur, manager, etc.)
    """
    admin = "admin"
    responsable = "responsable"
    technicien = "technicien"
    client = "client"


class User(Base):
    """
    Modèle Utilisateur - Authentification et autorisation centrale.
    
    Point d'entrée unique pour l'authentification système avec :
    - Gestion des identifiants et mots de passe (hachés)
    - Système RBAC avec rôles métier
    - Relations polymorphes selon rôle (technicien/client)
    - Audit complet des actions utilisateur
    - Notifications personnalisées et alertes
    - Sessions et gestion de l'activité
    
    Relations clés :
    - 1:1 avec Technicien (si rôle technicien)
    - 1:1 avec Client (si rôle client)
    - 1:N avec notifications, historiques, mouvements
    
    Performances :
    - Index composites sur email+active, username+role
    - Relations lazy=dynamic pour collections volumineuses
    - Propriétés calculées mises en cache côté application
    """
    __tablename__ = "users"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True

    # NOTE: Index composites pour optimiser les requêtes fréquentes
    __table_args__ = (
        Index('idx_user_email_active', 'email', 'is_active'),
        Index('idx_user_username_role', 'username', 'role'),
        Index('idx_user_role_active', 'role', 'is_active'),
        Index('idx_user_created_role', 'created_at', 'role'),
    )

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)

    # Informations d'identification
    username = Column(String(100), unique=True, index=True, nullable=False)
    full_name = Column(String(255), nullable=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)

    # Rôle et statut
    role = Column(Enum(UserRole), nullable=False, index=True)
    is_active = Column(Boolean, default=True, nullable=False, index=True)

    # Métadonnées temporelles
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    last_login = Column(DateTime, nullable=True)
    
    # Sécurité et sessions
    failed_login_attempts = Column(Integer, default=0, nullable=False)
    locked_until = Column(DateTime, nullable=True)
    password_changed_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    # 🔗 Relations ORM optimisées
    
    # Relations spécialisées selon rôle (1:1)
    technicien: Optional["Technicien"] = relationship(
        "Technicien", 
        uselist=False, 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"  # NOTE: Chargement immédiat pour relation 1:1
    )
    
    client: Optional["Client"] = relationship(
        "Client", 
        uselist=False, 
        back_populates="user",
        cascade="all, delete-orphan",
        lazy="select"
    )
    
    # Relations de traçabilité (1:N) - lazy dynamic pour performances
    notifications = relationship(
        "Notification", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic",
    order_by="desc(Notification.date_envoi)"
    )
    
    historiques = relationship(
        "HistoriqueIntervention", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(HistoriqueIntervention.horodatage)"
    )
    
    mouvements_stock = relationship(
        "MouvementStock", 
        back_populates="user", 
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(MouvementStock.date_mouvement)"
    )

    # Rapports générés par l'utilisateur (1:N)
    reports_created = relationship(
        "Report",
        back_populates="created_by",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    report_templates_created = relationship(
        "ReportTemplate",
        back_populates="created_by",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    report_schedules_created = relationship(
        "ReportSchedule",
        back_populates="created_by",
        lazy="dynamic",
        cascade="all, delete-orphan",
    )

    def __repr__(self) -> str:
        """Représentation concise pour debugging."""
        return f"<User(id={self.id}, username='{self.username}', role='{self.role.value}', active={self.is_active})>"

    # 🏷️ Propriétés métier pour RBAC et logique applicative
    
    @property
    def is_admin(self) -> bool:
        """Vérifie si l'utilisateur est administrateur système."""
        return self.role == UserRole.admin

    @property
    def is_responsable(self) -> bool:
        """Vérifie si l'utilisateur est responsable d'équipe."""
        return self.role == UserRole.responsable

    @property
    def is_technicien(self) -> bool:
        """Vérifie si l'utilisateur est technicien de terrain."""
        return self.role == UserRole.technicien

    @property
    def is_client(self) -> bool:
        """Vérifie si l'utilisateur est client externe."""
        return self.role == UserRole.client

    @property
    def is_staff(self) -> bool:
        """Vérifie si l'utilisateur fait partie du personnel interne."""
        return self.role in [UserRole.admin, UserRole.responsable, UserRole.technicien]

    @property
    def can_manage_users(self) -> bool:
        """Vérifie les permissions de gestion utilisateurs."""
        return self.role in [UserRole.admin]

    @property
    def can_manage_interventions(self) -> bool:
        """Vérifie les permissions de gestion interventions."""
        return self.role in [UserRole.admin, UserRole.responsable]

    @property
    def can_execute_interventions(self) -> bool:
        """Vérifie les permissions d'exécution interventions."""
        return self.role in [UserRole.admin, UserRole.responsable, UserRole.technicien]

    @property
    def can_manage_stock(self) -> bool:
        """Vérifie les permissions de gestion stock."""
        return self.role in [UserRole.admin, UserRole.responsable]

    @property
    def can_view_reports(self) -> bool:
        """Vérifie les permissions de consultation rapports."""
        return self.role in [UserRole.admin, UserRole.responsable]

    @property
    def display_name(self) -> str:
        """Nom d'affichage préféré pour l'interface."""
        return self.full_name.strip() if self.full_name.strip() else self.username

    @property
    def is_account_locked(self) -> bool:
        """Vérifie si le compte est temporairement verrouillé."""
        return (
            self.locked_until is not None and 
            self.locked_until > datetime.utcnow()
        )

    @property
    def password_needs_change(self) -> bool:
        """Vérifie si le mot de passe doit être changé (>90 jours)."""
        if not self.password_changed_at:
            return True
        age = datetime.utcnow() - self.password_changed_at
        return age > timedelta(days=90)

    @property
    def session_duration(self) -> Optional[timedelta]:
        """Calcule la durée de la session actuelle."""
        if not self.last_login:
            return None
        return datetime.utcnow() - self.last_login

    @property
    def notifications_non_lues(self) -> int:
        """Compte les notifications non lues (propriété calculée optimisée)."""
        return self.notifications.filter_by(lue=False).count()

    @property
    def derniere_activite(self) -> Optional[datetime]:
        """Retourne la date de dernière activité tracée."""
        dernier_historique = self.historiques.first()
        dernier_mouvement = self.mouvements_stock.first()
        
        dates = [
            self.last_login,
            dernier_historique.horodatage if dernier_historique else None,
            dernier_mouvement.date_mouvement if dernier_mouvement else None
        ]
        
        dates_valides = [d for d in dates if d is not None]
        return max(dates_valides) if dates_valides else self.created_at

    # 🔧 Méthodes métier et gestion de session
    
    def update_last_login(self) -> None:
        """Met à jour la date de dernière connexion et réinitialise les tentatives."""
        self.last_login = datetime.utcnow()
        self.failed_login_attempts = 0
        self.locked_until = None

    def increment_failed_login(self) -> None:
        """Incrémente les tentatives de connexion échouées et verrouille si nécessaire."""
        self.failed_login_attempts += 1
        
        # Verrouillage après 5 tentatives échouées
        if self.failed_login_attempts >= 5:
            self.locked_until = datetime.utcnow() + timedelta(minutes=30)

    def reset_password_age(self) -> None:
        """Marque le mot de passe comme récemment changé."""
        self.password_changed_at = datetime.utcnow()

    def unlock_account(self) -> None:
        """Déverrouille manuellement le compte (action admin)."""
        self.failed_login_attempts = 0
        self.locked_until = None

    def deactivate(self) -> None:
        """Désactive le compte utilisateur."""
        self.is_active = False
        self.updated_at = datetime.utcnow()

    def activate(self) -> None:
        """Réactive le compte utilisateur."""
        self.is_active = True
        self.failed_login_attempts = 0
        self.locked_until = None
        self.updated_at = datetime.utcnow()

    def peut_acceder_intervention(self, intervention_id: int) -> bool:
        """
        Vérifie si l'utilisateur peut accéder à une intervention spécifique.
        
        Args:
            intervention_id: ID de l'intervention à vérifier
            
        Returns:
            bool: True si accès autorisé
        """
        if self.is_admin or self.is_responsable:
            return True
            
        if self.is_technicien and self.technicien:
            # Technicien ne peut voir que ses interventions
            return any(
                interv.id == intervention_id 
                for interv in self.technicien.interventions
            )
            
        if self.is_client and self.client:
            # Client ne peut voir que ses interventions
            return any(
                interv.id == intervention_id 
                for interv in self.client.interventions
            )
            
        return False

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        """
        Sérialisation harmonisée en dictionnaire.
        
        Args:
            include_sensitive: Inclut données sensibles (admin uniquement)
            include_relations: Inclut les données des relations liées
            
        Returns:
            Dict contenant les données sérialisées
            
        NOTE: Interface standardisée pour tous les modèles ERP
        """
        # Données de base (toujours incluses)
        data = {
            "id": self.id,
            "username": self.username,
            "full_name": self.full_name,
            "email": self.email,
            "role": self.role.value,
            "is_active": self.is_active,
            "display_name": self.display_name,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "last_login": self.last_login.isoformat() if self.last_login else None,
            
            # Propriétés calculées utiles
            "is_staff": self.is_staff,
            "notifications_non_lues": self.notifications_non_lues,
            "derniere_activite": self.derniere_activite.isoformat() if self.derniere_activite else None,
        }
        
        # Données sensibles (admin/responsable uniquement)
        if include_sensitive:
            data.update({
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "failed_login_attempts": self.failed_login_attempts,
                "is_account_locked": self.is_account_locked,
                "locked_until": self.locked_until.isoformat() if self.locked_until else None,
                "password_needs_change": self.password_needs_change,
                "password_changed_at": self.password_changed_at.isoformat() if self.password_changed_at else None,
                "session_duration_minutes": int(self.session_duration.total_seconds() / 60) if self.session_duration else None,
                
                # Statistiques d'activité
                "nb_notifications": self.notifications.count(),
                "nb_historiques": self.historiques.count(),
                "nb_mouvements_stock": self.mouvements_stock.count(),
            })
        
        # Relations détaillées (pour vues complètes)
        if include_relations:
            data.update({
                "technicien": self.technicien.to_dict() if self.technicien else None,
                "client": self.client.to_dict() if self.client else None,
                
                # Permissions calculées
                "permissions": {
                    "can_manage_users": self.can_manage_users,
                    "can_manage_interventions": self.can_manage_interventions,
                    "can_execute_interventions": self.can_execute_interventions,
                    "can_manage_stock": self.can_manage_stock,
                    "can_view_reports": self.can_view_reports,
                }
            })
            
        return data