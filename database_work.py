import sqlite3
import os
import json # ну как словарь/список, хранит короче побочки


BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, 'medical_data.db')

def init_db():
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
            CREATE TABLE IF NOT EXISTS entries (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                input_type TEXT,
                content TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')
    # мед

    conn.execute('''
                    CREATE TABLE IF NOT EXISTS medicines (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        medicine_name TEXT NOT NULL UNIQUE,
                        official_side_effects TEXT,
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')
    # рев
    conn.execute('''
                       CREATE TABLE IF NOT EXISTS reviews (
                           id INTEGER PRIMARY KEY AUTOINCREMENT,
                           medicine_id INTEGER NOT NULL,
                           review_text TEXT NOT NULL,
                           source TEXT DEFAULT 'irecommend',
                           created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                           FOREIGN KEY (medicine_id) REFERENCES medicines (id) ON DELETE CASCADE
                       )
                   ''')

    conn.commit()
    conn.close()


def get_from_db(entry_id):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    result = conn.execute(''' 
            SELECT input_type, content FROM entries
            WHERE id = ?
    ''', (entry_id,)).fetchone()
    conn.close()
    if result:
        return dict(result)
    return None

def add_medicine(medicine, official_side_effects):
    conn = sqlite3.connect(DB_PATH)
    pobochki_json = json.dumps(official_side_effects, ensure_ascii=False)
    conn.execute('''
        INSERT INTO medicines (medicine, ofic_pobochki)
        VALUES (?, ?)
    ''', (medicine, pobochki_json))
    conn.commit()
    medicine_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return medicine_id

def get_medicine(medicine):
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    result = conn.execute('''
        SELECT * FROM medicines WHERE medicine = ?
    ''', (medicine,)).fetchone()
    conn.close()
    if result:
        return dict(result)
    return None


def add_review(medicine_id, review_text):
    conn = sqlite3.connect(DB_PATH)
    conn.execute('''
        INSERT INTO reviews (medicine_id, review)
        VALUES (?, ?)
    ''', (medicine_id, review_text))
    conn.commit()
    conn.close()


def get_reviews(medicine_id):
    conn = sqlite3.connect(DB_PATH)
    results = conn.execute('''
        SELECT review FROM reviews WHERE medicine_id = ?
    ''', (medicine_id,)).fetchall()
    conn.close()
    return [row[0] for row in results]

def save_into_db(input_type, user_input):
    conn = sqlite3.connect(DB_PATH)
    conn.execute(''' 
            insert into entries(input_type, content)
            values (?,?)
        ''', (input_type, user_input))
    conn.commit()
    entry_id = conn.execute('SELECT last_insert_rowid()').fetchone()[0]
    conn.close()
    return entry_id
