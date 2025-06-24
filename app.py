import os
import logging
from flask import Flask, render_template, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix
from flask_jwt_extended import JWTManager
from flask_socketio import SocketIO
from flask_mail import Mail
import redis

# Configure logging
logging.basicConfig(level=logging.DEBUG)

class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)

# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "nexus-dev-secret-key-2025")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# JWT Configuration
app.config['JWT_SECRET_KEY'] = os.environ.get("JWT_SECRET_KEY", "nexus-jwt-secret-2025")
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = False
jwt = JWTManager(app)

# WebSocket Configuration
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')

# Mail Configuration
app.config['MAIL_SERVER'] = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
app.config['MAIL_PORT'] = int(os.environ.get('MAIL_PORT', '587'))
app.config['MAIL_USE_TLS'] = os.environ.get('MAIL_USE_TLS', 'true').lower() in ['true', 'on', '1']
app.config['MAIL_USERNAME'] = os.environ.get('MAIL_USERNAME')
app.config['MAIL_PASSWORD'] = os.environ.get('MAIL_PASSWORD')
app.config['MAIL_DEFAULT_SENDER'] = os.environ.get('MAIL_DEFAULT_SENDER', 'noreply@nexus.local')
mail = Mail(app)

# Redis Configuration for notifications
try:
    redis_client = redis.Redis(host='localhost', port=6379, db=0, decode_responses=True)
    redis_client.ping()
except:
    redis_client = None

# Configure the database - Use PostgreSQL in production
database_url = os.environ.get("DATABASE_URL")
if database_url and database_url.startswith("postgres://"):
    database_url = database_url.replace("postgres://", "postgresql://", 1)
app.config["SQLALCHEMY_DATABASE_URI"] = database_url or "sqlite:///nexus.db"
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

# Import models and blueprints
from models import User, Project, Finding, Task, ActivityLog, UserProject
from auth import auth_bp
from admin import admin_bp
from secure import secure_bp
from flow import flow_bp
from client import client_bp
from reports import reports_bp
from activity import activity_bp
from analytics import analytics_bp
from enhanced_reports import enhanced_reports_bp
import notifications

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/auth')
app.register_blueprint(admin_bp, url_prefix='/admin')
app.register_blueprint(secure_bp, url_prefix='/secure')
app.register_blueprint(flow_bp, url_prefix='/flow')
app.register_blueprint(client_bp, url_prefix='/client')
app.register_blueprint(reports_bp, url_prefix='/reports')
app.register_blueprint(activity_bp, url_prefix='/activity')
app.register_blueprint(analytics_bp, url_prefix='/analytics')
app.register_blueprint(enhanced_reports_bp, url_prefix='/enhanced-reports')

# Register UI enhancements
from ui_enhancements import ui_bp
app.register_blueprint(ui_bp, url_prefix='/ui')

@app.route('/')
def index():
    """Route users based on their role after login"""
    if 'user_id' not in session:
        return redirect(url_for('auth.login'))
    
    user = User.query.get(session['user_id'])
    if not user:
        session.clear()
        return redirect(url_for('auth.login'))
    
    # Route based on user role
    if user.role in ['super_admin', 'admin']:
        return redirect(url_for('admin.dashboard'))
    elif user.role == 'pentester':
        return redirect(url_for('secure.dashboard'))
    elif user.role == 'developer':
        return redirect(url_for('flow.dashboard'))
    elif user.role == 'client':
        return redirect(url_for('client.dashboard'))
    else:
        return redirect(url_for('auth.login'))

@app.errorhandler(404)
def not_found(error):
    return render_template('error.html', error="Page not found"), 404

@app.errorhandler(403)
def forbidden(error):
    return render_template('error.html', error="Access denied"), 403

@app.errorhandler(500)
def internal_error(error):
    return render_template('error.html', error="Internal server error"), 500

# Create tables
with app.app_context():
    db.create_all()
    
    # Create default super admin if it doesn't exist
    from werkzeug.security import generate_password_hash
    super_admin = User.query.filter_by(role='super_admin').first()
    if not super_admin:
        default_admin = User(
            username='admin',
            email='admin@nexus.local',
            password_hash=generate_password_hash('admin123'),
            role='super_admin',
            first_name='System',
            last_name='Administrator'
        )
        db.session.add(default_admin)
        db.session.commit()
        logging.info("Default super admin created: admin@nexus.local / admin123")

# Make socketio available for main.py
__all__ = ['app', 'socketio']
