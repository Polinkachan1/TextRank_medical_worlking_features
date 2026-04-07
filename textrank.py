import re
import pymorphy2
import sqlite3
import json
import networkx as nx # херь для графов


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

def load_from_db(medicine, db_path ="medical_path.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    select drug_symptom_links.id, medicines.medicine_name, drug_symptom_links.symptom, drug_symptom_links.weight from drug_symptom_links
    join medicines on medicines.id = drug_symptom_links.medicine_id
    where medicines.medicine_name = ?
    ''', (medicine,))
    links = cursor.fetchall()
    cursor.execute('''select id, medicine_name, official_side_effects from medicines WHERE medicine_name = ?''', (medicine,))
    official_info = cursor.fetchall()
    conn.close()
    official_side_effects = {}
    medicines = {}
    for med_id, name, official_text in official_info:
        medicines[med_id] = name
        if official_text:
            symptoms = json.loads(official_text)
            normalized_symptoms = [normalize_phrase(s) for s in symptoms]
            official_side_effects[med_id] = normalized_symptoms
        else:
            symptoms = []

        official_side_effects[med_id] = symptoms
    return links, medicines, official_side_effects

def build_graph(links):
    G = nx.Graph() # наш граф
    for med_id, med_name, symptom, weight in links:
        G.add_node(med_name, type='medicine')  # добавляем узел препарата
        G.add_node(symptom, type="effect")  # добавляяем узел побочки
        G.add_edge(med_id, symptom, weight=weight)  # добавили ребро между ними с вессом
    medicine_nodes = [i for i in G.nodes() if G.nodes[i].get('type') == 'medicine']
    symptom_nodes = [i for i in G.nodes() if G.nodes[i].get('type') == "effect"]
    return G

def textrank(G):
    if G.number_of_nodes() == 0:# спец штука, которая проверяет количество узлов
        return {}
    ranks = nx.pagerank(G, weight='weight')

    symptom_ranks = {}
    for node, rank in ranks.items():
        if G.nodes[node].get('type') == 'effect':
            symptom_ranks[node] = rank
    sorted_ranks = dict(sorted(symptom_ranks.items(), key=lambda x: x[1], reverse=True))

    return sorted_ranks


def compare_feature(medicine_name, db_path="medical_data.db"):
    print(f"Препарат: {medicine_name.upper()}")

    links, medicines, official_effects = load_from_db(medicine_name, db_path) #данные загрузили

    medicine_id = list(medicines.keys())[0]

    offic = official_effects.get(medicine_id, [])
    print("\n Официальные побочные эффекты:")
    for effect in offic:
        print(f"- {effect}")
    offic_lower = [o.lower() for o in offic]
    G = build_graph(links)
    symptoms_rank = textrank(G)
    not_offic = []

    for sym, rank in symptoms_rank.items():
        if sym.lower() not in offic_lower:
            not_offic.append((sym, rank))

    not_offic.sort(key=lambda x: x[1], reverse=True)

    result = f"\n💊 ПРЕПАРАТ: {medicine_name.upper()}\n"
    result += f"\n📋 Официальные побочки: {', '.join(offic) if offic else 'нет'}\n"

    if not_offic:
        result += f"\n⚠️ НОВЫЕ (неявные) побочки:\n"
        for sym, rank in not_offic[:10]:
            result += f"   - {sym} (важность: {rank:.4f})\n"
    else:
        result += f"\n✅ Новых побочек не найдено\n"

    return result




