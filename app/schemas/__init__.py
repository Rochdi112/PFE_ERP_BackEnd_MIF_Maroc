"""
Schemas Pydantic pour l'API
"""

# Import des schémas utilisateurs
from .user import UserCreate, UserOut, UserRole, UserUpdate, TokenRequest, TokenResponse

# Import des schémas contrats
from .contrat import (
    ContratCreate, ContratOut, ContratUpdate, ContratSummary, ContratStats,
    TypeContrat, StatutContrat, ModePaiement,
    FactureCreate, FactureOut, FactureUpdate, StatutFacture,
    ContratRenouvellement, ContratResiliation
)

# Import des autres schémas existants
# Note: Autres schémas disponibles mais non importés automatiquement :
# - technicien, client, equipement, intervention, planning
# - document, notification, historique, stock
# - dashboard, report
