#!/usr/bin/env python3
"""
Script pour générer les clés RSA JWT pour l'authentification asymétrique.
Usage: python scripts/generate_jwt_keys.py
"""

import os
from pathlib import Path

from cryptography.hazmat.backends import default_backend
from cryptography.hazmat.primitives import serialization
from cryptography.hazmat.primitives.asymmetric import rsa


def generate_rsa_keypair():
    """Génère une paire de clés RSA pour JWT asymétrique."""
    
    # Generate private key
    private_key = rsa.generate_private_key(
        public_exponent=65537,
        key_size=2048,
        backend=default_backend()
    )
    
    # Get public key
    public_key = private_key.public_key()
    
    # Serialize private key
    private_pem = private_key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.PKCS8,
        encryption_algorithm=serialization.NoEncryption()
    )
    
    # Serialize public key
    public_pem = public_key.public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo
    )
    
    return private_pem.decode('utf-8'), public_pem.decode('utf-8')


def main():
    """Génère et sauvegarde les clés JWT RSA."""
    
    print("🔐 Génération des clés RSA pour JWT asymétrique...")
    
    # Generate keys
    private_key, public_key = generate_rsa_keypair()
    
    # Create keys directory
    keys_dir = Path("keys")
    keys_dir.mkdir(exist_ok=True)
    
    # Write private key
    private_key_path = keys_dir / "jwt_private.pem"
    with open(private_key_path, 'w') as f:
        f.write(private_key)
    
    # Write public key
    public_key_path = keys_dir / "jwt_public.pem"
    with open(public_key_path, 'w') as f:
        f.write(public_key)
    
    # Set secure permissions
    os.chmod(private_key_path, 0o600)  # Read-write for owner only
    os.chmod(public_key_path, 0o644)   # Read for everyone
    
    print(f"✅ Clé privée sauvegardée: {private_key_path}")
    print(f"✅ Clé publique sauvegardée: {public_key_path}")
    
    print("\n📝 Variables d'environnement à définir:")
    print("JWT_PRIVATE_KEY_PATH=keys/jwt_private.pem")
    print("JWT_PUBLIC_KEY_PATH=keys/jwt_public.pem")
    print("JWT_ALGORITHM=RS256")
    
    print("\n⚠️  IMPORTANT:")
    print("- Ajoutez 'keys/' au .gitignore pour la sécurité")
    print("- En production, utilisez un gestionnaire de secrets (Vault, etc.)")
    print("- Implémentez la rotation des clés régulièrement")


if __name__ == "__main__":
    main()