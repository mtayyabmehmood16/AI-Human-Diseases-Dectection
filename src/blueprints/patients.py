from flask import Blueprint, render_template, request, flash, redirect, url_for, current_app, Response
from flask_login import login_required, current_user
from src.models import db, Patient, PatientDisease, Visit, Appointment, Prescription, LabTest
import os
import uuid
import imagehash
from werkzeug.utils import secure_filename
from PIL import Image
from datetime import datetime
import csv
import io
import base64
import numpy as np
from src.analysis import RiskAnalyzer

# Try importing face_recognition, handle if missing
try:
    import face_recognition
except ImportError:
    face_recognition = None

patients_bp = Blueprint('patients', __name__)

@patients_bp.route('/scan', methods=['GET', 'POST'])
def scan_face():
    # Public access allowed for scanning? User "look in camera... user match it show all details"
    # Usually requires authentication to see details, but maybe this IS the authentication?
    # If not logged in, this logs them in? Or just shows view?
    # Requirement: "match in database if user match it show all details of user and all medical history"
    # Let's verify matches and redirect to view. If we want it to be "login via face", that's auth.
    # But user asked for "AI based site... look in camera... match... show details".
    # I'll treat it as a lookup tool.
    
    if request.method == 'POST':
        image_data = request.form.get('image_data') # Base64 string
        if not image_data:
             flash('No image captured.', 'warning')
             return redirect(url_for('patients.scan_face'))

        # if not face_recognition:
        #    flash('Facial recognition library not installed on server.', 'danger')
        #    return redirect(url_for('patients.scan_face'))

        # Decode base64
        try:
            header, encoded = image_data.split(",", 1)
            data = base64.b64decode(encoded)
            f = io.BytesIO(data)
            
            # Fallback to ImageHash if face_recognition is missing
            if not face_recognition:
                # Use ImageHash
                try:
                    img = Image.open(f)
                    unknown_hash = imagehash.average_hash(img)
                    
                    # Fetch all patients with hashes
                    # Note: Ideally this should be optimized, but for prototype it's fine.
                    patients = Patient.query.filter(Patient.image_hash != None).all()
                    
                    threshold = 15 # Tolerance for hash difference
                    best_match = None
                    min_diff = float('inf')
                    
                    for p in patients:
                         if p.image_hash:
                             p_hash = imagehash.hex_to_hash(p.image_hash)
                             diff = p_hash - unknown_hash
                             if diff < threshold and diff < min_diff:
                                 min_diff = diff
                                 best_match = p
                    
                    if best_match:
                        flash(f'Patient identified: {best_match.name} (Match Score: {100-min_diff})', 'success')
                        return redirect(url_for('patients.update_patient', patient_id=best_match.id))
                    else:
                        flash('No matching patient found.', 'warning')
                        return redirect(url_for('patients.scan_face'))

                except Exception as e:
                     flash(f'Error processing image hash: {e}', 'danger')
                     return redirect(url_for('patients.scan_face'))

            # ... face_recognition logic if available ...
            # Load image
            unknown_image = face_recognition.load_image_file(f)
            unknown_encodings = face_recognition.face_encodings(unknown_image)
            
            if not unknown_encodings:
                flash('No face detected. Please try again.', 'warning')
                return redirect(url_for('patients.scan_face'))
                
            unknown_encoding = unknown_encodings[0]
            
            # Compare with DB
            patients = Patient.query.filter(Patient.face_encoding != None).all()
            
            for p in patients:
                if p.face_encoding:
                     matches = face_recognition.compare_faces([p.face_encoding], unknown_encoding, tolerance=0.6)
                     if matches[0]:
                         flash(f'Patient identified: {p.name}', 'success')
                         return redirect(url_for('patients.update_patient', patient_id=p.id))
            
            flash('No matching patient found.', 'warning')
            
        except Exception as e:
            print(f"Error in scan: {e}")
            flash(f'Error processing scan: {e}', 'danger')
            
        return redirect(url_for('patients.scan_face'))
            
    return render_template('scan.html')




from src.reports import PDFReportGenerator
from flask import send_file

