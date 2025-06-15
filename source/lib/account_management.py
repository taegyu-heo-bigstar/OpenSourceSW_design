# account_management.py
#test
import sqlite3
import hashlib
import bcrypt
from datetime import datetime

class User:
    def __init__(self, user_id, username, name, password_hash, location):
        self.id = user_id
        self.username = username
        self.name = name
        self.password_hash = password_hash
        self.location = location

    def get_name(self):
        return self.name

    def get_username(self):
        return self.username

    def get_id(self):
        return self.id

    def get_location(self):
        return self.location


class AccountManager:
    """관리자 + 메일함 로직을 포함하는 DB 래퍼"""

    def __init__(self, db_path="users.db"):
        self.conn = sqlite3.connect(db_path, check_same_thread=False)
        self.cursor = self.conn.cursor()
        self.admin_ids = set()
        # --- 기존 테이블 ---
        self._create_user_table()
        # --- 신규: 메일 테이블 ---
        self._create_mail_table()
        self._load_admin_ids()

    # ---------------------------------------------------------------------
    # 기본 사용자/관리자 로직 -------------------------------------------------
    # ---------------------------------------------------------------------

    def _create_user_table(self):
        """users 테이블이 없으면 생성 + 초기 admin 계정 보장"""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL,
                password TEXT NOT NULL,
                location TEXT NOT NULL
            )"""
        )
        self.conn.commit()
        # admin 계정이 없으면 생성
        self.cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not self.cursor.fetchone():
            self.create_user("admin", "관리자", "admin", "서울")

    def _load_admin_ids(self):
        self.cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        self.admin_ids = {row[0] for row in self.cursor.fetchall()}

    def _hash_password(self, password: str) -> str:
        return bcrypt.hashpw(password.encode("utf-8"), bcrypt.gensalt()).decode("utf-8")

    def _generate_id(self, username: str) -> str:
        return hashlib.sha256(username.encode()).hexdigest()

    # ---------------- CRUD -------------------------------------------------
    def login(self, username, password):
        self.cursor.execute(
            "SELECT id, username, name, password, location FROM users WHERE username = ?",
            (username,),
        )
        row = self.cursor.fetchone()
        if row:
            user_id, db_username, name, stored_hash, location = row
            if bcrypt.checkpw(password.encode("utf-8"), stored_hash.encode("utf-8")):
                return User(user_id, db_username, name, stored_hash, location)
        return None

    def is_admin(self, user):
        return user.get_id() in self.admin_ids if user else False

    def create_user(self, username, name, password, location):
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            raise ValueError(f"'{username}'는 이미 존재하는 아이디입니다.")

        new_id = self._generate_id(username)
        hashed_pw = self._hash_password(password)

        self.cursor.execute(
            "INSERT INTO users (id, username, name, password, location) VALUES (?, ?, ?, ?, ?)",
            (new_id, username, name, hashed_pw, location),
        )
        self.conn.commit()

        if username == "admin":
            self.admin_ids.add(new_id)
        return True

    def delete_user(self, username):
        user_id = self._generate_id(username)
        if user_id in self.admin_ids:
            raise ValueError("초기 관리자 계정은 삭제할 수 없습니다.")
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_all_users(self, exclude_admin=True):
        query = "SELECT id, name, username, location FROM users"
        if exclude_admin:
            query += " WHERE username != 'admin'"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def get_username_by_id(self, user_id):
        self.cursor.execute("SELECT username FROM users WHERE id = ?", (user_id,))
        row = self.cursor.fetchone()
        return row[0] if row else None

    # ---------------------------------------------------------------------
    # 메일함 로직 -----------------------------------------------------------
    # ---------------------------------------------------------------------

    def _create_mail_table(self):
        """mails 테이블이 없으면 생성"""
        self.cursor.execute(
            """
            CREATE TABLE IF NOT EXISTS mails (
                mail_id   INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_id TEXT    NOT NULL,
                recipient_id TEXT NOT NULL,
                message   TEXT    NOT NULL,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                FOREIGN KEY(sender_id)   REFERENCES users(id),
                FOREIGN KEY(recipient_id) REFERENCES users(id)
            )"""
        )
        self.conn.commit()

    def send_mail(self, sender_id: str, recipient_id: str, message: str):
        message = message.strip()
        if not message:
            raise ValueError("메시지가 비어 있습니다.")
        # 수신자 존재 확인
        self.cursor.execute("SELECT id FROM users WHERE id = ?", (recipient_id,))
        if not self.cursor.fetchone():
            raise ValueError("존재하지 않는 수신자 ID입니다.")
        self.cursor.execute(
            "INSERT INTO mails (sender_id, recipient_id, message) VALUES (?, ?, ?)",
            (sender_id, recipient_id, message),
        )
        self.conn.commit()
        return True

    def get_inbox(self, user_id: str):
        """해당 사용자의 받은 메일 목록 최신순 반환"""
        self.cursor.execute(
            """
            SELECT sender_id, recipient_id, message, timestamp
            FROM   mails
            WHERE  recipient_id = ?
            ORDER BY timestamp DESC
            """,
            (user_id,),
        )
        return self.cursor.fetchall()

    # ---------------------------------------------------------------------
    def close_connection(self):
        self.conn.close()
