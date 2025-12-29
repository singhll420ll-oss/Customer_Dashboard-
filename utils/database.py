import psycopg2
from psycopg2.extras import RealDictCursor
import os
from contextlib import contextmanager

@contextmanager
def get_db():
    conn = psycopg2.connect(os.environ.get('DATABASE_URL'))
    conn.autocommit = False
    try:
        with conn.cursor(cursor_factory=RealDictCursor) as cur:
            yield cur
            conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()

def execute_query(query, params=None):
    with get_db() as cur:
        cur.execute(query, params or ())
        if query.strip().upper().startswith('SELECT'):
            return cur.fetchall()
        elif query.strip().upper().startswith('INSERT'):
            cur.execute("SELECT LASTVAL()")
            return cur.fetchone()['lastval']

def fetch_one(query, params=None):
    with get_db() as cur:
        cur.execute(query, params or ())
        return cur.fetchone()

def fetch_all(query, params=None):
    with get_db() as cur:
        cur.execute(query, params or ())
        return cur.fetchall()
