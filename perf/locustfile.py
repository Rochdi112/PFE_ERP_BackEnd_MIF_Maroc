# perf/locustfile.py

"""
Script de tests de performance Locust pour ERP MIF Maroc
Usage: locust -f perf/locustfile.py --users 100 --spawn-rate 10 -H http://localhost:8000
"""

import json
from random import randint

from locust import HttpUser, task, between


class ERPUser(HttpUser):
    wait_time = between(0.5, 2.0)
    
    def on_start(self):
        """Authentification au démarrage de chaque utilisateur"""
        self.token = None
        self.authenticate()
        
    def authenticate(self):
        """Authentification avec un utilisateur test"""
        response = self.client.post("/api/v1/auth/token", data={
            "username": "test@example.com",
            "password": "TempPass123!"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]
        else:
            print(f"Échec authentification: {response.status_code}")
            
    def get_headers(self):
        """Headers avec token d'authentification"""
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(3)
    def list_equipements(self):
        """Test de liste des équipements (lecture fréquente)"""
        self.client.get("/api/v1/equipements/", headers=self.get_headers())

    @task(3)
    def list_interventions(self):
        """Test de liste des interventions (lecture fréquente)"""
        self.client.get("/api/v1/interventions/", headers=self.get_headers())

    @task(2)
    def get_dashboard(self):
        """Test du tableau de bord"""
        self.client.get("/api/v1/dashboard/", headers=self.get_headers())

    @task(1)
    def create_intervention(self):
        """Test de création d'intervention (écriture moins fréquente)"""
        data = {
            "equipement_id": randint(1, 10),
            "titre": f"Test Performance {randint(1, 1000)}",
            "description": "Intervention créée par test de performance",
            "priorite": "MOYENNE",
            "statut": "OUVERTE"
        }
        self.client.post("/api/v1/interventions/", 
                        json=data, 
                        headers=self.get_headers())

    @task(1)
    def list_techniciens(self):
        """Test de liste des techniciens"""
        self.client.get("/api/v1/techniciens/", headers=self.get_headers())

    @task(1)
    def get_planning(self):
        """Test du planning"""
        self.client.get("/api/v1/planning/", headers=self.get_headers())

    @task(1)
    def health_check(self):
        """Test de santé de l'application"""
        self.client.get("/api/v1/health/")


class AdminUser(HttpUser):
    """Utilisateur administrateur pour tests spécialisés"""
    weight = 1  # Moins d'admins que d'utilisateurs normaux
    wait_time = between(1, 3)
    
    def on_start(self):
        self.token = None
        self.authenticate_admin()
        
    def authenticate_admin(self):
        """Authentification admin"""
        response = self.client.post("/api/v1/auth/token", data={
            "username": "admin@example.com", 
            "password": "AdminPass123!"
        })
        if response.status_code == 200:
            self.token = response.json()["access_token"]

    def get_headers(self):
        if self.token:
            return {"Authorization": f"Bearer {self.token}"}
        return {}

    @task(2)
    def manage_users(self):
        """Tests de gestion des utilisateurs (admin)"""
        self.client.get("/api/v1/users/", headers=self.get_headers())

    @task(1)
    def create_equipement(self):
        """Test de création d'équipement (admin)"""
        data = {
            "nom": f"Équipement Test {randint(1, 1000)}",
            "type": "INDUSTRIEL",
            "localisation": "Atelier Test",
            "statut": "OPERATIONNEL"
        }
        self.client.post("/api/v1/equipements/", 
                        json=data, 
                        headers=self.get_headers())

    @task(1)
    def view_reports(self):
        """Test d'accès aux rapports (admin)"""
        self.client.get("/api/v1/dashboard/admin", headers=self.get_headers())