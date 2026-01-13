# Hospital Management System (HMS)
A full-featured Hospital Management System built using Flask, SQLAlchemy, Jinja2, and SQLite, supporting Admin, Doctor, and Patient roles.
The system manages appointments, availability, medical history, and user profiles with a clean multi-role architecture.

## Features
### Admin:

Add, Edit, Delete Doctors & Patients

Blacklist / Reactivate Users

View Doctor & Patient Details

View All Appointments

View Patient Medical History

Dashboard with total counts

### Doctor:

View Assigned Patients

View Upcoming Appointments

Mark Appointment Completed

Add / Update Treatment & Notes

Provide Availability (Morning/Evening slots)

Auto-disable expired time slots

View Patient Full History

### Patient:

Edit Profile

Browse Departments & Doctors

View Doctor Details

Check Doctor Availability

Book / Cancel Appointments

View Upcoming Appointments

View Complete Appointment History

## Project Structure
/project   
│── app.py   
│── config.py  
│── models.py  
│── /routes  
│── /templates     
│── /static  
│── /instance (auto-created)  
│── hospital.db (auto-created)

## Database Models (Schema)

User – id, name, email, password, role, active

Doctor – specialization, experience, phone, address, department_id

Patient – age, gender, phone, address

Appointment – patient_id, doctor_id, date, time, status

Treatment – appointment_id, diagnosis, prescription, notes

Availability – doctor_id, date, time_slot, status

Department – name, description

## Tech Stack

Backend: Flask (Blueprints, Flask-Login)

Frontend: Jinja2, HTML, CSS (Bootstrap-lite)

Database: SQLite (SQLAlchemy ORM)

Authentication: Flask-Login Sessions

Templating: Jinja2

No JavaScript framework used (minimal JS only where required)

## How to Run the Project

### Install dependencies

pip install -r requirements.txt


### Run the app

python app.py


### Open in browser

http://127.0.0.1:5000

## Roles & Access Control

Role-based authentication implemented using Flask-Login:

Admin → full access

Doctor → medical operations & availability

Patient → booking & profile
