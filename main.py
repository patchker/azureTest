import flask

app = flask.Flask(__name__)

@app.route('/', methods=['GET'])
def home():
    return '<h1>Hello!</h1></p>'

# debug app:
# app.run()

if __name__ == "__main__":
    from waitress import serve
    serve(app, host="0.0.0.0", port=8080)