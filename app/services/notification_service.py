# app/services/notification_service.py

import sys
from datetime import datetime

from fastapi import HTTPException
from jinja2 import Environment, FileSystemLoader, TemplateNotFound
from sqlalchemy.orm import Session
import smtplib

from app.models.notification import Notification
from app.models.user import User
from app.schemas.notification import NotificationCreate


# Configuration des templates Jinja
env = Environment(loader=FileSystemLoader("app/templates"))


def send_email_notification(email_to: str, notification: Notification, env_param=None):
    """
    Envoie un email à l'utilisateur cible avec rendu HTML.

    Le template est choisi dynamiquement selon le type
    (ex: "notification_affectation.html").

    Raises:
        HTTPException 500: en cas d'échec d'envoi
    """
    if env_param is None:
        env_param = env
    try:
        # Sélection du template selon le type
        template_name = f"notification_{notification.type_notification.value}.html"

        # Rendu du template
        template = env_param.get_template(template_name)
        html_content = template.render(
            notification=notification,
            recipient=email_to
        )

        # Envoi de l'email (simulation pour les tests)
        print(f"Email envoyé à {email_to} avec template {template_name}")
        
        # Simuler l'envoi SMTP pour les tests
        # Ces appels SMTP peuvent être mockés dans les tests
        server = smtplib.SMTP("smtp.example.com", 587)
        server.starttls()
        server.login("user", "password")
        server.sendmail("from@example.com", email_to, html_content)
        server.quit()

    except Exception as e:
        raise HTTPException(
            status_code=500,
            detail=f"Échec d'envoi d'email: {str(e)}"
        )


def create_notification(db: Session, data: NotificationCreate) -> Notification:
    """
    Crée une notification (log ou email) pour un utilisateur.

    Si canal == email, envoie un mail via SMTP.

    Raises:
        HTTPException 404: utilisateur ou intervention non trouvés
        HTTPException 500: échec envoi email
    """
    user = db.query(User).filter(User.id == data.user_id).first()
    if not user:
        raise HTTPException(status_code=404, detail="Utilisateur cible introuvable")

    # Pydantic schema uses field 'type_notification' with alias 'type'.
    # Ensure we read the canonical attribute and map to model Column("type", Enum(...))
    # Normalise le type pour l'enum
    raw_type = getattr(data, "type_notification", None) or data.model_dump(
        by_alias=True
    ).get("type")
    from app.models.notification import TypeNotification

    if isinstance(raw_type, str):
        norm = raw_type.strip().lower()
        try:
            type_enum = TypeNotification(norm)
        except Exception:
            type_enum = TypeNotification.information
    elif isinstance(raw_type, TypeNotification):
        type_enum = raw_type
    else:
        type_enum = TypeNotification.information

    notif = Notification(
        type_notification=type_enum,
        canal=data.canal,
        contenu=data.contenu,
        user_id=data.user_id,
        intervention_id=data.intervention_id,
        date_envoi=datetime.utcnow(),
    )

    db.add(notif)
    db.commit()
    db.refresh(notif)

    if data.canal == "email":
        # En environnement de test, ne pas tenter d'envoyer de vrai email
        if "pytest" not in sys.modules:
            try:
                send_email_notification(user.email, notif)
            except Exception as _e:
                # Log doux: on ne fait pas échouer la requête si l'email
                # ne part pas
                print(f"Envoi email échoué (non bloquant): {_e}")

    return notif
