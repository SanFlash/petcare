import os
from datetime import date,timedelta
from werkzeug.security import generate_password_hash
from ..extensions import db
from ..models import User,Pet,Vaccination,Medication,Appointment,Reminder,MedicalRecord,WeightRecord,PreventiveCare
def ensure_demo_admin():
    email=os.getenv("DEMO_ADMIN_EMAIL","admin@petcare.local").strip().lower()
    password=os.getenv("DEMO_ADMIN_PASSWORD","PetCare@12345")
    user=User.query.filter_by(email=email).first()
    if not user:
        user=User(full_name="PetCare Demo Admin",email=email,password_hash=generate_password_hash(password),role="admin"); db.session.add(user); db.session.commit()
    elif user.role!="admin":
        user.role="admin"; db.session.commit()
    return user
def seed_demo_data(admin):
    if Pet.query.filter_by(owner_id=admin.id).first(): return
    today=date.today()
    bruno=Pet(owner_id=admin.id,name="Bruno",species="Dog",breed="Golden Retriever",gender="Male",weight=28.4,color="Golden",allergies="None recorded",conditions="None recorded",emergency_notes="Emergency vet: Example Animal Hospital")
    luna=Pet(owner_id=admin.id,name="Luna",species="Cat",breed="Domestic Shorthair",gender="Female",weight=4.7,color="Grey")
    db.session.add_all([bruno,luna]); db.session.flush()
    db.session.add(Vaccination(pet_id=bruno.id,vaccine_name="Rabies",vaccine_type="Core",given_date=today-timedelta(days=30),next_due_date=today+timedelta(days=335),veterinarian="Dr. Demo",clinic="PetCare Veterinary"))
    db.session.add(Vaccination(pet_id=luna.id,vaccine_name="FVRCP",vaccine_type="Core",given_date=today-timedelta(days=60),next_due_date=today+timedelta(days=305)))
    db.session.add(Medication(pet_id=bruno.id,name="Daily supplement",dosage="1 tablet",frequency="Once daily",start_date=today,end_date=today+timedelta(days=30),reason="Demo schedule"))
    db.session.add(Appointment(pet_id=bruno.id,vet_name="Dr. Demo",clinic="PetCare Veterinary",appointment_date=today+timedelta(days=7),reason="Routine checkup"))
    db.session.add(Reminder(pet_id=bruno.id,title="Routine checkup",reminder_type="appointment",due_date=today+timedelta(days=7)))
    db.session.add(Reminder(pet_id=luna.id,title="Deworming",reminder_type="deworming",due_date=today+timedelta(days=14)))
    db.session.add(MedicalRecord(pet_id=bruno.id,record_date=today-timedelta(days=30),veterinarian="Dr. Demo",clinic="PetCare Veterinary",reason="Routine checkup",diagnosis="No issue recorded",treatment="Preventive care reviewed"))
    db.session.add_all([WeightRecord(pet_id=bruno.id,recorded_on=today-timedelta(days=30),weight=27.8,unit="kg"),WeightRecord(pet_id=bruno.id,recorded_on=today,weight=28.4,unit="kg")])
    db.session.add(PreventiveCare(pet_id=luna.id,care_type="Flea & tick",performed_on=today-timedelta(days=20),next_due_date=today+timedelta(days=10)))
    db.session.commit()
