from flask import Blueprint, render_template, redirect, url_for, request, flash, make_response, jsonify
from flask_login import login_required, current_user
from models import db, Doctor, Appointment, Treatment, Availability, Patient
from datetime import datetime, timedelta

doctor_bp = Blueprint('doctor', __name__, url_prefix='/doctor')


@doctor_bp.route('/dashboard')
@login_required
def doctor_dashboard():

    if current_user.role != 'doctor':
        return "Access denied", 403

    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile not found. Please contact an administrator.', 'error')
        return redirect(url_for('auth.login'))

    appointments = Appointment.query.filter_by(doctor_id=doctor.id).filter(Appointment.status != "Cancelled").all()

    total_patients = len({appt.patient_id for appt in appointments})
    total_appointments = len(appointments)
    completed = sum(1 for a in appointments if a.status == "Completed")

    response = make_response(render_template(
        'dashboard_doctor.html',
        doctor=doctor,
        appointments=appointments,
        total_patients=total_patients,
        total_appointments=total_appointments,
        completed=completed
    ))

    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'

    return response



@doctor_bp.route('/update_history', methods=['GET', 'POST'])
@doctor_bp.route('/update_history/<int:appt_id>', methods=['GET', 'POST'])
@login_required
def update_history(appt_id=None):
    if current_user.role != 'doctor':
        return "Access denied", 403

    appointment = None
    patient = None

    if appt_id:
        appointment = Appointment.query.get_or_404(appt_id)
        patient = appointment.patient
    else:
        patient_id = request.args.get('patient_id') or request.form.get('patient_id')
        if patient_id:
            patient = Patient.query.get_or_404(int(patient_id))

    if request.method == 'POST':
        visit_type = request.form.get('visit_type', '')
        tests_done = request.form.get('tests_done', '')
        diagnosis = request.form.get('diagnosis', '')
        prescription = request.form.get('prescription', '')
        medicines = request.form.get('medicines', '')
        notes = request.form.get('notes', '')

        combined_notes = notes.strip()
        if medicines:
            if combined_notes:
                combined_notes = combined_notes + "\n" + f"Medicines: {medicines}"
            else:
                combined_notes = f"Medicines: {medicines}"

        if appointment:
            if appointment.treatment:
                appointment.treatment.visit_type = visit_type
                appointment.treatment.tests_done = tests_done
                appointment.treatment.diagnosis = diagnosis
                appointment.treatment.prescription = prescription
                appointment.treatment.notes = combined_notes
            else:
                new_treatment = Treatment(
                    appointment_id=appointment.id,
                    visit_type=visit_type,
                    tests_done=tests_done,
                    diagnosis=diagnosis,
                    prescription=prescription,
                    notes=combined_notes,
                    followup_required='No'
                )
                db.session.add(new_treatment)

            appointment.status = "Completed"
            db.session.commit()
            flash('Patient history updated.', 'success')
            return redirect(url_for('doctor.doctor_dashboard'))
        else:
            if not patient:
                flash('Missing patient for new visit.', 'error')
                return redirect(url_for('doctor.doctor_dashboard'))

            now = datetime.now()
            date_str = now.strftime('%Y-%m-%d')
            time_str = now.strftime('%H:%M')

            doctor = Doctor.query.filter_by(user_id=current_user.id).first()
            if not doctor:
                flash('Doctor profile missing.', 'error')
                return redirect(url_for('auth.login'))

            new_appointment = Appointment(
                patient_id=patient.id,
                doctor_id=doctor.id,
                date=date_str,
                time=time_str,
                status='Completed'
            )
            db.session.add(new_appointment)
            db.session.commit()

            new_treatment = Treatment(
                appointment_id=new_appointment.id,
                diagnosis=diagnosis,
                prescription=prescription,
                notes=combined_notes,
                followup_required='No'
            )
            db.session.add(new_treatment)
            db.session.commit()

            flash('New visit added to history.', 'success')
            return redirect(url_for('doctor.doctor_dashboard'))

    return render_template('update_history.html', appointment=appointment, patient=patient)


