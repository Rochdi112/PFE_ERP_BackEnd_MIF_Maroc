# app/api/v1/dashboard.py

from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import func, text
from typing import Dict, Any
from app.db.database import get_db
from app.core.rbac import get_current_user

router = APIRouter(
    prefix="/dashboard",
    tags=["dashboard"],
    responses={404: {"description": "Not found"}}
)

@router.get(
    "/stats",
    summary="Statistiques du tableau de bord",
    description="Retourne les statistiques principales pour le tableau de bord."
)
def get_dashboard_stats(
    db: Session = Depends(get_db),
    current_user = Depends(get_current_user)
) -> Dict[str, Any]:
    """
    Statistiques du tableau de bord pour l'utilisateur connecté.
    """

    # Interventions par statut
    intervention_stats = db.execute(text("""
        SELECT
            statut,
            COUNT(*) as count
        FROM interventions
        GROUP BY statut
    """)).fetchall()

    status_counts = {row[0]: row[1] for row in intervention_stats}

    # Total interventions ce mois
    monthly_interventions = db.execute(text("""
        SELECT COUNT(*) as count
        FROM interventions
        WHERE DATE_TRUNC('month', date_creation) = DATE_TRUNC('month', CURRENT_DATE)
    """)).scalar() or 0

    # Interventions terminées ce mois
    completed_monthly = db.execute(text("""
        SELECT COUNT(*) as count
        FROM interventions
        WHERE statut = 'cloturee'
        AND DATE_TRUNC('month', date_creation) = DATE_TRUNC('month', CURRENT_DATE)
    """)).scalar() or 0

    # Taux de résolution (interventions terminées / total * 100)
    total_interventions = db.execute(text("SELECT COUNT(*) FROM interventions")).scalar() or 1
    completed_interventions = db.execute(text("SELECT COUNT(*) FROM interventions WHERE statut = 'cloturee'")).scalar() or 0
    resolution_rate = round((completed_interventions / total_interventions) * 100, 1)

    # Évolution mensuelle (6 derniers mois)
    monthly_trends = db.execute(text("""
        SELECT
            TO_CHAR(date_creation, 'Mon') as month,
            COUNT(*) as total
        FROM interventions
        WHERE date_creation >= CURRENT_DATE - INTERVAL '6 months'
        GROUP BY TO_CHAR(date_creation, 'Mon'), EXTRACT(MONTH FROM date_creation)
        ORDER BY EXTRACT(MONTH FROM date_creation)
    """)).fetchall()

    monthly_data = [{"month": row[0], "total": row[1]} for row in monthly_trends]

    # Interventions par priorité
    priority_stats = db.execute(text("""
        SELECT
            priorite,
            COUNT(*) as count
        FROM interventions
        GROUP BY priorite
    """)).fetchall()

    priority_counts = {row[0]: row[1] for row in priority_stats}

    return {
        "interventions": {
            "ouverte": status_counts.get("ouverte", 0),
            "en_cours": status_counts.get("en_cours", 0),
            "en_attente": status_counts.get("en_attente", 0),
            "terminees": status_counts.get("cloturee", 0),
            "total_mensuel": monthly_interventions,
            "terminees_mensuel": completed_monthly
        },
        "taux_resolution": resolution_rate,
        "evolution_mensuelle": monthly_data,
        "priorites": {
            "urgente": priority_counts.get("urgente", 0),
            "haute": priority_counts.get("haute", 0),
            "normale": priority_counts.get("normale", 0),
            "basse": priority_counts.get("basse", 0)
        },
        "equipements": {
            "total": db.execute(text("SELECT COUNT(*) FROM equipements")).scalar() or 0,
            "operationnel": db.execute(text("SELECT COUNT(*) FROM equipements WHERE statut = 'operational'")).scalar() or 0,
            "maintenance": db.execute(text("SELECT COUNT(*) FROM equipements WHERE statut = 'maintenance'")).scalar() or 0
        },
        "utilisateurs": {
            "total": db.execute(text("SELECT COUNT(*) FROM users")).scalar() or 0,
            "actifs": db.execute(text("SELECT COUNT(*) FROM users WHERE is_active = true")).scalar() or 0
        }
    }
