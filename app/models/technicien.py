# app/models/technicien.py
"""
Modèle Technicien - Gestion des techniciens de maintenance.

Ce module gère les techniciens terrain de l'ERP :
- Profils techniques avec compétences spécialisées
- Organisation en équipes et zones géographiques
- Disponibilité et planning de travail
- Relations avec interventions et utilisateurs
- Niveaux d'habilitation et certifications
- KPI de performance et charge de travail

Architecture:
- Relation 1:1 avec User (rôle technicien)
- Relation N:N avec Competences (table d'association)
- Relations 1:N avec interventions assignées
- Index de performance sur équipe et disponibilité
- Propriétés calculées pour KPI terrain
- Interface to_dict() standardisée pour API
"""

from sqlalchemy import Column, Integer, String, ForeignKey, Table, DateTime, Boolean, Text, Enum, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base
from typing import TYPE_CHECKING, Optional, Dict, Any, List
import enum

# NOTE: Import conditionnel pour éviter les imports circulaires
if TYPE_CHECKING:
    from .user import User
    from .intervention import Intervention

# Import direct nécessaire pour les filtres
from .intervention import Intervention, StatutIntervention


class DisponibiliteTechnicien(str, enum.Enum):
    """
    États de disponibilité des techniciens.
    
    - disponible : prêt pour nouvelle affectation
    - occupe : intervention en cours
    - conge : en congés/absence
    - formation : en formation
    - indisponible : temporairement indisponible
    """
    disponible = "disponible"
    occupe = "occupe"
    conge = "conge"
    formation = "formation"
    indisponible = "indisponible"


class NiveauCompetence(str, enum.Enum):
    """
    Niveaux de maîtrise des compétences.
    
    - debutant : niveau 1, encadrement requis
    - intermediaire : niveau 2, autonome standard
    - avance : niveau 3, interventions complexes
    - expert : niveau 4, référent technique
    """
    debutant = "debutant"
    intermediaire = "intermediaire"
    avance = "avance"
    expert = "expert"


# Table d'association many-to-many entre Technicien et Compétence avec niveau
technicien_competence = Table(
    "technicien_competence",
    Base.metadata,
    Column("technicien_id", Integer, ForeignKey("techniciens.id", ondelete="CASCADE"), primary_key=True),
    Column("competence_id", Integer, ForeignKey("competences.id", ondelete="CASCADE"), primary_key=True),
    Column("niveau", Enum(NiveauCompetence), default=NiveauCompetence.intermediaire, nullable=False),
    Column("date_acquisition", DateTime, default=datetime.utcnow, nullable=False),
    Column("date_validation", DateTime, nullable=True),
    Column("validee_par", String(255), nullable=True),
    Index('idx_technicien_competence_niveau', 'technicien_id', 'niveau'),
)


