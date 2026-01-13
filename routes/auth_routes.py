from flask import Blueprint, render_template, redirect, url_for, request, flash, session, make_response
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from models import db, User, Patient

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/')
def home():
    return render_template('login.html')

@auth_bp.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        name = request.form['name']
        email = request.form['email']
        password = request.form['password']
        confirm_password = request.form['confirm_password']

        if password != confirm_password:
            flash("Passwords do not match.", "error")
            return redirect(url_for('auth.register'))

        existing_user = User.query.filter_by(email=email).first()
        if existing_user:
            flash('User with this email already exists. Please log in.', 'warning')
            return redirect(url_for('auth.login'))

        hashed_pw = generate_password_hash(password)
        user = User(name=name, email=email, password=hashed_pw, role='patient')
        db.session.add(user)
        db.session.commit()

        patient = Patient(user_id=user.id)
        db.session.add(patient)
        db.session.commit()

        flash('Registration successful!', 'success')
        return redirect(url_for('auth.login'))

    return render_template('register.html')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if not user:
            flash("User doesn't exist. Please register first.")
        elif not check_password_hash(user.password, password):
            flash("Incorrect password.")
        elif not user.active:
            flash("Your account is deactivated.", "error")
            return redirect(url_for('auth.login'))
        else:
            login_user(user)

            if user.role == 'admin':
                return redirect(url_for('admin.admin_dashboard'))
            elif user.role == 'doctor':
                return redirect(url_for('doctor.doctor_dashboard'))
            else:
                return redirect(url_for('patient.patient_dashboard'))

    return render_template('login.html')

@auth_bp.route('/logout')
@login_required
def logout():
    logout_user()
    session.clear()
    flash('Logged out successfully.')

    response = make_response(redirect(url_for('auth.login')))
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response

