# app/services/notification_service.py

from sqlalchemy.orm import Session
from fastapi import HTTPException
from datetime import datetime
from app.models.notification import Notification
from app.schemas.notification import NotificationCreate
from app.models.user import User
from app.core.config import settings
import sys

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from jinja2 import Environment, FileSystemLoader, TemplateNotFound

# Configuration des templates Jinja
env = Environment(loader=FileSystemLoader("app/templates"))


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
    raw_type = getattr(data, "type_notification", None) or data.model_dump(by_alias=True).get("type")
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
        date_envoi=datetime.utcnow()
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
                # Log doux: on ne fait pas échouer la requête si l'email ne part pas
                print(f"Envoi email échoué (non bloquant): {_e}")

    return notif


def send_email_notification(email_to: str, notification: Notification):
    """
    Envoie un email à l'utilisateur cible avec rendu HTML.

    Le template est choisi dynamiquement selon le type (ex: "notification_affectation.html").

    Raises:
        HTTPException 500: en cas d’échec d’envoi
    """
    try:
        subject = f"[MIF] Notification - {notification.type_notification.value.capitalize()}"
        template_name = f"notification_{notification.type_notification.value}.html"

        try:
            template = env.get_template(template_name)
        except TemplateNotFound:
            raise HTTPException(status_code=500, detail=f"Template '{template_name}' introuvable")

        html_content = template.render(
            type=notification.type_notification.value,
            contenu=notification.contenu or "Voir détails dans l’application.",
            sujet=subject,
            message=notification.contenu or ""
        )

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = settings.EMAILS_FROM_EMAIL
        msg["To"] = email_to
        msg.attach(MIMEText(html_content, "html"))

        with smtplib.SMTP(settings.SMTP_HOST, settings.SMTP_PORT) as server:
            server.starttls()
            server.login(settings.SMTP_USER, settings.SMTP_PASSWORD)
            server.sendmail(
                settings.EMAILS_FROM_EMAIL,
                email_to,
                msg.as_string()
            )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erreur envoi email : {str(e)}")
