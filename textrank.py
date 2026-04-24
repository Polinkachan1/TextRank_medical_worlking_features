import sqlite3
import json
from working_with_text import normalize_phrase


def load_from_db(medicine, db_path="medical_data.db"):
    """
    Загружает из базы данных:
    - связи препарат-симптом (кандидаты на побочки)
    - официальные побочные эффекты
    """
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    search_term = medicine.lower().strip()


    cursor.execute("""
        SELECT drug_symptom_links.symptom, drug_symptom_links.weight
        FROM drug_symptom_links
        JOIN medicines ON medicines.id = drug_symptom_links.medicine_id
        WHERE LOWER(medicines.medicine_name) LIKE ?
        ORDER BY drug_symptom_links.weight DESC
    """, (f'%{search_term}%',))
    links = cursor.fetchall()

    cursor.execute("""
        SELECT id, official_side_effects
        FROM medicines
        WHERE LOWER(medicine_name) LIKE ?
    """, (f'%{search_term}%',))
    row = cursor.fetchone()

    conn.close()

    medicine_id = None
    official_effects = []
    if row:
        medicine_id = row[0]
        if row[1]:
            official_effects = [normalize_phrase(x) for x in json.loads(row[1])]

    return medicine_id, links, official_effects


def load_sentences_for_symptom(medicine_name, symptom, db_path='medical_data.db'):
    """Загружает предложения для симптома из БД"""
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute('''
        SELECT sentence
        FROM symptom_sentences ss
        JOIN medicines m ON ss.medicine_id = m.id
        WHERE m.medicine_name = ? AND ss.symptom = ?
    ''', (medicine_name.lower(), symptom))

    rows = cursor.fetchall()
    conn.close()

    return [row[0] for row in rows]


def is_generic_single_word(symptom):
    generic_words = {
        "кожа", "губа", "глаз", "волос", "сустав",
        "кровь", "настроение", "нос", "спина", "колено",
        "поясница", "ресница"
    }
    norm = normalize_phrase(symptom)
    words = norm.split()
    return len(words) == 1 and words[0] in generic_words


def is_part_of_official(symptom, official_effects):
    sym_norm = normalize_phrase(symptom)
    sym_words = set(sym_norm.split())

    for official in official_effects:
        off_norm = normalize_phrase(official)
        off_words = set(off_norm.split())

        if sym_norm == off_norm:
            return True

        if sym_words and sym_words.issubset(off_words):
            return True

    return False


def compare_feature(medicine_name, db_path="medical_data.db"):
    medicine_id, links, official_effects = load_from_db(medicine_name, db_path)

    if medicine_id is None:
        return "<p>Препарат не найден.</p>"

    hidden_effects = []
    for symptom, weight in links:
        if is_generic_single_word(symptom):
            continue
        if is_part_of_official(symptom, official_effects):
            continue
        hidden_effects.append((symptom, weight))

    hidden_effects.sort(key=lambda x: x[1], reverse=True)

    html = f"<h3>💊 Препарат: {medicine_name.upper()}</h3>"
    html += "<p><b>📋 Официальные побочки:</b> "
    html += ", ".join(official_effects) if official_effects else "нет"
    html += "</p>"

    if hidden_effects:
        html += "<p><b>⚠️ Кандидаты на неявные побочки:</b></p><ul>"
        for symptom, weight in hidden_effects[:10]:
            html += f"<li><b>{symptom}</b> <span style='color: gray'>(score: {weight})</span><br>"

            sentences = load_sentences_for_symptom(medicine_name, symptom, db_path)
            if sentences:
                for sent in sentences:
                    html += f"<span style='color: #555; font-size: 0.9em;'>📝 &quot;{sent}&quot;</span><br>"
            else:
                html += "<span style='color: #888;'>❌ Нет предложений</span>"

            html += "</li>"
        html += "</ul>"
    else:
        html += "<p>✅ Новых кандидатов не найдено</p>"

    return html