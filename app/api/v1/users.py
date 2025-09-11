from typing import List

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.core.rbac import (
    admin_required,
    get_current_user,
)
from app.db.database import get_db
from app.schemas.user import UserCreate, UserOut, UserUpdate
from app.services.user_service import (
    create_user,
    deactivate_user,
    get_all_users,
    get_user_by_email,
    get_user_by_id,
    reactivate_user,
    update_user,
)

router = APIRouter(
    prefix="/users",
    tags=["utilisateurs"],
    responses={404: {"description": "Utilisateur non trouvé"}},
)

# get_db importé depuis app.db.database
# (compatible avec les overrides de tests)


@router.post(
    "/",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Créer un utilisateur",
    description=(
        "Création d'un nouvel utilisateur " "(réservé à l'administrateur uniquement)."
    ),
    dependencies=[Depends(admin_required)],
)
def create_new_user(data: UserCreate, db: Session = Depends(get_db)):
    """Création par l'admin."""
    return create_user(db, data)


# IMPORTANT: Déclarer la route statique /me AVANT la route dynamique /{user_id}
# pour éviter qu'elle ne soit capturée par le paramètre dynamique
# avec une dépendance admin.
@router.get(
    "/me",
    response_model=UserOut,
    summary="Voir son profil",
    description="Retourne le profil de l'utilisateur connecté.",
)
def get_my_profile(
    current_user=Depends(get_current_user), db: Session = Depends(get_db)
):
    """Voir son propre profil (self-service)."""
    email = None
    if isinstance(current_user, dict):
        email = current_user.get("email")
    else:
        email = getattr(current_user, "email", None)
    if not email:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return user


@router.put(
    "/update",
    response_model=UserOut,
    summary="Modifier son profil",
    description="Permet à l'utilisateur connecté de mettre à jour son profil.",
)
def update_my_profile(
    update_data: UserUpdate,
    db: Session = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Mise à jour profil user connecté."""
    # Supporte current_user dict ou objet
    email = None
    if isinstance(current_user, dict):
        email = current_user.get("email")
    else:
        email = getattr(current_user, "email", None)
    if not email:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    user = get_user_by_email(db, email)
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur non trouvé")
    return update_user(db, user.id, update_data)


@router.get(
    "/{user_id}",
    response_model=UserOut,
    summary="Lire un utilisateur par ID",
    description=(
        "Retourne un utilisateur par son ID. " "Accès réservé à l'administrateur."
    ),
    dependencies=[Depends(admin_required)],
)
def read_user(user_id: int, db: Session = Depends(get_db)):
    """Lecture par l'admin."""
    return get_user_by_id(db, user_id)


@router.get(
    "/",
    response_model=List[UserOut],
    summary="Lister tous les utilisateurs",
    description=("Liste complète des utilisateurs " "(réservé à l'administrateur)."),
    dependencies=[Depends(admin_required)],
)
def list_users(db: Session = Depends(get_db)):
    """Liste tous les users (admin)."""
    return get_all_users(db)


@router.delete(
    "/{user_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Désactiver un utilisateur",
    description="Soft delete (désactivation) utilisateur par l’admin.",
    dependencies=[Depends(admin_required)],
)
def disable_user(user_id: int, db: Session = Depends(get_db)):
    """Désactive (soft delete) un user."""
    deactivate_user(db, user_id)
    return


@router.patch(
    "/{user_id}/activate",
    response_model=UserOut,
    summary="Réactiver un utilisateur",
    description="Réactive un utilisateur désactivé (admin uniquement).",
    dependencies=[Depends(admin_required)],
)
def activate_user(user_id: int, db: Session = Depends(get_db)):
    """Réactive un user désactivé."""
    return reactivate_user(db, user_id)
