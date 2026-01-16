"""
Script to add CSRF tokens to all forms in templates.
This ensures all POST forms are protected against CSRF attacks.
"""
import os
import re
from pathlib import Path

# Template directory
TEMPLATE_DIR = Path(__file__).parent / 'templates'

# Forms that already have CSRF tokens
ALREADY_UPDATED = ['login.html', 'register.html']

# Files to update
FILES_TO_UPDATE = [
    'admin.html',
    'add_patient.html',
    'update_patient.html',
    'skin.html',
    'search_patients.html',
    'profile.html',
    'match_form.html',
    'find_form.html',
    'index.html'
]

def add_csrf_token(filepath):
    """Add CSRF token after form opening tag."""
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Pattern to match form tags without csrf_token
    # Matches: <form ...> followed by newline/whitespace, but NOT followed by {{ csrf_token() }}
    pattern = r'(<form[^>]*>)(\s*)(?!.*{{\s*csrf_token\(\)\s*}})'
    
    def replacement(match):
        form_tag = match.group(1)
        whitespace = match.group(2)
        # Determine indentation from the next line
        indent = '                        '  # Default indent
        return f'{form_tag}\n{indent}{{{{ csrf_token() }}}}{whitespace}'
    
    # Replace all form tags
    updated_content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    if updated_content != content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(updated_content)
        return True
    return False

def main():
    """Add CSRF tokens to all forms."""
    print("="*60)
    print("ADDING CSRF TOKENS TO FORMS")
    print("="*60)
    
    updated_count = 0
    
    for filename in FILES_TO_UPDATE:
        filepath = TEMPLATE_DIR / filename
        if not filepath.exists():
            print(f"[SKIP] {filename} - File not found")
            continue
        
        if add_csrf_token(filepath):
            print(f"[UPDATED] {filename}")
            updated_count += 1
        else:
            print(f"[NO CHANGE] {filename}")
    
    print("="*60)
    print(f"Updated {updated_count} files")
    print("="*60)
    print("\nCSRF protection is now active on all forms!")
    print("You can now submit forms without 'Bad Request' errors.")

if __name__ == '__main__':
    main()
