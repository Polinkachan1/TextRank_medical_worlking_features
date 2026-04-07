from flask import *
from database_work import *
from textrank_helper import build_and_save_links
from textrank import load_from_db, build_graph, textrank, compare_feature
import json


app = Flask(__name__)
init_db()


@app.route('/', methods=['GET', 'POST'])
def home():
    message = None
    if request.method == 'POST':
        user_input = request.form.get('drug_name', '').strip().lower()
        print(user_input)
        if user_input == '':
            return render_template('index.html', error =  "Вы не ввели никаких данных, введите название препарата или ссылку на него или текст с упоминанием препарата")
        medicine = get_medicine(user_input)

        build_and_save_links(user_input) #Сохранено {len(links)} связей в drug_symptom_links
        if not medicine:
            return render_template('index.html',
                                   error=f"Препарат '{user_input}' не найден в базе.")

        result_html = compare_feature(user_input)
        return render_template('index.html',
                               result=result_html,
                               drug_name=user_input)

    return render_template('index.html', error=None)


if __name__ == '__main__':
    app.run()