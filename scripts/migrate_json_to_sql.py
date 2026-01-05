import sys
import os
import json
import pathlib
from werkzeug.security import generate_password_hash

# Ensure project root is importable
project_root = pathlib.Path(__file__).resolve().parents[1]
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

from app import app, db, users
from src.models import User, Patient, PatientDisease, Visit, Appointment, Prescription, LabTest

def migrate():
    with app.app_context():
        # Create all tables
        db.create_all()

        print("Migrating Users...")
        # Migrate hardcoded users (like admin) from app.py
        for username, user_obj in users.items():
            if not User.query.filter_by(username=username).first():
                new_user = User(
                    id=user_obj.id,
                    username=user_obj.username,
                    password_hash=user_obj.password_hash,
                    role='admin' if username == 'admin' else 'staff'
                )
                db.session.add(new_user)
        
        print("Migrating Patients...")
        # Load patients from JSON
        patients_path = os.path.join(project_root, 'patients.json')
        if os.path.exists(patients_path):
            with open(patients_path, 'r') as f:
                patients_data = json.load(f)
            
            for p_data in patients_data:
                # Check if patient already exists to avoid duplicates on re-run
                if Patient.query.filter_by(id=p_data['id']).first():
                    continue

                # Create Patient
                patient = Patient(
                    id=p_data['id'],
                    name=p_data['name'],
                    age=p_data.get('age'),
                    address=p_data.get('address'),
                    image_path=p_data.get('image'),
                    image_hash=p_data.get('image_hash')
                )
                
                # Check if this patient has a user account (from previous register flow)
                if 'username' in p_data:
                    # Create User for patient
                    if not User.query.filter_by(username=p_data['username']).first():
                        user = User(
                            id=p_data['id'], # Reuse patient ID for user ID
                            username=p_data['username'],
                            password_hash=p_data.get('password_hash', ''),
                            role='patient'
                        )
                        db.session.add(user)
                        patient.user_id = user.id

                db.session.add(patient)
                db.session.flush() # flush to ensure patient ID is available for relationships

                # Diseases
                for d in p_data.get('diseases', []):
                    d_name = d['name'] if isinstance(d, dict) else d
                    d_date = d.get('added_date') if isinstance(d, dict) else None
                    db.session.add(PatientDisease(patient_id=patient.id, name=d_name, added_date=d_date))

                # Visits
                for v in p_data.get('visits', []):
                    db.session.add(Visit(patient_id=patient.id, date=v.get('date'), time=v.get('time'), notes=v.get('notes')))

                # Appointments
                for a in p_data.get('appointments', []):
                    db.session.add(Appointment(patient_id=patient.id, date=a.get('date'), time=a.get('time'), purpose=a.get('purpose')))
                
                # Prescriptions
                for pr in p_data.get('prescriptions', []):
                    db.session.add(Prescription(patient_id=patient.id, medication=pr.get('medication'), dosage=pr.get('dosage'), duration=pr.get('duration'), notes=pr.get('notes')))

                # Lab Tests
                for l in p_data.get('lab_tests', []):
                    db.session.add(LabTest(patient_id=patient.id, name=l.get('name'), date=l.get('date'), notes=l.get('notes')))

        db.session.commit()
        print("Migration complete!")

if __name__ == '__main__':
    migrate()
