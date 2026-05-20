"""
PostgreSQL database setup script.
Run this once after installing PostgreSQL and editing .env with your credentials.

Usage:
    python setup_db.py
"""

import os
import sys

# Load .env first
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("ERROR: python-dotenv not installed. Run: pip install python-dotenv")
    sys.exit(1)

try:
    import psycopg2
    from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
except ImportError:
    print("ERROR: psycopg2-binary not installed. Run: pip install psycopg2-binary")
    sys.exit(1)

DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://postgres:postgres@localhost:5432/freight_exchange"
)

# Parse the DB name from the URL to create it if needed
# e.g. postgresql://user:pass@host:port/freight_exchange
db_name = DATABASE_URL.rsplit("/", 1)[-1]
base_url = DATABASE_URL.rsplit("/", 1)[0] + "/postgres"  # connect to default DB first


def create_database():
    print(f"Connecting to PostgreSQL (postgres DB) to create '{db_name}'...")
    try:
        conn = psycopg2.connect(base_url)
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cur = conn.cursor()
        cur.execute(f"SELECT 1 FROM pg_database WHERE datname='{db_name}'")
        if cur.fetchone():
            print(f"  Database '{db_name}' already exists — skipping creation.")
        else:
            cur.execute(f'CREATE DATABASE "{db_name}"')
            print(f"  Database '{db_name}' created successfully.")
        conn.close()
    except Exception as e:
        print(f"\nERROR connecting to PostgreSQL:\n  {e}")
        print("\nMake sure:")
        print("  1. PostgreSQL is running (check Services or pg_ctl)")
        print("  2. Credentials in .env are correct")
        print(f"  3. DATABASE_URL = {DATABASE_URL}")
        sys.exit(1)


def initialize_schema():
    print("Creating tables and seeding data...")
    try:
        from database.db_manager import DatabaseManager
        DatabaseManager().initialize()
        print("  Tables created and seed data loaded.")
    except Exception as e:
        print(f"\nERROR during initialization:\n  {e}")
        sys.exit(1)


if __name__ == "__main__":
    print("=" * 55)
    print("  FreightExchange — PostgreSQL Setup")
    print("=" * 55)
    print(f"  DATABASE_URL = {DATABASE_URL}\n")

    create_database()
    initialize_schema()

    print("\n" + "=" * 55)
    print("  Setup complete! You can now launch the app.")
    print("=" * 55)
