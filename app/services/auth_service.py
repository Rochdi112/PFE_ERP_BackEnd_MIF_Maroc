# app/services/auth_service.py

from datetime import datetime, timedelta
from secrets import token_urlsafe

from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.security import create_access_token, verify_password
from app.models.refresh_token import RefreshToken
from app.models.user import User
from app.schemas.user import TokenResponse


def authenticate_user(db: Session, email: str, password: str) -> TokenResponse:
    """
    Authentifie un utilisateur avec email et mot de passe.
    Retourne un JWT Token si succès.

    Args:
        db (Session): Session SQLAlchemy.
        email (str): Email de l'utilisateur.
        password (str): Mot de passe brut.

    Returns:
        TokenResponse: Token JWT pour accès API.

    Raises:
        HTTPException: 401 si credentials invalides.
        HTTPException: 403 si compte désactivé.
    """
    user = db.query(User).filter(User.email == email).first()

    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Email ou mot de passe incorrect",
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,  # Identifiant principal (RFC JWT)
            "role": getattr(
                user.role, "value", str(user.role)
            ),  # Rôle RBAC sérialisé en string
            "user_id": user.id,  # Id utilisateur unique (utile pour tracking)
        }
    )

    refresh_token = create_refresh_token(db, user.id)

    # ✅ Correction : retourner aussi token_type="bearer" pour compatibilité
    # Pydantic/Swagger
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")


def create_refresh_token(db: Session, user_id: int) -> str:
    """Crée un nouveau refresh token pour l'utilisateur"""
    token = token_urlsafe(48)
    refresh = RefreshToken(
        user_id=user_id,
        token=token,
        expires_at=datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
    )
    db.add(refresh)
    db.commit()
    return token


def rotate_refresh_token(db: Session, old_token: str) -> str:
    """Fait tourner un refresh token et retourne un nouveau"""
    rt = db.query(RefreshToken).filter_by(token=old_token, revoked=False, rotated=False).first()
    if not rt or rt.expires_at < datetime.utcnow():
        raise HTTPException(status_code=401, detail="Refresh token invalide")
    rt.rotated = True
    db.commit()
    return create_refresh_token(db, rt.user_id)


def revoke_all_user_tokens(db: Session, user_id: int):
    """Révoque tous les refresh tokens d'un utilisateur"""
    db.query(RefreshToken).filter_by(user_id=user_id, revoked=False).update({"revoked": True})
    db.commit()


def authenticate_user_by_username(
    db: Session, username: str, password: str
) -> TokenResponse:
    """
    Authentifie via username + password (compatibilité tests legacy).

    Retourne un JWT identique à authenticate_user.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Identifiants invalides"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN, detail="Compte désactivé"
        )
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": getattr(user.role, "value", str(user.role)),
            "user_id": user.id,
        }
    )
    refresh_token = create_refresh_token(db, user.id)
    return TokenResponse(access_token=access_token, refresh_token=refresh_token, token_type="bearer")
