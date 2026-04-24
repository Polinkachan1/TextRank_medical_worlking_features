from flask import *
from database_work import init_db, get_medicine
from textrank_helper import build_and_save_links
from textrank import compare_feature

app = Flask(__name__)
init_db()


@app.route('/', methods=['GET', 'POST'])
def home():
    if request.method == 'POST':
        user_input = request.form.get('drug_name', '').strip().lower()

        if user_input == '':
            return render_template(
                'index.html',
                error="Вы не ввели никаких данных, введите название препарата"
            )

        medicine = get_medicine(user_input)
        if not medicine:
            return render_template(
                'index.html',
                error=f"Препарат '{user_input}' не найден в базе."
            )

        build_and_save_links(user_input)
        result_html = compare_feature(user_input)

        return render_template(
            'index.html',
            result=result_html,
            drug_name=user_input
        )

    return render_template('index.html', error=None)


if __name__ == '__main__':
    app.run(debug=True)