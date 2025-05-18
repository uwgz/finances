from flask import Blueprint

main = Blueprint("main", __name__)

# Import views and errors so they're registered with the blueprint
from . import views, errors
