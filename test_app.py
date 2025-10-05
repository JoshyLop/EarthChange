from flask import Flask
import os

app = Flask(__name__)

@app.route('/')
def hello():
    return '<h1>NASA Earth Change - Test</h1><p>La aplicación está funcionando correctamente!</p>'

@app.route('/health')
def health():
    return {'status': 'ok'}, 200

@app.route('/ping')
def ping():
    return 'OK'

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=False, host='0.0.0.0', port=port)