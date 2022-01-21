from flask import Blueprint
from flask_cors import CORS
from . import bodylab, user_question, purchase, explore

api = Blueprint('api', __name__)
CORS(api)
