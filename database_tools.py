# database_tools.py

import sqlite3
import json
import logging
import re 
import os
from typing import List

# Konfigurasi database path
DB_PATH = "suggestion_history.db" 

def init_suggestion_db():
    """Menginisialisasi tabel riwayat saran dan memastikan file database ada."""
    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS suggestion_history (
            suggestion_id INTEGER PRIMARY KEY,
            user_prompt TEXT NOT NULL,
            assistant_response TEXT NOT NULL,
            suggestions_json TEXT NOT NULL,
            created_at TEXT DEFAULT (strftime('%Y-%m-%d %H:%M:%S', 'now'))
        )
        """)
        conn.commit()
        logging.info("Database suggestion_history.db successfully initialized.")
    except sqlite3.Error as e:
        logging.error(f"Error initializing suggestion database: {e}")
    finally:
        if conn:
            conn.close()

def save_suggestion_history(user_prompt: str, assistant_response: str, suggestions: List[str]) -> bool:
    """Menyimpan konteks dan saran yang dihasilkan ke dalam database."""
    # Pastikan database telah diinisialisasi sebelum menyimpan
    if not os.path.exists(DB_PATH):
        init_suggestion_db()

    conn = None
    try:
        conn = sqlite3.connect(DB_PATH)
        cursor = conn.cursor()
        
        suggestions_json = json.dumps(suggestions)
        
        query = """
        INSERT INTO suggestion_history (user_prompt, assistant_response, suggestions_json) 
        VALUES (?, ?, ?)
        """
        # Bersihkan konten respons dari saran yang mungkin menempel
        clean_response = re.sub(r'(\n\n---\n\*\*Saran.*?:.*?)', '', assistant_response, flags=re.DOTALL) 
        clean_response = re.sub(r'(\n\n---\n\*\*Suggestion.*?:.*?)', '', clean_response, flags=re.DOTALL) 
        
        cursor.execute(query, (user_prompt, clean_response, suggestions_json))
        conn.commit()
        logging.info(f"Suggestions saved to DB. ID: {cursor.lastrowid}")
        return True
    except sqlite3.Error as e:
        logging.error(f"DB error saving suggestions: {e}")
        return False
    finally:
        if conn:
            conn.close()

# Inisialisasi DB saat modul ini diimpor pertama kali
if not os.path.exists(DB_PATH):
    init_suggestion_db()