from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response
from flask_login import login_required, current_user
from models import db, User, Patient, Doctor, Appointment, Department, Availability
from datetime import datetime, timedelta

patient_bp = Blueprint('patient', __name__, url_prefix='/patient')


@patient_bp.route('/dashboard')
@login_required
def patient_dashboard():
    if current_user.role != 'patient':
        return "Access denied", 403
    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        patient = Patient(user_id=current_user.id)
        db.session.add(patient)
        db.session.commit()
    departments = Department.query.all()
    doctors = Doctor.query.join(User).filter(User.active == True).all()
    appointments = Appointment.query.filter_by(patient_id=patient.id).all()

    return render_template(
        'dashboard_patient.html',
        patient=patient,
        doctors=doctors,
        departments=departments,
        appointments=appointments
    )


@patient_bp.route('/edit_profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    if current_user.role != 'patient':
        return "Access denied", 403

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        patient = Patient(user_id=current_user.id)
        db.session.add(patient)
        db.session.commit()

    if request.method == 'POST':
        current_user.name = request.form['name']
        current_user.email = request.form['email']
        patient.age = request.form['age']
        patient.gender = request.form['gender']
        patient.phone = request.form['phone']
        patient.address = request.form['address']

        db.session.commit()
        flash("Profile updated successfully!", "success")
        return redirect(url_for('patient.patient_dashboard'))

    return render_template('edit_patient_profile.html', patient=patient)


@patient_bp.route('/department/<int:dept_id>')
@login_required
def department_details(dept_id):
    if current_user.role != 'patient':
        return "Access denied", 403

    department = Department.query.get_or_404(dept_id)
    doctors = Doctor.query.filter_by(department_id=dept_id).all()

    return render_template(
        'department_details.html',
        department=department,
        doctors=doctors
    )


@patient_bp.route('/doctor/<int:doctor_id>')
@login_required
def doctor_details(doctor_id):
    if current_user.role != 'patient':
        return "Access denied", 403

    doctor = Doctor.query.get_or_404(doctor_id)
    department = Department.query.get(doctor.department_id)

    return render_template(
        'doctor_details.html',
        doctor=doctor,
        department=department
    )


@patient_bp.route('/doctor/<int:doctor_id>/availability', methods=['GET', 'POST'])
@login_required
def doctor_availability_for_patient(doctor_id):
    if current_user.role != 'patient':
        return "Access denied", 403
    if request.method == 'POST':
        doctor_id = request.form.get('doctor_id', doctor_id)

    doctor = Doctor.query.get(doctor_id)
    if not doctor:
        flash('Doctor not found.', 'error')
        return redirect(url_for('patient.patient_dashboard'))

    availabilities = Availability.query.filter_by(doctor_id=doctor.id).all()

    today = datetime.now().date()
    next_7 = [(today + timedelta(days=i)) for i in range(7)]
    
    SLOTS = [
        { 'key': 'morning', 'label': '08:00 - 12:00', 'end_hour': 12, 'end_min': 0 },
        { 'key': 'evening', 'label': '16:00 - 21:00', 'end_hour': 21, 'end_min': 0 }
    ]

    avail_map = {}
    for a in availabilities:
        try:
            ad = datetime.strptime(a.date, '%Y-%m-%d').date()
        except Exception:
            continue
        avail_map.setdefault(ad.isoformat(), {})[a.time_slot] = a

    now_dt = datetime.now()
    disabled_map = {}
    for d in next_7:
        ds = d.isoformat()
        disabled_map[ds] = {}
        for slot in SLOTS:
            try:
                end_dt = datetime.combine(d, datetime.min.time()).replace(hour=slot['end_hour'], minute=slot['end_min'])
            except Exception:
                disabled_map[ds][slot['label']] = False
                continue
            disabled_map[ds][slot['label']] = (end_dt <= now_dt)

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        patient = Patient(user_id=current_user.id)
        db.session.add(patient)
        db.session.commit()

    if request.method == 'POST':
        avail_id = request.form.get('avail_id')
        if not avail_id:
            flash('No slot selected.', 'error')
            return redirect(url_for('patient.doctor_availability_for_patient', doctor_id=doctor.id))

        slot = Availability.query.get(avail_id)
        if not slot or slot.status != 'Available':
            flash('Slot is no longer available.', 'error')
            return redirect(url_for('patient.doctor_availability_for_patient', doctor_id=doctor.id))

        new_appointment = Appointment(
            patient_id=patient.id,
            doctor_id=doctor.id,
            date=slot.date,
            time=slot.time_slot,
            status='Booked'
        )
        db.session.add(new_appointment)
        slot.status = 'Booked'
        db.session.commit()

        flash('Appointment booked successfully!', 'success')
        return redirect(url_for('patient.patient_dashboard'))

    return render_template(
        'doctor_availability_for_patient.html',
        doctor=doctor,
        availabilities=availabilities,
        next_7=next_7,
        slots=SLOTS,
        avail_map=avail_map,
        disabled_map=disabled_map
    )


@patient_bp.route('/appointments')
@login_required
def patient_appointments():
    if current_user.role != 'patient':
        return "Access denied", 403

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile missing.', 'error')
        return redirect(url_for('patient.patient_dashboard'))

    appointments = Appointment.query.filter_by(patient_id=patient.id).all()

    return render_template('patient_appointments.html', patient=patient, appointments=appointments)


@patient_bp.route('/cancel_appointment/<int:appt_id>')
@login_required
def cancel_appointment(appt_id):
    if current_user.role != 'patient':
        return "Access denied", 403

    appointment = Appointment.query.get_or_404(appt_id)

    patient = Patient.query.filter_by(user_id=current_user.id).first()
    if not patient:
        flash('Patient profile missing.', 'error')
        return redirect(url_for('patient.patient_dashboard'))

    if appointment.patient_id != patient.id:
        return "Unauthorized", 403

    availability = Availability.query.filter_by(
        doctor_id=appointment.doctor_id,
        date=appointment.date,
        time_slot=appointment.time
    ).first()
    if availability:
        availability.status = 'Available'

    appointment.status = "Cancelled"
    db.session.commit()

    flash("Appointment cancelled.", "info")
    return redirect(url_for('patient.patient_dashboard'))
