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
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_year_baselines (
                    id SERIAL PRIMARY KEY,
                    journal VARCHAR(255),
                    year INTEGER,
                    citations_list TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(journal, year)
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
            add_postgres_col("api_usage", "INTEGER")
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
                    total_citations INTEGER,
                    api_usage INTEGER
                );
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS journal_year_baselines (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    journal TEXT,
                    year INTEGER,
                    citations_list TEXT,
                    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(journal, year)
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
            add_sqlite_col("api_usage", "INTEGER")
                
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database initialization failed: {e}")

def log_calculation(ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count=None, total_citations=None, api_usage=None):
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
                (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations, api_usage)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
            """
            cursor.execute(query, (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations, api_usage))
        else:
            query = """
                INSERT INTO calculation_logs 
                (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations, api_usage)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """
            cursor.execute(query, (ip_address, user_agent, researcher_name, papers_count, pindex, pindex_weighted, anonymous_user_id, total_papers_count, total_citations, api_usage))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Database logging failed: {e}")

import json
from datetime import datetime, timedelta
import pandas as pd

def get_cached_journal_cell(journal, year):
    try:
        conn = get_db_connection()
        cursor = conn.cursor()
        
        postgres_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
        
        if postgres_url:
            cursor.execute("SELECT citations_list, created_at FROM journal_year_baselines WHERE journal = %s AND year = %s", (journal, year))
        else:
            cursor.execute("SELECT citations_list, created_at FROM journal_year_baselines WHERE journal = ? AND year = ?", (journal, year))
            
        row = cursor.fetchone()
        conn.close()
        
        if row:
            citations_list_json, created_at = row
            if isinstance(created_at, str):
                try:
                    created_at = datetime.fromisoformat(created_at.replace("Z", "+00:00"))
                except ValueError:
                    created_at = datetime.strptime(created_at.split('.')[0], "%Y-%m-%d %H:%M:%S")
                    
            # Check if older than 7 days
            if datetime.now().replace(tzinfo=None) - created_at.replace(tzinfo=None) > timedelta(days=7):
                return None
                
            citations = json.loads(citations_list_json)
            df = pd.DataFrame({"times_cited": citations})
            return df
            
        return None
    except Exception as e:
        print(f"Failed to get cached journal cell: {e}")
        return None

def save_journal_cell(journal, year, cell_df):
    if "times_cited" not in cell_df.columns or len(cell_df) == 0:
        return
        
    try:
        citations = cell_df["times_cited"].tolist()
        citations_json = json.dumps(citations)
        
        conn = get_db_connection()
        cursor = conn.cursor()
        
        postgres_url = os.environ.get("DATABASE_URL") or os.environ.get("POSTGRES_URL") or os.environ.get("POSTGRES_PRISMA_URL")
        if postgres_url:
            query = """
                INSERT INTO journal_year_baselines (journal, year, citations_list)
                VALUES (%s, %s, %s)
                ON CONFLICT (journal, year) DO UPDATE 
                SET citations_list = EXCLUDED.citations_list,
                    created_at = CURRENT_TIMESTAMP
            """
            cursor.execute(query, (journal, year, citations_json))
        else:
            query = """
                INSERT OR REPLACE INTO journal_year_baselines (journal, year, citations_list, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """
            cursor.execute(query, (journal, year, citations_json))
            
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"Failed to save journal cell to cache: {e}")
