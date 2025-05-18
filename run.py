from decouple import config
from app import create_app, db
from app.models import User, Role
from flask_migrate import Migrate

# Create app using factory pattern
app = create_app(config("FLASK_CONFIG", default="default"))

# Initialize Flask-Migrate
migrate = Migrate(app, db)


# Shell context for `flask shell`
@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role)


if __name__ == "__main__":
    app.run(debug=True)
