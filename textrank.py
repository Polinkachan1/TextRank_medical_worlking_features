import sqlite3
import networkx as nx # херь для графов

def load_from_db(db_path ="medical_path.db"):
    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()
    cursor.execute('''
    select drug_symptoms_links.id, medicines.medicine_name, drug_symptoms_links.symptom, drug_symptoms_links.weight from drug_symptoms_links
    join medicines on medicines.id = drug_symptoms_links.medicine_id
    ''')
    links = cursor.fetchall()
    cursor.execute('''
    select id, medicine_name, official_side_effects from medicines 
    ''')
    official_info = cursor.fetchall()
    conn.close()
    official_side_effects = {}
    medicines = {}
    for med_id, name, official_side_effects_text in official_info:
        medicines[med_id] = name
        if official_side_effects_text:
            symptoms = [s.strip().lower() for s in official_side_effects_text.split(',') if s.strip()]
        else:
            symptoms = []

        official_side_effects[med_id] = symptoms
    return links, medicines, official_side_effects

def build_graph(links):
    G = nx.Graph() # наш граф
    for med_id, med_name, symptom, weight in links:

        G.add_node(med_id, name=med_name, type='medicine')  # добавляем узел препарата
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

    links, medicines, official_effects = load_from_db(db_path) #данные загрузили

    medicine_id = None
    for klych, name in medicines.items():
        if klych.lower() == medicine_name.lower():
            medicine_id = klych
            break
    if medicine_id is None:
        print(f"Препарат {medicine_name} не найден")
        return

    offic = official_effects.get(medicine_id, [])
    print("\n Официальные побочные эффекты:")
    for effect in offic:
        print(f"- {effect}")

    G = build_graph(links)
    symptoms_rank = textrank(G)

    not_offic = []
    for sym, rank in symptoms_rank.items():
        offic_lower = []
        for i in offic:
            offic_lower.append(i.lower())
        if sym.lower() not in offic_lower:
            not_offic.append((sym, rank))

        print("\n Неочевидные побочные эффекты: ")
        for symp, rank in not_offic:
            print(f"{symp}(вес: {rank:4f})")
            return not_offic




