# app/models/client.py
"""
Modèle Client - Gestion des entreprises clientes.

Ce module gère les clients externes de l'ERP :
- Entreprises clientes avec informations détaillées
- Contact principal et coordonnées complètes
- Relations avec utilisateurs, interventions, contrats
- Gestion des équipements sous contrat
- Historique commercial et maintenance
- Facturation et niveau de service

Architecture:
- Relation 1:1 avec User (rôle client)
- Relations 1:N avec interventions, contrats, équipements
- Index de performance sur secteur et ville
- Propriétés calculées pour KPI commerciaux
- Interface to_dict() standardisée pour API
"""

import enum
from datetime import datetime, timedelta
from typing import TYPE_CHECKING, Any, Dict, List, Optional

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Enum,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.db.database import Base

# NOTE: Import conditionnel pour éviter les imports circulaires
if TYPE_CHECKING:
    from .contrat import Contrat
    from .equipement import Equipement
    from .user import User

# Import direct nécessaire pour les filtres
from .intervention import Intervention


class TypeClient(str, enum.Enum):
    """
    Types de clients selon la classification commerciale.

    - entreprise : société privée standard
    - collectivite : collectivité territoriale/publique
    - association : association/ONG
    - particulier : client particulier (rare en B2B)
    """

    entreprise = "entreprise"
    collectivite = "collectivite"
    association = "association"
    particulier = "particulier"


class NiveauService(str, enum.Enum):
    """
    Niveaux de service contractuels.

    - premium : service 24/7, SLA renforcé
    - standard : service heures ouvrables
    - basique : service différé
    """

    premium = "premium"
    standard = "standard"
    basique = "basique"


