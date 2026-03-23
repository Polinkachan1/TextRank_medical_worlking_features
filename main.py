from flask import *
from database_work import *
app = Flask(__name__)
init_db()
@app.route('/', methods=['GET', 'POST'])
def home():
    message = None
    if request.method == 'POST':
        link_or_text = request.form.get("input_type")
        user_input = request.form.get("user_input")
        if user_input == '':
            return render_template('index.html', error =  "Вы не ввели никаких данных, введите название препарата или ссылку на него или текст с упоминанием препарата")
        entry_id = save_into_db(link_or_text, user_input)
        saved_id = get_from_db(entry_id)
        return render_template('index.html',
            result=saved_id['content'],
            entry_id=entry_id,
            input_type=saved_id['input_type'])

    return render_template('index.html', message=None)


if __name__ == '__main__':
    app.run()