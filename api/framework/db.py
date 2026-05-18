import os
import sqlite3

def get_db_connection():
    postgres_url = os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
    if postgres_url:
        try:
            import psycopg2
            return psycopg2.connect(postgres_url)
        except ImportError:
            print("psycopg2 is not installed. Falling back to local SQLite.")
            
    # Fallback to local SQLite database in workspace
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "pindex_usage.db")
    return sqlite3.connect(db_path)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        postgres_url = os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
        if postgres_url:
            # PostgreSQL schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculation_logs (
                    id SERIAL PRIMARY KEY,
                    timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    ip_address VARCHAR(255),
                    user_agent TEXT,
                    researcher_name VARCHAR(255),
                    papers_count INTEGER,
                    pindex DOUBLE PRECISION,
                    pindex_weighted DOUBLE PRECISION
                );
            """)
        else:
            # SQLite schema
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS calculation_logs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    ip_address TEXT,
                    user_agent TEXT,
                    researcher_name TEXT,
                    papers_count INTEGER,
                    pindex REAL,
                    pindex_weighted REAL
                );
            """)
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization failed: {e}")

def log_calculation(ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Handle NaN values
        import math
        if pindex is not None and (math.isnan(pindex) or math.isinf(pindex)):
            pindex = None
        if pindex_weighted is not None and (math.isnan(pindex_weighted) or math.isinf(pindex_weighted)):
            pindex_weighted = None
            
        postgres_url = os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
        
        if postgres_url:
            query = """
                INSERT INTO calculation_logs 
                (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted)
                VALUES (%s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted))
        else:
            query = """
                INSERT INTO calculation_logs 
                (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted)
                VALUES (?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database logging failed: {e}")
