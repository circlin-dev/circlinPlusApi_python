from api import api
from config.database import DB_URL
from global_things.constants import APP_ROOT
from global_things.functions import slack_error_notification
from flask import Flask, render_template
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
import logging

app = Flask(__name__)
CORS(app)

#For nginx log
logging.basicConfig(filename=f'{APP_ROOT}/execution_log.log', filemode='a+', format=' [%(filename)s:%(lineno)s:%(funcName)s()]- %(asctime)s - %(levelname)s - %(message)s', level=logging.INFO)
gunicorn_logger = logging.getLogger('gunicorn.error')
app.logger.handlers = gunicorn_logger.handlers
app.logger.setLevel(gunicorn_logger.level)

#For Blueprint api activation.
app.register_blueprint(api, url_prefix="/api")

#app.config.from_pyfile('./config/database.py')
app.config["SQLALCHEMY_DATABASE_URI"] = DB_URL
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True #Automatic commit for database.

db = SQLAlchemy()

@app.route('/testing')
def hello_world():
    return 'Hello World!'

@app.route('/bodylab_form')
def bodylab_form():
    return render_template('bodylab_form.html')

if __name__ == '__main__':
    try:
        app.run(host='0.0.0.0', debug=True) #0.0.0.0 for production or 127.0.0.1 for local development
    except Exception as e:
        slack_error_notification(error_log=e)
