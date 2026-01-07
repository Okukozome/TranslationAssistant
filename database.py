# database.py
import mysql.connector
from mysql.connector import Error
from config import DB_CONFIG


class DatabaseManager:
    """
    数据库管理类：负责所有与 MySQL 数据库的交互逻辑，包括初始化、用户管理和历史记录操作。

    """

    def __init__(self):
        """
        初始化方法：在实例化时尝试建立连接并初始化必要的数据库表。

        """
        self.init_db()

    def get_connection(self):
        """
        建立数据库连接。
        :return: 返回 mysql.connector 连接对象，若连接失败则返回 None。

        """
        try:
            # 使用 config.py 中定义的 DB_CONFIG 配置信息进行连接
            return mysql.connector.connect(**DB_CONFIG)
        except Error as err:
            print(f"Database Connection Error: {err}")
            return None

    def init_db(self):
        """
        初始化数据库表结构：创建用户表 (users) 和翻译历史表 (history)。

        """
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            # 创建用户表：存储用户名和密码
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS users
                           (
                               id
                               INT
                               AUTO_INCREMENT
                               PRIMARY
                               KEY,
                               username
                               VARCHAR
                           (
                               255
                           ) UNIQUE NOT NULL,
                               password VARCHAR
                           (
                               255
                           ) NOT NULL
                               )
                           """)
            # 创建历史记录表：存储原文、译文、目标语言及关联的用户 ID
            cursor.execute("""
                           CREATE TABLE IF NOT EXISTS history
                           (
                               id
                               INT
                               AUTO_INCREMENT
                               PRIMARY
                               KEY,
                               user_id
                               INT,
                               original_text
                               TEXT,
                               translated_text
                               TEXT,
                               target_lang
                               VARCHAR
                           (
                               10
                           ),
                               created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                               FOREIGN KEY
                           (
                               user_id
                           ) REFERENCES users
                           (
                               id
                           )
                               )
                           """)
            conn.commit()
            conn.close()

    def register_user(self, username, password):
        """
        注册新用户。
        :param username: 用户名
        :param password: 密码（简单起见使用明文，后续考虑哈希加密）
        :return: 注册成功返回 True，用户名冲突或连接失败返回 False。

        """
        conn = self.get_connection()
        if not conn: return False
        cursor = conn.cursor()
        try:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, password))
            conn.commit()
            return True
        except Error:
            # 捕获异常，通常是由于用户名唯一约束冲突
            return False
        finally:
            if conn.is_connected(): conn.close()

    def login_user(self, username, password):
        """
        验证用户登录。
        :param username: 用户名
        :param password: 密码
        :return: 验证通过返回用户 ID (int)，否则返回 None。

        """
        conn = self.get_connection()
        if not conn: return None
        cursor = conn.cursor()
        # 查询匹配用户名和密码的记录
        cursor.execute("SELECT id FROM users WHERE username=%s AND password=%s", (username, password))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else None

    def add_history(self, user_id, original, translated, lang):
        """
        添加一条翻译历史记录。
        :param user_id: 关联的用户 ID
        :param original: 待翻译的原文内容
        :param translated: 翻译后的文本内容
        :param lang: 目标语言名称

        """
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute(
                "INSERT INTO history (user_id, original_text, translated_text, target_lang) VALUES (%s, %s, %s, %s)",
                (user_id, original, translated, lang))
            conn.commit()
            conn.close()

    def get_user_history(self, user_id):
        """
        获取指定用户的所有翻译历史。
        :param user_id: 用户 ID
        :return: 包含历史记录元组的列表，按创建时间倒序排列。

        """
        conn = self.get_connection()
        if not conn: return []
        cursor = conn.cursor()
        cursor.execute(
            "SELECT id, original_text, translated_text, target_lang, created_at FROM history WHERE user_id=%s ORDER BY created_at DESC",
            (user_id,))
        results = cursor.fetchall()
        conn.close()
        return results

    def delete_history(self, history_id):
        """
        根据 ID 删除特定的历史记录。
        :param history_id: 历史记录的唯一标识 ID

        """
        conn = self.get_connection()
        if conn:
            cursor = conn.cursor()
            cursor.execute("DELETE FROM history WHERE id=%s", (history_id,))
            conn.commit()
            conn.close()