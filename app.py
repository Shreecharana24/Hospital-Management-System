from flask import Flask
from flask_login import LoginManager
from werkzeug.security import generate_password_hash
from models import db, User, Department, Doctor
from routes.admin_routes import admin_bp
from routes.doctor_routes import doctor_bp
from routes.patient_routes import patient_bp
from routes.auth_routes import auth_bp

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your_secret_key_here'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///hospital.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db.init_app(app)

def no_cache(response):
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, max-age=0'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


app.register_blueprint(auth_bp)
app.register_blueprint(admin_bp)
app.register_blueprint(doctor_bp)
app.register_blueprint(patient_bp)

app.after_request(no_cache)


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        if not User.query.filter_by(email="admin@hospital.com").first():
            admin_user = User(
                name="Admin",
                email="admin@hospital.com",
                password=generate_password_hash("admin123"),
                role="admin"
            )
            db.session.add(admin_user)
            db.session.commit()
        
        PREDEFINED_DEPARTMENTS = [
            {
                "name": "Cardiology",
                "description": "The Cardiology Department focuses on the diagnosis, treatment, and management of heart-related disorders. It includes specialists such as interventional cardiologists, non-invasive cardiologists, and cardiac electrophysiologists who work together to deliver comprehensive cardiovascular care."
            },
            {
                "name": "Neurology",
                "description": "The Neurology Department deals with conditions affecting the brain, spinal cord, and nervous system. Neurologists specialize in diagnosing and managing disorders like epilepsy, stroke, migraines, and neurodegenerative diseases, ensuring complete neurological care."
            },
            {
                "name": "Orthopedics",
                "description": "The Orthopedics Department specializes in disorders of the bones, joints, muscles, and ligaments. Orthopedic surgeons and specialists manage fractures, joint issues, sports injuries, and spine problems, providing both surgical and non-surgical treatments."
            },
            {
                "name": "Pulmonology",
                "description": "The Pulmonology Department is dedicated to the diagnosis and treatment of lung and respiratory conditions. Pulmonologists focus on diseases such as asthma, COPD, lung infections, and sleep-related breathing disorders, offering extensive respiratory care."
            },
            {
                "name": "General Medicine",
                "description": "The General Medicine Department provides primary and preventive healthcare for a wide range of medical conditions. Physicians manage chronic diseases, infections, lifestyle disorders, and routine health evaluations, ensuring overall patient wellness."
            },
            {
                "name": "Dermatology",
                "description": "The Dermatology Department addresses conditions related to the skin, hair, and nails. Dermatologists diagnose and treat issues such as acne, eczema, infections, allergies, and skin cancers, offering both medical and cosmetic skin care services."
            },
            {
                "name": "Pediatrics",
                "description": "The Pediatrics Department offers healthcare services for infants, children, and adolescents. Pediatricians manage childhood illnesses, growth and developmental concerns, vaccinations, and long-term pediatric conditions with a child-centered approach."
            },
            {
                "name": "ENT",
                "description": "The ENT Department specializes in disorders of the ear, nose, throat, and related structures of the head and neck. ENT specialists treat infections, allergies, hearing disorders, sinus issues, and voice problems through medical and surgical interventions."
            },
            {
                "name": "Gynecology",
                "description": "The Gynecology Department provides specialized care for women's reproductive health. Gynecologists manage issues such as menstrual disorders, hormonal concerns, pregnancy-related conditions, and reproductive system diseases, ensuring comprehensive women's health care."
            },
            {
                "name": "Psychiatry",
                "description": "The Psychiatry Department focuses on mental health, emotional well-being, and behavioral disorders. Psychiatrists diagnose and treat conditions like anxiety, depression, bipolar disorder, and other psychological issues through therapy and medical management."
            }
        ]
        for dept_data in PREDEFINED_DEPARTMENTS:
            if not Department.query.filter_by(name=dept_data["name"]).first():
                dept = Department(name=dept_data["name"], description=dept_data["description"])
                db.session.add(dept)
        db.session.commit()
        
        existing_doctors = Doctor.query.filter(Doctor.department_id == None).all()
        for doctor in existing_doctors:
            spec = doctor.specialization
            dept = Department.query.filter_by(name=spec).first()
            if not dept:
                dept = Department(name=spec, description='')
                db.session.add(dept)
                db.session.commit()
            doctor.department_id = dept.id
        db.session.commit()

    app.run(debug=True)
