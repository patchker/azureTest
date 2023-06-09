import os
from flask import (Flask, redirect, render_template, request,
                   send_from_directory, url_for, session)

app = Flask(__name__)
app.secret_key = 'your_secret_key'  # Remember to set a secret key

SECRET_CODE = 'your_secret_code'  # Set your secret code

@app.route('/')
def index():
   if 'code' in session and session['code'] == SECRET_CODE:
       print('Request for index page received')
       return render_template('index.html')
   else:
       return redirect(url_for('enter_code'))

@app.route('/enter_code', methods=['GET', 'POST'])
def enter_code():
    if request.method == 'POST':
        code = request.form.get('code')
        if code == SECRET_CODE:
            session['code'] = code
            return redirect(url_for('index'))
        else:
            return 'Invalid code', 403
    else:
        return render_template('enter_code.html')

@app.route('/favicon.ico')
def favicon():
    return send_from_directory(os.path.join(app.root_path, 'static'),
                               'favicon.ico', mimetype='image/vnd.microsoft.icon')

@app.route('/hello', methods=['POST'])
def hello():
    if 'code' not in session or session['code'] != SECRET_CODE:
        return 'Unauthorized', 403

    name = request.form.get('name')

    if name:
        print('Request for hello page received with name=%s' % name)
        return render_template('hello.html', name = name)
    else:
        print('Request for hello page received with no name or blank name -- redirecting')
        return redirect(url_for('index'))

if __name__ == '__main__':
   app.run()
