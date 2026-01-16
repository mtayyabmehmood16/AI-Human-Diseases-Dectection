"""
Setup script to create .env file for the Medical Management System.
Run this script to set up your environment configuration.
"""
import secrets
import os
from pathlib import Path

def create_env_file():
    """Create .env file with secure defaults."""
    env_path = Path(__file__).parent / '.env'
    
    if env_path.exists():
        response = input(".env file already exists. Overwrite? (y/N): ")
        if response.lower() != 'y':
            print("Setup cancelled.")
            return
    
    # Generate secure secret key
    secret_key = secrets.token_hex(32)
    
    # Get API key from user
    print("\n" + "="*60)
    print("MEDICAL MANAGEMENT SYSTEM - ENVIRONMENT SETUP")
    print("="*60)
    print("\nPlease provide the following information:\n")
    
    api_key = input("Enter your Google Gemini API Key: ").strip()
    if not api_key:
        print("⚠️  Warning: No API key provided. AI features will not work.")
        api_key = "your-gemini-api-key-here"
    
    # Create .env content
    env_content = f"""# Flask Configuration
FLASK_ENV=development
SECRET_KEY={secret_key}
DEBUG=True

# Database Configuration
DATABASE_URL=sqlite:///instance/app.db

# Google Gemini AI Configuration
GEMINI_API_KEY={api_key}

# File Upload Configuration
UPLOAD_FOLDER=static/uploads
MAX_CONTENT_LENGTH=16777216

# Security Configuration
SESSION_COOKIE_SECURE=False
SESSION_COOKIE_HTTPONLY=True
SESSION_COOKIE_SAMESITE=Lax
PERMANENT_SESSION_LIFETIME=3600

# Rate Limiting
RATELIMIT_ENABLED=True
RATELIMIT_STORAGE_URL=memory://

# Logging
LOG_LEVEL=INFO
LOG_FILE=logs/app.log
"""
    
    # Write .env file
    with open(env_path, 'w') as f:
        f.write(env_content)
    
    print("\n[SUCCESS] .env file created successfully!")
    print(f"Location: {env_path}")
    print(f"Secret Key: {secret_key[:20]}... (generated)")
    print(f"API Key: {'SET' if api_key != 'your-gemini-api-key-here' else 'NOT SET'}")
    print("\n" + "="*60)
    print("NEXT STEPS:")
    print("="*60)
    print("1. Review your .env file")
    print("2. Run: python app.py")
    print("3. Visit: http://localhost:5000")
    print("="*60 + "\n")

if __name__ == '__main__':
    try:
        create_env_file()
    except KeyboardInterrupt:
        print("\n\nSetup cancelled by user.")
    except Exception as e:
        print(f"\n[ERROR] {e}")
