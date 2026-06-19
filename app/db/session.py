import sqlite3
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "credential_audit.db")

def init_db():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    
    # TABEL 1: Log Penerbitan Token (Split)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS split_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER NOT NULL,
            role_level INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # TABEL 2: Log Penggunaan Token (Recover)
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS recover_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            uid INTEGER NOT NULL,
            role_level INTEGER NOT NULL,
            token_hash TEXT NOT NULL,
            algorithm TEXT NOT NULL,
            status TEXT NOT NULL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    conn.commit()
    conn.close()

def insert_split_log(uid: int, role_level: int, token_hash: str, algorithm: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO split_logs (uid, role_level, token_hash, algorithm, status) VALUES (?, ?, ?, ?, ?)",
        (uid, role_level, token_hash, algorithm, status)
    )
    conn.commit()
    conn.close()

def insert_recover_log(uid: int, role_level: int, token_hash: str, algorithm: str, status: str):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO recover_logs (uid, role_level, token_hash, algorithm, status) VALUES (?, ?, ?, ?, ?)",
        (uid, role_level, token_hash, algorithm, status)
    )
    conn.commit()
    conn.close()

def verify_token_hash(token_hash: str) -> bool:
    # Cek token valid HANYA dari tabel penerbitan (split_logs)
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM split_logs WHERE token_hash = ?", (token_hash,))
    result = cursor.fetchone()
    conn.close()
    return result is not None