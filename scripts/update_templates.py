import os

ROOT_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
TEMPLATES_DIR = os.path.join(ROOT_DIR, 'templates')

REPLACEMENTS = {
    "url_for('index'": "url_for('main.index'",
    "url_for('match'": "url_for('main.match'",
    "url_for('find'": "url_for('main.find'",
    "url_for('status'": "url_for('main.status'",
    "url_for('reload'": "url_for('main.reload'",
    "url_for('chat'": "url_for('main.chat'",
    "url_for('add_patient'": "url_for('patients.add_patient'",
    "url_for('view_patients'": "url_for('patients.view_patients'",
    "url_for('search_patients'": "url_for('patients.search_patients'",
    "url_for('update_patient'": "url_for('patients.update_patient'",
    "url_for('bulk_delete_patients'": "url_for('patients.bulk_delete_patients'",
    "url_for('export_patients_csv'": "url_for('patients.export_patients_csv'",
    "url_for('login'": "url_for('auth.login'",
    "url_for('logout'": "url_for('auth.logout'",
    "url_for('register'": "url_for('auth.register'",
    "url_for('profile'": "url_for('auth.profile'",
    "url_for('admin'": "url_for('admin.manage_users'",
    "url_for('delete_user'": "url_for('admin.delete_user'"
}

def update_templates():
    print(f"Scanning templates in {TEMPLATES_DIR}...")
    for filename in os.listdir(TEMPLATES_DIR):
        if filename.endswith('.html'):
            filepath = os.path.join(TEMPLATES_DIR, filename)
            with open(filepath, 'r', encoding='utf-8') as f:
                content = f.read()
            
            original_content = content
            for old, new in REPLACEMENTS.items():
                content = content.replace(old, new)
            
            # Special case for double quotes if any: url_for("index"
            for old, new in REPLACEMENTS.items():
                old_dq = old.replace("'", '"')
                new_dq = new.replace("'", '"')
                content = content.replace(old_dq, new_dq)

            if content != original_content:
                with open(filepath, 'w', encoding='utf-8') as f:
                    f.write(content)
                print(f"Updated {filename}")
            else:
                print(f"No changes in {filename}")

if __name__ == '__main__':
    update_templates()
