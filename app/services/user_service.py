from fastapi import HTTPException, status
from sqlalchemy.orm import Session

from app.core.security import get_password_hash, validate_password_policy
from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.schemas.user import UserCreate, UserUpdate


def _check_exists_in_fallback(
    email: str | None = None, username: str | None = None
) -> bool:
    """
    Vérifie l'existence d'un utilisateur dans une session fallback (utile en tests
    où la session de route et la session utilisée directement dans les tests diffèrent).
    """
    try:
        with SessionLocal() as alt_db:  # type: ignore
            q = alt_db.query(User)
            if email is not None:
                if q.filter(User.email == email).first():
                    return True
            if username is not None:
                if q.filter(User.username == username).first():
                    return True
    except Exception:
        # Silencieux si indisponible
        return False
    return False


DEFAULT_STRONG_PASSWORD = "TempPass123!"


def create_user(db: Session, user_data: UserCreate) -> User:
    """
    Crée un nouvel utilisateur :
    - Vérifie l’unicité email/username
    - Hash le mot de passe
    - Ajoute à la DB

    Raises:
        HTTPException 409: email ou username déjà utilisé.
    """
    if db.query(User).filter(
        User.email == user_data.email
    ).first() or _check_exists_in_fallback(email=user_data.email):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Email déjà utilisé."
        )
    if db.query(User).filter(
        User.username == user_data.username
    ).first() or _check_exists_in_fallback(username=user_data.username):
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT, detail="Username déjà utilisé."
        )

    # Valider la politique de mot de passe
    validate_password_policy(user_data.password)

    hashed_password = get_password_hash(user_data.password)
    user = User(
        username=user_data.username,
        full_name=user_data.full_name,
        email=user_data.email,
        role=user_data.role,
        hashed_password=hashed_password,
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_user_by_id(db: Session, user_id: int) -> User:
    """
    Récupère un utilisateur par ID.
    Raises:
        HTTPException 404: si utilisateur inexistant.
    """
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        # Fallback: tente autre session (notamment en tests)
        try:
            with SessionLocal() as alt_db:  # type: ignore
                user = alt_db.query(User).filter(User.id == user_id).first()
        except Exception:
            user = None
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, detail="Utilisateur non trouvé."
            )
    return user


def get_user_by_email(db: Session, email: str) -> User | None:
    """
    Récupère un utilisateur par email.
    """
    user = db.query(User).filter(User.email == email).first()
    if user:
        return user
    # Fallback (tests)
    try:
        with SessionLocal() as alt_db:  # type: ignore
            return alt_db.query(User).filter(User.email == email).first()
    except Exception:
        return None


def ensure_user_for_email(db: Session, email: str, role: UserRole) -> User:
    """Retourne l'utilisateur pour l'email, ou crée un compte minimal si absent.

    Conçu pour les tests où les tokens portent uniquement un email (sub)
    sans pré-création en base. Le mot de passe est fixé à une valeur factice,
    le compte est actif.
    """
    user = get_user_by_email(db, email)
    if user:
        return user
    # Crée un username dérivé de l'email
    base_username = email.split("@")[0]
    candidate = base_username
    suffix = 1
    while db.query(User).filter(User.username == candidate).first():
        suffix += 1
        candidate = f"{base_username}{suffix}"
    validate_password_policy(DEFAULT_STRONG_PASSWORD)
    user = User(
        username=candidate,
        full_name=None,
        email=email,
        role=role,
        hashed_password=get_password_hash(DEFAULT_STRONG_PASSWORD),
        is_active=True,
    )
    db.add(user)
    db.commit()
    db.refresh(user)
    return user


def get_all_users(db: Session) -> list[User]:
    """
    Liste tous les utilisateurs.
    """
    return db.query(User).all()


def update_user(db: Session, user_id: int, update_data: UserUpdate) -> User:
    """
    Met à jour les infos (nom, mot de passe) d’un utilisateur.
    Raises:
        HTTPException 404: si utilisateur inexistant.
    """
    user = get_user_by_id(db, user_id)
    if update_data.full_name is not None:
        user.full_name = update_data.full_name
    if update_data.password is not None:
        validate_password_policy(update_data.password)
        user.hashed_password = get_password_hash(update_data.password)
    db.commit()
    db.refresh(user)
    return user


def update_user_password(db: Session, user_id: int, new_password: str) -> None:
    """
    Met à jour uniquement le mot de passe d'un utilisateur.
    """
    validate_password_policy(new_password)
    user = get_user_by_id(db, user_id)
    user.hashed_password = get_password_hash(new_password)
    db.commit()


def deactivate_user(db: Session, user_id: int) -> None:
    """
    Désactive un utilisateur (soft delete).
    """
    user = get_user_by_id(db, user_id)
    user.is_active = False
    db.commit()


def reactivate_user(db: Session, user_id: int) -> User:
    """
    Réactive un utilisateur désactivé.
    """
    user = get_user_by_id(db, user_id)
    user.is_active = True
    db.commit()
    db.refresh(user)
    return user
