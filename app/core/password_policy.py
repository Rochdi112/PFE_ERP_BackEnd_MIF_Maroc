# app/core/password_policy.py

import re
from typing import List


def validate_password_strength(password: str) -> List[str]:
    """
    Valide la robustesse d'un mot de passe selon les critères OWASP.
    
    Exigences Go-Prod :
    - Au moins 8 caractères
    - Au moins une lettre minuscule
    - Au moins une lettre majuscule  
    - Au moins un chiffre
    - Au moins un caractère spécial
    
    Args:
        password (str): Le mot de passe à valider
        
    Returns:
        List[str]: Liste des erreurs (vide si valide)
    """
    errors = []
    
    # Longueur minimale
    if len(password) < 8:
        errors.append("Le mot de passe doit contenir au moins 8 caractères")
    
    # Lettre minuscule
    if not re.search(r'[a-z]', password):
        errors.append("Le mot de passe doit contenir au moins une lettre minuscule")
    
    # Lettre majuscule
    if not re.search(r'[A-Z]', password):
        errors.append("Le mot de passe doit contenir au moins une lettre majuscule")
    
    # Chiffre
    if not re.search(r'[0-9]', password):
        errors.append("Le mot de passe doit contenir au moins un chiffre")
    
    # Caractère spécial
    if not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
        errors.append("Le mot de passe doit contenir au moins un caractère spécial (!@#$%^&*(),.?\":{}|<>)")
    
    # Mots de passe courants interdits
    common_passwords = [
        "password", "123456", "123456789", "qwerty", "abc123", 
        "password123", "admin", "root", "user", "test", "guest"
    ]
    if password.lower() in common_passwords:
        errors.append("Ce mot de passe est trop courant et n'est pas autorisé")
    
    return errors


def is_password_valid(password: str) -> bool:
    """
    Vérifie si un mot de passe respecte la politique de sécurité.
    
    Args:
        password (str): Le mot de passe à valider
        
    Returns:
        bool: True si le mot de passe est valide
    """
    return len(validate_password_strength(password)) == 0