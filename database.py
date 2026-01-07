# database.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG

class DatabaseManager:
    def __init__(self):
        self.init_db()

    def get_connection(self):
        try:
            return mysql.connector.connect(**DB_CONFIG)
        except Error as err:
            print(f"Database Connection Error: {err}")
            return None

    def init_db(self):
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    username VARCHAR(255) UNIQUE NOT NULL,
                    password VARCHAR(255) NOT NULL
                )
            """)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS history (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    user_id INT,
                    original_text TEXT,
                    translated_text TEXT,
                    target_lang VARCHAR(10),
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    FOREIGN KEY (user_id) REFERENCES users(id)
                )
            """)
            conn.commit()
            conn.close()

    def register_user(self, username, password):
        conn = self.get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return True
        except Error:
            return False
        finally:
            if conn.is_connected(): conn.close()

    def login_user(self, username, password):
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        cursor.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def add_history(self, user_id, original, translated, lang):
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("INSERT INTO history (user_id, original_text, translated_text, target_lang) VALUES (%s, %s, %s, %s)",
                           (user_id, original, translated, lang))
            conn.commit()
            conn.close()

    def get_user_history(self, user_id):
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute("SELECT id, original_text, translated_text, target_lang, created_at FROM history WHERE user_id=%s ORDER BY created_at DESC", (user_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def delete_history(self, history_id):
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE id=%s", (history_id,))
            conn.commit()
            conn.close()