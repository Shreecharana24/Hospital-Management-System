from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()

class User(UserMixin, db.Model): 
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password = db.Column(db.String(200), nullable=False)
    role = db.Column(db.String(20), nullable=False) 
    active = db.Column(db.Boolean, default=True)  
    
    doctor = db.relationship('Doctor', backref='user', uselist=False)
    patient = db.relationship('Patient', backref='user', uselist=False)

    def __repr__(self):
        return f"<User {self.name} - {self.role}>"

class Department(db.Model):
    __tablename__ = 'departments'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    doctors = db.relationship('Doctor', backref='department', lazy=True)

    def __repr__(self):
        return f"<Department {self.name}>"

class Doctor(db.Model):
    __tablename__ = 'doctors'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)

    specialization = db.Column(db.String(100), nullable=False)
    experience = db.Column(db.Integer)  
    phone = db.Column(db.String(20))    
    address = db.Column(db.String(200))

    availability = db.Column(db.String(100))
    department_id = db.Column(db.Integer, db.ForeignKey('departments.id'))

    appointments = db.relationship('Appointment', backref='doctor', lazy=True)

    def __repr__(self):
        return f"<Doctor {self.user.name} ({self.specialization})>"


class Patient(db.Model):
    __tablename__ = 'patients'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    age = db.Column(db.Integer)
    gender = db.Column(db.String(10))
    phone = db.Column(db.String(15))
    address = db.Column(db.String(200))

    appointments = db.relationship('Appointment', backref='patient', lazy=True)

    def __repr__(self):
        return f"<Patient {self.user.name}>"


class Appointment(db.Model):
    __tablename__ = 'appointments'

    id = db.Column(db.Integer, primary_key=True)
    patient_id = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.String(20))
    time = db.Column(db.String(20))
    status = db.Column(db.String(20), default='Booked')  

    treatment = db.relationship('Treatment', backref='appointment', uselist=False)

    def __repr__(self):
        return f"<Appointment {self.id} - {self.status}>"


class Treatment(db.Model):
    __tablename__ = 'treatments'

    id = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    visit_type = db.Column(db.String(100))
    tests_done = db.Column(db.Text)
    diagnosis = db.Column(db.Text)
    prescription = db.Column(db.Text)
    notes = db.Column(db.Text)
    followup_required = db.Column(db.String(5))

    def __repr__(self):
        return f"<Treatment for Appointment {self.appointment_id}>"
    
class Availability(db.Model):
    __tablename__ = 'availabilities'

    id = db.Column(db.Integer, primary_key=True)
    doctor_id = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    date = db.Column(db.String(20), nullable=False)
    time_slot = db.Column(db.String(20), nullable=False)
    status = db.Column(db.String(10), default='Available') 

    def __repr__(self):
        return f"<Availability {self.date} {self.time_slot} - {self.status}>"

