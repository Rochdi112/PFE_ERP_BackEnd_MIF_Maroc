# app/services/document_service.py

import os
from datetime import datetime
from uuid import uuid4

from cryptography.fernet import Fernet
from fastapi import HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models.document import Document
from app.models.intervention import Intervention

# Initialiser Fernet avec la clé de chiffrement
if settings.FILES_ENC_KEY:
    fernet = Fernet(settings.FILES_ENC_KEY.encode())
else:
    # Clé de développement - NE PAS UTILISER EN PRODUCTION
    from cryptography.fernet import Fernet
    fernet = Fernet(Fernet.generate_key())


def save_uploaded_file(file: UploadFile) -> str:
    """
    Sauvegarde physique d'un fichier uploadé dans le dossier `uploads/`.
    Le fichier est chiffré avec Fernet avant sauvegarde.

    Returns:
        str: chemin relatif à stocker en base (ex: uploads/abcd1234.png)
    """
    os.makedirs(settings.UPLOAD_DIRECTORY, exist_ok=True)

    extension = os.path.splitext(file.filename)[1]
    if not extension:
        raise HTTPException(
            status_code=400, detail="Le fichier doit avoir une extension valide"
        )

    unique_name = f"{uuid4().hex}{extension}"
    file_path = os.path.join(settings.UPLOAD_DIRECTORY, unique_name)

    # Lire et chiffrer le contenu
    content = file.file.read()
    encrypted_content = fernet.encrypt(content)

    with open(file_path, "wb") as f:
        f.write(encrypted_content)

    # Return path relative that frontend can GET via /static/... endpoint
    return f"static/uploads/{unique_name}"


def read_encrypted_file(file_path: str) -> bytes:
    """
    Lit et déchiffre un fichier chiffré.

    Args:
        file_path: chemin relatif du fichier (ex: static/uploads/abc123.png)

    Returns:
        bytes: contenu déchiffré du fichier
    """
    # Convertir le chemin relatif en absolu
    if file_path.startswith("static/uploads/"):
        relative_path = file_path.replace("static/uploads/", "")
        full_path = os.path.join(settings.UPLOAD_DIRECTORY, relative_path)
    else:
        full_path = file_path

    if not os.path.exists(full_path):
        raise HTTPException(status_code=404, detail="Fichier non trouvé")

    with open(full_path, "rb") as f:
        encrypted_content = f.read()

    return fernet.decrypt(encrypted_content)


def create_document(db: Session, file: UploadFile, intervention_id: int) -> Document:
    """
    Associe un fichier uploadé à une intervention existante.

    Raises:
        HTTPException 404: si l'intervention est introuvable
    """
    intervention = (
        db.query(Intervention).filter(Intervention.id == intervention_id).first()
    )
    if not intervention:
        raise HTTPException(status_code=404, detail="Intervention cible introuvable")

    chemin = save_uploaded_file(file)

    document = Document(
        nom_fichier=file.filename,
        chemin=chemin,
        intervention_id=intervention_id,
        date_upload=datetime.utcnow(),
    )

    db.add(document)
    db.commit()
    db.refresh(document)
    return document
