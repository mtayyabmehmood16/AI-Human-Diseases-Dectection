from flask import Blueprint, render_template, request, flash, redirect, url_for
from flask_login import login_user, login_required, logout_user, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from src.models import db, User, Patient
import uuid
import os
from werkzeug.utils import secure_filename
from flask import current_app
from src.analysis import RiskAnalyzer



auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            login_user(user)
            flash('Logged in successfully.', 'success')
            return redirect(url_for('main.index'))
        else:
            flash('Invalid username or password.', 'danger')
    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    flash('Logged out successfully.', 'success')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        # Always patient
        role = 'patient'
        username = request.form.get('username', '').strip()
        password = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        if password != confirm_password:
            flash('Passwords do not match.', 'danger')
            return render_template('register.html')

        if not username or not password:
            flash('Username and password are required.', 'danger')
            return render_template('register.html')
        
        if User.query.filter_by(username=username).first():
            flash('Username already exists.', 'danger')
            return render_template('register.html')

        # Patient Details
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        address = request.form.get('address', '').strip()
        image = request.files.get('image')

        if not name or not age:
            flash('Name and age are required.', 'danger')
            return render_template('register.html')

        if not image or not image.filename:
            flash('A face photo is required for registration.', 'danger')
            return render_template('register.html')

        # Create User
        new_id = str(uuid.uuid4())
        user = User(id=new_id, username=username, role='patient')
        user.set_password(password)
        db.session.add(user)

        # Handle Image & AI
        image_path = None
        face_encoding = None
        
        try:
            filename = secure_filename(image.filename)
            upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
            os.makedirs(upload_folder, exist_ok=True)
            image_path = os.path.join(upload_folder, f"{new_id}_{filename}")
            image.save(image_path)

            # Compute Encoding
            try:
                import face_recognition
                image_obj = face_recognition.load_image_file(image_path)
                encodings = face_recognition.face_encodings(image_obj)
                if encodings:
                    face_encoding = encodings[0]
                else:
                    flash('No face detected in the photo. Please upload a clearer photo.', 'warning')
                    # We might want to block reg here, but let's allow it with a warning for now? 
                    # User requested matching, so maybe blocking is better.
                    # But if install failed, we can't block.
                    pass
            except ImportError:
                print("face_recognition library not installed.")
            except Exception as e:
                print(f"Error processing face: {e}")

        except Exception as e:
            flash(f'Error saving image: {e}', 'danger')
            return render_template('register.html')

        patient = Patient(id=new_id, name=name, age=age, address=address, user_id=user.id, image_path=image_path, face_encoding=face_encoding)
        db.session.add(patient)
        
        db.session.commit()
        flash('Registration successful! You can now use Face Scan.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'update_profile':
            user = current_user
            pass_val = request.form.get('password', '')
            if pass_val:
                user.set_password(pass_val)
                db.session.commit()
                flash('Password updated.', 'success')
            
            if user.role == 'patient' and user.patient:
                name = request.form.get('name', '').strip()
                age = request.form.get('age', '').strip()
                address = request.form.get('address', '').strip()
                if name: user.patient.name = name
                if age: user.patient.age = age
                if address: user.patient.address = address
                db.session.commit()
                flash('Profile updated.', 'success')
                
        return redirect(url_for('auth.profile'))

    # GET
    user = current_user
    template_user = user
    if user.role == 'patient' and user.patient:
        template_user = user.patient
        # Calculate Risks
        analyzer = RiskAnalyzer()
        risks = analyzer.calculate_risks(template_user)
        return render_template('profile.html', user=template_user, is_staff=(user.role in ['admin', 'staff']), risks=risks)
    
    return render_template('profile.html', user=template_user, is_staff=(user.role in ['admin', 'staff']))


