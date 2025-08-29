# app/models/intervention.py
"""
Modèle Intervention - Cœur métier de l'ERP de maintenance.

Ce module gère le cycle de vie complet des interventions :
- Maintenance préventive et corrective planifiée
- Affectation et suivi des techniciens terrain
- Gestion des statuts et workflow d'intervention
- Traçabilité complète et audit des actions
- Relations avec équipements, clients, contrats
- Gestion des pièces détachées et coûts

Architecture:
- Modèle central du domaine métier maintenance
- Machine d'état robuste pour workflow
- Relations ORM optimisées avec cascade
- Propriétés calculées pour KPI temps réel
- Interface to_dict() standardisée pour API
- Audit trail complet via historiques
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime, Boolean, Enum, Text, Index
from sqlalchemy.orm import relationship
from datetime import datetime, timedelta
from app.db.database import Base
import enum
from typing import TYPE_CHECKING, Optional, Dict, Any, List

# NOTE: Import conditionnel pour éviter les imports circulaires
if TYPE_CHECKING:
    from .user import User
    from .technicien import Technicien
    from .equipement import Equipement
    from .client import Client
    from .contrat import Contrat
    from .document import Document
    from .historique import HistoriqueIntervention
    from .notification import Notification
    from .stock import MouvementStock, InterventionPiece


class InterventionType(str, enum.Enum):
    """
    Types d'intervention de maintenance.
    
    - corrective : intervention suite à panne ou dysfonctionnement
    - preventive : maintenance planifiée selon cycles
    - ameliorative : amélioration/upgrade d'équipement
    - diagnostic : expertise et analyse technique
    """
    corrective = "corrective"
    preventive = "preventive"
    ameliorative = "ameliorative"
    diagnostic = "diagnostic"


class StatutIntervention(str, enum.Enum):
    """
    Machine d'état pour le workflow d'intervention.
    
    Workflow standard :
    ouverte → affectee → en_cours → [en_attente] → cloturee → archivee
    
    - ouverte : nouvelle intervention créée
    - affectee : technicien assigné
    - en_cours : travaux démarrés sur site
    - en_attente : pause (attente pièce/autorisation)
    - cloturee : travaux terminés et validés
    - annulee : intervention annulée
    - archivee : archivage administratif
    """
    ouverte = "ouverte"
    affectee = "affectee"
    en_cours = "en_cours"
    en_attente = "en_attente"
    cloturee = "cloturee"
    annulee = "annulee"
    archivee = "archivee"


class PrioriteIntervention(str, enum.Enum):
    """
    Niveaux de priorité métier.
    
    - urgente : intervention immédiate (< 2h)
    - haute : intervention rapide (< 24h)
    - normale : intervention standard (< 72h)
    - basse : intervention différable (< 1 semaine)
    - programmee : intervention planifiée
    """
    urgente = "urgente"
    haute = "haute"
    normale = "normale"
    basse = "basse"
    programmee = "programmee"


class Intervention(Base):
    """
    Modèle Intervention - Gestion complète des interventions de maintenance.
    
    Point central du workflow de maintenance avec :
    - Cycle de vie complet avec machine d'état
    - Affectation et suivi des ressources (technicien, équipement)
    - Planification et respect des délais
    - Gestion des coûts et consommables
    - Traçabilité et audit complet des actions
    - Relations contractuelles et client
    
    Relations clés :
    - N:1 avec Equipement (cible de l'intervention)
    - N:1 avec Technicien (exécutant assigné)
    - N:1 avec Client (demandeur/propriétaire)
    - N:1 avec Contrat (couverture contractuelle)
    - 1:N avec Documents (rapports, photos, plans)
    - 1:N avec Historiques (audit trail)
    - 1:N avec Notifications (alertes automatiques)
    - 1:N avec MouvementsStock (pièces consommées)
    
    Performances :
    - Index composites sur statut+priorité, technicien+statut
    - Relations lazy=dynamic pour collections volumineuses
    - Propriétés calculées optimisées pour KPI
    """
    __tablename__ = "interventions"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True

    # NOTE: Index composites pour requêtes métier critiques
    __table_args__ = (
        Index('idx_intervention_statut_priorite', 'statut', 'priorite'),
        Index('idx_intervention_technicien_statut', 'technicien_id', 'statut'),
    # La colonne DB est nommée "type" (attribut Python: type_intervention)
    Index('idx_intervention_equipement_type', 'equipement_id', 'type'),
        Index('idx_intervention_client_statut', 'client_id', 'statut'),
        Index('idx_intervention_dates', 'date_creation', 'date_limite'),
    Index('idx_intervention_type_urgence', 'type', 'urgence'),
    )

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)
    
    # Informations de base
    titre = Column(String(255), nullable=False, index=True)
    description = Column(Text, nullable=True)
    type_intervention = Column("type", Enum(InterventionType), nullable=False, index=True)
    
    # Cycle de vie et priorités
    statut = Column(Enum(StatutIntervention), default=StatutIntervention.ouverte, nullable=False, index=True)
    priorite = Column(Enum(PrioriteIntervention), default=PrioriteIntervention.normale, nullable=False, index=True)
    urgence = Column(Boolean, default=False, nullable=False, index=True)
    
    # Dates critiques du workflow
    date_creation = Column(DateTime, default=datetime.utcnow, nullable=False, index=True)
    date_limite = Column(DateTime, nullable=True, index=True)
    date_affectation = Column(DateTime, nullable=True)
    date_debut_travaux = Column(DateTime, nullable=True)
    date_fin_travaux = Column(DateTime, nullable=True)
    date_cloture = Column(DateTime, nullable=True)
    date_archivage = Column(DateTime, nullable=True)
    
    # Gestion des délais et performances
    duree_estimee = Column(Integer, nullable=True)  # en minutes
    duree_reelle = Column(Integer, nullable=True)   # en minutes
    temps_deplacement = Column(Integer, nullable=True)  # en minutes
    
    # Gestion financière
    cout_estime = Column(Integer, nullable=True)    # en centimes d'euro
    cout_reel = Column(Integer, nullable=True)      # en centimes d'euro
    cout_pieces = Column(Integer, nullable=True)    # en centimes d'euro
    cout_main_oeuvre = Column(Integer, nullable=True)  # en centimes d'euro
    
    # Résultats et validation
    rapport_intervention = Column(Text, nullable=True)
    travaux_realises = Column(Text, nullable=True)
    recommandations = Column(Text, nullable=True)
    validation_client = Column(Boolean, default=False, nullable=False)
    satisfaction_client = Column(Integer, nullable=True)  # Note 1-5
    
    # Métadonnées système
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    created_by_id = Column(Integer, ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    
    # Relation équipement (optionnelle pour compat tests)
    equipement_id = Column(Integer, ForeignKey("equipements.id", ondelete="CASCADE"), nullable=True, index=True)
    
    # Relations optionnelles métier
    technicien_id = Column(Integer, ForeignKey("techniciens.id", ondelete="SET NULL"), nullable=True, index=True)
    client_id = Column(Integer, ForeignKey("clients.id", ondelete="CASCADE"), nullable=True, index=True)
    contrat_id = Column(Integer, ForeignKey("contrats.id", ondelete="SET NULL"), nullable=True, index=True)

    # 🔗 Relations ORM optimisées pour performance
    
    # Relations principales (N:1) - chargement immédiat pour données critiques
    equipement: "Equipement" = relationship(
        "Equipement", 
        back_populates="interventions", 
        lazy="select"
    )
    
    technicien: Optional["Technicien"] = relationship(
        "Technicien", 
        back_populates="interventions", 
        lazy="select"
    )
    
    client: Optional["Client"] = relationship(
        "Client", 
        back_populates="interventions", 
        lazy="select"
    )
    
    contrat: Optional["Contrat"] = relationship(
        "Contrat", 
        back_populates="interventions", 
        lazy="select"
    )
    
    created_by: Optional["User"] = relationship(
        "User",
        foreign_keys=[created_by_id],
        lazy="select"
    )
    
    # Relations de traçabilité (1:N) - lazy dynamic pour volumes
    documents = relationship(
        "Document", 
        back_populates="intervention", 
        cascade="all, delete-orphan",
        lazy="dynamic",
    order_by="desc(Document.date_upload)"
    )
    
    historiques = relationship(
        "HistoriqueIntervention", 
        back_populates="intervention", 
        cascade="all, delete-orphan",
        order_by="desc(HistoriqueIntervention.horodatage)",
        lazy="dynamic"
    )
    
    notifications = relationship(
        "Notification", 
        back_populates="intervention", 
        cascade="all, delete-orphan",
        lazy="dynamic",
    order_by="desc(Notification.date_envoi)"
    )
    
    # Relations stock et consommables (1:N)
    mouvements_stock = relationship(
        "MouvementStock", 
        back_populates="intervention", 
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(MouvementStock.date_mouvement)"
    )
    
    pieces_utilisees = relationship(
        "InterventionPiece", 
        back_populates="intervention", 
        cascade="all, delete-orphan",
        lazy="dynamic"
    )

    def __repr__(self) -> str:
        """Représentation concise pour debugging."""
        return (
            f"<Intervention(id={self.id}, titre='{self.titre[:30]}...', "
            f"statut='{self.statut.value}', priorite='{self.priorite.value}')>"
        )

    # Compatibilité: accepter les kwargs "type" et valeurs str pour les enums
    def __init__(self, **kwargs: Any) -> None:  # type: ignore[override]
        # Mappe 'type' JSON -> attribut ORM 'type_intervention'
        t = kwargs.pop("type", None)
        if t is not None and "type_intervention" not in kwargs:
            if isinstance(t, str):
                norm = (
                    t.lower()
                    .replace("é", "e")
                    .replace("è", "e")
                    .replace("ê", "e")
                    .replace("à", "a")
                )
                try:
                    kwargs["type_intervention"] = InterventionType(norm)
                except Exception:
                    # Dernier recours: laisse la valeur telle quelle
                    kwargs["type_intervention"] = t
            else:
                kwargs["type_intervention"] = t

        # Normalise statut/priorite si fournis en string
        def _normalize(s: str) -> str:
            return (
                s.lower()
                .replace("é", "e").replace("è", "e").replace("ê", "e")
                .replace("à", "a").replace("ô", "o").replace("î", "i")
            )

        s = kwargs.get("statut")
        if isinstance(s, str):
            try:
                kwargs["statut"] = StatutIntervention(_normalize(s))
            except Exception:
                pass
        p = kwargs.get("priorite")
        if isinstance(p, str):
            try:
                kwargs["priorite"] = PrioriteIntervention(_normalize(p))
            except Exception:
                pass

        # Affectation standard
        for key, value in kwargs.items():
            setattr(self, key, value)

    # 🏷️ Propriétés métier et machine d'état

    @property
    def est_ouverte(self) -> bool:
        """Vérifie si l'intervention est ouverte (nouveau)."""
        return self.statut == StatutIntervention.ouverte

    @property
    def est_affectee(self) -> bool:
        """Vérifie si l'intervention est affectée à un technicien."""
        return self.statut == StatutIntervention.affectee

    @property
    def est_en_cours(self) -> bool:
        """Vérifie si l'intervention est en cours d'exécution."""
        return self.statut == StatutIntervention.en_cours

    @property
    def est_en_attente(self) -> bool:
        """Vérifie si l'intervention est en attente (pause)."""
        return self.statut == StatutIntervention.en_attente

    @property
    def est_terminee(self) -> bool:
        """Vérifie si l'intervention est terminée (clôturée/archivée)."""
        return self.statut in [StatutIntervention.cloturee, StatutIntervention.archivee]

    @property
    def est_cloturee(self) -> bool:
        """Vérifie si l'intervention est clôturée."""
        return self.statut == StatutIntervention.cloturee

    @property
    def est_annulee(self) -> bool:
        """Vérifie si l'intervention est annulée."""
        return self.statut == StatutIntervention.annulee

    @property
    def est_active(self) -> bool:
        """Vérifie si l'intervention est dans un état actif."""
        return self.statut in [
            StatutIntervention.ouverte,
            StatutIntervention.affectee,
            StatutIntervention.en_cours,
            StatutIntervention.en_attente
        ]

    @property
    def est_urgente(self) -> bool:
        """Vérifie si l'intervention est urgente."""
        return self.urgence or self.priorite == PrioriteIntervention.urgente

    @property
    def est_preventive(self) -> bool:
        """Vérifie si c'est une maintenance préventive."""
        return self.type_intervention == InterventionType.preventive

    @property
    def est_corrective(self) -> bool:
        """Vérifie si c'est une maintenance corrective."""
        return self.type_intervention == InterventionType.corrective

    @property
    def est_en_retard(self) -> bool:
        """Vérifie si l'intervention est en retard par rapport à la date limite."""
        if not self.date_limite or self.est_terminee or self.est_annulee:
            return False
        return datetime.utcnow() > self.date_limite

    @property
    def delai_restant(self) -> Optional[timedelta]:
        """Calcule le délai restant avant la date limite."""
        if not self.date_limite or self.est_terminee or self.est_annulee:
            return None
        return self.date_limite - datetime.utcnow()

    @property
    def delai_restant_heures(self) -> Optional[int]:
        """Délai restant en heures (plus lisible)."""
        delai = self.delai_restant
        return int(delai.total_seconds() / 3600) if delai else None

    @property
    def duree_reelle_calculee(self) -> Optional[int]:
        """Calcule la durée réelle si dates disponibles (en minutes)."""
        if self.date_debut_travaux and self.date_fin_travaux:
            delta = self.date_fin_travaux - self.date_debut_travaux
            return int(delta.total_seconds() / 60)
        elif self.date_debut_travaux and self.est_en_cours:
            # Durée partielle pour intervention en cours
            delta = datetime.utcnow() - self.date_debut_travaux
            return int(delta.total_seconds() / 60)
        return self.duree_reelle

    @property
    def duree_totale_incluant_attentes(self) -> Optional[int]:
        """Durée totale depuis affectation jusqu'à clôture (en minutes)."""
        if self.date_affectation and self.date_cloture:
            delta = self.date_cloture - self.date_affectation
            return int(delta.total_seconds() / 60)
        elif self.date_affectation and self.est_active:
            delta = datetime.utcnow() - self.date_affectation
            return int(delta.total_seconds() / 60)
        return None

    @property
    def temps_ecoule_depuis_creation(self) -> timedelta:
        """Calcule le temps écoulé depuis la création."""
        return datetime.utcnow() - self.date_creation

    @property
    def temps_ecoule_depuis_affectation(self) -> Optional[timedelta]:
        """Temps écoulé depuis l'affectation au technicien."""
        if not self.date_affectation:
            return None
        return datetime.utcnow() - self.date_affectation

    @property
    def ecart_duree_prevue_reelle(self) -> Optional[int]:
        """Écart entre durée estimée et réelle (en minutes)."""
        if self.duree_estimee and self.duree_reelle_calculee:
            return self.duree_reelle_calculee - self.duree_estimee
        return None

    @property
    def taux_respect_delai(self) -> Optional[float]:
        """Taux de respect des délais (1.0 = parfait, >1.0 = dépassement)."""
        if not self.duree_estimee or not self.duree_reelle_calculee:
            return None
        return round(self.duree_reelle_calculee / self.duree_estimee, 2)

    @property
    def niveau_priorite_numerique(self) -> int:
        """Convertit la priorité en valeur numérique pour tri/calculs."""
        mapping = {
            PrioriteIntervention.urgente: 5,
            PrioriteIntervention.haute: 4,
            PrioriteIntervention.normale: 3,
            PrioriteIntervention.basse: 2,
            PrioriteIntervention.programmee: 1
        }
        return mapping.get(self.priorite, 0)

    @property
    def cout_total_reel(self) -> float:
        """Calcule le coût total réel (main d'œuvre + pièces) en euros."""
        total_centimes = 0
        if self.cout_main_oeuvre:
            total_centimes += self.cout_main_oeuvre
        if self.cout_pieces:
            total_centimes += self.cout_pieces
        return round(total_centimes / 100, 2)

    @property
    def cout_pieces_calcule(self) -> float:
        """Calcule le coût des pièces à partir des mouvements stock."""
        total = 0.0
        for piece_utilisee in self.pieces_utilisees:
            if piece_utilisee.piece_detachee and piece_utilisee.piece_detachee.prix_unitaire:
                total += (
                    float(piece_utilisee.piece_detachee.prix_unitaire) / 100 * 
                    piece_utilisee.quantite_utilisee
                )
        return round(total, 2)

    @property
    def ecart_cout_estime_reel(self) -> Optional[float]:
        """Écart entre coût estimé et réel en euros."""
        if self.cout_estime and self.cout_total_reel > 0:
            estime_euros = self.cout_estime / 100
            return round(self.cout_total_reel - estime_euros, 2)
        return None

    @property
    def nb_documents(self) -> int:
        """Nombre de documents attachés."""
        return self.documents.count()

    @property
    def nb_pieces_utilisees(self) -> int:
        """Nombre de types de pièces différentes utilisées."""
        return self.pieces_utilisees.count()

    @property
    def nb_historiques(self) -> int:
        """Nombre d'entrées dans l'historique."""
        return self.historiques.count()

    @property
    def derniere_modification(self) -> datetime:
        """Date de dernière modification (dernier historique ou updated_at)."""
        dernier_historique = self.historiques.first()
        if dernier_historique:
            return dernier_historique.horodatage
        return self.updated_at or self.date_creation

    @property
    def technicien_assigne(self) -> Optional[str]:
        """Nom du technicien assigné (pour affichage)."""
        if self.technicien and self.technicien.user:
            return self.technicien.user.display_name
        return None

    @property
    def client_nom(self) -> Optional[str]:
        """Nom du client (pour affichage)."""
        if self.client:
            return self.client.nom_entreprise or self.client.nom_contact
        return None

    @property
    def equipement_nom(self) -> str:
        """Nom de l'équipement (toujours présent)."""
        return self.equipement.nom if self.equipement else f"Équipement #{self.equipement_id}"

    @property
    def satisfaction_client_label(self) -> Optional[str]:
        """Label de satisfaction client."""
        if not self.satisfaction_client:
            return None
        labels = {
            1: "Très insatisfait",
            2: "Insatisfait", 
            3: "Neutre",
            4: "Satisfait",
            5: "Très satisfait"
        }
        return labels.get(self.satisfaction_client)

    @property
    def statut_couleur(self) -> str:
        """Couleur associée au statut (pour UI)."""
        couleurs = {
            StatutIntervention.ouverte: "#orange",
            StatutIntervention.affectee: "#blue",
            StatutIntervention.en_cours: "#green",
            StatutIntervention.en_attente: "#yellow",
            StatutIntervention.cloturee: "#gray",
            StatutIntervention.annulee: "#red",
            StatutIntervention.archivee: "#lightgray"
        }
        return couleurs.get(self.statut, "#black")

    @property
    def priorite_couleur(self) -> str:
        """Couleur associée à la priorité (pour UI)."""
        couleurs = {
            PrioriteIntervention.urgente: "#red",
            PrioriteIntervention.haute: "#orange",
            PrioriteIntervention.normale: "#blue",
            PrioriteIntervention.basse: "#green",
            PrioriteIntervention.programmee: "#purple"
        }
        return couleurs.get(self.priorite, "#black")

    # 🔧 Méthodes métier pour gestion du workflow

    def peut_etre_modifiee(self) -> bool:
        """Vérifie si l'intervention peut encore être modifiée."""
        return self.statut not in [
            StatutIntervention.cloturee, 
            StatutIntervention.archivee,
            StatutIntervention.annulee
        ]

    def peut_etre_affectee(self) -> bool:
        """Vérifie si l'intervention peut être affectée à un technicien."""
        return self.statut in [StatutIntervention.ouverte, StatutIntervention.affectee]

    def peut_etre_demarree(self) -> bool:
        """Vérifie si l'intervention peut être démarrée."""
        return (
            self.statut == StatutIntervention.affectee and 
            self.technicien_id is not None
        )

    def peut_etre_mise_en_attente(self) -> bool:
        """Vérifie si l'intervention peut être mise en attente."""
        return self.statut == StatutIntervention.en_cours

    def peut_etre_reprise(self) -> bool:
        """Vérifie si l'intervention en attente peut être reprise."""
        return self.statut == StatutIntervention.en_attente

    def peut_etre_cloturee(self) -> bool:
        """Vérifie si l'intervention peut être clôturée."""
        return self.statut in [StatutIntervention.en_cours, StatutIntervention.en_attente]

    def peut_etre_annulee(self) -> bool:
        """Vérifie si l'intervention peut être annulée."""
        return self.statut not in [
            StatutIntervention.cloturee,
            StatutIntervention.archivee,
            StatutIntervention.annulee
        ]

    def peut_etre_archivee(self) -> bool:
        """Vérifie si l'intervention peut être archivée."""
        return self.statut == StatutIntervention.cloturee

    def affecter_technicien(self, technicien_id: int, user_id: Optional[int] = None) -> None:
        """
        Affecte un technicien à l'intervention.
        
        Args:
            technicien_id: ID du technicien à affecter
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_affectee():
            self.technicien_id = technicien_id
            self.date_affectation = datetime.utcnow()
            if self.statut == StatutIntervention.ouverte:
                self.statut = StatutIntervention.affectee
            self.updated_at = datetime.utcnow()

    def demarrer_travaux(self, user_id: Optional[int] = None) -> None:
        """
        Démarre les travaux de l'intervention.
        
        Args:
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_demarree():
            self.date_debut_travaux = datetime.utcnow()
            self.statut = StatutIntervention.en_cours
            self.updated_at = datetime.utcnow()

    def mettre_en_attente(self, raison: str = None, user_id: Optional[int] = None) -> None:
        """
        Met l'intervention en attente.
        
        Args:
            raison: Raison de la mise en attente
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_mise_en_attente():
            self.statut = StatutIntervention.en_attente
            self.updated_at = datetime.utcnow()

    def reprendre_travaux(self, user_id: Optional[int] = None) -> None:
        """
        Reprend une intervention en attente.
        
        Args:
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_reprise():
            self.statut = StatutIntervention.en_cours
            self.updated_at = datetime.utcnow()

    def cloturer(
        self, 
        duree_reelle: Optional[int] = None, 
        cout_reel: Optional[int] = None,
        rapport: Optional[str] = None,
        user_id: Optional[int] = None
    ) -> None:
        """
        Clôture l'intervention.
        
        Args:
            duree_reelle: Durée réelle en minutes
            cout_reel: Coût réel en centimes
            rapport: Rapport de fin d'intervention
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_cloturee():
            self.date_fin_travaux = datetime.utcnow()
            self.date_cloture = datetime.utcnow()
            self.statut = StatutIntervention.cloturee
            
            if duree_reelle is not None:
                self.duree_reelle = duree_reelle
            if cout_reel is not None:
                self.cout_reel = cout_reel
            if rapport:
                self.rapport_intervention = rapport
                
            # Calcul automatique du coût des pièces
            if not self.cout_pieces:
                self.cout_pieces = int(self.cout_pieces_calcule * 100)
                
            self.updated_at = datetime.utcnow()

    def annuler(self, raison: str, user_id: Optional[int] = None) -> None:
        """
        Annule l'intervention.
        
        Args:
            raison: Raison de l'annulation
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_annulee():
            self.statut = StatutIntervention.annulee
            if raison and not self.rapport_intervention:
                self.rapport_intervention = f"Annulation: {raison}"
            self.updated_at = datetime.utcnow()

    def archiver(self, user_id: Optional[int] = None) -> None:
        """
        Archive l'intervention.
        
        Args:
            user_id: ID de l'utilisateur effectuant l'action (pour audit)
        """
        if self.peut_etre_archivee():
            self.statut = StatutIntervention.archivee
            self.date_archivage = datetime.utcnow()
            self.updated_at = datetime.utcnow()

    def ajouter_piece(self, piece_detachee_id: int, quantite: int) -> None:
        """
        Ajoute une pièce détachée utilisée dans l'intervention.
        
        Args:
            piece_detachee_id: ID de la pièce détachée
            quantite: Quantité utilisée
            
        NOTE: La création du mouvement de stock sera gérée par le service
        """
        from app.models.stock import InterventionPiece
        
        # Vérifier si la pièce n'est pas déjà ajoutée
        existing = self.pieces_utilisees.filter_by(piece_detachee_id=piece_detachee_id).first()
        if existing:
            existing.quantite_utilisee += quantite
        else:
            nouvelle_piece = InterventionPiece(
                intervention_id=self.id,
                piece_detachee_id=piece_detachee_id,
                quantite_utilisee=quantite
            )

    def calculer_sla_respect(self) -> Optional[bool]:
        """
        Vérifie le respect du SLA basé sur la priorité.
        
        Returns:
            bool: True si SLA respecté, False sinon, None si pas applicable
        """
        if not self.date_cloture or not self.date_creation:
            return None
            
        duree_reelle = (self.date_cloture - self.date_creation).total_seconds() / 3600  # en heures
        
        # Définition des SLA par priorité (en heures)
        sla_heures = {
            PrioriteIntervention.urgente: 2,
            PrioriteIntervention.haute: 24,
            PrioriteIntervention.normale: 72,
            PrioriteIntervention.basse: 168,  # 1 semaine
            PrioriteIntervention.programmee: None  # Pas de SLA
        }
        
        sla = sla_heures.get(self.priorite)
        return duree_reelle <= sla if sla is not None else None

    def get_prochaines_actions(self) -> List[str]:
        """
        Retourne la liste des actions possibles selon l'état actuel.
        
        Returns:
            List[str]: Liste des actions possibles
        """
        actions = []
        
        if self.peut_etre_affectee():
            actions.append("affecter_technicien")
        if self.peut_etre_demarree():
            actions.append("demarrer_travaux")
        if self.peut_etre_mise_en_attente():
            actions.append("mettre_en_attente")
        if self.peut_etre_reprise():
            actions.append("reprendre_travaux")
        if self.peut_etre_cloturee():
            actions.append("cloturer")
        if self.peut_etre_annulee():
            actions.append("annuler")
        if self.peut_etre_archivee():
            actions.append("archiver")
        if self.peut_etre_modifiee():
            actions.extend(["modifier", "ajouter_document", "ajouter_piece"])
            
        return actions

    def to_dict(self, include_sensitive: bool = False, include_relations: bool = False) -> Dict[str, Any]:
        """
        Sérialisation harmonisée en dictionnaire.
        
        Args:
            include_sensitive: Inclut données sensibles/coûts (admin/responsable)
            include_relations: Inclut les données des relations liées
            
        Returns:
            Dict contenant les données sérialisées
            
        NOTE: Interface standardisée pour tous les modèles ERP
        """
        # Données de base (toujours incluses)
        data = {
            "id": self.id,
            "titre": self.titre,
            "description": self.description,
            "type_intervention": self.type_intervention.value,
            "statut": self.statut.value,
            "priorite": self.priorite.value,
            "urgence": self.urgence,
            "date_creation": self.date_creation.isoformat() if self.date_creation else None,
            "date_limite": self.date_limite.isoformat() if self.date_limite else None,
            "equipement_id": self.equipement_id,
            "technicien_id": self.technicien_id,
            "client_id": self.client_id,
            "contrat_id": self.contrat_id,
            
            # Propriétés calculées utiles
            "est_active": self.est_active,
            "est_en_retard": self.est_en_retard,
            "est_urgente": self.est_urgente,
            "delai_restant_heures": self.delai_restant_heures,
            "niveau_priorite_numerique": self.niveau_priorite_numerique,
            "technicien_assigne": self.technicien_assigne,
            "client_nom": self.client_nom,
            "equipement_nom": self.equipement_nom,
            "statut_couleur": self.statut_couleur,
            "priorite_couleur": self.priorite_couleur,
            "nb_documents": self.nb_documents,
            "derniere_modification": self.derniere_modification.isoformat() if self.derniere_modification else None,
            "prochaines_actions": self.get_prochaines_actions(),
        }
        
        # Données sensibles (coûts, détails techniques)
        if include_sensitive:
            data.update({
                "created_at": self.created_at.isoformat() if self.created_at else None,
                "updated_at": self.updated_at.isoformat() if self.updated_at else None,
                "date_affectation": self.date_affectation.isoformat() if self.date_affectation else None,
                "date_debut_travaux": self.date_debut_travaux.isoformat() if self.date_debut_travaux else None,
                "date_fin_travaux": self.date_fin_travaux.isoformat() if self.date_fin_travaux else None,
                "date_cloture": self.date_cloture.isoformat() if self.date_cloture else None,
                "date_archivage": self.date_archivage.isoformat() if self.date_archivage else None,
                
                # Durées et performances
                "duree_estimee": self.duree_estimee,
                "duree_reelle": self.duree_reelle_calculee,
                "duree_totale_incluant_attentes": self.duree_totale_incluant_attentes,
                "temps_deplacement": self.temps_deplacement,
                "ecart_duree_prevue_reelle": self.ecart_duree_prevue_reelle,
                "taux_respect_delai": self.taux_respect_delai,
                
                # Coûts détaillés
                "cout_estime": float(self.cout_estime) / 100 if self.cout_estime else None,
                "cout_reel": float(self.cout_reel) / 100 if self.cout_reel else None,
                "cout_pieces": float(self.cout_pieces) / 100 if self.cout_pieces else None,
                "cout_main_oeuvre": float(self.cout_main_oeuvre) / 100 if self.cout_main_oeuvre else None,
                "cout_total_reel": self.cout_total_reel,
                "cout_pieces_calcule": self.cout_pieces_calcule,
                "ecart_cout_estime_reel": self.ecart_cout_estime_reel,
                
                # Qualité et satisfaction
                "rapport_intervention": self.rapport_intervention,
                "travaux_realises": self.travaux_realises,
                "recommandations": self.recommandations,
                "validation_client": self.validation_client,
                "satisfaction_client": self.satisfaction_client,
                "satisfaction_client_label": self.satisfaction_client_label,
                
                # KPI et métriques
                "sla_respect": self.calculer_sla_respect(),
                "nb_pieces_utilisees": self.nb_pieces_utilisees,
                "nb_historiques": self.nb_historiques,
                "temps_ecoule_depuis_creation": int(self.temps_ecoule_depuis_creation.total_seconds() / 3600),  # heures
                "temps_ecoule_depuis_affectation": int(self.temps_ecoule_depuis_affectation.total_seconds() / 3600) if self.temps_ecoule_depuis_affectation else None,
            })
        
        # Relations détaillées (pour vues complètes)
        if include_relations:
            data.update({
                "equipement": self.equipement.to_dict() if self.equipement else None,
                "technicien": self.technicien.to_dict() if self.technicien else None,
                "client": self.client.to_dict() if self.client else None,
                "contrat": self.contrat.to_dict() if self.contrat else None,
                "created_by": self.created_by.to_dict() if self.created_by else None,
                
                # Historique récent (5 dernières entrées)
                "historiques_recents": [h.to_dict() for h in list(self.historiques.limit(5))],
                "documents_recents": [d.to_dict() for d in list(self.documents.limit(5))],
                
                # Workflow et états possibles
                "peut_etre_modifiee": self.peut_etre_modifiee(),
                "peut_etre_affectee": self.peut_etre_affectee(),
                "peut_etre_demarree": self.peut_etre_demarree(),
                "peut_etre_cloturee": self.peut_etre_cloturee(),
                "peut_etre_annulee": self.peut_etre_annulee(),
                "peut_etre_archivee": self.peut_etre_archivee(),
            })
            
        return data