@doctor_bp.route('/availability', methods=['GET', 'POST'])
@login_required
def doctor_availability():
    if current_user.role != 'doctor':
        return "Access denied", 403

    doctor = Doctor.query.filter_by(user_id=current_user.id).first()

    def parse_end_datetime(date_str, time_slot_str):
        """
        Parse common time slot formats and return a datetime for the end time.
        Supported examples: '10:00 AM - 12:00 PM', '10:00-12:00', '10:00 - 12:00'
        Returns a datetime or None if parsing fails.
        """
        if not time_slot_str:
            return None

        parts = time_slot_str.split('-')
        if len(parts) < 2:
            return None

        end_part = parts[-1].strip()

        fmts = ['%I:%M %p', '%H:%M', '%I %p', '%H%M']
        for fmt in fmts:
            try:
                t = datetime.strptime(end_part, fmt).time()
                dt = datetime.strptime(date_str, '%Y-%m-%d')
                return datetime.combine(dt.date(), t)
            except Exception:
                continue

        try:
            compact = end_part.replace(' ', '')
            t = datetime.strptime(compact, '%I:%M%p').time()
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return datetime.combine(dt.date(), t)
        except Exception:
            return None

    avail_list = Availability.query.filter_by(doctor_id=doctor.id).all()
    now = datetime.now()
    removed = False
    for a in list(avail_list):
        end_dt = parse_end_datetime(a.date, a.time_slot)
        if end_dt and end_dt <= now:
            db.session.delete(a)
            removed = True

    if removed:
        db.session.commit()

    if request.method == 'POST':
        date = request.form['date']
        time_slot = request.form['time_slot']
        status = request.form['status']

        end_dt = parse_end_datetime(date, time_slot)
        if end_dt is None:
            flash('Could not parse time slot. Use format like "10:00 AM - 12:00 PM" or "10:00-12:00".', 'error')
            return redirect(url_for('doctor.doctor_availability'))

        if end_dt <= now:
            flash('Cannot add availability that ends in the past.', 'error')
            return redirect(url_for('doctor.doctor_availability'))

        new_avail = Availability(doctor_id=doctor.id, date=date, time_slot=time_slot, status=status)
        db.session.add(new_avail)
        db.session.commit()

        flash('Availability added.', 'success')
        return redirect(url_for('doctor.doctor_availability'))

    availabilities = Availability.query.filter_by(doctor_id=doctor.id).all()

    now_dt = datetime.now()
    today = now_dt.date()
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

            disabled_map[ds][slot['label']] = (end_dt <= datetime.now())

    return render_template(
        'doctor_availability.html',
        doctor=doctor,
        availabilities=availabilities,
        next_7=next_7,
        slots=SLOTS,
        avail_map=avail_map,
        now=now_dt,
        disabled_map=disabled_map
    )


@doctor_bp.route('/toggle_availability/<int:avail_id>')
@login_required
def toggle_availability(avail_id):
    if current_user.role != 'doctor':
        return "Access denied", 403

    avail = Availability.query.get_or_404(avail_id)
    avail.status = 'Unavailable' if avail.status == 'Available' else 'Available'
    db.session.commit()

    flash('Availability updated.', 'success')
    return redirect(url_for('doctor.doctor_availability'))





@doctor_bp.route('/availability/toggle', methods=['POST'])
@login_required
def toggle_availability_post():
    if current_user.role != 'doctor':
        flash('Access denied', 'error')
        return redirect(url_for('doctor.doctor_availability'))

    date = request.form.get('date')
    time_slot = request.form.get('time_slot')
    if not date or not time_slot:
        flash('Missing parameters for toggle.', 'error')
        return redirect(url_for('doctor.doctor_availability'))

    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile missing.', 'error')
        return redirect(url_for('auth.login'))

    avail = Availability.query.filter_by(doctor_id=doctor.id, date=date, time_slot=time_slot).first()
    if avail:
        avail.status = 'Unavailable' if avail.status == 'Available' else 'Available'
        db.session.commit()
        flash('Availability updated.', 'success')
        return redirect(url_for('doctor.doctor_availability'))

    new_avail = Availability(doctor_id=doctor.id, date=date, time_slot=time_slot, status='Available')
    db.session.add(new_avail)
    db.session.commit()
    flash('Availability added.', 'success')
    return redirect(url_for('doctor.doctor_availability'))


@doctor_bp.route('/availability/save', methods=['POST'])
@login_required
def save_availability():
    if current_user.role != 'doctor':
        flash('Access denied', 'error')
        return redirect(url_for('auth.login'))

    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile missing.', 'error')
        return redirect(url_for('auth.login'))

    changes_made = 0
    for key, value in request.form.items():
        if key.startswith('change_'):
            change_key = key[7:]  
            try:
                date_str, slot_label = change_key.rsplit('|', 1)
            except:
                continue
            
            status = value 
            
            existing = Availability.query.filter_by(
                doctor_id=doctor.id,
                date=date_str,
                time_slot=slot_label
            ).first()
            
            if status == 'none':
                if existing:
                    db.session.delete(existing)
                    changes_made += 1
            else:
                if existing:
                    existing.status = status
                else:
                    new_avail = Availability(
                        doctor_id=doctor.id,
                        date=date_str,
                        time_slot=slot_label,
                        status=status
                    )
                    db.session.add(new_avail)
                changes_made += 1
    
    db.session.commit()
    
    if changes_made > 0:
        flash(f'Availability updated ({changes_made} slot(s) changed).', 'success')
    else:
        flash('No changes made.', 'info')
    
    return redirect(url_for('doctor.doctor_dashboard'))

@doctor_bp.route('/patient_history/<int:patient_id>')
@login_required
def patient_history(patient_id):
    if current_user.role != 'doctor':
        return "Access denied", 403

    patient = Patient.query.get_or_404(patient_id)
    doctor = Doctor.query.filter_by(user_id=current_user.id).first()
    if not doctor:
        flash('Doctor profile missing.', 'error')
        return redirect(url_for('auth.login'))

    appointments = Appointment.query.filter_by(patient_id=patient.id, doctor_id=doctor.id).all()

    return render_template(
        'patient_history.html',
        patient=patient,
        appointments=appointments
    )

