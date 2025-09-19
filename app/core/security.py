# app/core/security.py

from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext

from app.core.config import settings

# Configuration du hash de mot de passe
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Configuration du schéma Bearer pour JWT
security = HTTPBearer()

# Constantes pour la politique de mot de passe
ALLOWED_SYMBOLS = "!@#$%^&*()-_+=[]{};:,.?/|"
MIN_PASSWORD_LENGTH = 10


def get_password_hash(password: str) -> str:
    """Retourne le hash du mot de passe"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Vérifie si le mot de passe correspond au hash"""
    return pwd_context.verify(plain_password, hashed_password)


def validate_password_policy(password: str) -> None:
    """Valide la politique de mot de passe"""

    missing_requirements: list[str] = []

    if len(password) < MIN_PASSWORD_LENGTH:
        missing_requirements.append(f"au moins {MIN_PASSWORD_LENGTH} caractères")
    if password.lower() == password:
        missing_requirements.append("une lettre majuscule")
    if password.upper() == password:
        missing_requirements.append("une lettre minuscule")
    if not any(char.isdigit() for char in password):
        missing_requirements.append("un chiffre")
    if not any(char in ALLOWED_SYMBOLS for char in password):
        missing_requirements.append(f"un symbole parmi {ALLOWED_SYMBOLS}")

    if missing_requirements:
        requirements = ", ".join(missing_requirements)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Le mot de passe doit contenir {requirements}.",
        )


def create_access_token(data: dict, expires_delta: timedelta = None) -> str:
    """Crée un token JWT d'accès avec expiration"""
    to_encode = data.copy()
    expire = datetime.utcnow() + (
        expires_delta or timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    )
    to_encode.update({"exp": expire})
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def verify_token(token: str) -> dict:
    """Vérifie et décode un token JWT"""
    try:
        payload = jwt.decode(
            token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]
        )
        return payload
    except JWTError:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
):
    """
    Extrait et valide l'utilisateur courant depuis le token JWT
    """
    token = credentials.credentials
    payload = verify_token(token)

    email: str = payload.get("sub")
    if email is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Token invalide",
            headers={"WWW-Authenticate": "Bearer"},
        )

    # Retourne un objet utilisateur simplifié
    return {
        "user_id": payload.get("user_id"),
        "email": email,
        "role": payload.get("role"),
        "is_active": payload.get("is_active", True),
    }
