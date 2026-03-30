import sqlite3
import os


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