from flask import Blueprint

api = Blueprint('api', __name__)
from . import bodylab, user_question, purchase
