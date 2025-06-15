import sqlite3
import hashlib

class Item:
    """
    아이템의 데이터 구조를 정의하는 클래스.
    - __init__: 객체 생성 시 사용. name 기반으로 id 자동 생성.
    - from_db: 데이터베이스 데이터로 객체를 재구성할 때 사용.
    """
    # __init__ 메소드에서 description을 category로 변경하고 기본값을 설정합니다.
    def __init__(self, name, quantity, price, cost, category="기타"):
        if not name:
            raise ValueError("아이템 이름은 비어있을 수 없습니다.")
        self.name = name
        self.item_id = self._generate_id(name)
        self.quantity = quantity
        self.price = price
        self.cost = cost
        # description 속성을 category로 변경합니다.
        self.category = category
    
    def _generate_id(self, name):
        """이름을 SHA256으로 해싱하여 고유 ID로 사용합니다. (16자리로 축약)"""
        return hashlib.sha256(name.encode('utf-8')).hexdigest()[:16]

    @classmethod
    # from_db 메소드에서도 description을 category로 변경합니다.
    def from_db(cls, name, item_id, quantity, price, cost, category):
        """DB 데이터로 객체를 만들 때 사용하는 별도의 생성 로직입니다."""
        instance = cls.__new__(cls)
        instance.name = name
        instance.item_id = item_id
        instance.quantity = quantity
        instance.price = price
        instance.cost = cost
        instance.category = category
        return instance

    def to_tuple(self):
        """Treeview에 값을 넣기 위한 튜플을 반환합니다."""
        # 반환하는 튜플에 description 대신 category를 포함합니다.
        return (self.name, self.item_id, self.quantity, self.price, self.cost, self.category)

class Inventory:
    """인벤토리 데이터베이스 관리를 담당하는 클래스"""
    def __init__(self, db_path="inventory.db"):
        self.conn = sqlite3.connect(db_path)
        self.cursor = self.conn.cursor()
        self._create_table()

    def _create_table(self):
        # 테이블 스키마에서 description 컬럼을 category로 변경합니다.
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS items (
            owner_id TEXT NOT NULL,
            item_id TEXT NOT NULL,
            name TEXT,
            quantity INTEGER,
            price INTEGER,
            cost INTEGER,
            category TEXT,
            PRIMARY KEY (owner_id, item_id)
        )""")
        self.conn.commit()

    def add_item(self, owner_id, item: Item):
        try:
            # INSERT 쿼리에서 category 컬럼에 값을 추가하도록 수정합니다.
            self.cursor.execute(
                "INSERT INTO items (owner_id, item_id, name, quantity, price, cost, category) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (owner_id, item.item_id, item.name, item.quantity, item.price, item.cost, item.category)
            )
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError(f"'{item.name}' 이름의 아이템이 이미 존재합니다.")

    def update_item(self, owner_id, original_item_id, **kwargs):
        # kwargs에 category가 포함되어 들어오면 자동으로 처리됩니다.
        fields = [f"{key} = ?" for key in kwargs]
        values = list(kwargs.values())
        if not fields: return
        values.extend([owner_id, original_item_id])
        query = f"UPDATE items SET {', '.join(fields)} WHERE owner_id = ? AND item_id = ?"
        try:
            self.cursor.execute(query, tuple(values))
            self.conn.commit()
        except sqlite3.IntegrityError:
            raise ValueError("변경하려는 이름의 아이템이 이미 존재합니다.")

    def delete_item(self, owner_id, item_id):
        self.cursor.execute("DELETE FROM items WHERE owner_id = ? AND item_id = ?", (owner_id, item_id))
        self.conn.commit()

    def list_items(self, owner_id):
        """특정 사용자의 모든 아이템 목록을 불러옵니다."""
        # SELECT 쿼리에서 description 대신 category를 가져옵니다.
        self.cursor.execute("SELECT name, item_id, quantity, price, cost, category FROM items WHERE owner_id = ?", (owner_id,))
        rows = self.cursor.fetchall()
        # Item.from_db를 사용하여 객체를 재구성합니다.
        return [Item.from_db(*row) for row in rows]

    def close(self):
        self.conn.close()

