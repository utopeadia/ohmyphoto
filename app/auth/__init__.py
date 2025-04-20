from flask import Blueprint

bp = Blueprint('auth', __name__)

# Import routes, forms, models after creating the blueprint
from . import routes
