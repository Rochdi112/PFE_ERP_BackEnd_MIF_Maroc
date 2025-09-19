# app/core/encryption.py

"""
Service de chiffrement avec rotation des clés Fernet.
Supporte le déchiffrement avec plusieurs clés pour la compatibilité.
"""

from typing import List, Optional

from cryptography.fernet import Fernet, MultiFernet
from fastapi import HTTPException

from app.core.config import settings
from app.core.logging import get_logger

logger = get_logger(__name__)


class EncryptionService:
    """Service de chiffrement avec support de rotation des clés."""
    
    def __init__(self):
        self._fernet = None
        self._keys = None
        self._initialize_keys()
    
    def _initialize_keys(self):
        """Initialise les clés Fernet depuis la configuration."""
        keys = settings.get_fernet_keys()
        
        if not keys:
            logger.warning("Aucune clé Fernet configurée, génération automatique")
            # Générer une clé temporaire pour les tests
            key = Fernet.generate_key().decode()
            keys = [key]
            logger.info("Clé Fernet temporaire générée (à remplacer en production)")
        
        # Utiliser les clés précédemment stockées si disponibles
        if hasattr(self, '_keys') and self._keys:
            keys = self._keys
        
        # Convertir les chaînes en objets Fernet
        fernet_keys = []
        for key in keys:
            try:
                fernet_keys.append(Fernet(key.encode() if isinstance(key, str) else key))
            except Exception as e:
                logger.error(f"Clé Fernet invalide ignorée: {e}")
        
        if not fernet_keys:
            raise ValueError("Aucune clé Fernet valide disponible")
        
        # La première clé est utilisée pour le chiffrement
        # Toutes les clés sont utilisées pour le déchiffrement (rotation)
        if len(fernet_keys) == 1:
            self._fernet = fernet_keys[0]
        else:
            self._fernet = MultiFernet(fernet_keys)
        
        self._keys = keys
        logger.info(f"Service de chiffrement initialisé avec {len(fernet_keys)} clé(s)")
    
    def encrypt(self, data: str) -> str:
        """Chiffre une chaîne de caractères."""
        try:
            if not isinstance(data, str):
                data = str(data)
            
            encrypted = self._fernet.encrypt(data.encode('utf-8'))
            return encrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erreur de chiffrement: {e}")
            raise HTTPException(status_code=500, detail="Erreur de chiffrement")
    
    def decrypt(self, encrypted_data: str) -> str:
        """Déchiffre une chaîne de caractères."""
        try:
            if isinstance(encrypted_data, str):
                encrypted_data = encrypted_data.encode('utf-8')
            
            decrypted = self._fernet.decrypt(encrypted_data)
            return decrypted.decode('utf-8')
            
        except Exception as e:
            logger.error(f"Erreur de déchiffrement: {e}")
            raise HTTPException(status_code=500, detail="Erreur de déchiffrement")
    
    def encrypt_file_content(self, content: bytes) -> bytes:
        """Chiffre le contenu d'un fichier."""
        try:
            return self._fernet.encrypt(content)
        except Exception as e:
            logger.error(f"Erreur de chiffrement fichier: {e}")
            raise HTTPException(status_code=500, detail="Erreur de chiffrement fichier")
    
    def decrypt_file_content(self, encrypted_content: bytes) -> bytes:
        """Déchiffre le contenu d'un fichier."""
        try:
            return self._fernet.decrypt(encrypted_content)
        except Exception as e:
            logger.error(f"Erreur de déchiffrement fichier: {e}")
            raise HTTPException(status_code=500, detail="Erreur de déchiffrement fichier")
    
    def get_active_key_count(self) -> int:
        """Retourne le nombre de clés actives."""
        return len(self._keys) if self._keys else 0
    
    def rotate_keys(self, new_key: str):
        """Ajoute une nouvelle clé en tête (devient la clé active)."""
        if not new_key:
            raise ValueError("Nouvelle clé requise")
        
        try:
            # Tester la validité de la nouvelle clé
            Fernet(new_key.encode())
            
            # Ajouter la nouvelle clé en tête de liste
            keys = [new_key] + (self._keys or [])
            
            # Limiter à 3 clés max pour éviter la surcharge
            if len(keys) > 3:
                keys = keys[:3]
                logger.info("Anciennes clés supprimées (limite 3 clés actives)")
            
            # Réinitialiser avec les nouvelles clés
            original_keys = self._keys
            self._keys = keys
            
            try:
                self._initialize_keys()
                logger.info(f"Rotation des clés effectuée, {len(keys)} clé(s) actives")
            except Exception as e:
                # Restaurer les anciennes clés en cas d'erreur
                self._keys = original_keys
                self._initialize_keys()
                raise e
            
        except Exception as e:
            logger.error(f"Erreur lors de la rotation des clés: {e}")
            raise ValueError(f"Rotation des clés échouée: {e}")


# Instance globale du service
encryption_service = EncryptionService()


def encrypt_data(data: str) -> str:
    """Fonction utilitaire pour chiffrer des données."""
    return encryption_service.encrypt(data)


def decrypt_data(encrypted_data: str) -> str:
    """Fonction utilitaire pour déchiffrer des données."""
    return encryption_service.decrypt(encrypted_data)


def encrypt_file(content: bytes) -> bytes:
    """Fonction utilitaire pour chiffrer un fichier."""
    return encryption_service.encrypt_file_content(content)


def decrypt_file(encrypted_content: bytes) -> bytes:
    """Fonction utilitaire pour déchiffrer un fichier."""
    return encryption_service.decrypt_file_content(encrypted_content)