# app/api/v1/documents.py

import os
from typing import List

from fastapi import (
    APIRouter,
    Depends,
    File,
    HTTPException,
    UploadFile,
    status,
)
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.rbac import (
    admin_required,
)
from app.db.database import get_db
from app.models.document import Document
from app.schemas.document import DocumentOut
from app.services.document_service import create_document

router = APIRouter(
    prefix="/documents",
    tags=["documents"],
    responses={404: {"description": "Document non trouvé"}},
)

# Dépendance DB
# get_db central (override en tests)


@router.post(
    "/",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un document",
    description=(
        "Upload d'un fichier lié à une intervention " "(photo, rapport, preuve, etc.)."
    ),
    dependencies=[Depends(admin_required)],
)
def upload_document(
    intervention_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return create_document(db, file, intervention_id)


# Alias attendu par certains tests: /documents/upload
@router.post(
    "/upload",
    response_model=DocumentOut,
    status_code=status.HTTP_201_CREATED,
    summary="Uploader un document (alias)",
    dependencies=[Depends(admin_required)],
)
def upload_document_alias(
    intervention_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    return create_document(db, file, intervention_id)


@router.get(
    "/",
    response_model=List[DocumentOut],
    summary="Lister tous les documents",
    description=(
        "Accès à la liste de tous les documents liés aux interventions "
        "(admin/responsable uniquement)."
    ),
    dependencies=[Depends(admin_required)],
)
def list_documents(db: Session = Depends(get_db)):
    return db.query(Document).all()


# Endpoint attendu par tests: /documents/{intervention_id}
@router.get(
    "/{intervention_id}",
    response_model=List[DocumentOut],
    summary="Lister les documents d'une intervention",
    dependencies=[Depends(admin_required)],
)
def list_documents_by_intervention(
    intervention_id: int,
    db: Session = Depends(get_db),
):
    return db.query(Document).filter(Document.intervention_id == intervention_id).all()


@router.delete(
    "/{document_id}",
    status_code=status.HTTP_200_OK,
    summary="Supprimer un document",
    description="Supprime le document (enregistrement + fichier sur disque)",
    dependencies=[Depends(admin_required)],
)
def delete_document(
    document_id: int,
    db: Session = Depends(get_db),
):
    doc = db.query(Document).filter(Document.id == document_id).first()
    if not doc:
        raise HTTPException(status_code=404, detail="Document non trouvé")
    # Supprime le fichier physique si présent
    try:
        chemin = doc.chemin or ""
        # chemin est de la forme "static/uploads/<uuid>.<ext>"
        # reconstruire chemin absolu
        if chemin:
            # settings.UPLOAD_DIRECTORY pointe vers .../app/static/uploads
            uploads_dir = settings.UPLOAD_DIRECTORY
            # On ne garde que le nom de fichier réel
            filename = os.path.basename(chemin)
            abs_path = os.path.join(uploads_dir, filename)
            if os.path.isfile(abs_path):
                os.remove(abs_path)
    except Exception:
        # On ne bloque pas la suppression DB si suppression fichier échoue
        pass
    db.delete(doc)
    db.commit()
    return {"detail": "Document supprimé"}
