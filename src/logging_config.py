"""
Logging configuration for the Medical Management System.
Provides structured logging with file rotation and different levels per environment.
"""
import logging
import logging.handlers
import os
from pathlib import Path


def setup_logging(app):
    """
    Configure logging for the application.
    
    Args:
        app: Flask application instance
    """
    log_level = getattr(logging, app.config.get('LOG_LEVEL', 'INFO'))
    log_file = app.config.get('LOG_FILE')
    
    # Create logs directory if it doesn't exist
    if log_file:
        log_dir = Path(log_file).parent
        os.makedirs(log_dir, exist_ok=True)
    
    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(log_level)
    
    # Remove existing handlers
    root_logger.handlers = []
    
    # Console handler (for development)
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_formatter = logging.Formatter(
        '[%(asctime)s] %(levelname)s in %(module)s: %(message)s'
    )
    console_handler.setFormatter(console_formatter)
    root_logger.addHandler(console_handler)
    
    # File handler with rotation (for all environments)
    if log_file:
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5
        )
        file_handler.setLevel(log_level)
        file_formatter = logging.Formatter(
            '[%(asctime)s] %(levelname)s [%(name)s.%(funcName)s:%(lineno)d] %(message)s'
        )
        file_handler.setFormatter(file_formatter)
        root_logger.addHandler(file_handler)
    
    # Set Flask app logger
    app.logger.setLevel(log_level)
    
    # Log startup message
    app.logger.info(f"Application starting in {app.config.get('ENV', 'unknown')} mode")
    app.logger.info(f"Log level: {logging.getLevelName(log_level)}")


def log_request(app):
    """Add request logging middleware."""
    
    @app.before_request
    def before_request():
        from flask import request
        app.logger.debug(f"Request: {request.method} {request.path}")
    
    @app.after_request
    def after_request(response):
        from flask import request
        app.logger.debug(f"Response: {request.method} {request.path} - {response.status_code}")
        return response
