from flask import Flask
from flask_bootstrap import Bootstrap
from flask_mail import Mail
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_migrate import Migrate


from config import config_dict

# Initialize extensions (without app context yet)
bootstrap = Bootstrap()
mail = Mail()
moment = Moment()
db = SQLAlchemy()
login_manager = LoginManager()
login_manager.login_view = "main.login"
migrate = Migrate()  



def create_app(config_name):
    app = Flask(__name__)

    # Load config
    app.config.from_object(config_dict[config_name])
    config_dict[config_name].init_app(app)

    # Initialize extensions
    bootstrap.init_app(app)
    mail.init_app(app)
    moment.init_app(app)
    db.init_app(app)
    migrate.init_app(app, db) 
    login_manager.init_app(app)

    # Register blueprints
    from .main import main as main_blueprint
    app.register_blueprint(main_blueprint)

    return app



# User loader callback
from app.models import User


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))
