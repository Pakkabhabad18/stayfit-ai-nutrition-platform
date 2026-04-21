from flask import Flask
from flask_cors import CORS
from flask_jwt_extended import JWTManager
from flask_sqlalchemy import SQLAlchemy
from app.config import Config
import os

db = SQLAlchemy()
jwt = JWTManager()


def create_app(service_name='all'):
    app = Flask(__name__)
    app.config.from_object(Config)

    # Initialize extensions
    db.init_app(app)
    jwt.init_app(app)
    CORS(app, origins=["http://localhost:5173", "http://127.0.0.1:5173"], supports_credentials=True)

    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

    # Register blueprints based on microservice being started
    if service_name in ('all', 'auth'):
        from app.routes.auth import auth_bp
        app.register_blueprint(auth_bp, url_prefix='/api/auth')
        
    if service_name in ('all', 'meals'):
        from app.routes.meals import meals_bp
        from app.routes.recommendations import recommendations_bp
        app.register_blueprint(meals_bp, url_prefix='/api/meals')
        app.register_blueprint(recommendations_bp, url_prefix='/api/recommendations')
        
    if service_name in ('all', 'analytics'):
        from app.routes.analytics import analytics_bp
        app.register_blueprint(analytics_bp, url_prefix='/api/analytics')
        
    if service_name in ('all', 'notifications'):
        from app.routes.notifications import notifications_bp
        app.register_blueprint(notifications_bp, url_prefix='/api/notifications')

    # Create tables
    with app.app_context():
        db.create_all()

    return app
