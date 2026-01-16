"""
Quick troubleshooting script for CSRF token issues.
"""
from flask import Flask, render_template_string
from flask_wtf.csrf import CSRFProtect

# Create test app
app = Flask(__name__)
app.config['SECRET_KEY'] = 'test-secret-key'
app.config['WTF_CSRF_ENABLED'] = True

# Initialize CSRF
csrf = CSRFProtect(app)

# Test template
test_template = """
<!DOCTYPE html>
<html>
<body>
    <h1>CSRF Token Test</h1>
    <form method="POST">
        {{ csrf_token() }}
        <input type="text" name="test" placeholder="Test input">
        <button type="submit">Submit</button>
    </form>
    
    <h2>Debug Info:</h2>
    <p>CSRF Enabled: {{ config.WTF_CSRF_ENABLED }}</p>
    <p>Secret Key Set: {{ config.SECRET_KEY[:10] }}...</p>
</body>
</html>
"""

@app.route('/', methods=['GET', 'POST'])
def test():
    return render_template_string(test_template)

if __name__ == '__main__':
    print("="*60)
    print("CSRF TOKEN TROUBLESHOOTING")
    print("="*60)
    print(f"CSRF Protection: {'ENABLED' if app.config['WTF_CSRF_ENABLED'] else 'DISABLED'}")
    print(f"Secret Key: {'SET' if app.config['SECRET_KEY'] else 'NOT SET'}")
    print("="*60)
    print("\nStarting test server on http://localhost:5001")
    print("Visit the page and check if CSRF token appears in the form")
    print("="*60)
    app.run(port=5001, debug=True)
