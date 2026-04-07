import re
import sqlite3
import json
from collections import defaultdict
import pymorphy2

morph = pymorphy2.MorphAnalyzer()


def normalize_phrase(phrase):
    if not phrase:
        return ""
    phrase = re.sub(r'[^\w\s]', ' ', phrase.lower())
    words = phrase.split()
    normalized = []
    for word in words:
        if len(word) > 2:
            try:
                parsed = morph.parse(word)[0]
                normalized.append(parsed.normal_form)
            except:
                normalized.append(word)

    return ' '.join(normalized)


def extract_symptom_like_phrases(text):
    # Паттерн: прилагательное + существительное
    pattern = r'(\w+[аяоеийы])\s+(\w+[а-я]+)'
    matches = re.findall(pattern, text.lower())

    phrases = []
    for adj, noun in matches:
        if len(adj) > 2 and len(noun) > 2:
            phrases.append(f"{adj} {noun}")

    # Ещё паттерн: существительное + прилагательное
    pattern2 = r'(\w+[а-я]+)\s+(\w+[аяоеийы])'
    matches2 = re.findall(pattern2, text.lower())
    for noun, adj in matches2:
        if len(noun) > 2 and len(adj) > 2:
            phrases.append(f"{adj} {noun}")

    return list(set(phrases))

# Ключевые слова для поиска
def get_all_symptoms_for_key_words(db_path='medical_data.db'):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('SELECT official_side_effects FROM medicines WHERE official_side_effects != ""')
    all_side_effects = cursor.fetchall()

    SYMPTOMS = set()

    for (effects_text,) in all_side_effects:
        if effects_text:
            try:
                symptoms_list = json.loads(effects_text)
                for symptom in symptoms_list:
                    normalized = normalize_phrase(symptom)
                    if normalized:
                        SYMPTOMS.add(normalized)
            except:
                pass

    conn.close()
    return list(SYMPTOMS)

def is_symptom_like(phrase, all_symptoms):
    words = phrase.split()
    for symptom in all_symptoms:
        if phrase == symptom:
            return True
        symptom_words = symptom.split()
        for sw in symptom_words:
            if sw in words:
                return True
    return False


# берем симптомы и ищем по ключевым словам есть ли такие у нас
def get_symptoms_from_text(text, medicine_name=None, db_path='medical_data.db'):
    if not text:
        return []
    phrases = extract_symptom_like_phrases(text)
    all_symptoms = get_all_symptoms_for_key_words(db_path)
    result = []
    for phrase in phrases:
        normalized = normalize_phrase(phrase)
        if len(normalized) < 4:
            continue
        if medicine_name and medicine_name.lower() in normalized:
            continue
        if is_symptom_like(normalized, all_symptoms):
            result.append(normalized)
    return list(set(result))

# создаем еще одну таблицу для симптомов и добавляем каждому симптому вес в соответствии с частотой его встречаемости
def build_and_save_links(medicine,db_path='medical_data.db'):
    print(f"🔍 Начало обработки для {medicine}")
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    conn.execute('''
                CREATE TABLE IF NOT EXISTS drug_symptom_links (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    medicine_id INTEGER NOT NULL,
                    symptom TEXT,
                    weight INTEGER DEFAULT 1,
                    unique(medicine_id, symptom)
                )
            ''')
    # Получаем все отзывы по лекарству, которое ищем
    cursor.execute('''
    select reviews.id, reviews.review_text, reviews.medicine_id, medicines.medicine_name from reviews 
    join medicines on medicines.id = reviews.medicine_id
    where review_text != "" and medicines.medicine_name = (?)
    ''', (medicine,))
    reviews = cursor.fetchall()
    links = defaultdict(int) # создаем базовый словарь для симптомов с подсчетом вхождений симптомов
    for id, review_text, medicine_id, medicine_name in reviews:
        symptoms = get_symptoms_from_text(review_text, medicine_name=medicine)
        if symptoms:
            for symptom in symptoms:
                links[(medicine_id, symptom)] += 1
            print(f"  {medicine_name}: {', '.join(symptoms)}")

    cursor.execute('DELETE FROM drug_symptom_links WHERE medicine_id = (select id from medicines where medicine_name = ?)', (medicine, ))
    for (medicine_id, symptom), weight in links.items():
        cursor.execute('''
                    INSERT INTO drug_symptom_links (medicine_id, symptom, weight)
                    VALUES (?, ?, ?)
                ''', (medicine_id, symptom, weight))
    conn.commit()
    conn.close()

    print(f"Сохранено {len(links)} связей для препарата '{medicine}'")
    return links
