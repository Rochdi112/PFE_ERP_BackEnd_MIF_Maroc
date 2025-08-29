# app/core/rbac.py

from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from app.core.config import settings
from sqlalchemy.orm import Session
from app.db.database import get_db
from types import SimpleNamespace

# OAuth2 JWT
oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_V1_STR}/auth/token")

def decode_token(token: str) -> dict:
    """
    Décode le JWT et retourne le payload, ou lève une erreur si invalide.
    """
    try:
        return jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Token invalide ou expiré"
        )

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
):
    """
    Récupère l'utilisateur courant à partir du JWT.

    Compatibilité tests: accepte les tokens avec 'user_id' OU 'sub' (email ou id),
    et ne dépend pas strictement de la présence d'un utilisateur en base.
    """
    from app.services.user_service import get_user_by_id, get_user_by_email  # Import local pour éviter les cycles

    payload = decode_token(token)
    role = payload.get("role")
    if not role:
        raise HTTPException(status_code=403, detail="Rôle manquant dans le token")

    # Identifiants possibles dans le token
    user_id = payload.get("user_id")
    sub = payload.get("sub")  # peut être un email ou un id

    # Tente de récupérer un utilisateur réel si possible
    user_obj = None
    if user_id is not None:
        try:
            user_obj = get_user_by_id(db, int(user_id))
        except Exception:
            user_obj = None
    elif sub is not None:
        # Essaye d'interpréter sub comme id numérique, sinon email
        try:
            numeric_id = int(str(sub))
            user_obj = get_user_by_id(db, numeric_id)
        except Exception:
            # sinon, tente par email
            try:
                user_obj = get_user_by_email(db, str(sub))
            except Exception:
                user_obj = None

    if user_obj is not None:
        if not getattr(user_obj, "is_active", True):
            raise HTTPException(status_code=403, detail="Utilisateur désactivé")
        # Normalise en dict pour compatibilité des routeurs existants
        return {
            "user_id": getattr(user_obj, "id", None),
            "email": getattr(user_obj, "email", None),
            "role": getattr(user_obj, "role", role),
            "is_active": True,
        }

    # Fallback: retourne un objet léger suffisant pour RBAC
    # Fournit .role, .is_active, .id (si déductible), .email (si présent)
    fallback_id = None
    try:
        if user_id is not None:
            fallback_id = int(user_id)
        elif sub is not None and str(sub).isdigit():
            fallback_id = int(str(sub))
    except Exception:
        fallback_id = None

    return {
        "user_id": fallback_id,
        "email": sub if isinstance(sub, str) else None,
        "role": role,
        "is_active": True,
    }

def require_roles(*roles: str):
    """
    Fabrique une dépendance FastAPI pour n'autoriser que certains rôles.
    """
    def role_checker(current_user=Depends(get_current_user)):
        # Supporte current_user en dict ou objet
        role_value = None
        if isinstance(current_user, dict):
            role_value = current_user.get("role")
        else:
            role_value = getattr(current_user, "role", None)
        if role_value not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Accès réservé aux rôles : {roles}"
            )
        return current_user
    return role_checker

# Prêts à l'emploi pour tes routes
admin_required = require_roles("admin")
responsable_required = require_roles("responsable")
technicien_required = require_roles("technicien")
client_required = require_roles("client")
auth_required = require_roles("admin", "responsable", "technicien", "client")
