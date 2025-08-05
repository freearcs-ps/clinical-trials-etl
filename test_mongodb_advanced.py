#!/usr/bin/env python3
"""
Test de connexion MongoDB avec différentes stratégies TLS/SSL
"""
import os
from dotenv import load_dotenv
from pymongo import MongoClient
import ssl

# Charger les variables d'environnement
load_dotenv()


def test_mongodb_connections():
    """Teste différentes stratégies de connexion MongoDB"""

    mongodb_uri = os.getenv("MONGODB_URI")
    mongodb_db = os.getenv("MONGODB_DATABASE", "clinical_trials")

    if not mongodb_uri:
        print("❌ MONGODB_URI manquante dans .env")
        return False

    print(f"🔍 Test avec URI: {mongodb_uri[:50]}...")
    print(f"🔍 Database: {mongodb_db}")
    print("=" * 60)

    # Stratégies de connexion à tester
    strategies = [
        {
            "name": "1. Configuration standard MongoDB 4.x",
            "options": {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "retryWrites": True,
                "w": "majority",
            },
        },
        {
            "name": "2. TLS avec certificats flexibles",
            "options": {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "tls": True,
                "tlsAllowInvalidCertificates": True,
            },
        },
        {
            "name": "3. SSL Context personnalisé (Python)",
            "options": {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "ssl": True,
                "ssl_cert_reqs": ssl.CERT_NONE,
                "ssl_check_hostname": False,
            },
        },
        {
            "name": "4. TLS insecure",
            "options": {
                "serverSelectionTimeoutMS": 30000,
                "connectTimeoutMS": 30000,
                "tlsInsecure": True,
            },
        },
        {
            "name": "5. Aucune option TLS (laisser MongoDB gérer)",
            "options": {"serverSelectionTimeoutMS": 30000, "connectTimeoutMS": 30000},
        },
    ]

    for strategy in strategies:
        print(f"\n🔄 Test: {strategy['name']}")
        print("-" * 50)

        client = None
        try:
            client = MongoClient(mongodb_uri, **strategy["options"])

            # Test de connexion
            client.admin.command("ping")
            print("✅ Connexion réussie!")

            # Test de base de données
            db = client[mongodb_db]
            collection = db.trials

            # Test de comptage
            count = collection.count_documents({})
            print(f"✅ Nombre de documents: {count}")

            # Test de lecture d'un document
            sample = collection.find_one({})
            if sample:
                print("✅ Document de test récupéré")
                print(f"   ID: {str(sample.get('_id', 'N/A'))[:50]}")
            else:
                print("⚠️  Aucun document dans la collection")

            print(f"🎉 SUCCÈS avec {strategy['name']}")
            return True

        except Exception as e:
            error_msg = str(e)
            print(f"❌ Échec: {error_msg[:200]}...")

            # Analyser le type d'erreur
            if "SSL" in error_msg or "TLS" in error_msg:
                print("💡 Erreur TLS/SSL détectée")
            elif "timeout" in error_msg.lower():
                print("💡 Erreur de timeout détectée")
            elif "authentication" in error_msg.lower():
                print("💡 Erreur d'authentification détectée")
            else:
                print("💡 Autre type d'erreur")

        finally:
            if client:
                try:
                    client.close()
                except:
                    pass

    print("\n" + "=" * 60)
    print("❌ Toutes les stratégies ont échoué")
    return False


def check_environment():
    """Vérifie l'environnement et les versions"""
    print("🔍 Vérification de l'environnement")
    print("=" * 40)

    try:
        import pymongo

        print(f"✅ PyMongo version: {pymongo.version}")
    except ImportError:
        print("❌ PyMongo non installé")

    try:
        import ssl

        print(f"✅ SSL version: {ssl.OPENSSL_VERSION}")
        print(f"✅ SSL protocoles supportés: {ssl.ssl_version}")
    except ImportError:
        print("❌ SSL non disponible")

    try:
        import dnspython

        print(f"✅ DNSPython disponible")
    except ImportError:
        print("❌ DNSPython non installé")

    print()


if __name__ == "__main__":
    print("🧪 Test avancé de connexion MongoDB Atlas")
    print("=" * 60)

    check_environment()
    success = test_mongodb_connections()

    print("\n" + "=" * 60)
    if success:
        print("🎉 Au moins une stratégie de connexion a fonctionné!")
    else:
        print("💥 Toutes les stratégies ont échoué")
        print("\n💡 Solutions à essayer:")
        print("   1. Vérifiez que votre cluster MongoDB Atlas est démarré")
        print("   2. Vérifiez votre nom d'utilisateur et mot de passe")
        print("   3. Vérifiez que votre IP est dans la liste blanche")
        print("   4. Essayez de redémarrer votre cluster Atlas")
        print("   5. Contactez le support MongoDB Atlas")
