from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from api import api
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
from global_things.functions import slack_error_notification

app = Flask(__name__)
CORS(app)
app.config.from_pyfile('./config/database.py')
app.register_blueprint(api, url_prefix="/api")
try:
    db = create_engine(app.config['DB_URL'], encoding="utf-8", max_overflow=0)
    app.database = db
except Exception as e:
    # slack_error_notification(error_log=e)
    print(e)


@app.route('/')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)