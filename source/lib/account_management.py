# account_management.py

import sqlite3
import hashlib
import bcrypt
# import re # 더 이상 필요 없으므로 삭제

class User:
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
    def __init__(self, db_path="users.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self.admin_ids = set()
        self._create_user_table()
        self._load_admin_ids()

    def _create_user_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id TEXT PRIMARY KEY, username TEXT UNIQUE NOT NULL,
                name TEXT NOT NULL, password TEXT NOT NULL, location TEXT NOT NULL 
            )''')
        self.conn.commit()
        self.cursor.execute("SELECT * FROM users WHERE username='admin'")
        if not self.cursor.fetchone():
            # 기본 관리자 지역을 '서울'으로 설정
            self.create_user("admin", "관리자", "admin", "서울")

    def _load_admin_ids(self):
        self.cursor.execute("SELECT id FROM users WHERE username = 'admin'")
        self.admin_ids = {row[0] for row in self.cursor.fetchall()}

    def _hash_password(self, password):
        return bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())

    def _generate_id(self, username):
        return hashlib.sha256(username.encode()).hexdigest()

    # *** 삭제된 부분 ***: 주소 형식 검증 메소드 (_is_valid_korean_address) 삭제
    
    def login(self, username, password):
        self.cursor.execute("SELECT id, username, name, password, location FROM users WHERE username = ?", (username,))
        row = self.cursor.fetchone()
        if row:
            user_id, db_username, name, stored_hash, location = row
            if bcrypt.checkpw(password.encode('utf-8'), stored_hash.encode('utf-8')):
                return User(user_id, db_username, name, stored_hash, location)
        return None

    def is_admin(self, user):
        return user.get_id() in self.admin_ids if user else False

    def create_user(self, username, name, password, location):
        self.cursor.execute("SELECT id FROM users WHERE username = ?", (username,))
        if self.cursor.fetchone():
            raise ValueError(f"'{username}'는 이미 존재하는 아이디입니다.")
        
        # *** 삭제된 부분 ***: 주소 형식 검증 로직 호출 부분 삭제
        
        new_id = self._generate_id(username)
        hashed_pw = self._hash_password(password).decode('utf-8')
        
        self.cursor.execute("INSERT INTO users (id, username, name, password, location) VALUES (?, ?, ?, ?, ?)",
                            (new_id, username, name, hashed_pw, location))
        self.conn.commit()
        
        if username == 'admin': self.admin_ids.add(new_id)
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
        if exclude_admin: query += " WHERE username != 'admin'"
        self.cursor.execute(query)
        return self.cursor.fetchall()

    def close_connection(self):
        self.conn.close()