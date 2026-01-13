from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from werkzeug.security import generate_password_hash
from models import db, User, Doctor, Patient, Appointment, Department, Treatment
from datetime import date

admin_bp = Blueprint('admin', __name__, url_prefix='/admin')

DEPARTMENTS = [
    'Cardiology',
    'Neurology',
    'Orthopedics',
    'Pulmonology',
    'General Medicine',
    'Dermatology',
    'Pediatrics',
    'ENT (Ear, Nose, Throat)',
    'Gynecology',
    'Psychiatry'
]


@admin_bp.route('/dashboard')
@login_required
def admin_dashboard():
    if current_user.role != 'admin':
        return "Access denied", 403

    total_doctors = Doctor.query.count()
    total_patients = Patient.query.count()
    total_appointments = Appointment.query.filter(Appointment.status != "Cancelled").count()

    doctors = Doctor.query.all()
    patients = Patient.query.all()
    appointments = Appointment.query.filter(Appointment.status != "Cancelled").all()

    response = make_response(render_template(
        'dashboard_admin.html',
        user=current_user,
        total_doctors=total_doctors,
        total_patients=total_patients,
        total_appointments=total_appointments,
        doctors=doctors,
        patients=patients,
        appointments=appointments
    ))

    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response



@admin_bp.route('/edit_patient/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_patient(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    patient = Patient.query.get_or_404(id)
    user = patient.user

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.phone = request.form['phone']
        patient.address = request.form['address']

        db.session.commit()
        flash("Patient details updated.")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('edit_patient.html', patient=patient)

@admin_bp.route('/doctor/details/<int:doctor_id>')
@login_required
def view_doctor_details(doctor_id):
    if current_user.role != 'admin':
        return "Access denied", 403

    doctor = Doctor.query.get_or_404(doctor_id)

    department = None
    if doctor.department_id:
        from models import Department
        department = Department.query.get(doctor.department_id)

    return render_template(
        'doctor_details.html',
        doctor=doctor,
        department=department
    )


@admin_bp.route('/edit_doctor/<int:id>', methods=['GET', 'POST'])
@login_required
def edit_doctor(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    doctor = Doctor.query.get_or_404(id)
    user = doctor.user

    if request.method == 'POST':
        user.name = request.form['name']
        user.email = request.form['email']
        dept_choice = request.form.get('department')
        custom_dept = request.form.get('custom_department', '').strip()
        
        if dept_choice == 'other' and custom_dept:
            specialization = custom_dept
        elif dept_choice and dept_choice != 'other':
            specialization = dept_choice
        else:
            flash("Please select or enter a department.")
            return redirect(url_for('admin.edit_doctor', id=id))
        
        doctor.specialization = specialization
        doctor.experience = request.form.get('experience')
        doctor.phone = request.form.get('phone')
        doctor.address = request.form.get('address')

        dept = Department.query.filter_by(name=specialization).first()
        if not dept:
            dept = Department(name=specialization, description='')
            db.session.add(dept)
            db.session.commit()

        doctor.department_id = dept.id

        db.session.commit()
        flash("Doctor details updated.")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('edit_doctor.html', doctor=doctor, departments=DEPARTMENTS)


@admin_bp.route('/add_doctor', methods=['GET', 'POST'])
@login_required
def add_doctor():
    if current_user.role != 'admin':
        return "Access denied", 403

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        dept_choice = request.form.get('department')
        custom_dept = request.form.get('custom_department', '').strip()
        
        if dept_choice == 'other' and custom_dept:
            specialization = custom_dept
        elif dept_choice and dept_choice != 'other':
            specialization = dept_choice
        else:
            flash("Please select or enter a department.")
            return redirect(url_for('admin.add_doctor'))
        
        experience = request.form.get('experience')
        phone = request.form.get('phone')
        address = request.form.get('address')

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for('admin.add_doctor'))

        user = User(name=name, email=email, password=generate_password_hash(password), role='doctor')
        db.session.add(user)
        db.session.commit()

        dept = Department.query.filter_by(name=specialization).first()
        if not dept:
            dept = Department(name=specialization, description='')
            db.session.add(dept)
            db.session.commit()

        doctor = Doctor(
            user_id=user.id,
            specialization=specialization,
            department_id=dept.id,
            experience=experience,
            phone=phone,
            address=address
        )
        db.session.add(doctor)
        db.session.commit()

        flash("Doctor added.")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('add_doctor.html', departments=DEPARTMENTS)


@admin_bp.route('/add_patient', methods=['GET', 'POST'])
@login_required
def add_patient():
    if current_user.role != 'admin':
        return "Access denied", 403

    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        age = request.form['age']
        gender = request.form['gender']
        phone = request.form['phone']
        address = request.form['address']

        if User.query.filter_by(email=email).first():
            flash("Email already exists.")
            return redirect(url_for('admin.add_patient'))

        user = User(name=name, email=email, password=generate_password_hash(password), role='patient')
        db.session.add(user)
        db.session.commit()

        patient = Patient(
            user_id=user.id,
            age=age,
            gender=gender,
            phone=phone,
            address=address
        )
        db.session.add(patient)
        db.session.commit()

        flash("Patient added.")
        return redirect(url_for('admin.admin_dashboard'))

    return render_template('add_patient.html')

@admin_bp.route('/patient/details/<int:patient_id>')
@login_required
def view_patient_details(patient_id):
    if current_user.role != 'admin':
        return "Access denied", 403

    patient = Patient.query.get_or_404(patient_id)
    user = patient.user  # linked User object

    return render_template(
        'patient_details.html',
        patient=patient,
        user=user
    )


@admin_bp.route('/delete_doctor/<int:id>')
@login_required
def delete_doctor(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    doctor = Doctor.query.get_or_404(id)
    user = doctor.user

    appointments = Appointment.query.filter_by(doctor_id=id).all()
    appt_ids = [a.id for a in appointments]

    if appt_ids:
        Treatment.query.filter(Treatment.appointment_id.in_(appt_ids)).delete(synchronize_session=False)

    Appointment.query.filter_by(doctor_id=id).delete(synchronize_session=False)

    db.session.delete(doctor)
    db.session.delete(user)

    db.session.commit()

    flash("Doctor deleted along with related appointments.", "success")
    return redirect(url_for('admin.admin_dashboard'))



@admin_bp.route('/blacklist_doctor/<int:id>')
@login_required
def blacklist_doctor(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    doctor = Doctor.query.get_or_404(id)
    doctor.user.active = False
    db.session.commit()

    flash("Doctor blacklisted.")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/reactivate_doctor/<int:id>')
@login_required
def reactivate_doctor(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    doctor = Doctor.query.get_or_404(id)
    doctor.user.active = True
    db.session.commit()

    flash("Doctor reactivated.")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/delete_patient/<int:id>')
@login_required
def delete_patient(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    patient = Patient.query.get_or_404(id)
    user = patient.user
    db.session.delete(patient)
    db.session.delete(user)
    db.session.commit()

    flash("Patient deleted.")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/blacklist_patient/<int:id>')
@login_required
def blacklist_patient(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    patient = Patient.query.get_or_404(id)
    patient.user.active = False
    db.session.commit()

    flash("Patient blacklisted.")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/reactivate_patient/<int:id>')
@login_required
def reactivate_patient(id):
    if current_user.role != 'admin':
        return "Access denied", 403

    patient = Patient.query.get_or_404(id)
    patient.user.active = True
    db.session.commit()

    flash("Patient reactivated.")
    return redirect(url_for('admin.admin_dashboard'))


@admin_bp.route('/patient_history/<int:patient_id>')
@login_required
def patient_history(patient_id):
    if current_user.role != 'admin':
        return "Access denied", 403

    patient = Patient.query.get_or_404(patient_id)
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()

    return render_template("patient_history.html", patient=patient, appointments=appointments)
