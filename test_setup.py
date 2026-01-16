"""Quick test to verify the application initializes correctly."""
from app import app

print("="*60)
print("APPLICATION INITIALIZATION TEST")
print("="*60)
print(f"Environment: {app.config.get('FLASK_ENV')}")
print(f"Debug Mode: {app.config.get('DEBUG')}")
print(f"CSRF Protection: {app.config.get('WTF_CSRF_ENABLED')}")
print(f"Rate Limiting: {app.config.get('RATELIMIT_ENABLED')}")
print(f"API Key Configured: {'Yes' if app.config.get('GEMINI_API_KEY') else 'No'}")
print(f"Database: {app.config.get('SQLALCHEMY_DATABASE_URI')[:30]}...")
print("="*60)
print("[SUCCESS] Application initialized successfully!")
print("="*60)
print("\nYou can now run: python app.py")
