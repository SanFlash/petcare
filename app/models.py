from datetime import datetime, timezone
from .extensions import db
def utcnow(): return datetime.now(timezone.utc)
class User(db.Model):
    __tablename__="users"
    id=db.Column(db.Integer,primary_key=True); full_name=db.Column(db.String(120),nullable=False); email=db.Column(db.String(255),unique=True,nullable=False,index=True); password_hash=db.Column(db.String(255),nullable=False); phone=db.Column(db.String(30)); role=db.Column(db.String(30),default="owner",nullable=False); is_active=db.Column(db.Boolean,default=True,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class Pet(db.Model):
    __tablename__="pets"
    id=db.Column(db.Integer,primary_key=True); owner_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False,index=True);
    owner=db.relationship("User",backref="pets") name=db.Column(db.String(120),nullable=False); species=db.Column(db.String(60),nullable=False); breed=db.Column(db.String(120)); gender=db.Column(db.String(30)); date_of_birth=db.Column(db.Date); weight=db.Column(db.Float); weight_unit=db.Column(db.String(10),default="kg"); color=db.Column(db.String(60)); microchip_id=db.Column(db.String(120)); photo_url=db.Column(db.Text); allergies=db.Column(db.Text); conditions=db.Column(db.Text); diet=db.Column(db.Text); behavior_notes=db.Column(db.Text); emergency_notes=db.Column(db.Text); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class MedicalRecord(db.Model):
    __tablename__="medical_records"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); record_date=db.Column(db.Date,nullable=False); veterinarian=db.Column(db.String(120)); clinic=db.Column(db.String(160)); reason=db.Column(db.String(255)); symptoms=db.Column(db.Text); diagnosis=db.Column(db.Text); treatment=db.Column(db.Text); prescription=db.Column(db.Text); notes=db.Column(db.Text); follow_up_date=db.Column(db.Date); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class Vaccination(db.Model):
    __tablename__="vaccinations"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); vaccine_name=db.Column(db.String(120),nullable=False); vaccine_type=db.Column(db.String(120)); given_date=db.Column(db.Date,nullable=False); next_due_date=db.Column(db.Date); batch_number=db.Column(db.String(120)); veterinarian=db.Column(db.String(120)); clinic=db.Column(db.String(160)); notes=db.Column(db.Text); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class Medication(db.Model):
    __tablename__="medications"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); name=db.Column(db.String(120),nullable=False); dosage=db.Column(db.String(120)); frequency=db.Column(db.String(120)); start_date=db.Column(db.Date,nullable=False); end_date=db.Column(db.Date); administration_instructions=db.Column(db.Text); veterinarian=db.Column(db.String(120)); reason=db.Column(db.String(255)); notes=db.Column(db.Text); active=db.Column(db.Boolean,default=True,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class Appointment(db.Model):
    __tablename__="appointments"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); vet_name=db.Column(db.String(120)); clinic=db.Column(db.String(160)); appointment_date=db.Column(db.Date,nullable=False); appointment_time=db.Column(db.Time); reason=db.Column(db.String(255)); notes=db.Column(db.Text); status=db.Column(db.String(30),default="upcoming",nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class Reminder(db.Model):
    __tablename__="reminders"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); title=db.Column(db.String(160),nullable=False); reminder_type=db.Column(db.String(50),default="custom",nullable=False); due_date=db.Column(db.Date,nullable=False,index=True); due_time=db.Column(db.Time); recurrence=db.Column(db.String(50),default="none"); status=db.Column(db.String(30),default="upcoming",nullable=False); notes=db.Column(db.Text); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
    pet=db.relationship("Pet",lazy="joined")
class Notification(db.Model):
    __tablename__="notifications"
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("users.id"),nullable=False,index=True); title=db.Column(db.String(160),nullable=False); message=db.Column(db.Text,nullable=False); channel=db.Column(db.String(30),default="in_app",nullable=False); status=db.Column(db.String(30),default="pending",nullable=False); is_read=db.Column(db.Boolean,default=False,nullable=False); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class WeightRecord(db.Model):
    __tablename__="weight_records"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); recorded_on=db.Column(db.Date,nullable=False); weight=db.Column(db.Float,nullable=False); unit=db.Column(db.String(10),default="kg"); notes=db.Column(db.Text)
class PreventiveCare(db.Model):
    __tablename__="preventive_care"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); care_type=db.Column(db.String(80),nullable=False); performed_on=db.Column(db.Date,nullable=False); next_due_date=db.Column(db.Date); notes=db.Column(db.Text)
class MedicalDocument(db.Model):
    __tablename__="medical_documents"
    id=db.Column(db.Integer,primary_key=True); pet_id=db.Column(db.Integer,db.ForeignKey("pets.id"),nullable=False,index=True); file_name=db.Column(db.String(255),nullable=False); storage_path=db.Column(db.Text,nullable=False); content_type=db.Column(db.String(120)); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
class AuditLog(db.Model):
    __tablename__="audit_logs"
    id=db.Column(db.Integer,primary_key=True); user_id=db.Column(db.Integer,db.ForeignKey("users.id")); action=db.Column(db.String(120),nullable=False); target_type=db.Column(db.String(80)); target_id=db.Column(db.Integer); created_at=db.Column(db.DateTime(timezone=True),default=utcnow,nullable=False)
