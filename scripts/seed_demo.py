#!/usr/bin/env python3
# scripts/seed_demo.py

"""
Script de génération de données de démonstration pour ERP MIF Maroc
Usage: python scripts/seed_demo.py
"""

import sys
import os
from datetime import datetime, timedelta

# Ajouter le répertoire racine au Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app.db.database import SessionLocal
from app.models.user import User, UserRole
from app.models.equipement import Equipement, TypeEquipement, StatutEquipement
from app.models.technicien import Technicien, StatutTechnicien
from app.models.intervention import (
    Intervention, 
    StatutIntervention, 
    PrioriteIntervention
)
from app.core.security import get_password_hash


def create_demo_users(db):
    """Crée les utilisateurs de démonstration"""
    print("📋 Création des utilisateurs de démonstration...")
    
    demo_users = [
        {
            "username": "admin",
            "full_name": "Administrateur Système",
            "email": "admin@mif-maroc.com",
            "password": "AdminPass123!",
            "role": UserRole.ADMIN
        },
        {
            "username": "responsable",
            "full_name": "Jean Responsable",
            "email": "responsable@mif-maroc.com", 
            "password": "RespPass123!",
            "role": UserRole.RESPONSABLE
        },
        {
            "username": "technicien1",
            "full_name": "Ahmed Technicien",
            "email": "ahmed@mif-maroc.com",
            "password": "TechPass123!",
            "role": UserRole.TECHNICIEN
        },
        {
            "username": "client1",
            "full_name": "Société ABC",
            "email": "contact@abc.com",
            "password": "ClientPass123!",
            "role": UserRole.CLIENT
        }
    ]
    
    for user_data in demo_users:
        existing = db.query(User).filter(User.email == user_data["email"]).first()
        if not existing:
            user = User(
                username=user_data["username"],
                full_name=user_data["full_name"],
                email=user_data["email"],
                hashed_password=get_password_hash(user_data["password"]),
                role=user_data["role"],
                is_active=True
            )
            db.add(user)
            print(f"  ✅ Utilisateur créé: {user_data['email']} ({user_data['role'].value})")
        else:
            print(f"  ⏭️  Utilisateur existe: {user_data['email']}")
    
    db.commit()


def create_demo_equipements(db):
    """Crée les équipements de démonstration"""
    print("🏭 Création des équipements de démonstration...")
    
    demo_equipements = [
        {
            "nom": "Compresseur Atlas Copco GA15",
            "type": TypeEquipement.INDUSTRIEL,
            "numero_serie": "AC-2023-001",
            "localisation": "Atelier Principal - Zone A",
            "statut": StatutEquipement.OPERATIONNEL,
            "date_installation": datetime(2023, 1, 15),
        },
        {
            "nom": "Pompe Centrifuge Grundfos",
            "type": TypeEquipement.INDUSTRIEL, 
            "numero_serie": "GF-2023-005",
            "localisation": "Station de Pompage",
            "statut": StatutEquipement.OPERATIONNEL,
            "date_installation": datetime(2023, 3, 20),
        },
        {
            "nom": "Générateur Caterpillar 250kW",
            "type": TypeEquipement.INDUSTRIEL,
            "numero_serie": "CAT-2022-012",
            "localisation": "Salle Génératrice", 
            "statut": StatutEquipement.EN_MAINTENANCE,
            "date_installation": datetime(2022, 11, 10),
        },
        {
            "nom": "Convoyeur Bande B-Series",
            "type": TypeEquipement.INDUSTRIEL,
            "numero_serie": "CV-2023-003",
            "localisation": "Ligne Production 1",
            "statut": StatutEquipement.OPERATIONNEL,
            "date_installation": datetime(2023, 2, 5),
        }
    ]
    
    for eq_data in demo_equipements:
        existing = db.query(Equipement).filter(
            Equipement.numero_serie == eq_data["numero_serie"]
        ).first()
        if not existing:
            equipement = Equipement(**eq_data)
            db.add(equipement)
            print(f"  ✅ Équipement créé: {eq_data['nom']}")
        else:
            print(f"  ⏭️  Équipement existe: {eq_data['nom']}")
    
    db.commit()


