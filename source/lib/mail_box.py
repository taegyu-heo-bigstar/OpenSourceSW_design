import sqlite3
from datetime import datetime

class Mail:
    """메일 한 건의 데이터를 담는 클래스입니다."""
    def __init__(self, mail_id, sender_name, sender_id, receiver_id, message, timestamp):
        self.mail_id = mail_id
        self.sender_name = sender_name
        self.sender_id = sender_id
        self.receiver_id = receiver_id
        self.message = message
        self.timestamp = timestamp

    def to_list_tuple(self):
        """메일 목록(Treeview)에 표시하기 위한 튜플을 반환합니다."""
        return (self.sender_name, self.timestamp)

class Mailbox:
    """메일 데이터베이스 관리를 담당하는 클래스입니다."""
    def __init__(self, db_path="mailbox.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS mails (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                sender_name TEXT NOT NULL,
                sender_id TEXT NOT NULL,
                receiver_id TEXT NOT NULL,
                message TEXT NOT NULL,
                timestamp TEXT NOT NULL
            )''')
        self.conn.commit()

    def send_mail(self, sender_name, sender_id, receiver_id, message):
        """새로운 메일을 데이터베이스에 저장합니다."""
        if not all([sender_name, sender_id, receiver_id, message]):
            raise ValueError("메일 정보가 불완전합니다.")
        
        timestamp = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        
        self.cursor.execute(
            "INSERT INTO mails (sender_name, sender_id, receiver_id, message, timestamp) VALUES (?, ?, ?, ?, ?)",
            (sender_name, sender_id, receiver_id, message, timestamp)
        )
        self.conn.commit()

    def get_mails_for_user(self, user_id):
        """특정 사용자가 받은 모든 메일을 시간순으로 정렬하여 반환합니다."""
        self.cursor.execute(
            "SELECT * FROM mails WHERE receiver_id = ? ORDER BY timestamp DESC",
            (user_id,)
        )
        rows = self.cursor.fetchall()
        return [Mail(*row) for row in rows]

    def close(self):
        """데이터베이스 연결을 닫습니다."""
        self.conn.close()