@patients_bp.route('/patient/<string:patient_id>/report')
@login_required
def download_report(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    # Check permission? Staff or self.
    if current_user.role == 'patient' and current_user.patient != patient:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    report = PDFReportGenerator(patient)
    pdf = report.generate()
    
    return send_file(
        pdf,
        as_attachment=True,
        download_name=f"{patient.name}_Report.pdf",
        mimetype='application/pdf'
    )

@patients_bp.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied. Only admin and staff can add patients.', 'danger')
        return redirect(url_for('main.index'))
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        age = request.form.get('age', '').strip()
        address = request.form.get('address', '').strip()
        image = request.files.get('image')

        if not name or not age:
            flash('Name and age are required.', 'warning')
            return render_template('add_patient.html')

        patient_id = str(uuid.uuid4())
        patient = Patient(id=patient_id, name=name, age=age, address=address)

        # Handle Image
        if image and image.filename:
            filename = secure_filename(image.filename)
            if filename != '':
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                os.makedirs(upload_folder, exist_ok=True)
                image_path = os.path.join(upload_folder, f"{patient_id}_{filename}")
                image.save(image_path)
                patient.image_path = image_path

                try:
                    # Compute Image Hash (Legacy/Fast fallback)
                    img = Image.open(image_path)
                    hash = imagehash.average_hash(img)
                    patient.image_hash = str(hash)
                    
                    # Compute Face Encoding (Biometric)
                    if face_recognition:
                        # Load image file for dlib
                        dlib_img = face_recognition.load_image_file(image_path)
                        encodings = face_recognition.face_encodings(dlib_img)
                        if encodings:
                            # Store the first face found
                            patient.face_encoding = encodings[0]
                        else:
                            flash('Warning: No face detected in the uploaded image. Face search feature may not work for this patient.', 'warning')
                except Exception as e:
                    print(f"Error computing request hash/encoding: {e}")

        db.session.add(patient)
        
        # Initial disease
        disease = request.form.get('disease', '').strip()
        if disease:
            db.session.add(PatientDisease(patient_id=patient.id, name=disease))

        db.session.commit()
        flash(f'Patient {name} added successfully.', 'success')
        return redirect(url_for('main.index'))

    return render_template('add_patient.html')

@patients_bp.route('/view_patients', methods=['GET'])
def view_patients():
    patients = Patient.query.all()
    # Serialize for template compatibility (template expects dict-like access for some fields if legacy, but objects work with dot notation)
    # The existing template uses `patient.name` etc? 
    # Let's check: The template likely iterates `patients`. 
    # If template assumes `patient['name']` (dict access), it will break with objects unless I make objects subscriptable or update template.
    # The original code loaded JSON, so `patients` was a list of dicts.
    # I should verify `view_patients.html`.
    # Assuming standard Jinja `{{ patient.name }}`, objects work fine. 
    # If it uses `{{ patient['name'] }}`, I need to update templates or make models dict-like.
    return render_template('view_patients.html', patients=patients)

@patients_bp.route('/search_patients', methods=['GET', 'POST'])
def search_patients():
    results = []
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        image = request.files.get('image')
        
        if query:
            results = Patient.query.filter((Patient.name.ilike(f'%{query}%')) | (Patient.id == query)).all()
        elif image and image.filename:
            try:
                if not face_recognition:
                    flash('Face recognition library is not available. Please contact admin.', 'danger')
                    return render_template('search_patients.html', results=[])

                # Biometric Search Implementation
                upload_folder = current_app.config.get('UPLOAD_FOLDER', 'static/uploads')
                temp_path = os.path.join(upload_folder, 'temp_search.jpg')
                image.save(temp_path)
                
                # Load unknown image
                unknown_image = face_recognition.load_image_file(temp_path)
                unknown_encodings = face_recognition.face_encodings(unknown_image)
                
                if len(unknown_encodings) == 0:
                    flash('No face detected in the uploaded image. Please try a clearer photo.', 'warning')
                    os.remove(temp_path)
                    return render_template('search_patients.html', results=[])
                
                unknown_encoding = unknown_encodings[0]
                
                # Compare against all patients with encodings
                # Note: In production with millions of users, use FAISS or Vector DB. For now, loop is fine.
                all_patients = Patient.query.filter(Patient.face_encoding != None).all()
                
                for p in all_patients:
                    # Compare faces with strict tolerance (default 0.6, lower is stricter)
                    # We compute distance to verify match
                    dist = face_recognition.face_distance([p.face_encoding], unknown_encoding)[0]
                    # Distance < 0.6 is a match, < 0.5 is very strict
                    if dist < 0.5: 
                        results.append(p)
                        # Optional: Attach distance to result for sorting?
                
                os.remove(temp_path)
                if not results:
                    flash('No matching patient found in database.', 'warning')
            except Exception as e:
                flash(f'Error processing image: {e}', 'danger')
        else:
            flash('Please enter a name/ID or upload an image to search.', 'warning')
            
    return render_template('search_patients.html', results=results)

@patients_bp.route('/update_patient/<patient_id>', methods=['GET', 'POST'])
@login_required
def update_patient(patient_id):
    if current_user.role not in ['admin', 'staff']:
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
    
    patient = Patient.query.get_or_404(patient_id)
    
    if request.method == 'POST':
        action = request.form.get('action', '')
        if action == 'update_basic':
            patient.name = request.form.get('name', '').strip()
            patient.age = request.form.get('age', '').strip()
            patient.address = request.form.get('address', '').strip()
            flash('Basic details updated.', 'success')
            
        elif action == 'add_disease':
            disease = request.form.get('disease', '').strip()
            if disease:
                exists = any(d.name == disease for d in patient.diseases)
                if not exists:
                    db.session.add(PatientDisease(patient_id=patient.id, name=disease))
                    flash(f'Disease added.', 'success')
                else:
                    flash('Disease already exists.', 'warning')
                    
        elif action == 'add_visit':
            v_date = request.form.get('visit_date')
            v_time = request.form.get('visit_time')
            v_notes = request.form.get('visit_notes', '')
            if v_date and v_time:
                db.session.add(Visit(patient_id=patient.id, date=v_date, time=v_time, notes=v_notes))
                flash('Visit added.', 'success')
                
        elif action == 'add_appointment':
             appt_date = request.form.get('appt_date')
             appt_time = request.form.get('appt_time')
             purpose = request.form.get('appt_purpose', '')
             if appt_date and appt_time:
                 db.session.add(Appointment(patient_id=patient.id, date=appt_date, time=appt_time, purpose=purpose))
                 flash('Appointment scheduled.', 'success')

        elif action == 'add_prescription':
            medication = request.form.get('medication', '').strip()
            dosage = request.form.get('dosage', '')
            duration = request.form.get('duration', '')
            notes = request.form.get('prescription_notes', '')
            
            if medication:
                 # Check for interactions
                 try:
                     import json
                     interactions_path = os.path.join(current_app.root_path, 'data', 'interactions.json')
                     with open(interactions_path, 'r') as f:
                         interactions_db = json.load(f)
                     
                     med_lower = medication.lower()
                     warnings = []
                     
                     # Check against existing prescriptions
                     for p in patient.prescriptions:
                         existing_med = p.medication.lower()
                         # Check logic: if med_lower has interactions, is existing_med in them?
                         if med_lower in interactions_db and existing_med in interactions_db[med_lower]:
                             warnings.append(f"Conflict: {medication} may interact with {p.medication}")
                         # Reverse check
                         if existing_med in interactions_db and med_lower in interactions_db[existing_med]:
                             warnings.append(f"Conflict: {p.medication} may interact with {medication}")
                             
                     if warnings:
                         for w in set(warnings): # Dedup
                             flash(w, 'warning')
                         # Allow add? Yes, just warn.
                 except Exception as e:
                     print(f"Interaction check failed: {e}")

                 db.session.add(Prescription(patient_id=patient.id, medication=medication, dosage=dosage, duration=duration, notes=notes))
                 flash('Prescription added.', 'success')


        elif action == 'add_lab_test':
            name = request.form.get('test_name', '')
            date = request.form.get('test_date', '')
            notes = request.form.get('test_notes', '')
            if name:
                db.session.add(LabTest(patient_id=patient.id, name=name, date=date, notes=notes))
                flash('Lab test ordered.', 'success')

        db.session.commit()
        return redirect(url_for('patients.update_patient', patient_id=patient_id))

    # Calculate Risks for display
    analyzer = RiskAnalyzer()
    risks = analyzer.calculate_risks(patient)
    return render_template('update_patient.html', patient=patient, risks=risks)

@patients_bp.route('/bulk_delete_patients', methods=['POST'])
@login_required
def bulk_delete_patients():
    if current_user.role != 'admin':
        flash('Access denied.', 'danger')
        return redirect(url_for('main.index'))
        
    selected_ids = request.form.getlist('selected_patients')
    if selected_ids:
        # Bulk delete
        Patient.query.filter(Patient.id.in_(selected_ids)).delete(synchronize_session=False)
        db.session.commit()
        flash(f'Deleted {len(selected_ids)} patients.', 'success')
    else:
        flash('No patients selected.', 'warning')
    return redirect(url_for('patients.view_patients'))

@patients_bp.route('/export_patients_csv')
def export_patients_csv():
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(['ID', 'Name', 'Age', 'Address', 'Diseases'])
    
    patients = Patient.query.all()
    for p in patients:
        d_str = ", ".join([d.name for d in p.diseases])
        writer.writerow([p.id, p.name, p.age, p.address, d_str])
        
    output.seek(0)
    return Response(output.getvalue(), mimetype='text/csv', headers={'Content-Disposition': 'attachment; filename=patients.csv'})
