import os
import sqlite3

def get_db_connection():
    # Support Neon connection strings as well as Vercel standard ones
    postgres_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
    if postgres_url:
        # Try pg8000 (pure Python, 100% reliable on Vercel)
        try:
            import pg8000.dbapi
            import urllib.parse
            import ssl
            url = urllib.parse.urlparse(postgres_url)
            ssl_context = ssl.create_default_context()
            return pg8000.dbapi.connect(
                user=url.username,
                password=url.password,
                host=url.hostname,
                database=url.path[1:],
                port=url.port or 5432,
                ssl_context=ssl_context
            )
        except ImportError:
            # Fallback to psycopg2 if pg8000 is not installed
            try:
                import psycopg2
                return psycopg2.connect(postgres_url)
            except Exception as e:
                raise Exception(f"Failed to connect to Neon Postgres via psycopg2: {e}")
        except Exception as e:
            raise Exception(f"Failed to connect to Neon Postgres via pg8000: {e}")
            
    # Fallback to local SQLite database ONLY if no Postgres URL is configured
    db_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "pindex_usage.db")
    return sqlite3.connect(db_path)

def init_db():
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        postgres_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
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
                    pindex_weighted DOUBLE PRECISION,
                    anonymous_user_id VARCHAR(255),
                    total_papers_count INTEGER,
                    total_citations INTEGER
                );
            """)
            
            # Helper to add column if it does not exist (PostgreSQL)
            def add_postgres_col(col_name, col_type):
                cursor.execute(f"""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='calculation_logs' AND column_name='{col_name}';
                """)
                if not cursor.fetchone():
                    try:
                        cursor.execute(f"ALTER TABLE calculation_logs ADD COLUMN {col_name} {col_type};")
                    except Exception:
                        pass
            
            add_postgres_col("anonymous_user_id", "VARCHAR(255)")
            add_postgres_col("total_papers_count", "INTEGER")
            add_postgres_col("total_citations", "INTEGER")
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
                    pindex_weighted REAL,
                    anonymous_user_id TEXT,
                    total_papers_count INTEGER,
                    total_citations INTEGER
                );
            """)
            
            # Helper to add column if it does not exist (SQLite)
            def add_sqlite_col(col_name, col_type):
                try:
                    cursor.execute(f"ALTER TABLE calculation_logs ADD COLUMN {col_name} {col_type};")
                except Exception:
                    pass
            
            add_sqlite_col("anonymous_user_id", "TEXT")
            add_sqlite_col("total_papers_count", "INTEGER")
            add_sqlite_col("total_citations", "INTEGER")
                
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization failed: {e}")

def log_calculation(ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count=None, total_citations=None):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        # Handle NaN values
        import math
        if pindex is not None and (math.isnan(pindex) or math.isinf(pindex)):
            pindex = None
        if pindex_weighted is not None and (math.isnan(pindex_weighted) or math.isinf(pindex_weighted)):
            pindex_weighted = None
            
        postgres_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
        
        if postgres_url:
            query = """
                INSERT INTO calculation_logs 
                (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations))
        else:
            query = """
                INSERT INTO calculation_logs 
                (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database logging failed: {e}")
