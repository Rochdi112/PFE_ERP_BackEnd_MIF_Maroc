# app/core/brute_force.py

"""
Protection contre les attaques par force brute.
Implémente un système de rate limiting avec backoff exponentiel.
"""

import time
from datetime import datetime, timedelta
from typing import Dict, Optional

from fastapi import HTTPException, Request

from app.core.audit import audit_logger
from app.core.logging import get_logger

logger = get_logger(__name__)


class BruteForceProtection:
    """Service de protection contre les attaques par force brute."""
    
    def __init__(self):
        # Stockage en mémoire des tentatives (en prod: Redis recommandé)
        self._attempts: Dict[str, Dict] = {}
        
        # Configuration
        self.max_attempts = 5  # Nombre max de tentatives
        self.lockout_duration = 300  # Verrouillage 5 minutes
        self.window_duration = 900  # Fenêtre de 15 minutes
        
    def _get_key(self, identifier: str, ip_address: str) -> str:
        """Génère une clé unique pour l'identification."""
        return f"{identifier}:{ip_address}"
    
    def _cleanup_old_attempts(self):
        """Nettoie les anciennes tentatives expirées."""
        now = datetime.utcnow()
        expired_keys = []
        
        for key, data in self._attempts.items():
            if now > data.get('reset_time', now):
                expired_keys.append(key)
        
        for key in expired_keys:
            del self._attempts[key]
    
    def record_failed_attempt(
        self,
        identifier: str,
        ip_address: str,
        request_id: Optional[str] = None
    ) -> Dict:
        """
        Enregistre une tentative échouée et retourne l'état.
        
        Returns:
            Dict avec 'locked', 'attempts', 'lockout_until', 'retry_after'
        """
        self._cleanup_old_attempts()
        
        key = self._get_key(identifier, ip_address)
        now = datetime.utcnow()
        
        if key not in self._attempts:
            self._attempts[key] = {
                'count': 0,
                'first_attempt': now,
                'last_attempt': now,
                'locked_until': None,
                'reset_time': now + timedelta(seconds=self.window_duration)
            }
        
        attempt_data = self._attempts[key]
        attempt_data['count'] += 1
        attempt_data['last_attempt'] = now
        
        # Vérifier si le verrouillage est nécessaire
        if attempt_data['count'] >= self.max_attempts:
            # Backoff exponentiel: 5min, 10min, 20min, etc.
            lockout_multiplier = min(2 ** (attempt_data['count'] - self.max_attempts), 8)
            lockout_seconds = self.lockout_duration * lockout_multiplier
            
            attempt_data['locked_until'] = now + timedelta(seconds=lockout_seconds)
            
            # Log de sécurité
            audit_logger.log_brute_force_attempt(
                ip_address=ip_address,
                user_email=identifier,
                attempt_count=attempt_data['count'],
                request_id=request_id
            )
            
            logger.warning(
                f"Brute force détecté: {identifier} depuis {ip_address}",
                extra_fields={
                    "identifier": identifier,
                    "ip_address": ip_address,
                    "attempt_count": attempt_data['count'],
                    "lockout_duration": lockout_seconds,
                    "request_id": request_id
                }
            )
        
        return {
            'locked': attempt_data.get('locked_until') and attempt_data.get('locked_until') > now,
            'attempts': attempt_data['count'],
            'lockout_until': attempt_data.get('locked_until'),
            'retry_after': max(0, int((attempt_data.get('locked_until', now) - now).total_seconds())) if attempt_data.get('locked_until') else 0
        }
    
    def is_locked(self, identifier: str, ip_address: str) -> Dict:
        """
        Vérifie si l'identifiant/IP est verrouillé.
        
        Returns:
            Dict avec 'locked', 'attempts', 'retry_after'
        """
        self._cleanup_old_attempts()
        
        key = self._get_key(identifier, ip_address)
        
        if key not in self._attempts:
            return {'locked': False, 'attempts': 0, 'retry_after': 0}
        
        attempt_data = self._attempts[key]
        now = datetime.utcnow()
        
        locked_until = attempt_data.get('locked_until')
        is_locked = locked_until and locked_until > now
        
        retry_after = 0
        if is_locked:
            retry_after = int((locked_until - now).total_seconds())
        
        return {
            'locked': is_locked,
            'attempts': attempt_data['count'],
            'retry_after': retry_after
        }
    
    def clear_attempts(self, identifier: str, ip_address: str):
        """Efface les tentatives pour un identifiant/IP (après connexion réussie)."""
        key = self._get_key(identifier, ip_address)
        if key in self._attempts:
            del self._attempts[key]
    
    def check_and_raise_if_locked(
        self,
        identifier: str,
        ip_address: str,
        request_id: Optional[str] = None
    ):
        """
        Vérifie le verrouillage et lève une exception si nécessaire.
        
        Raises:
            HTTPException: Si l'accès est verrouillé
        """
        status = self.is_locked(identifier, ip_address)
        
        if status['locked']:
            retry_after = status['retry_after']
            
            raise HTTPException(
                status_code=429,
                detail=f"Trop de tentatives échouées. Réessayez dans {retry_after} secondes.",
                headers={"Retry-After": str(retry_after)}
            )


# Instance globale
brute_force_protection = BruteForceProtection()


def get_client_ip(request: Request) -> str:
    """Extrait l'adresse IP du client."""
    # Vérifier les headers de proxy (X-Forwarded-For, X-Real-IP)
    forwarded_for = request.headers.get("X-Forwarded-For")
    if forwarded_for:
        # Prendre la première IP (client original)
        return forwarded_for.split(",")[0].strip()
    
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip.strip()
    
    # IP directe
    return request.client.host if request.client else "unknown"


def check_brute_force_protection(
    identifier: str,
    request: Request,
    request_id: Optional[str] = None
):
    """
    Vérifie la protection contre les attaques par force brute.
    
    Args:
        identifier: Email ou nom d'utilisateur
        request: Objet Request FastAPI
        request_id: ID de corrélation
    
    Raises:
        HTTPException: Si l'accès est verrouillé
    """
    ip_address = get_client_ip(request)
    brute_force_protection.check_and_raise_if_locked(
        identifier, ip_address, request_id
    )


def record_failed_login(
    identifier: str,
    request: Request,
    request_id: Optional[str] = None
):
    """
    Enregistre une tentative de connexion échouée.
    
    Args:
        identifier: Email ou nom d'utilisateur
        request: Objet Request FastAPI
        request_id: ID de corrélation
    """
    ip_address = get_client_ip(request)
    return brute_force_protection.record_failed_attempt(
        identifier, ip_address, request_id
    )


def clear_failed_attempts(identifier: str, request: Request):
    """
    Efface les tentatives échouées après une connexion réussie.
    
    Args:
        identifier: Email ou nom d'utilisateur
        request: Objet Request FastAPI
    """
    ip_address = get_client_ip(request)
    brute_force_protection.clear_attempts(identifier, ip_address)