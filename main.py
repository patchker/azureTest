from flask import Flask, Response, request, render_template, redirect, url_for
from flask_login import LoginManager, UserMixin, login_required, login_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)

# Flask-Login requires to set up a secret key for sessions
app.secret_key = ''

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = "login" # specify what view to go to when a login is required

# User class for the user's properties
class User(UserMixin):
    def __init__(self, id, password):
        self.id = id
        self.password = password

# Assume we have the following user:
user = User('user', generate_password_hash('password'))

@login_manager.user_loader
def load_user(user_id):
    return user if user_id == user.id else None

@app.route('/')
@login_required
def home():
    return Response("Hello, World!")

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username')
        password = request.form.get('password')

        if username == user.id and check_password_hash(user.password, password):
            login_user(user)
            return redirect(url_for('home'))

    return render_template('login.html')

@app.route('/logout')
def logout():
    logout_user()
    return redirect(url_for('login'))

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
