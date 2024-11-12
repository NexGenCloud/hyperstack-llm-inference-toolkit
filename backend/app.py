import os

from flask import Flask
from flask_migrate import Migrate

from utils.db import db
from utils.rate_limits import RateLimitExceeded, rate_limit_error_handler


def create_app(app_name=__name__):
    # Initialize and configure the Flask app
    app = Flask(app_name)
    app.config.from_object(os.getenv('APP_SETTINGS', 'config.LocalConfig'))
    db.init_app(app)

    # Initialize database and migration modules into the app
    Migrate(app, db)

    # Register v1 API blueprints into the app
    from blueprints.v1.apis import v1_bp

    app.register_blueprint(v1_bp, url_prefix='/api/v1')

    return app


app = create_app()


@app.errorhandler(RateLimitExceeded)
def handle_rate_limit_exceeded(error):
    return rate_limit_error_handler(error)


@app.teardown_appcontext
def shutdown_session(exception=None):
    """
    Remove the database session after each request.
    """
    db.session.remove()
