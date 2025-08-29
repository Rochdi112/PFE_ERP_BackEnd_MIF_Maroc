# app/tasks/notification_tasks.py

from fastapi import BackgroundTasks
from app.models.notification import Notification
from app.models.user import User
from app.db.database import SessionLocal
from app.core.config import settings
from app.core.security import get_password_hash
from datetime import datetime
from app.schemas.notification import NotificationCreate

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

conf = ConnectionConfig(
    MAIL_USERNAME=settings.SMTP_USER,
    MAIL_PASSWORD=settings.SMTP_PASSWORD,
    MAIL_FROM=settings.EMAILS_FROM_EMAIL,
    MAIL_PORT=settings.SMTP_PORT,
    MAIL_SERVER=settings.SMTP_HOST,
    MAIL_FROM_NAME="ERP Interventions",
    MAIL_STARTTLS=True,
    MAIL_SSL_TLS=False,
    USE_CREDENTIALS=True,
    VALIDATE_CERTS=True
)

templates_path = Path("app/templates")
env = Environment(loader=FileSystemLoader(templates_path))

def send_email_notification(subject: str, to_email: str, template_name: str, context: dict):
    """Construit et envoie un e-mail avec template HTML"""
    template = env.get_template(template_name)
    html_content = template.render(**context)

    message = MessageSchema(
        subject=subject,
        recipients=[to_email],
        body=html_content,
        subtype="html"
    )

    fm = FastMail(conf)
    return fm.send_message(message)

def send_intervention_assignment_email(intervention_title: str, technicien: User):
    """Envoie un e-mail au technicien lors d’une affectation"""
    return send_email_notification(
        subject="Nouvelle intervention assignée",
        to_email=technicien.email,
        template_name="notification_affectation.html",
        context={"user": technicien.full_name, "titre": intervention_title}
    )

def send_cloture_notification(intervention_title: str, client: User):
    """Envoie un e-mail de clôture d’intervention au client"""
    return send_email_notification(
        subject="Intervention clôturée",
        to_email=client.email,
        template_name="notification_cloture.html",
        context={"user": client.full_name, "titre": intervention_title}
    )
