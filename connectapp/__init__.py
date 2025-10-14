import os
from flask import Flask
from config import Config
from .extensions import db, login_manager
from .models import User  # Import User model
from .routes.auth_routes import auth_bp
from .routes.dashboard_routes import dashboard_bp
from .routes.profile_routes import profile_bp

def create_app():
    # Get the absolute path to the project root
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

    app = Flask(
        __name__,
        template_folder=os.path.join(project_root, 'connectapp', 'templates'), # Explicitly set template folder path
        static_folder=os.path.join(project_root, 'static') # Explicitly set static folder path
    )
    app.config.from_object(Config)

    db.init_app(app)
    login_manager.init_app(app)

    # User loader for Flask-Login
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(int(user_id))

    with app.app_context():
        db.create_all()  # Create database tables

    app.register_blueprint(auth_bp, url_prefix='/')
    app.register_blueprint(dashboard_bp, url_prefix='/')
    app.register_blueprint(profile_bp, url_prefix='/')

    return app
