# app/core/audit.py

"""
Service d'audit et de logging sécurisé pour traçabilité Go-Prod.
Enregistre les événements critiques de sécurité avec corrélation.
"""

from datetime import datetime
from typing import Any, Dict, Optional

from app.core.logging import get_logger

logger = get_logger(__name__)


class AuditEventType:
    """Types d'événements d'audit de sécurité."""
    
    # Authentification
    LOGIN_SUCCESS = "auth.login.success"
    LOGIN_FAILED = "auth.login.failed"
    LOGIN_BRUTEFORCE = "auth.login.bruteforce"
    
    # Tokens
    TOKEN_CREATED = "auth.token.created"
    TOKEN_REFRESHED = "auth.token.refreshed"
    TOKEN_REVOKED = "auth.token.revoked"
    TOKEN_INVALID = "auth.token.invalid"
    
    # Mot de passe
    PASSWORD_CHANGED = "auth.password.changed"
    PASSWORD_RESET = "auth.password.reset"
    PASSWORD_POLICY_VIOLATION = "auth.password.policy_violation"
    
    # Accès aux documents
    DOCUMENT_ACCESSED = "doc.accessed"
    DOCUMENT_UPLOADED = "doc.uploaded"
    DOCUMENT_DELETED = "doc.deleted"
    DOCUMENT_ENCRYPTION_FAILED = "doc.encryption.failed"
    
    # Accès privilégiés
    ADMIN_ACTION = "admin.action"
    RBAC_VIOLATION = "rbac.violation"
    
    # Système
    CONFIG_CHANGED = "system.config.changed"
    KEY_ROTATION = "system.key.rotation"
    
    # Sécurité
    SECURITY_ALERT = "security.alert"
    RATE_LIMIT_EXCEEDED = "security.rate_limit.exceeded"


class AuditLogger:
    """Logger d'audit sécurisé avec corrélation des événements."""
    
    def __init__(self):
        self.logger = get_logger("audit")
    
    def log_event(
        self,
        event_type: str,
        user_id: Optional[int] = None,
        user_email: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None,
        resource: Optional[str] = None,
        action: Optional[str] = None,
        success: bool = True,
        details: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """
        Enregistre un événement d'audit sécurisé.
        
        Args:
            event_type: Type d'événement (utiliser AuditEventType)
            user_id: ID utilisateur concerné
            user_email: Email utilisateur
            request_id: ID de corrélation de la requête
            ip_address: Adresse IP source
            user_agent: User-Agent du client
            resource: Ressource concernée
            action: Action effectuée
            success: Succès/échec de l'opération
            details: Détails supplémentaires
            **kwargs: Autres métadonnées
        """
        
        audit_data = {
            "audit_event": event_type,
            "timestamp": datetime.utcnow().isoformat(),
            "success": success,
        }
        
        # Informations utilisateur
        if user_id:
            audit_data["user_id"] = user_id
        if user_email:
            audit_data["user_email"] = user_email
        
        # Informations de requête
        if request_id:
            audit_data["request_id"] = request_id
        if ip_address:
            audit_data["ip_address"] = ip_address
        if user_agent:
            audit_data["user_agent"] = user_agent
        
        # Informations de ressource
        if resource:
            audit_data["resource"] = resource
        if action:
            audit_data["action"] = action
        
        # Détails supplémentaires
        if details:
            audit_data["details"] = details
        
        # Métadonnées additionnelles
        audit_data.update(kwargs)
        
        # Log avec le niveau approprié
        level = "WARNING" if not success else "INFO"
        
        if level == "WARNING":
            self.logger.warning(
                f"Audit: {event_type}",
                extra={"extra_fields": audit_data}
            )
        else:
            self.logger.info(
                f"Audit: {event_type}",
                extra={"extra_fields": audit_data}
            )
    
    def log_login_success(
        self,
        user_id: int,
        user_email: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log une connexion réussie."""
        self.log_event(
            AuditEventType.LOGIN_SUCCESS,
            user_id=user_id,
            user_email=user_email,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login"
        )
    
    def log_login_failed(
        self,
        user_email: str,
        reason: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ):
        """Log une tentative de connexion échouée."""
        self.log_event(
            AuditEventType.LOGIN_FAILED,
            user_email=user_email,
            request_id=request_id,
            ip_address=ip_address,
            user_agent=user_agent,
            action="login",
            success=False,
            details={"failure_reason": reason}
        )
    
    def log_brute_force_attempt(
        self,
        ip_address: str,
        user_email: Optional[str] = None,
        attempt_count: int = 1,
        request_id: Optional[str] = None
    ):
        """Log une tentative de force brute."""
        self.log_event(
            AuditEventType.LOGIN_BRUTEFORCE,
            user_email=user_email,
            request_id=request_id,
            ip_address=ip_address,
            action="brute_force",
            success=False,
            details={"attempt_count": attempt_count}
        )
    
    def log_password_change(
        self,
        user_id: int,
        user_email: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log un changement de mot de passe."""
        self.log_event(
            AuditEventType.PASSWORD_CHANGED,
            user_id=user_id,
            user_email=user_email,
            request_id=request_id,
            ip_address=ip_address,
            action="password_change"
        )
    
    def log_document_access(
        self,
        user_id: int,
        document_id: int,
        action: str,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None,
        success: bool = True
    ):
        """Log un accès à un document."""
        event_type = AuditEventType.DOCUMENT_ACCESSED
        if action == "upload":
            event_type = AuditEventType.DOCUMENT_UPLOADED
        elif action == "delete":
            event_type = AuditEventType.DOCUMENT_DELETED
        
        self.log_event(
            event_type,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            resource=f"document_{document_id}",
            action=action,
            success=success
        )
    
    def log_admin_action(
        self,
        user_id: int,
        action: str,
        target: Optional[str] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log une action administrative."""
        self.log_event(
            AuditEventType.ADMIN_ACTION,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            resource=target,
            action=action
        )
    
    def log_security_alert(
        self,
        alert_type: str,
        details: Dict[str, Any],
        user_id: Optional[int] = None,
        request_id: Optional[str] = None,
        ip_address: Optional[str] = None
    ):
        """Log une alerte de sécurité."""
        self.log_event(
            AuditEventType.SECURITY_ALERT,
            user_id=user_id,
            request_id=request_id,
            ip_address=ip_address,
            action=alert_type,
            success=False,
            details=details
        )


# Instance globale du logger d'audit
audit_logger = AuditLogger()


# Fonctions utilitaires
def log_login_success(user_id: int, user_email: str, **kwargs):
    """Log une connexion réussie."""
    audit_logger.log_login_success(user_id, user_email, **kwargs)


def log_login_failed(user_email: str, reason: str, **kwargs):
    """Log une connexion échouée."""
    audit_logger.log_login_failed(user_email, reason, **kwargs)


def log_document_access(user_id: int, document_id: int, action: str, **kwargs):
    """Log un accès à un document."""
    audit_logger.log_document_access(user_id, document_id, action, **kwargs)


def log_security_alert(alert_type: str, details: Dict[str, Any], **kwargs):
    """Log une alerte de sécurité."""
    audit_logger.log_security_alert(alert_type, details, **kwargs)