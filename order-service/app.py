from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return 'Welcome to the Home Page!'

@app.route('/about')
def about():
    return 'This is the About Page!'

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5004, debug=True)