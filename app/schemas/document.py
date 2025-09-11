from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field

# ---------- BASE ----------


class DocumentBase(BaseModel):
    """
    Champs communs pour tous les schémas de document :
    - Nom du fichier tel qu'enregistré
    - Chemin relatif dans /static/uploads/
    """

    nom_fichier: str = Field(alias="filename")
    chemin: str = Field(alias="path")  # Ex: "static/uploads/preuve_345.pdf"


# ---------- CRÉATION ----------


class DocumentCreate(DocumentBase):
    """
    Schéma utilisé lors de l'upload d'un document :
    - Requiert l'identifiant de l'intervention à laquelle il est lié
    """

    intervention_id: int


# ---------- RÉPONSE API ----------


class DocumentOut(DocumentBase):
    """
    Schéma renvoyé par l'API pour un document :
    - Contient les métadonnées complètes
    """

    id: int
    date_upload: datetime
    intervention_id: int

    model_config = ConfigDict(
        from_attributes=True,
        validate_by_name=True,
        populate_by_name=True,
    )