def create_demo_techniciens(db):
    """Crée les techniciens de démonstration"""
    print("👷 Création des techniciens de démonstration...")
    
    demo_techniciens = [
        {
            "nom": "Bennani",
            "prenom": "Mohammed",
            "email": "m.bennani@mif-maroc.com",
            "telephone": "+212 6 12 34 56 78",
            "specialite": "Mécanique Industrielle",
            "statut": StatutTechnicien.DISPONIBLE,
        },
        {
            "nom": "Alami", 
            "prenom": "Fatima",
            "email": "f.alami@mif-maroc.com",
            "telephone": "+212 6 87 65 43 21",
            "specialite": "Électricité et Automation",
            "statut": StatutTechnicien.DISPONIBLE,
        },
        {
            "nom": "Tazi",
            "prenom": "Youssef", 
            "email": "y.tazi@mif-maroc.com",
            "telephone": "+212 6 55 44 33 22",
            "specialite": "Hydraulique et Pneumatique",
            "statut": StatutTechnicien.EN_MISSION,
        }
    ]
    
    for tech_data in demo_techniciens:
        existing = db.query(Technicien).filter(
            Technicien.email == tech_data["email"]
        ).first()
        if not existing:
            technicien = Technicien(**tech_data)
            db.add(technicien)
            print(f"  ✅ Technicien créé: {tech_data['prenom']} {tech_data['nom']}")
        else:
            print(f"  ⏭️  Technicien existe: {tech_data['prenom']} {tech_data['nom']}")
    
    db.commit()


def create_demo_interventions(db):
    """Crée les interventions de démonstration"""
    print("🔧 Création des interventions de démonstration...")
    
    # Récupérer les IDs des équipements et techniciens créés
    equipements = db.query(Equipement).all()
    techniciens = db.query(Technicien).all()
    
    if not equipements or not techniciens:
        print("  ⚠️  Pas d'équipements ou techniciens - intervention ignorée")
        return
    
    demo_interventions = [
        {
            "titre": "Maintenance préventive compresseur",
            "description": "Contrôle mensuel du compresseur Atlas Copco : vérification pression, changement filtres, contrôle huile",
            "equipement_id": equipements[0].id,
            "technicien_id": techniciens[0].id,
            "priorite": PrioriteIntervention.MOYENNE,
            "statut": StatutIntervention.TERMINEE,
            "date_debut": datetime.now() - timedelta(days=5),
            "date_fin": datetime.now() - timedelta(days=4),
        },
        {
            "titre": "Réparation pompe centrifuge",
            "description": "Remplacement joint défaillant sur pompe Grundfos - fuite détectée",
            "equipement_id": equipements[1].id,
            "technicien_id": techniciens[1].id,
            "priorite": PrioriteIntervention.HAUTE,
            "statut": StatutIntervention.EN_COURS,
            "date_debut": datetime.now() - timedelta(days=1),
        },
        {
            "titre": "Révision générale générateur",
            "description": "Révision 500h générateur Caterpillar : contrôle moteur, test démarrage, vérification circuit",
            "equipement_id": equipements[2].id,
            "technicien_id": techniciens[2].id,
            "priorite": PrioriteIntervention.HAUTE,
            "statut": StatutIntervention.PLANIFIEE,
            "date_debut": datetime.now() + timedelta(days=2),
        }
    ]
    
    for interv_data in demo_interventions:
        existing = db.query(Intervention).filter(
            Intervention.titre == interv_data["titre"]
        ).first()
        if not existing:
            intervention = Intervention(**interv_data)
            db.add(intervention)
            print(f"  ✅ Intervention créée: {interv_data['titre']}")
        else:
            print(f"  ⏭️  Intervention existe: {interv_data['titre']}")
    
    db.commit()


def main():
    """Point d'entrée principal"""
    print("🚀 Génération des données de démonstration ERP MIF Maroc")
    print("=" * 60)
    
    db = SessionLocal()
    try:
        create_demo_users(db)
        create_demo_equipements(db)
        create_demo_techniciens(db)
        create_demo_interventions(db)
        
        print("=" * 60)
        print("✅ Données de démonstration créées avec succès!")
        print("\n📋 Comptes de connexion créés:")
        print("  Admin: admin@mif-maroc.com / AdminPass123!")
        print("  Responsable: responsable@mif-maroc.com / RespPass123!")
        print("  Technicien: ahmed@mif-maroc.com / TechPass123!")
        print("  Client: contact@abc.com / ClientPass123!")
        
    except Exception as e:
        print(f"❌ Erreur lors de la génération: {e}")
        db.rollback()
        raise
    finally:
        db.close()


if __name__ == "__main__":
    main()