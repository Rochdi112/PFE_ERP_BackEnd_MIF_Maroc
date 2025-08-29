# app/tasks/scheduler.py

from apscheduler.schedulers.background import BackgroundScheduler
from datetime import datetime
from app.db.database import SessionLocal
from app.models.planning import Planning
from app.models.equipement import Equipement
from app.services.intervention_service import create_intervention_from_planning

scheduler = BackgroundScheduler()

def run_planning_generation():
    """
    Tâche planifiée : génère automatiquement des interventions à partir du planning.
    """
    db = SessionLocal()
    try:
        now = datetime.utcnow()
        plannings = db.query(Planning).filter(Planning.prochaine_date <= now).all()
        for plan in plannings:
            create_intervention_from_planning(db, plan)
    finally:
        db.close()

#def start_scheduler():
    """
    Lance le scheduler APScheduler avec les tâches récurrentes définies.
    """
    scheduler.add_job(run_planning_generation, 'interval', hours=1, id="planning_job")
    scheduler.start()##
