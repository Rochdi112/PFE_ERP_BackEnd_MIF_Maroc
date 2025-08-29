# app/schemas/user.py

from pydantic import BaseModel, EmailStr, ConfigDict
from enum import Enum
from typing import Optional
from datetime import datetime

# ===============================
# 🎯 ENUM des rôles utilisateur
# ===============================
class UserRole(str, Enum):
    """
    Rôles disponibles dans l’ERP :
    - admin : contrôle total
    - responsable : supervise les interventions
    - technicien : effectue les interventions
    - client : consultation uniquement
    """
    admin = "admin"
    responsable = "responsable"
    technicien = "technicien"
    client = "client"

# ================================
# 👤 Schéma de base utilisateur
# ================================
class UserBase(BaseModel):
    """
    Champs partagés entre création, affichage et mise à jour :
    - username : identifiant unique
    - full_name : nom complet
    - email : adresse email unique
    - role : rôle de l'utilisateur
    """
    username: str
    full_name: str
    email: EmailStr
    role: UserRole

# =======================================
# 📥 Schéma de création (input POST)
# =======================================
class UserCreate(UserBase):
    """
    Données nécessaires pour créer un nouvel utilisateur :
    - hérite de UserBase
    - ajoute : password (en clair, à hasher)
    """
    password: str

# =======================================
# 📤 Schéma de sortie (output GET)
# =======================================
class UserOut(UserBase):
    """
    Données renvoyées par l'API :
    - toutes les infos utilisateur sauf le mot de passe
    - audit : id, statut, timestamps
    """
    id: int
    is_active: bool
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None

    model_config = ConfigDict(from_attributes=True)  # Active l'ORM mode pour SQLAlchemy

# =======================================
# 🔁 Schéma de mise à jour utilisateur
# =======================================
class UserUpdate(BaseModel):
    """
    Champs modifiables par l'utilisateur :
    - nom complet
    - mot de passe
    """
    full_name: Optional[str] = None
    password: Optional[str] = None

# =======================================
# 🔐 Schémas pour l'authentification
# =======================================
class TokenRequest(BaseModel):
    """
    Données attendues lors de la connexion :
    - email
    - mot de passe
    """
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    """
    Réponse retournée après login :
    - access_token : JWT signé
    - token_type : 'bearer'
    """
    access_token: str
    token_type: str = "bearer"
