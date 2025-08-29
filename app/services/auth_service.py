# app/services/auth_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models.user import User
from app.schemas.user import TokenResponse
from app.core.security import verify_password, create_access_token

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
            detail="Email ou mot de passe incorrect"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )

    access_token = create_access_token(
        data={
            "sub": user.email,    # Identifiant principal (RFC JWT)
            "role": getattr(user.role, "value", str(user.role)),  # Rôle RBAC sérialisé en string
            "user_id": user.id    # Id utilisateur unique (utile pour tracking)
        }
    )

    # ✅ Correction : retourner aussi token_type="bearer" pour compatibilité Pydantic/Swagger
    return TokenResponse(access_token=access_token, token_type="bearer")

def authenticate_user_by_username(db: Session, username: str, password: str) -> TokenResponse:
    """
    Authentifie via username + password (compatibilité tests legacy).

    Retourne un JWT identique à authenticate_user.
    """
    user = db.query(User).filter(User.username == username).first()
    if not user or not verify_password(password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Identifiants invalides"
        )
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Compte désactivé"
        )
    access_token = create_access_token(
        data={
            "sub": user.email,
            "role": getattr(user.role, "value", str(user.role)),
            "user_id": user.id,
        }
    )
    return TokenResponse(access_token=access_token, token_type="bearer")
