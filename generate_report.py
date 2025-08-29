#!/usr/bin/env python3
"""
📊 Générateur de rapport local pour ERP MIF Maroc
Lance les tests et génère un rapport complet comme dans CI/CD
"""

import os
import sys
import subprocess
import datetime
from pathlib import Path


def run_command(command, description):
    """Exécute une commande et retourne le résultat."""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ {description} - Succès")
            return True, result.stdout
        else:
            print(f"❌ {description} - Échec")
            print(f"Erreur: {result.stderr}")
            return False, result.stderr
    except Exception as e:
        print(f"❌ {description} - Exception: {e}")
        return False, str(e)


def generate_coverage_report():
    """Génère le rapport de couverture."""
    success, output = run_command(
        "pytest app/tests/ --cov=app --cov-report=html:reports/htmlcov --cov-report=term --cov-report=xml:reports/coverage.xml -v",
        "Génération du rapport de couverture"
    )
    return success


def run_security_scan():
    """Lance un scan de sécurité."""
    success, output = run_command(
        "pip-audit --requirement requirements.txt --output reports/security-audit.txt || echo 'pip-audit non disponible'",
        "Scan de sécurité"
    )
    return success


def run_linting():
    """Lance les outils de qualité de code."""
    commands = [
        ("black --check app/ || echo 'Black: formatage requis'", "Vérification formatage Black"),
        ("isort --check-only app/ || echo 'isort: tri imports requis'", "Vérification tri imports"),
        ("flake8 app/ --max-line-length=88 --extend-ignore=E203,W503 --output-file=reports/flake8.txt || echo 'Flake8: problèmes détectés'", "Analyse statique Flake8"),
    ]
    
    results = []
    for command, description in commands:
        success, output = run_command(command, description)
        results.append((description, success))
    
    return results


def generate_html_report():
    """Génère un rapport HTML personnalisé."""
    html_content = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>📊 Rapport ERP MIF Maroc - {datetime.datetime.now().strftime('%Y-%m-%d %H:%M')}</title>
    <style>
        body {{ font-family: Arial, sans-serif; margin: 40px; background-color: #f5f5f5; }}
        .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; border-radius: 10px; text-align: center; }}
        .section {{ background: white; margin: 20px 0; padding: 20px; border-radius: 8px; box-shadow: 0 2px 4px rgba(0,0,0,0.1); }}
        .success {{ color: #28a745; }}
        .error {{ color: #dc3545; }}
        .warning {{ color: #ffc107; }}
        .badge {{ padding: 4px 8px; border-radius: 4px; font-size: 12px; font-weight: bold; }}
        .badge-success {{ background-color: #28a745; color: white; }}
        .badge-error {{ background-color: #dc3545; color: white; }}
        .timestamp {{ color: #6c757d; font-size: 14px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>🚦 ERP MIF Maroc - Rapport de Qualité</h1>
        <p class="timestamp">Généré le {datetime.datetime.now().strftime('%d/%m/%Y à %H:%M:%S')}</p>
    </div>
    
    <div class="section">
        <h2>📊 Résumé Exécutif</h2>
        <p>Ce rapport présente l'état de la qualité du code et des tests du backend FastAPI.</p>
        <ul>
            <li>🧪 <strong>Tests</strong>: Exécution des tests unitaires et d'intégration</li>
            <li>📈 <strong>Couverture</strong>: Mesure de la couverture de code</li>
            <li>🔍 <strong>Qualité</strong>: Analyse statique et formatage</li>
            <li>🔒 <strong>Sécurité</strong>: Scan des vulnérabilités</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>🧪 Résultats des Tests</h2>
        <p>Voir le fichier <code>reports/htmlcov/index.html</code> pour le rapport détaillé de couverture.</p>
        <p>📁 Fichiers de rapport générés :</p>
        <ul>
            <li><code>reports/coverage.xml</code> - Rapport de couverture XML</li>
            <li><code>reports/htmlcov/</code> - Rapport HTML interactif</li>
            <li><code>reports/flake8.txt</code> - Résultats Flake8</li>
            <li><code>reports/security-audit.txt</code> - Audit de sécurité</li>
        </ul>
    </div>
    
    <div class="section">
        <h2>🔧 Actions Recommandées</h2>
        <ol>
            <li>Corrigez les tests qui échouent</li>
            <li>Améliorez la couverture de code (objectif: 80%+)</li>
            <li>Résolvez les problèmes de formatage avec <code>black app/</code></li>
            <li>Triez les imports avec <code>isort app/</code></li>
            <li>Corrigez les warnings Flake8</li>
        </ol>
    </div>
    
    <div class="section">
        <h2>🔗 Liens Utiles</h2>
        <ul>
            <li><a href="htmlcov/index.html">📊 Rapport de couverture détaillé</a></li>
            <li><a href="../README.md">📖 Documentation du projet</a></li>
            <li><a href="../app/tests/">🧪 Dossier des tests</a></li>
        </ul>
    </div>
</body>
</html>
    """
    
    Path("reports").mkdir(exist_ok=True)
    with open("reports/rapport-qualite.html", "w", encoding="utf-8") as f:
        f.write(html_content)
    
    print("✅ Rapport HTML généré: reports/rapport-qualite.html")


def main():
    """Fonction principale."""
    print("📊 === Génération de rapport local ERP MIF Maroc ===\n")
    
    # Créer le dossier reports
    Path("reports").mkdir(exist_ok=True)
    
    # Lancer les différents checks
    print("🧪 Lancement des tests et génération des rapports...\n")
    
    # Tests et couverture
    coverage_success = generate_coverage_report()
    
    # Qualité de code
    print("\n🎨 Vérification de la qualité du code...")
    lint_results = run_linting()
    
    # Sécurité
    print("\n🔒 Scan de sécurité...")
    security_success = run_security_scan()
    
    # Génération du rapport HTML
    print("\n📄 Génération du rapport HTML...")
    generate_html_report()
    
    # Résumé final
    print("\n📋 === RÉSUMÉ ===")
    print(f"✅ Tests et couverture: {'Succès' if coverage_success else 'Échec'}")
    print("🎨 Qualité de code:")
    for description, success in lint_results:
        status = "✅" if success else "⚠️"
        print(f"   {status} {description}")
    print(f"🔒 Sécurité: {'✅ OK' if security_success else '⚠️ Vérifiez les résultats'}")
    
    print("\n📁 Fichiers générés dans le dossier 'reports/':")
    for file in Path("reports").glob("*"):
        print(f"   📄 {file.name}")
    
    print("\n🌐 Ouvrez 'reports/rapport-qualite.html' dans votre navigateur pour voir le rapport complet.")
    
    if coverage_success:
        print("\n🎉 Génération de rapport terminée avec succès !")
        return 0
    else:
        print("\n⚠️ Quelques problèmes détectés. Consultez les rapports pour plus de détails.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
