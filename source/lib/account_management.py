import sqlite3
import hashlib
import bcrypt
# Mailbox 클래스를 임포트합니다.
from mail_box import Mailbox

class User:
    """사용자 정보를 담는 데이터 클래스입니다."""
    def __init__(self, user_id, username, name, password_hash, location):
        self.id = user_id
        self.username = username
        self.name = name
        self.password_hash = password_hash
        self.location = location
    def get_name(self): return self.name
    def get_username(self): return self.username
    def get_id(self): return self.id
    def get_location(self): return self.location

class AccountManager:
    """사용자 계정 데이터베이스 관리를 담당하는 클래스입니다."""
    def __init__(self, db_path="users.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        
        # Mailbox 인스턴스를 생성합니다.
        self.mailbox = Mailbox()

        self._create_user_table()
        # admin_ids는 is_admin에서 사용되므로 로드합니다.
        self._load_admin_ids()

    def _create_user_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, password TEXT NOT NULL, location TEXT NOT NULL 
            )''')
        self.conn.commit()
        # 'admin' 계정이 없으면 생성합니다.
        self.cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not self.cursor.fetchone():
            self.create_user("admin", "관리자", "admin", "서울")

    def _load_admin_ids(self):
        self.cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        self.admin_ids = {row[0] for row in self.cursor.fetchall()}

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
    
    def _generate_id(self, username):
        return hashlib.sha256(username.encode()).hexdigest()
    
    def login(self, username, password):
        self.cursor.execute("SELECT id, username, name, password, location FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if row:
            user_id, db_username, name, stored_hash_str, location = row
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash_str.encode('utf-8')):
                return User(user_id, db_username, name, stored_hash_str, location)
        return None

    def is_admin(self, user):
        return user.get_id() in self.admin_ids if user else False

    def create_user(self, username, name, password, location):
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            raise ValueError(f"'{username}'는 이미 존재하는 아이디입니다.")
        
        new_id = self._generate_id(username)
        hashed_pw = self._hash_password(password).decode('utf-8')
        
        self.cursor.execute("INSERT INTO users (id, username, name, password, location) VALUES (?, ?, ?, ?, ?)",
                            (new_id, username, name, hashed_pw, location))
        self.conn.commit()
        
        if username == 'admin': self.admin_ids.add(new_id)
        return True

    def delete_user(self, username):
        if username == 'admin':
            raise ValueError("초기 관리자 계정은 삭제할 수 없습니다.")
        self.cursor.execute("DELETE FROM users WHERE username = ?", (username,))
        self.conn.commit()
        return self.cursor.rowcount > 0

    def get_all_users(self, exclude_user_id=None):
        """
        모든 사용자 목록을 반환합니다.
        - exclude_user_id: 제공된 user_id를 가진 사용자는 목록에서 제외됩니다.
        - 'admin' 사용자는 항상 제외됩니다.
        """
        # *** 수정된 부분: 쿼리 로직을 명확하게 수정합니다. ***
        query = "SELECT id, name, username, location FROM users WHERE username != ?"
        params = ['admin']

        if exclude_user_id:
            query += " AND id != ?"
            params.append(exclude_user_id)
            
        self.cursor.execute(query, params)
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()
        self.mailbox.close()
