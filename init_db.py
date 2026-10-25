# Creates the database and tables from sql/schema.sql and loads sql/seed.sql.
# Running it again wipes the data and starts fresh.
import os
import sys
import psycopg2
from config import DB_CONFIG, DB_NAME

BASE = os.path.dirname(os.path.abspath(__file__))


def run_file(conn, name):
    filepath = os.path.join(BASE, "sql", name)
    with open(filepath, encoding="utf-8") as f:
        sql = f.read()
    with conn.cursor() as cur:
        cur.execute(sql)
    conn.commit()
    print(f"Successfully executed: {name}")


def init_postgres():
    print(f"Connecting to PostgreSQL at {DB_CONFIG['host']}:{DB_CONFIG['port']}...")
    try:
        # connect to the default postgres database just to create ours if not exists
        conn = psycopg2.connect(dbname="postgres", **DB_CONFIG)
        conn.autocommit = True
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM pg_database WHERE datname = %s", (DB_NAME,))
        if cur.fetchone() is None:
            cur.execute(f'CREATE DATABASE "{DB_NAME}"')
            print(f"Created database: {DB_NAME}")
        else:
            print(f"Database '{DB_NAME}' already exists.")
        conn.close()

        # Connect to target database and execute DDL & DML
        conn = psycopg2.connect(dbname=DB_NAME, **DB_CONFIG)
        run_file(conn, "schema.sql")
        run_file(conn, "seed.sql")
        conn.close()
        print("Database initialized successfully on PostgreSQL!")
        return True
    except psycopg2.OperationalError as e:
        print(f"\n[PostgreSQL Connection Notice]")
        print(f"Could not connect to PostgreSQL server: {e}")
        print("Tip: Ensure the PostgreSQL service is started and DB_PASSWORD environment variable is set if needed.")
        print("Example: set DB_PASSWORD=your_password (Windows) or export DB_PASSWORD=your_password (Mac/Linux)\n")
        return False


if __name__ == "__main__":
    success = init_postgres()
    if not success:
        sys.exit(1)
