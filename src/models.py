from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
import uuid

db = SQLAlchemy()

def init_db(app):
    db.init_app(app)

class User(UserMixin, db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    username = db.Column(db.String(64), unique=True, index=True)
    password_hash = db.Column(db.String(128))
    role = db.Column(db.String(20), default='patient') # 'admin', 'staff', 'patient'
    
    # Relationships
    patient = db.relationship('Patient', backref='user_account', uselist=False, lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

class Patient(db.Model):
    id = db.Column(db.String(36), primary_key=True, default=lambda: str(uuid.uuid4()))
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.String(10)) # Keeping as string to match JSON, or int? JSON has "age": "25" usually.
    address = db.Column(db.String(200))
    image_path = db.Column(db.String(200))
    image_hash = db.Column(db.String(64))
    face_encoding = db.Column(db.PickleType)
    
    # Link to user account if they have one
    user_id = db.Column(db.String(36), db.ForeignKey('user.id'), nullable=True)

    # Relationships
    diseases = db.relationship('PatientDisease', backref='patient', lazy=True, cascade="all, delete-orphan")
    visits = db.relationship('Visit', backref='patient', lazy=True, cascade="all, delete-orphan")
    appointments = db.relationship('Appointment', backref='patient', lazy=True, cascade="all, delete-orphan")
    prescriptions = db.relationship('Prescription', backref='patient', lazy=True, cascade="all, delete-orphan")
    lab_tests = db.relationship('LabTest', backref='patient', lazy=True, cascade="all, delete-orphan")

class PatientDisease(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patient.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    added_date = db.Column(db.String(30), default=datetime.now().isoformat())

class Visit(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    notes = db.Column(db.Text)

class Appointment(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patient.id'), nullable=False)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    purpose = db.Column(db.String(200))

class Prescription(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patient.id'), nullable=False)
    medication = db.Column(db.String(100), nullable=False)
    dosage = db.Column(db.String(50))
    duration = db.Column(db.String(50))
    notes = db.Column(db.Text)

class LabTest(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.String(36), db.ForeignKey('patient.id'), nullable=False)
    name = db.Column(db.String(100), nullable=False)
    date = db.Column(db.String(20))
    notes = db.Column(db.Text)
