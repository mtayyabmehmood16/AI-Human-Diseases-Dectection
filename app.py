import sys
import pathlib
import os

# ensure project root is importable
project_root = pathlib.Path(__file__).resolve().parents[0]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from flask import Flask, redirect, url_for, render_template
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from src.models import db, init_db, User
from flask_migrate import Migrate
from flask_babel import Babel
from flask import request

def get_locale():
    # Check if language is in query string
    lang = request.args.get('lang')
    if lang in ['en', 'es']:
        return lang
    # Best match from browser
    return request.accept_languages.best_match(['en', 'es'])

from config import get_config
from src.logging_config import setup_logging, log_request

def create_app(config_name=None):
    """Application factory pattern."""
    app = Flask(__name__)
    
    # Load configuration
    config_class = get_config(config_name)
    app.config.from_object(config_class)
    config_class.init_app(app)
    
    # Initialize logging
    setup_logging(app)
    log_request(app)
    
    # Initialize extensions
    init_db(app)
    migrate = Migrate(app, db)
    babel = Babel(app, locale_selector=get_locale)
    
    # CSRF Protection
    csrf = CSRFProtect(app)
    
    # Rate Limiting
    limiter = Limiter(
        app=app,
        key_func=get_remote_address,
        default_limits=[app.config.get('RATELIMIT_DEFAULT', "200 per day")],
        storage_uri=app.config.get('RATELIMIT_STORAGE_URL'),
        enabled=app.config.get('RATELIMIT_ENABLED', True)
    )
    
    # Login Manager
    login_manager = LoginManager()
    login_manager.init_app(app)
    login_manager.login_view = 'auth.login'
    from flask_babel import _
    login_manager.login_message = _('Please log in to access this page.')
    login_manager.login_message_category = 'info'
    
    @login_manager.user_loader
    def load_user(user_id):
        return User.query.get(user_id)
    
    # Register Blueprints
    from src.blueprints.auth import auth_bp
    from src.blueprints.patients import patients_bp
    from src.blueprints.main import main_bp
    from src.blueprints.admin import admin_bp
    
    app.register_blueprint(auth_bp)
    app.register_blueprint(patients_bp)
    app.register_blueprint(main_bp)
    app.register_blueprint(admin_bp)
    
    # Error Handlers
    @app.errorhandler(404)
    def not_found_error(error):
        app.logger.warning(f"404 error: {error}")
        return render_template('errors/404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        app.logger.error(f"500 error: {error}")
        db.session.rollback()
        return render_template('errors/500.html'), 500
    
    @app.errorhandler(403)
    def forbidden_error(error):
        app.logger.warning(f"403 error: {error}")
        return render_template('errors/403.html'), 403
    
    @app.errorhandler(429)
    def ratelimit_error(error):
        app.logger.warning(f"Rate limit exceeded: {error}")
        return render_template('errors/429.html'), 429
    
    # Health check endpoint
    @app.route('/health')
    def health():
        return {'status': 'healthy', 'version': '1.0.0'}, 200
    
    app.logger.info("Application initialized successfully")
    
    return app

app = create_app()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=int(os.environ.get('PORT', 5000)), debug=app.config.get('DEBUG', True))

