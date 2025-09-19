from fastapi import APIRouter, Depends, Form
from sqlalchemy.orm import Session

from app.core.rbac import get_current_user
from app.core.security import create_access_token
from app.db.database import get_db
from app.schemas.user import TokenResponse, UserOut
from app.services.auth_service import (
    authenticate_user,
    authenticate_user_by_username,
    create_refresh_token,
    revoke_all_user_tokens,
    rotate_refresh_token,
)

router = APIRouter(
    prefix="/auth",
    tags=["auth"],
    responses={404: {"description": "Not found"}},
)

# utilise le get_db central (surchargé dans les tests)


@router.post(
    "/token",
    response_model=TokenResponse,
    summary="Connexion utilisateur",
    description="Authentifie un utilisateur avec email + mot de passe. "
    "Retourne un token JWT si valide.",
)
def login(
    email: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    """
    ⚙️ Endpoint de login :
    - Vérifie l'email + mot de passe.
    - Retourne un token JWT avec rôle embarqué.
    - Utilisé dans le header `Authorization: Bearer <token>`
    """
    return authenticate_user(db, email, password)


@router.post(
    "/login",
    response_model=TokenResponse,
    summary="Connexion utilisateur (username/password)",
    description="Authentifie un utilisateur avec username + mot de passe. "
    "Retourne un token JWT si valide.",
)
def login_username(
    username: str = Form(...), password: str = Form(...), db: Session = Depends(get_db)
):
    """
    Endpoint de login via username pour compatibilité avec certains tests.
    """
    return authenticate_user_by_username(db, username, password)


@router.post(
    "/refresh",
    response_model=TokenResponse,
    summary="Rafraîchir les tokens",
    description="Échange un refresh token valide contre de nouveaux tokens.",
)
def refresh_token(refresh_token: str = Form(...), db: Session = Depends(get_db)):
    """
    Échange un refresh token contre de nouveaux access et refresh tokens.
    Le refresh token est marqué comme rotated.
    """
    new_refresh = rotate_refresh_token(db, refresh_token)
    # Pour créer l'access token, on doit récupérer l'utilisateur
    from app.models.refresh_token import RefreshToken

    rt = db.query(RefreshToken).filter_by(token=refresh_token).first()
    if not rt:
        from fastapi import HTTPException

        raise HTTPException(status_code=401, detail="Token invalide")

    user = rt.user
    access = create_access_token(
        data={
            "sub": user.email,
            "role": user.role.value,
            "user_id": user.id,
        }
    )
    return TokenResponse(
        access_token=access, refresh_token=new_refresh, token_type="bearer"
    )


@router.post(
    "/logout",
    summary="Déconnexion utilisateur",
    description="Révoque tous les refresh tokens de l'utilisateur connecté.",
)
def logout(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Révoque tous les refresh tokens de l'utilisateur pour le déconnecter.
    """
    revoke_all_user_tokens(db, current_user["user_id"])
    return {"message": "Déconnexion réussie"}


# ======= ROUTE /me (infos utilisateur courant via JWT) =========


@router.get(
    "/me",
    response_model=UserOut,
    summary="Informations de l'utilisateur courant",
    description="Retourne les infos du profil de l'utilisateur connecté, "
    "à partir du JWT envoyé dans le header.",
)
def get_me(current_user=Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Récupère l'utilisateur courant à partir du JWT Bearer.
    Utile pour le frontend (profil, header...).
    """
    # current_user contient : {'user_id': ..., 'email': ..., 'role': ...}
    # On va récupérer l'utilisateur complet dans la base
    # (UserOut = toutes les infos du user)
    from app.services.user_service import (
        get_user_by_email,
    )

    user = get_user_by_email(db, current_user["email"])
    if not user:
        from fastapi import HTTPException, status

        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé",
        )
    return user


@router.post(
    "/change-password",
    summary="Changer le mot de passe",
    description="Permet à l'utilisateur connecté de changer son mot de passe.",
)
def change_password(
    current_password: str = Form(...),
    new_password: str = Form(...),
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """
    Change le mot de passe de l'utilisateur connecté.
    Vérifie d'abord l'ancien mot de passe.
    """
    from fastapi import HTTPException, status

    from app.services.auth_service import verify_password
    from app.services.user_service import (
        get_user_by_email,
        update_user_password,
    )

    user = get_user_by_email(db, current_user["email"])
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Utilisateur non trouvé",
        )

    # Vérifier l'ancien mot de passe
    if not verify_password(current_password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Mot de passe actuel incorrect",
        )

    # Mettre à jour le mot de passe
    update_user_password(db, user.id, new_password)
    return {"message": "Mot de passe changé avec succès"}
