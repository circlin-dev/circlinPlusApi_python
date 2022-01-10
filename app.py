from flask import Flask, request, jsonify, current_app
from flask_cors import CORS
from api import api
from flask.json import JSONEncoder
from sqlalchemy import create_engine, text
from global_things.functions import slack_error_notification
import logging

app = Flask(__name__)
CORS(app)

APP_ROOT="/home/ubuntu/circlinMembersApi_python/circlinMembersApi_flask"
logging.basicConfig(filename=f'{APP_ROOT}/execution_log.log', filemode='a+', format=' [%(filename)s:%(lineno)s:%(funcName)s()]- %(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

app.config.from_pyfile('./config/database.py')
app.register_blueprint(api, url_prefix="/api")
try:
    db = create_engine(app.config['DB_URL'], encoding="utf-8", max_overflow=0)
    app.database = db
except Exception as e:
    # slack_error_notification(error_log=e)
    print(e)


@app.route('/testing')
def hello_world():
    return 'Hello World!'


if __name__ == '__main__':
    app.run(host='0.0.0.0', debug=True)