class Client(Base):
    """
    Modèle Client - Entreprises et organisations clientes.

    Gestion complète des clients externes avec :
    - Informations légales et commerciales
    - Contact principal et coordonnées
    - Classification métier et niveau de service
    - Relations avec utilisateurs et interventions
    - Contrats de maintenance et équipements
    - Historique commercial et satisfaction

    Relations clés :
    - 1:1 avec User (compte d'accès client)
    - 1:N avec Interventions (demandes maintenance)
    - 1:N avec Contrats (accords commerciaux)
    - 1:N avec Equipements (parc client)

    Performances :
    - Index composites sur secteur+ville, type+niveau_service
    - Relations lazy=dynamic pour collections volumineuses
    - Propriétés calculées pour KPI commerciaux
    """

    __tablename__ = "clients"
    # Autorise les annotations non-Mapped legacy (compat SQLAlchemy 2.0)
    __allow_unmapped__ = True

    # NOTE: Index composites pour requêtes commerciales fréquentes
    __table_args__ = (
        Index("idx_client_secteur_ville", "secteur_activite", "ville"),
        Index("idx_client_type_niveau", "type_client", "niveau_service"),
        Index("idx_client_actif_creation", "is_active", "date_creation"),
        Index("idx_client_nom_email", "nom_entreprise", "email"),
    )

    # Clé primaire
    id = Column(Integer, primary_key=True, index=True)

    # Informations légales et entreprise
    nom_entreprise = Column(String(255), nullable=False, index=True)
    nom_commercial = Column(String(255), nullable=True)  # Enseigne commerciale
    type_client = Column(
        Enum(TypeClient), default=TypeClient.entreprise, nullable=False, index=True
    )
    secteur_activite = Column(String(100), nullable=True, index=True)
    taille_entreprise = Column(String(50), nullable=True)  # TPE, PME, ETI, GE

    # Identifiants légaux
    numero_siret = Column(String(14), nullable=True, unique=True, index=True)
    numero_tva = Column(String(20), nullable=True)
    code_ape = Column(String(10), nullable=True)

    # Contact principal et coordonnées
    nom_contact = Column(String(255), nullable=False)
    prenom_contact = Column(String(255), nullable=True)
    fonction_contact = Column(String(100), nullable=True)
    email = Column(String(255), nullable=False, unique=True, index=True)
    telephone = Column(String(20), nullable=True)
    telephone_mobile = Column(String(20), nullable=True)
    fax = Column(String(20), nullable=True)

    # Adresse complète
    adresse_ligne1 = Column(String(255), nullable=True)
    adresse_ligne2 = Column(String(255), nullable=True)
    code_postal = Column(String(10), nullable=True, index=True)
    ville = Column(String(100), nullable=True, index=True)
    region = Column(String(100), nullable=True)
    pays = Column(String(100), default="France", nullable=False)

    # Service et commercial
    niveau_service = Column(
        Enum(NiveauService), default=NiveauService.standard, nullable=False, index=True
    )
    chiffre_affaires_annuel = Column(Numeric(12, 2), nullable=True)  # En euros
    nb_employes = Column(Integer, nullable=True)

    # Statut et métadonnées
    is_active = Column(Boolean, default=True, nullable=False, index=True)
    date_creation = Column(
        DateTime, default=datetime.utcnow, nullable=False, index=True
    )
    date_modification = Column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False
    )
    date_premier_contrat = Column(DateTime, nullable=True)
    date_derniere_intervention = Column(DateTime, nullable=True)

    # Notes et observations
    notes_commerciales = Column(Text, nullable=True)
    instructions_particulieres = Column(Text, nullable=True)

    # Clé étrangère vers User (obligatoire)
    user_id = Column(
        Integer,
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        unique=True,
        index=True,
    )

    # 🔗 Relations ORM optimisées

    # Relation principale avec utilisateur (1:1)
    user: "User" = relationship("User", back_populates="client", lazy="select")

    # Relations métier (1:N) - lazy dynamic pour performances
    interventions = relationship(
        "Intervention",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(Intervention.date_creation)",
    )

    contrats = relationship(
        "Contrat",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="desc(Contrat.date_debut)",
    )

    equipements = relationship(
        "Equipement",
        back_populates="client",
        cascade="all, delete-orphan",
        lazy="dynamic",
        order_by="Equipement.nom",
    )

    def __repr__(self) -> str:
        """Représentation concise pour debugging."""
        return (
            f"<Client(id={self.id}, entreprise='{self.nom_entreprise}', "
            f"contact='{self.nom_contact}', actif={self.is_active})>"
        )

    # 🏷️ Propriétés métier et KPI commerciaux

    @property
    def nom_complet_contact(self) -> str:
        """Nom complet du contact principal."""
        if self.prenom_contact:
            return f"{self.prenom_contact} {self.nom_contact}"
        return self.nom_contact

    @property
    def adresse_complete(self) -> str:
        """Adresse complète formatée."""
        parts = []
        if self.adresse_ligne1:
            parts.append(self.adresse_ligne1)
        if self.adresse_ligne2:
            parts.append(self.adresse_ligne2)
        if self.code_postal and self.ville:
            parts.append(f"{self.code_postal} {self.ville}")
        if self.pays and self.pays != "France":
            parts.append(self.pays)
        return "\n".join(parts)

    @property
    def nom_affichage(self) -> str:
        """Nom d'affichage préféré (commercial ou entreprise)."""
        return self.nom_commercial or self.nom_entreprise

    @property
    def anciennete_jours(self) -> int:
        """Ancienneté du client en jours."""
        return (datetime.utcnow() - self.date_creation).days

    @property
    def anciennete_annees(self) -> float:
        """Ancienneté du client en années."""
        return round(self.anciennete_jours / 365.25, 1)

    @property
    def est_nouveau_client(self) -> bool:
        """Vérifie si c'est un nouveau client (< 6 mois)."""
        return self.anciennete_jours < 180

    @property
    def est_client_premium(self) -> bool:
        """Vérifie si c'est un client premium."""
        return self.niveau_service == NiveauService.premium

    @property
    def nb_interventions_total(self) -> int:
        """Nombre total d'interventions pour ce client."""
        return self.interventions.count()

    @property
    def nb_interventions_ouvertes(self) -> int:
        """Nombre d'interventions actuellement ouvertes."""
        from app.models.intervention import StatutIntervention

        return self.interventions.filter(
            Intervention.statut.in_(
                [
                    StatutIntervention.ouverte,
                    StatutIntervention.affectee,
                    StatutIntervention.en_cours,
                    StatutIntervention.en_attente,
                ]
            )
        ).count()

    @property
    def nb_interventions_mois_courant(self) -> int:
        """Nombre d'interventions du mois en cours."""
        debut_mois = datetime.utcnow().replace(
            day=1, hour=0, minute=0, second=0, microsecond=0
        )
        return self.interventions.filter(
            Intervention.date_creation >= debut_mois
        ).count()

    @property
    def nb_contrats_actifs(self) -> int:
        """Nombre de contrats actuellement actifs."""
        from app.models.contrat import StatutContrat

        return self.contrats.filter_by(statut=StatutContrat.actif).count()

    @property
    def nb_equipements_total(self) -> int:
        """Nombre total d'équipements sous contrat."""
        return self.equipements.count()

    @property
    def nb_equipements_operationnels(self) -> int:
        """Nombre d'équipements opérationnels."""
        from app.models.equipement import StatutEquipement

        return self.equipements.filter_by(statut=StatutEquipement.operationnel).count()

    @property
    def derniere_intervention(self) -> Optional["Intervention"]:
        """Dernière intervention créée pour ce client."""
        return self.interventions.first()

    @property
    def derniere_intervention_date(self) -> Optional[datetime]:
        """Date de la dernière intervention."""
        derniere = self.derniere_intervention
        return derniere.date_creation if derniere else None

    @property
    def temps_depuis_derniere_intervention(self) -> Optional[timedelta]:
        """Temps écoulé depuis la dernière intervention."""
        if not self.derniere_intervention_date:
            return None
        return datetime.utcnow() - self.derniere_intervention_date

    @property
    def contrat_principal(self) -> Optional["Contrat"]:
        """Contrat principal actif (le plus récent)."""
        from app.models.contrat import StatutContrat

        return self.contrats.filter_by(statut=StatutContrat.actif).first()

    @property
    def taux_satisfaction_moyen(self) -> Optional[float]:
        """Taux de satisfaction moyen basé sur les interventions."""
        interventions_avec_note = self.interventions.filter(
            Intervention.satisfaction_client.isnot(None)
        ).all()

        if not interventions_avec_note:
            return None

        total = sum(i.satisfaction_client for i in interventions_avec_note)
        return round(total / len(interventions_avec_note), 2)

    @property
    def cout_maintenance_total(self) -> float:
        """Coût total de maintenance facturé (basé sur interventions)."""
        total_centimes = 0
        for intervention in self.interventions:
            if intervention.cout_reel:
                total_centimes += intervention.cout_reel
        return round(total_centimes / 100, 2)

    @property
    def cout_maintenance_annuel(self) -> float:
        """Coût de maintenance des 12 derniers mois."""
        un_an_ago = datetime.utcnow() - timedelta(days=365)
        interventions_recentes = self.interventions.filter(
            Intervention.date_creation >= un_an_ago
        ).all()

        total_centimes = sum(i.cout_reel for i in interventions_recentes if i.cout_reel)
        return round(total_centimes / 100, 2)

    @property
    def delai_moyen_intervention(self) -> Optional[float]:
        """Délai moyen de traitement des interventions (en heures)."""
        interventions_terminees = self.interventions.filter(
            Intervention.date_cloture.isnot(None)
        ).all()

        if not interventions_terminees:
            return None

        delais = [
            (i.date_cloture - i.date_creation).total_seconds() / 3600
            for i in interventions_terminees
        ]
        return round(sum(delais) / len(delais), 1)

    @property
    def niveau_priorite_commerciale(self) -> int:
        """Niveau de priorité commerciale calculé (1-5)."""
        score = 1

        # Bonus selon niveau de service
        if self.niveau_service == NiveauService.premium:
            score += 2
        elif self.niveau_service == NiveauService.standard:
            score += 1

        # Bonus selon chiffre d'affaires
        if self.chiffre_affaires_annuel:
            ca = float(self.chiffre_affaires_annuel)
            if ca >= 1000000:  # > 1M€
                score += 2
            elif ca >= 100000:  # > 100k€
                score += 1

        # Bonus selon ancienneté
        if self.anciennete_annees >= 5:
            score += 1

        return min(score, 5)

    @property
    def statut_commercial(self) -> str:
        """Statut commercial calculé."""
        if not self.is_active:
            return "Inactif"
        elif self.est_nouveau_client:
            return "Nouveau"
        elif self.nb_contrats_actifs == 0:
            return "Prospect"
        elif self.nb_interventions_mois_courant > 5:
            return "Actif+"
        else:
            return "Actif"

    @property
    def telephone_principal(self) -> Optional[str]:
        """Téléphone principal (mobile prioritaire)."""
        return self.telephone_mobile or self.telephone

    @property
    def identifiant_legal(self) -> Optional[str]:
        """Identifiant légal principal (SIRET prioritaire)."""
        return self.numero_siret or self.numero_tva

    # 🔧 Méthodes métier pour gestion client

    def desactiver(self, raison: str = None) -> None:
        """Désactive le client."""
        self.is_active = False
        self.date_modification = datetime.utcnow()
        if raison and not self.notes_commerciales:
            self.notes_commerciales = f"Désactivation: {raison}"

    def reactiver(self) -> None:
        """Réactive le client."""
        self.is_active = True
        self.date_modification = datetime.utcnow()

    def mettre_a_jour_derniere_intervention(self) -> None:
        """Met à jour la date de dernière intervention."""
        self.date_derniere_intervention = datetime.utcnow()
        self.date_modification = datetime.utcnow()

    def peut_etre_supprime(self) -> bool:
        """Vérifie si le client peut être supprimé du système."""
        # Ne peut pas supprimer s'il y a des interventions actives
        return (
            self.nb_interventions_ouvertes == 0
            and self.nb_contrats_actifs == 0
            and not self.is_active
        )

    def get_interventions_urgentes(self) -> List["Intervention"]:
        """Retourne les interventions urgentes en cours."""
        from app.models.intervention import PrioriteIntervention, StatutIntervention

        return list(
            self.interventions.filter(
                Intervention.statut.in_(
                    [
                        StatutIntervention.ouverte,
                        StatutIntervention.affectee,
                        StatutIntervention.en_cours,
                    ]
                ),
                Intervention.priorite.in_(
                    [PrioriteIntervention.urgente, PrioriteIntervention.haute]
                ),
            ).all()
        )

    def get_equipements_en_panne(self) -> List["Equipement"]:
        """Retourne les équipements actuellement en panne."""
        from app.models.equipement import StatutEquipement

        return list(self.equipements.filter_by(statut=StatutEquipement.panne).all())

    def calculer_sla_global(self) -> Optional[float]:
        """Calcule le respect global des SLA sur les 6 derniers mois."""
        six_mois_ago = datetime.utcnow() - timedelta(days=180)
        interventions_recentes = self.interventions.filter(
            Intervention.date_creation >= six_mois_ago,
            Intervention.date_cloture.isnot(None),
        ).all()

        if not interventions_recentes:
            return None

        sla_respectes = sum(
            1 for i in interventions_recentes if i.calculer_sla_respect() is True
        )

        return round(sla_respectes / len(interventions_recentes) * 100, 1)

    def generer_rapport_activite(self, nb_mois: int = 12) -> Dict[str, Any]:
        """
        Génère un rapport d'activité sur les N derniers mois.

        Args:
            nb_mois: Nombre de mois à analyser

        Returns:
            Dict avec les KPI d'activité
        """
        date_debut = datetime.utcnow() - timedelta(days=nb_mois * 30)

        interventions_periode = self.interventions.filter(
            Intervention.date_creation >= date_debut
        ).all()

        return {
            "periode_mois": nb_mois,
            "nb_interventions": len(interventions_periode),
            "nb_preventives": sum(1 for i in interventions_periode if i.est_preventive),
            "nb_correctives": sum(1 for i in interventions_periode if i.est_corrective),
            "cout_total": sum(
                i.cout_total_reel for i in interventions_periode if i.cout_total_reel
            ),
            "delai_moyen_heures": self.delai_moyen_intervention,
            "taux_satisfaction": self.taux_satisfaction_moyen,
            "sla_respect": self.calculer_sla_global(),
            "equipements_total": self.nb_equipements_total,
            "equipements_operationnels": self.nb_equipements_operationnels,
        }

    def to_dict(
        self, include_sensitive: bool = False, include_relations: bool = False
    ) -> Dict[str, Any]:
        """
        Sérialisation harmonisée en dictionnaire.

        Args:
            include_sensitive: Inclut données sensibles/commerciales (admin/responsable)
            include_relations: Inclut les données des relations liées

        Returns:
            Dict contenant les données sérialisées

        NOTE: Interface standardisée pour tous les modèles ERP
        """
        # Données de base (toujours incluses)
        data = {
            "id": self.id,
            "nom_entreprise": self.nom_entreprise,
            "nom_commercial": self.nom_commercial,
            "nom_affichage": self.nom_affichage,
            "type_client": self.type_client.value,
            "secteur_activite": self.secteur_activite,
            "niveau_service": self.niveau_service.value,
            "nom_contact": self.nom_contact,
            "nom_complet_contact": self.nom_complet_contact,
            "fonction_contact": self.fonction_contact,
            "email": self.email,
            "telephone_principal": self.telephone_principal,
            "ville": self.ville,
            "code_postal": self.code_postal,
            "pays": self.pays,
            "is_active": self.is_active,
            "date_creation": (
                self.date_creation.isoformat() if self.date_creation else None
            ),
            # Propriétés calculées utiles
            "statut_commercial": self.statut_commercial,
            "anciennete_annees": self.anciennete_annees,
            "est_nouveau_client": self.est_nouveau_client,
            "est_client_premium": self.est_client_premium,
            "nb_interventions_total": self.nb_interventions_total,
            "nb_interventions_ouvertes": self.nb_interventions_ouvertes,
            "nb_equipements_total": self.nb_equipements_total,
            "derniere_intervention_date": (
                self.derniere_intervention_date.isoformat()
                if self.derniere_intervention_date
                else None
            ),
        }

        # Données sensibles (commerciales, financières)
        if include_sensitive:
            data.update(
                {
                    "date_modification": (
                        self.date_modification.isoformat()
                        if self.date_modification
                        else None
                    ),
                    "numero_siret": self.numero_siret,
                    "numero_tva": self.numero_tva,
                    "code_ape": self.code_ape,
                    "identifiant_legal": self.identifiant_legal,
                    "taille_entreprise": self.taille_entreprise,
                    "chiffre_affaires_annuel": (
                        float(self.chiffre_affaires_annuel)
                        if self.chiffre_affaires_annuel
                        else None
                    ),
                    "nb_employes": self.nb_employes,
                    "telephone": self.telephone,
                    "telephone_mobile": self.telephone_mobile,
                    "fax": self.fax,
                    "adresse_ligne1": self.adresse_ligne1,
                    "adresse_ligne2": self.adresse_ligne2,
                    "adresse_complete": self.adresse_complete,
                    "region": self.region,
                    "notes_commerciales": self.notes_commerciales,
                    "instructions_particulieres": self.instructions_particulieres,
                    # KPI commerciaux
                    "niveau_priorite_commerciale": self.niveau_priorite_commerciale,
                    "nb_contrats_actifs": self.nb_contrats_actifs,
                    "nb_interventions_mois_courant": self.nb_interventions_mois_courant,
                    "nb_equipements_operationnels": self.nb_equipements_operationnels,
                    "taux_satisfaction_moyen": self.taux_satisfaction_moyen,
                    "cout_maintenance_total": self.cout_maintenance_total,
                    "cout_maintenance_annuel": self.cout_maintenance_annuel,
                    "delai_moyen_intervention": self.delai_moyen_intervention,
                    "sla_global": self.calculer_sla_global(),
                    "date_premier_contrat": (
                        self.date_premier_contrat.isoformat()
                        if self.date_premier_contrat
                        else None
                    ),
                    "date_derniere_intervention": (
                        self.date_derniere_intervention.isoformat()
                        if self.date_derniere_intervention
                        else None
                    ),
                }
            )

        # Relations détaillées (pour vues complètes)
        if include_relations:
            data.update(
                {
                    "user": self.user.to_dict() if self.user else None,
                    "user_id": self.user_id,
                    # Relations métier limitées (pour éviter surcharge)
                    "contrat_principal": (
                        self.contrat_principal.to_dict()
                        if self.contrat_principal
                        else None
                    ),
                    "derniere_intervention": (
                        self.derniere_intervention.to_dict()
                        if self.derniere_intervention
                        else None
                    ),
                    "interventions_urgentes": [
                        i.to_dict() for i in self.get_interventions_urgentes()
                    ],
                    "equipements_en_panne": [
                        e.to_dict() for e in self.get_equipements_en_panne()
                    ],
                    # Métadonnées système
                    "peut_etre_supprime": self.peut_etre_supprime(),
                    "temps_depuis_derniere_intervention": (
                        int(
                            self.temps_depuis_derniere_intervention.total_seconds()
                            / 3600
                        )
                        if self.temps_depuis_derniere_intervention
                        else None
                    ),
                    # Rapport d'activité synthétique
                    "rapport_activite_6_mois": self.generer_rapport_activite(6),
                }
            )

        return data
