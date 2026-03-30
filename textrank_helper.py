import sqlite3
from collections import defaultdict

# Ключевые слова для поиска
def get_all_symptoms_for_key_words(db_path='medical_data.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
        select official_side_effects from medicines
        where official_side_effects != ""
        ''')
    all_side_effects = cursor.fetchall()
    SYMPTOMS = set() # чтоб ниче не повторялось
    for (effects_text,) in all_side_effects:
        symptoms_list = [i.lower() for i in effects_text.split(",")]
        for symptom in symptoms_list:
            SYMPTOMS.add(symptom)
    return list(SYMPTOMS)

# берем симптомы и ищем по ключевым словам есть ли такие у нас
def get_symptoms_from_text(text):
    if not text:
        return []
    text_lower = text.lower()
    found = []
    for symptom in get_all_symptoms_for_key_words():
        if symptom in text_lower:
            found.append(symptom)
    return list(set(found))

# создаем еще одну таблицу для симптомов и добавляем каждому симптому вес в соответствии с частотой его встречаемости
def build_and_save_links(db_path='medical_data.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.execute('''
                CREATE TABLE IF NOT EXISTS drug_symptoms_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine_id INTEGER NOT NULL,
                    symptom TEXT,
                    weight INTEGER DEFAULT 1,
                    unique(medicine_id, symptom)
                )
            ''')
    # Получаем все отзывы
    cursor.execute('''
    select reviews.id, reviews.review_text, reviews.medicine_id, medicines.medicine_name from reviews 
    join medicines on medicines.id = reviews.medicine_id
    where review_text != ""
    ''')
    reviews = cursor.fetchall()
    links = defaultdict(int) # создаем базовый словарь для симптомов с подсчетом вхождений симптомов
    for id, review_text, medicine_id, medicine_name in reviews:
        symptoms = get_symptoms_from_text(review_text)
        if symptoms:
            for symptom in symptoms:
                links[(medicine_id, symptom)] += 1
            print(f"  {medicine_name}: {', '.join(symptoms)}")

        cursor.execute('DELETE FROM drug_symptom_links')
        for (medicine_id, symptom), weight in links.items():
            cursor.execute('''
                    INSERT INTO drug_symptom_links (medicine_id, symptom, weight)
                    VALUES (?, ?, ?)
                ''', (medicine_id, symptom, weight))
        conn.commit()
        conn.close()

        print(f"Сохранено {len(links)} связей в drug_symptom_links")
        return links
