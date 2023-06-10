import os
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, session, flash)
import json
import random
import re
import sqlite3
import time
from datetime import datetime, timedelta

import requests
from bs4 import BeautifulSoup
from flask import Flask, render_template
from flask import redirect, url_for
from flask import request, jsonify
from flask_cors import CORS
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from datetime import datetime, timedelta
import pandas as pd


import scripto

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Remember to set a secret key

SECRET_CODE = 'your_secret_code'  # Set your secret code


@app.before_first_request
def init_db():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS data
(id INTEGER PRIMARY KEY AUTOINCREMENT, parametr1 TEXT, parametr2 TEXT, parametr3 TEXT, parametr4 TEXT, parametr5 TEXT, parametr6 TEXT )''')
    # Dodaj na początku kodu, np. po otwarciu połączenia z bazą danych
    c.execute('''
        CREATE TABLE IF NOT EXISTS wyslane (
            id INTEGER PRIMARY KEY,
            parametr1 TEXT,
            parametr2 TEXT,
            data TEXT,
            attacktype TEXT,
            size INT,
            units TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS niewyslane (
            id INTEGER PRIMARY KEY,
            parametr1 TEXT,
            parametr2 TEXT,
            data TEXT,
            attacktype TEXT,
            reason TEXT,
            url TEXT,
            massorsingle TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS wojska (
            id INTEGER PRIMARY KEY,
            coords TEXT,
            unit_count TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS przybywajace (
            id INTEGER PRIMARY KEY,
            defender_coords TEXT,
            attacker_coords TEXT,
            arrival_time TEXT
        )
    ''')

    conn.commit()
    conn.close()

# zmienna sterująca skryptem
script_enabled = False
is_stopping = False

@app.route('/lista')
def lista():
    if 'authorized' in session:

        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('SELECT * FROM data order by parametr3')
        rekordy = c.fetchall()
        conn.close()

        # Zlicz różne typy ataków
        licznik_typow_atakow = {
            'FAKE': 0,
            'OFF': 0,
            'BURZAK': 0,
            'FAKE SZLACHCIC': 0,
            'SZLACHCIC': 0
        }
        for rekord in rekordy:
            typ_ataku = rekord[4]
            if typ_ataku and typ_ataku.startswith('BURZAK'):
                licznik_typow_atakow['BURZAK'] += 1
            elif typ_ataku in licznik_typow_atakow:
                licznik_typow_atakow[typ_ataku] += 1

        return render_template('lista.html', rekordy=rekordy, licznik_typow_atakow=licznik_typow_atakow)
    else:
        return redirect(url_for('enter_code'))
@app.route('/', methods=['GET', 'POST'])
def home():
    if 'authorized' in session:
        if request.method == 'POST':
            global script_enabled
            script_enabled = True
            global is_stopping
            is_stopping = False
            print("[STARTED]")
            #wynik = uruchom_moj_skrypt()
            wynik = "Hej"
            return render_template('wynik.html', wynik=wynik)

        # Połącz się z bazą danych
        conn = sqlite3.connect('data.db')
        c = conn.cursor()

        conn = sqlite3.connect('data.db')
        c = conn.cursor()
        c.execute('SELECT parametr3 FROM data ORDER BY id DESC LIMIT 1')
        ostatni_atak = c.fetchone()
        c.execute('SELECT COUNT(*) FROM data')
        ilosc_niewyslanych = c.fetchone()[0]
        conn.close()

        # Przekazuj informacje do szablonu
        return render_template('index.html', ostatni_atak=ostatni_atak, ilosc_niewyslanych=ilosc_niewyslanych)

    else:
        return redirect(url_for('enter_code'))



@app.route('/wyslane')
def wyslane():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM wyslane order by data')
    rekordy = c.fetchall()

    for i, rekord in enumerate(rekordy):
        rekordy[i] = list(rekord)
        rekordy[i][6] = json.loads(rekordy[i][6])

    conn.close()
    return render_template('wyslane.html', rekordy=rekordy)



@app.route('/niewyslane')
def niewyslane():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT * FROM niewyslane order by data')
    rekordy = c.fetchall()
    conn.close()
    return render_template('niewyslane.html', rekordy=rekordy)


@app.route('/usun/<int:id>', methods=['POST'])
def usun(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))


@app.route('/wyslane_delete_all', methods=['POST'])
def wyslane_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM wyslane ")
    conn.commit()
    conn.close()
    return redirect(url_for('wyslane'))


@app.route('/burzaki_delete_all', methods=['POST'])
def burzaki_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data WHERE parametr4 LIKE 'BURZAK%'")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))
@app.route('/grubasy_delete_all', methods=['POST'])
def grubasy_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data where parametr4='SZLACHCIC'")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))

@app.route('/fejkgrubasy_delete_all', methods=['POST'])
def fejkgrubasy_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data where parametr4='FAKE SZLACHCIC'")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))


@app.route('/niewyslane_delete_all', methods=['POST'])
def niewyslane_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM niewyslane ")
    conn.commit()
    conn.close()
    return redirect(url_for('niewyslane'))


@app.route('/lista_delete_all', methods=['POST'])
def lista_delete_all():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM data ")
    conn.commit()
    conn.close()
    return redirect(url_for('lista'))


@app.route('/usun_niewyslane/<int:id>', methods=['POST'])
def usun_niewyslane(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM niewyslane WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('niewyslane'))


@app.route('/usun_wyslane/<int:id>', methods=['POST'])
def usun_wyslane(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute("DELETE FROM wyslane WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return redirect(url_for('wyslane'))


@app.route('/restore/<int:id>', methods=['POST'])
def restore(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    # Pobieranie rekordu z tabeli 'data' na podstawie id
    c.execute("SELECT * FROM niewyslane WHERE id=?", (id,))
    record = c.fetchone()
    print("Record1",record)
    record = record[1:]
    #record = record[:-2] + record[-1:]
    record = record[:4] + record[5:]

    print("Record2",record)

    if record:
        # Wstawianie rekordu do tabeli 'wyslane'
        c.execute('''
            INSERT INTO data (parametr1, parametr2, parametr3, parametr4, parametr5, parametr6)
            VALUES (?, ?, ?, ?, ?, ?)
        ''', record)
        print("Record:",record)

        # Usuwanie rekordu z tabeli 'data'
        c.execute("DELETE FROM niewyslane WHERE id=?", (id,))

        conn.commit()
        conn.close()
    return redirect(url_for('lista'))


@app.route('/edytuj/<int:id>', methods=['GET', 'POST'])
def edytuj(id):
    conn = sqlite3.connect('data.db')
    c = conn.cursor()

    if request.method == 'POST':
        parametr1 = request.form.get('parametr1')
        parametr2 = request.form.get('parametr2')
        parametr3 = request.form.get('parametr3')
        parametr4 = request.form.get('parametr4')

        # Sprawdzenie i poprawienie wartości parametr3
        try:
            dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
        except ValueError:
            try:
                dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
                miliseconds = dt.strftime("%f")
                while len(miliseconds) < 3:
                    miliseconds += '0'
                parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds
            except ValueError:
                dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S")
                parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S") + '.000'

        # Poprawka dla milisekund
        dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
        miliseconds = dt.strftime("%f")[:3]
        while len(miliseconds) < 3:
            miliseconds += '0'
        parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds

        c.execute("UPDATE data SET parametr1=?, parametr2=?, parametr3=?, parametr4=? WHERE id=?",
                  (parametr1, parametr2, parametr3, parametr4, id))
        conn.commit()
        conn.close()
        return redirect(url_for('lista'))
    else:
        c.execute("SELECT * FROM data WHERE id=?", (id,))
        rekord = c.fetchone()
        conn.close()
        return render_template('edytuj.html', rekord=rekord)


@app.route('/zapisz', methods=['POST'])
def zapisz():
    parametr1 = request.form.get('parametr1')
    parametr2 = request.form.get('parametr2')
    parametr3 = request.form.get('parametr3')
    parametr4 = request.form.get('parametr4')
    parametr5 = request.form.get('parametr5')


    # Sprawdzenie i poprawienie wartości parametr3
    try:
        dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
    except ValueError:
        try:
            dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
            miliseconds = dt.strftime("%f")
            while len(miliseconds) < 3:
                miliseconds += '0'
            parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds
        except ValueError:
            dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S")
            parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S") + '.000'

    # Poprawka dla milisekund
    dt = datetime.strptime(parametr3, "%Y-%m-%dT%H:%M:%S.%f")
    miliseconds = dt.strftime("%f")[:3]
    while len(miliseconds) < 3:
        miliseconds += '0'
    parametr3 = dt.strftime("%Y-%m-%dT%H:%M:%S.") + miliseconds

    conn = sqlite3.connect("data.db")
    c = conn.cursor()
    c.execute("INSERT INTO data (parametr1, parametr2, parametr3, parametr4, parametr5, parametr6) VALUES (?, ?, ?,?,?,?)",
              (parametr1, parametr2, parametr3, parametr4, parametr5, "0"))
    conn.commit()
    conn.close()

    return redirect(url_for('lista'))


@app.route('/massadding')
def massadding():
    return render_template('massadding.html')



@app.route('/process_text', methods=['POST'])
def process_text():
    text = request.form.get('input_text')

    # dzielimy tekst na linie
    lines = text.split('[*]')

    # pomiń nagłówek tabeli
    lines = lines[1:]

    attacks = []


    # iteracja przez każdą linię
    for line in lines:
        if line:
            # tworzymy słownik do przechowywania informacji o ataku
            attack = {}


            # dodajemy url do słownika
            url = re.search(r'\[url=(.*?)\]', line)
            if url:
                attack['url'] = url.group(1)
                print(attack['url'])
            attack_type_and_column = re.search(r'\[\|\].*?\[\|\](.*?)\[\|\](.*?)\[\|\]', line)
            if attack_type_and_column:
                attack_type = attack_type_and_column.group(1)
                next_column = attack_type_and_column.group(2)
                print("attack type:", attack_type)
                print("next column:", next_column)

                if 'fake gruby' in attack_type:
                    attack['type'] = 'FAKE SZLACHCIC'
                elif 'fake' in attack_type:
                    attack['type'] = 'FAKE'
                elif 'Katapulty' in attack_type:

                    units_building = attack_type.split('-')
                    attack['type'] = 'BURZAK - '+units_building[1]+" - "+units_building[2]


                else:
                    if int(next_column)>0:
                        attack['type'] = 'SZLACHCIC'
                    else:
                        attack['type'] = 'OFF'




            date_time = re.search(
                r'\[\|\](\d{4}-\d{2}-\d{2})\s*\[b\]\[color=#\w{6}\](\d{2}:\d{2}:\d{2})\[/color\]\[/b\]-\[b\]\[color=#\w{6}\](\d{2}:\d{2}:\d{2})\[/color\]\[/b\]',
                line)

            if date_time:
                date = date_time.group(1)
                time1 = date_time.group(2)
                time2 = date_time.group(3)
                attack['date'] = f'{date} {time1} {time2}'

            # koordynaty
            coords = re.findall(r'\[coord\](.*?)\[/coord\]', line)
            if coords:
                attack['from_village'] = coords[0]
                attack['target'] = coords[1]

            attacks.append(attack)

    for attack in attacks:
        print(attack)

    return render_template('table_page.html', table_data=attacks)

@app.route('/stop_script', methods=['POST'])
def stop_script():
    global is_stopping
    is_stopping = True
    global script_enabled
    print("[TRYING TO STOP]")

    return render_template('wynik.html', wynik="Skrypt zatrzymany")

@app.route('/get_script_status', methods=['GET'])
def get_script_status(is_stopping=is_stopping):

    status = script_enabled  # Ta funkcja powinna być zdefiniowana zgodnie z twoim rzeczywistym użyciem
    is_stopping = is_stopping # Ta funkcja powinna być zdefiniowana zgodnie z twoim rzeczywistym użyciem
    return jsonify({'status': status, 'isStopping': is_stopping})

if __name__ == "__main__":
    app.run(debug=True)
@app.route('/debug', methods=['GET', 'POST'])
def debug():
    if request.method == 'POST':
        wynik = uruchom_debug()

        return render_template('wynik.html', wynik=wynik)


    return render_template('index.html')

def uruchom_debug():
    is_successful, message = debug()

    if is_successful:
        return message
    else:
        return f"Błąd: {message}"

def debug():
    options = Options()
    options.add_argument('--user-data-dir=/path/to/user-data')
    options.add_argument('--profile-directory=Default')
    options.add_argument("--start-minimized")
    options.add_extension("windscribe.crx")
    # options.add_argument('--headless')
    # options.add_argument('--no-sandbox')

    options.add_argument(
        "user-agent=Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/58.0.3029.110 Safari/537")
    driver = webdriver.Chrome(options=options)
    time.sleep(1)
    driver.get("https://plemiona.pl")
    time.sleep(600)

@app.route('/update_data', methods=['GET'])
def update_data():
    conn = sqlite3.connect('data.db')
    c = conn.cursor()
    c.execute('SELECT data FROM wyslane ORDER BY id DESC LIMIT 1')
    ostatni_atak = c.fetchone()

    c.execute('SELECT COUNT(*) FROM wyslane')
    ilosc_wyslanych = c.fetchone()[0]




    c.execute('SELECT COUNT(*) FROM niewyslane')
    ilosc_niewyslanych = c.fetchone()[0]

    c.execute('SELECT COUNT(*) FROM data')
    ilosc_kolejka = c.fetchone()[0]


    conn.close()

    if ostatni_atak is not None:
        ostatni_atak = [(ostatni_atak[0][-12:-4],)]
    else:
        ostatni_atak= " - "

    if ilosc_wyslanych is None:
        ilosc_wyslanych=" - "

    if ilosc_niewyslanych is None:
        ilosc_niewyslanych=" - "

    if ilosc_kolejka is None:
        ilosc_kolejka=" - "

    # zwróć dane jako JSON
    return jsonify({'ostatni_atak': ostatni_atak, 'ilosc_wyslanych': ilosc_wyslanych, 'ilosc_niewyslanych':ilosc_niewyslanych, 'ilosc_kolejka':ilosc_kolejka})


@app.route('/save', methods=['GET', 'POST'])
def save():
    return render_template('zapisz.html')

@app.route('/add_to_db', methods=['POST'])
def add_to_db():
    types = request.form.getlist('type')
    dates = request.form.getlist('date')
    from_villages = request.form.getlist('from_village')
    targets = request.form.getlist('target')
    urls = request.form.getlist('url')  # dodajemy odczytywanie url
    print(urls)

    conn = sqlite3.connect("data.db")
    c = conn.cursor()

    # Lista przechowująca wszystkie wcześniej wylosowane czasy ataków
    attack_times = []

    for i in range(len(types)):
        type = types[i]
        date = dates[i]
        from_village = from_villages[i]
        target = targets[i]
        url = urls[i]  # przypisujemy url

        date_str, start_time_str, end_time_str = date.split(' ')

        start_time = datetime.strptime(date_str + ' ' + start_time_str, '%Y-%m-%d %H:%M:%S')
        end_time = datetime.strptime(date_str + ' ' + end_time_str, '%Y-%m-%d %H:%M:%S')

        # Jeżeli end_time jest wcześniejszy niż start_time, dodajemy jeden dzień do end_time
        if end_time < start_time:
            end_time += timedelta(days=1)

        time_range = end_time - start_time
        if time_range.total_seconds() > 0:

            while True:
                random_seconds = random.randrange(int(time_range.total_seconds()))
                random_time = start_time + timedelta(seconds=random_seconds)

                if all(abs((random_time - old_time).total_seconds()) >= 60 for old_time in attack_times):
                    break
            attack_times.append(random_time)

            attack_time = random_time.strftime('%Y-%m-%dT%H:%M:%S.%f')
            attack_time = attack_time[:-3]

            c.execute("INSERT INTO data (parametr4, parametr3, parametr1, parametr2, parametr5,parametr6) VALUES (?, ?, ?, ?, ?,?)",
                      (type, attack_time, from_village, target, url,"1"))  # dodajemy url do zapytania SQL
    conn.commit()
    conn.close()

    return redirect(url_for('lista'))


def uruchom_moj_skrypt():
    is_successful, message = scripto.scripto()

    if is_successful:
        return message
    else:
        return f"Błąd: {message}"

@app.route('/enter_code', methods=['GET', 'POST'])
def enter_code():
    if request.method == 'POST':
        code = request.form.get('code')
        if code == SECRET_CODE:
            session['authorized'] = True
            return redirect(url_for('home'))
        else:
            flash('Invalid code, try again.')
            return redirect(url_for('enter_code'))
    else:
        # renderuj formularz, gdy metoda to GET
        return render_template('enter_code.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
    if 'authorized' not in session:
        return 'Unauthorized', 403

    name = request.form.get('name')

    if name:
        print('Request for hello page received with name=%s' % name)
        return render_template('hello.html', name = name)
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('home'))

if __name__ == '__main__':
   app.run()