class Competence(Base):
    """
    Modèle Compétence - Domaines d'expertise technique.
    
    Définit les compétences techniques requises pour les interventions :
    - Domaines d'expertise (électrique, mécanique, informatique...)
    - Niveaux de certification et habilitations
    - Relations avec techniciens qualifiés
    - Prérequis et formations associées
    """
    __tablename__ = "competences"

    # NOTE: Index pour recherches fréquentes par nom et domaine
    __table_args__ = (
        Index('idx_competence_nom_domaine', 'nom', 'domaine'),
        Index('idx_competence_actif_domaine', 'is_active', 'domaine'),
    )

    id = Column(Integer, primary_key=True, index=True)
    nom = Column(String(255), nullable=False, unique=True, index=True)
    domaine = Column(String(100), nullable=False, index=True)  # Ex: Électricité, Mécanique, IT
    description = Column(Text, nullable=True)
    niveau_requis_minimum = Column(Enum(NiveauCompetence), default=NiveauCompetence.intermediaire, nullable=False)
    
    # Métadonnées et validation
    is_active = Column(Boolean, default=True, nullable=False)
    necessite_certification = Column(Boolean, default=False, nullable=False)
    duree_validite_mois = Column(Integer, nullable=True)  # Validité de la certification
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)

    # Relations ORM
    techniciens = relationship(
        "Technicien",
        secondary=technicien_competence,
        back_populates="competences",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        """Représentation concise pour debugging."""
        return f"<Competence(id={self.id}, nom='{self.nom}', domaine='{self.domaine}')>"

    @property
    def nb_techniciens_qualifies(self) -> int:
        """Nombre de techniciens maîtrisant cette compétence."""
        return self.techniciens.count()

    def to_dict(self) -> Dict[str, Any]:
        """Sérialisation en dictionnaire."""
        return {
            "id": self.id,
            "nom": self.nom,
            "domaine": self.domaine,
            "description": self.description,
            "niveau_requis_minimum": self.niveau_requis_minimum.value,
            "is_active": self.is_active,
            "necessite_certification": self.necessite_certification,
            "duree_validite_mois": self.duree_validite_mois,
            "nb_techniciens_qualifies": self.nb_techniciens_qualifies,
        }


class Technicien(Base):
    """
    Modèle Technicien - Personnel technique de maintenance.
    
    Gestion complète des techniciens terrain avec :
    - Profil technique et compétences spécialisées
    - Organisation en équipes et zones d'intervention
    - Disponibilité temps réel et planning
    - Affectation et suivi des interventions
    - Performance et charge de travail
    - Habilitations et certifications
    
    Relations clés :
    - 1:1 avec User (compte utilisateur)
    - N:N avec Competences (expertise technique)
    - 1:N avec Interventions (affectations)
    
    Performances :
    - Index composites sur équipe+disponibilité, zone+niveau
    - Relations lazy=dynamic pour collections volumineuses
    - Propriétés calculées pour KPI de performance
    """
    __tablename__ = "techniciens"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True

    # NOTE: Index composites pour optimiser affectations et planning
    __table_args__ = (
        Index('idx_technicien_equipe_dispo', 'equipe', 'disponibilite'),
        Index('idx_technicien_zone_niveau', 'zone_intervention', 'niveau_technicien'),
        Index('idx_technicien_actif_equipe', 'is_active', 'equipe'),
    )

    id = Column(Integer, primary_key=True, index=True)
    
    # Organisation et équipe
    equipe = Column(String(100), nullable=True, index=True)
    numero_badge = Column(String(20), unique=True, nullable=True, index=True)
    niveau_technicien = Column(Enum(NiveauCompetence), default=NiveauCompetence.intermediaire, nullable=False, index=True)
    
    # Zone d'intervention et mobilité
    zone_intervention = Column(String(255), nullable=True, index=True)
    rayon_deplacement_km = Column(Integer, default=50, nullable=False)
    vehicule_service = Column(String(100), nullable=True)
    
    # Disponibilité et planning
    disponibilite = Column(Enum(DisponibiliteTechnicien), default=DisponibiliteTechnicien.disponible, nullable=False, index=True)
    horaires_travail = Column(String(100), default="08:00-17:00", nullable=True)
    astreinte = Column(Boolean, default=False, nullable=False)
    
    # Statut et dates
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    date_embauche = Column(DateTime, nullable=True)
    date_fin_contrat = Column(DateTime, nullable=True)
    
    # Contact d'urgence
    telephone_urgence = Column(String(20), nullable=True)
    
    # Métadonnées système
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    derniere_connexion = Column(DateTime, nullable=True)
    
    # Notes et observations
    notes_rh = Column(Text, nullable=True)
    qualifications_speciales = Column(Text, nullable=True)

    # Clé étrangère vers User (obligatoire)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, unique=True, index=True)

    # 🔗 Relations ORM optimisées
    
    # Relation principale avec utilisateur (1:1)
    user: "User" = relationship(
        "User", 
        back_populates="technicien", 
        lazy="select"
    )

    # Relations avec compétences (N:N avec métadonnées)
    competences = relationship(
        "Competence",
        secondary=technicien_competence,
        back_populates="techniciens",
        lazy="select"
    )

    # Relations avec interventions (1:N) - lazy dynamic pour performances
    interventions = relationship(
        "Intervention", 
        back_populates="technicien",
        lazy="dynamic",
        order_by="desc(Intervention.date_creation)"
    )

    def __repr__(self) -> str:
        """Représentation concise pour debugging."""
        return f"<Technicien(id={self.id}, user='{self.user.username if self.user else 'N/A'}', équipe='{self.equipe}', dispo='{self.disponibilite.value}')>"

    # 🏷️ Propriétés métier et KPI de performance

    @property
    def nom_complet(self) -> str:
        """Nom complet du technicien via l'utilisateur."""
        return self.user.display_name if self.user else f"Technicien #{self.id}"

    @property
    def email(self) -> Optional[str]:
        """Email du technicien via l'utilisateur."""
        return self.user.email if self.user else None

    @property
    def est_disponible(self) -> bool:
        """Vérifie si le technicien est disponible pour nouvelle affectation."""
        return (
            self.is_active and 
            self.disponibilite == DisponibiliteTechnicien.disponible
        )

    @property
    def est_occupe(self) -> bool:
        """Vérifie si le technicien est occupé sur intervention."""
        return self.disponibilite == DisponibiliteTechnicien.occupe

    @property
    def est_en_conge(self) -> bool:
        """Vérifie si le technicien est en congé."""
        return self.disponibilite == DisponibiliteTechnicien.conge

    @property
    def est_expert(self) -> bool:
        """Vérifie si le technicien a un niveau expert."""
        return self.niveau_technicien == NiveauCompetence.expert

    @property
    def anciennete_jours(self) -> Optional[int]:
        """Ancienneté en jours depuis l'embauche."""
        if not self.date_embauche:
            return None
        return (datetime.utcnow() - self.date_embauche).days

    @property
    def anciennete_annees(self) -> Optional[float]:
        """Ancienneté en années."""
        if not self.anciennete_jours:
            return None
        return round(self.anciennete_jours / 365.25, 1)

    @property
    def nb_interventions_total(self) -> int:
        """Nombre total d'interventions assignées."""
        return self.interventions.count()

    @property
    def nb_interventions_actives(self) -> int:
        """Nombre d'interventions actuellement actives."""
        return self.interventions.filter(
            Intervention.statut.in_([
                StatutIntervention.affectee,
                StatutIntervention.en_cours,
                StatutIntervention.en_attente
            ])
        ).count()

    @property
    def nb_interventions_en_cours(self) -> int:
        """Nombre d'interventions en cours d'exécution."""
        return self.interventions.filter_by(statut=StatutIntervention.en_cours).count()

    @property
    def nb_interventions_mois_courant(self) -> int:
        """Nombre d'interventions du mois en cours."""
        debut_mois = datetime.utcnow().replace(day=1, hour=0, minute=0, second=0, microsecond=0)
        return self.interventions.filter(
            Intervention.date_creation >= debut_mois
        ).count()

    @property
    def nb_interventions_terminees(self) -> int:
        """Nombre d'interventions terminées."""
        return self.interventions.filter_by(statut=StatutIntervention.cloturee).count()

    @property
    def nb_competences(self) -> int:
        """Nombre de compétences maîtrisées."""
        return len(self.competences)

    @property
    def charge_travail_actuelle(self) -> str:
        """Évaluation textuelle de la charge de travail."""
        nb_actives = self.nb_interventions_actives
        if nb_actives == 0:
            return "Libre"
        elif nb_actives <= 2:
            return "Normale"
        elif nb_actives <= 4:
            return "Élevée"
        else:
            return "Surchargé"

    @property
    def niveau_charge_numerique(self) -> int:
        """Niveau de charge numérique (0-5) pour tri/affectation."""
        return min(self.nb_interventions_actives, 5)

    @property
    def derniere_intervention(self) -> Optional["Intervention"]:
        """Dernière intervention assignée."""
        return self.interventions.first()

    @property
    def derniere_intervention_date(self) -> Optional[datetime]:
        """Date de la dernière intervention."""
        derniere = self.derniere_intervention
        return derniere.date_creation if derniere else None

    @property
    def intervention_en_cours(self) -> Optional["Intervention"]:
        """Intervention actuellement en cours d'exécution."""
        return self.interventions.filter_by(statut=StatutIntervention.en_cours).first()

    @property
    def taux_reussite(self) -> Optional[float]:
        """Taux de réussite basé sur les interventions clôturées."""
        terminees = self.nb_interventions_terminees
        if terminees == 0:
            return None
        
        # Considère comme réussie une intervention clôturée sans réouverture rapide
        reussites = 0
        for intervention in self.interventions.filter_by(statut=StatutIntervention.cloturee).all():
            # Vérifier s'il n'y a pas eu de réouverture dans les 7 jours
            if intervention.date_cloture:
                interventions_suivantes = self.interventions.filter(
                    Intervention.equipement_id == intervention.equipement_id,
                    Intervention.date_creation > intervention.date_cloture,
                    Intervention.date_creation <= intervention.date_cloture + timedelta(days=7)
                ).count()
                if interventions_suivantes == 0:
                    reussites += 1
                    
        return round(reussites / terminees * 100, 1)

    @property
    def temps_moyen_intervention(self) -> Optional[float]:
        """Temps moyen d'intervention en heures."""
        interventions_avec_duree = self.interventions.filter(
            Intervention.duree_reelle.isnot(None)
        ).all()
        
        if not interventions_avec_duree:
            return None
            
        total_minutes = sum(i.duree_reelle for i in interventions_avec_duree)
        return round(total_minutes / len(interventions_avec_duree) / 60, 1)

    @property
    def satisfaction_moyenne(self) -> Optional[float]:
        """Note de satisfaction moyenne des clients."""
        interventions_notees = self.interventions.filter(
            Intervention.satisfaction_client.isnot(None)
        ).all()
        
        if not interventions_notees:
            return None
            
        total = sum(i.satisfaction_client for i in interventions_notees)
        return round(total / len(interventions_notees), 2)

    @property
    def competences_par_domaine(self) -> Dict[str, List[str]]:
        """Compétences groupées par domaine."""
        domaines = {}
        for competence in self.competences:
            if competence.domaine not in domaines:
                domaines[competence.domaine] = []
            domaines[competence.domaine].append(competence.nom)
        return domaines

    @property
    def niveau_global(self) -> str:
        """Niveau global calculé basé sur compétences et expérience."""
        if self.est_expert or self.nb_competences >= 5:
            return "Expert"
        elif self.niveau_technicien == NiveauCompetence.avance or self.nb_competences >= 3:
            return "Avancé"
        elif self.anciennete_annees and self.anciennete_annees >= 2:
            return "Confirmé"
        else:
            return "Junior"

    @property
    def statut_disponibilite_couleur(self) -> str:
        """Couleur associée au statut (pour UI)."""
        couleurs = {
            DisponibiliteTechnicien.disponible: "#green",
            DisponibiliteTechnicien.occupe: "#orange",
            DisponibiliteTechnicien.conge: "#blue",
            DisponibiliteTechnicien.formation: "#purple",
            DisponibiliteTechnicien.indisponible: "#red"
        }
        return couleurs.get(self.disponibilite, "#gray")

    @property
    def peut_prendre_urgence(self) -> bool:
        """Vérifie si peut prendre une intervention urgente."""
        return (
            self.est_disponible or 
            (self.nb_interventions_actives <= 1 and self.astreinte)
        )

    @property
    def score_affectation(self) -> int:
        """Score d'affectation pour algorithme automatique (0-100)."""
        score = 50  # Base
        
        # Bonus disponibilité
        if self.est_disponible:
            score += 30
        elif self.nb_interventions_actives <= 1:
            score += 15
        else:
            score -= 20
            
        # Bonus compétences
        score += min(self.nb_competences * 5, 20)
        
        # Bonus niveau
        niveau_bonus = {
            NiveauCompetence.expert: 15,
            NiveauCompetence.avance: 10,
            NiveauCompetence.intermediaire: 5,
            NiveauCompetence.debutant: 0
        }
        score += niveau_bonus.get(self.niveau_technicien, 0)
        
        # Bonus satisfaction
        if self.satisfaction_moyenne and self.satisfaction_moyenne >= 4.5:
            score += 10
        elif self.satisfaction_moyenne and self.satisfaction_moyenne <= 3.0:
            score -= 10
            
        return max(0, min(100, score))

    # 🔧 Méthodes métier pour gestion technicien

    def changer_disponibilite(self, nouvelle_dispo: DisponibiliteTechnicien, raison: str = None) -> None:
        """
        Change la disponibilité du technicien.
        
        Args:
            nouvelle_dispo: Nouvelle disponibilité
            raison: Raison du changement (optionnel)
        """
        ancienne_dispo = self.disponibilite
        self.disponibilite = nouvelle_dispo
        self.updated_at = datetime.utcnow()
        
        # Mise à jour automatique de la dernière connexion si passage en disponible
        if nouvelle_dispo == DisponibiliteTechnicien.disponible:
            self.derniere_connexion = datetime.utcnow()

    def marquer_occupe(self) -> None:
        """Marque le technicien comme occupé."""
        self.changer_disponibilite(DisponibiliteTechnicien.occupe)

    def marquer_disponible(self) -> None:
        """Marque le technicien comme disponible."""
        self.changer_disponibilite(DisponibiliteTechnicien.disponible)

    def ajouter_competence(self, competence: Competence, niveau: NiveauCompetence = NiveauCompetence.intermediaire) -> None:
        """
        Ajoute une compétence au technicien.
        
        Args:
            competence: Compétence à ajouter
            niveau: Niveau de maîtrise
        """
        if competence not in self.competences:
            self.competences.append(competence)
            # NOTE: Le niveau sera géré par la table d'association

    def retirer_competence(self, competence: Competence) -> None:
        """Retire une compétence du technicien."""
        if competence in self.competences:
            self.competences.remove(competence)

    def peut_intervenir_sur(self, competences_requises: List[str]) -> bool:
        """
        Vérifie si le technicien peut intervenir selon les compétences requises.
        
        Args:
            competences_requises: Liste des noms de compétences requises
            
        Returns:
            bool: True si le technicien a toutes les compétences
        """
        competences_technicien = [c.nom for c in self.competences]
        return all(comp in competences_technicien for comp in competences_requises)

    def est_dans_zone(self, localisation: str) -> bool:
        """
        Vérifie si une localisation est dans la zone d'intervention.
        
        Args:
            localisation: Localisation à vérifier
            
        Returns:
            bool: True si dans la zone (simplifié pour l'exemple)
        """
        if not self.zone_intervention:
            return True  # Pas de restriction de zone
        
        # Logique simplifiée - à améliorer avec géolocalisation
        return localisation.lower() in self.zone_intervention.lower()

    def get_interventions_urgentes(self) -> List["Intervention"]:
        """Retourne les interventions urgentes assignées."""
        from .intervention import PrioriteIntervention
        return list(self.interventions.filter(
            Intervention.priorite.in_([
                PrioriteIntervention.urgente,
                PrioriteIntervention.haute
            ]),
            Intervention.statut.in_([
                StatutIntervention.affectee,
                StatutIntervention.en_cours,
                StatutIntervention.en_attente
            ])
        ).all())

    def get_interventions_en_retard(self) -> List["Intervention"]:
        """Retourne les interventions en retard."""
        interventions_actives = self.interventions.filter(
            Intervention.statut.in_([
                StatutIntervention.affectee,
                StatutIntervention.en_cours,
                StatutIntervention.en_attente
            ])
        ).all()
        
        return [i for i in interventions_actives if i.est_en_retard]

    def calculer_charge_semaine(self, date_debut: Optional[datetime] = None) -> Dict[str, Any]:
        """
        Calcule la charge de travail pour la semaine.
        
        Args:
            date_debut: Date de début de semaine (défaut: lundi courant)
            
        Returns:
            Dict avec les métriques de charge
        """
        if not date_debut:
            # Début de semaine (lundi)
            aujourd_hui = datetime.utcnow()
            date_debut = aujourd_hui - timedelta(days=aujourd_hui.weekday())
            
        date_fin = date_debut + timedelta(days=7)
        
        interventions_semaine = self.interventions.filter(
            Intervention.date_creation >= date_debut,
            Intervention.date_creation < date_fin
        ).all()
        
        return {
            "date_debut": date_debut.isoformat(),
            "date_fin": date_fin.isoformat(),
            "nb_interventions": len(interventions_semaine),
            "nb_urgentes": len([i for i in interventions_semaine if i.est_urgente]),
            "temps_total_estime": sum(i.duree_estimee or 0 for i in interventions_semaine),
            "temps_total_reel": sum(i.duree_reelle_calculee or 0 for i in interventions_semaine if i.est_terminee),
            "nb_terminees": len([i for i in interventions_semaine if i.est_terminee]),
        }

    def generer_rapport_performance(self, nb_mois: int = 6) -> Dict[str, Any]:
        """
        Génère un rapport de performance sur les N derniers mois.
        
        Args:
            nb_mois: Nombre de mois à analyser
            
        Returns:
            Dict avec les KPI de performance
        """
        date_debut = datetime.utcnow() - timedelta(days=nb_mois * 30)
        
        interventions_periode = self.interventions.filter(
            Intervention.date_creation >= date_debut
        ).all()
        
        return {
            "periode_mois": nb_mois,
            "nb_interventions": len(interventions_periode),
            "nb_terminees": len([i for i in interventions_periode if i.est_terminee]),
            "taux_completion": round(len([i for i in interventions_periode if i.est_terminee]) / len(interventions_periode) * 100, 1) if interventions_periode else 0,
            "taux_reussite": self.taux_reussite,
            "satisfaction_moyenne": self.satisfaction_moyenne,
            "temps_moyen_intervention": self.temps_moyen_intervention,
            "nb_urgentes_traitees": len([i for i in interventions_periode if i.est_urgente]),
            "charge_moyenne": round(len(interventions_periode) / nb_mois, 1),
        }

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        """
        Sérialisation harmonisée en dictionnaire.
        
        Args:
            include_sensitive: Inclut données sensibles/RH (admin/responsable)
            include_relations: Inclut les données des relations liées
            
        Returns:
            Dict contenant les données sérialisées
            
        NOTE: Interface standardisée pour tous les modèles ERP
        """
        # Données de base (toujours incluses)
        data = {
            "id": self.id,
            "nom_complet": self.nom_complet,
            "numero_badge": self.numero_badge,
            "equipe": self.equipe,
            "niveau_technicien": self.niveau_technicien.value,
            "niveau_global": self.niveau_global,
            "zone_intervention": self.zone_intervention,
            "disponibilite": self.disponibilite.value,
            "statut_disponibilite_couleur": self.statut_disponibilite_couleur,
            "is_active": self.is_active,
            "astreinte": self.astreinte,
            
            # Propriétés calculées utiles
            "est_disponible": self.est_disponible,
            "est_occupe": self.est_occupe,
            "charge_travail_actuelle": self.charge_travail_actuelle,
            "niveau_charge_numerique": self.niveau_charge_numerique,
            "peut_prendre_urgence": self.peut_prendre_urgence,
            "score_affectation": self.score_affectation,
            "nb_interventions_total": self.nb_interventions_total,
            "nb_interventions_actives": self.nb_interventions_actives,
            "nb_competences": self.nb_competences,
            "competences_par_domaine": self.competences_par_domaine,
            "derniere_intervention_date": self.derniere_intervention_date.isoformat() if self.derniere_intervention_date else None,
        }
        
        # Données sensibles (RH, performances)
        if include_sensitive:
            data.update({
                "user_id": self.user_id,
                "email": self.email,
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "date_embauche": self.date_embauche.isoformat() if self.date_embauche else None,
                "date_fin_contrat": self.date_fin_contrat.isoformat() if self.date_fin_contrat else None,
                "anciennete_annees": self.anciennete_annees,
                "rayon_deplacement_km": self.rayon_deplacement_km,
                "vehicule_service": self.vehicule_service,
                "horaires_travail": self.horaires_travail,
                "telephone_urgence": self.telephone_urgence,
                "notes_rh": self.notes_rh,
                "qualifications_speciales": self.qualifications_speciales,
                "derniere_connexion": self.derniere_connexion.isoformat() if self.derniere_connexion else None,
                
                # KPI de performance
                "taux_reussite": self.taux_reussite,
                "temps_moyen_intervention": self.temps_moyen_intervention,
                "satisfaction_moyenne": self.satisfaction_moyenne,
                "nb_interventions_mois_courant": self.nb_interventions_mois_courant,
                "nb_interventions_terminees": self.nb_interventions_terminees,
                "nb_interventions_en_cours": self.nb_interventions_en_cours,
            })
        
        # Relations détaillées (pour vues complètes)
        if include_relations:
            data.update({
                "user": self.user.to_dict() if self.user else None,
                "competences": [c.to_dict() for c in self.competences],
                
                # Interventions limitées (pour éviter surcharge)
                "intervention_en_cours": self.intervention_en_cours.to_dict() if self.intervention_en_cours else None,
                "interventions_urgentes": [i.to_dict() for i in self.get_interventions_urgentes()],
                "interventions_en_retard": [i.to_dict() for i in self.get_interventions_en_retard()],
                
                # Rapport de performance synthétique
                "charge_semaine_courante": self.calculer_charge_semaine(),
                "rapport_performance_6_mois": self.generer_rapport_performance(6),
            })
            
        return data

