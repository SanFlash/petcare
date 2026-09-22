from flask import Blueprint,jsonify,request,render_template
from flask_jwt_extended import create_access_token,set_access_cookies,unset_jwt_cookies,jwt_required,verify_jwt_in_request,get_jwt_identity,get_jwt
from werkzeug.security import check_password_hash,generate_password_hash
from datetime import datetime,date,time
from .extensions import db,limiter
from .models import User,Pet,MedicalRecord,Vaccination,Medication,Appointment,Reminder,Notification
from .services.notifications import notify_owner,process_due_reminders,send_sms
import re

web=Blueprint("web",__name__)
api=Blueprint("api",__name__)

@web.get("/")
def home(): return render_template("home.html")

@web.get("/login")
def login_page(): return render_template("login.html")

@web.get("/register")
def register_page(): return render_template("register.html")

@web.get("/dashboard")
@jwt_required(optional=True,locations=["cookies"])
def dashboard():
    identity=get_jwt_identity()
    if identity is None: return render_template("login.html", login_redirect="/dashboard")
    uid=int(identity); user=db.session.get(User,uid)
    process_due_reminders(owner_id=uid)
    pets=Pet.query.filter_by(owner_id=uid).order_by(Pet.name).all()
    reminders=Reminder.query.join(Pet).filter(Pet.owner_id==uid).order_by(Reminder.due_date.asc()).limit(20).all()
    unread=Notification.query.filter_by(user_id=uid,is_read=False).count()
    return render_template("dashboard.html",user=user,pets=pets,reminders=reminders,unread=unread,today=date.today())

@web.get("/pets/<int:pet_id>")
@jwt_required(optional=True,locations=["cookies"])
def pet_detail(pet_id):
    identity=get_jwt_identity()
    if identity is None: return render_template("login.html", login_redirect=f"/pets/{pet_id}")
    uid=int(identity); pet=Pet.query.filter_by(id=pet_id,owner_id=uid).first()
    if not pet:return ("Pet not found",404)
    return render_template("pet_detail.html",pet=pet,
        medical_records=MedicalRecord.query.filter_by(pet_id=pet.id).order_by(MedicalRecord.record_date.desc()).all(),
        vaccinations=Vaccination.query.filter_by(pet_id=pet.id).order_by(Vaccination.given_date.desc()).all(),
        medications=Medication.query.filter_by(pet_id=pet.id).order_by(Medication.start_date.desc()).all(),
        appointments=Appointment.query.filter_by(pet_id=pet.id).order_by(Appointment.appointment_date.asc()).all(),
        reminders=Reminder.query.filter_by(pet_id=pet.id).order_by(Reminder.due_date.asc()).all(),
        today=date.today())

@web.get("/admin")
@jwt_required(optional=True,locations=["cookies"])
def admin_page():
    identity=get_jwt_identity()
    if identity is None: return render_template("login.html", login_redirect="/admin")
    if get_jwt().get("role")!="admin": return render_template("admin.html", access_denied=True, users=[], pets=[], reminders=[], notifications=[]),403
    return render_template("admin.html",
        users=User.query.order_by(User.created_at.desc()).all(),
        pets=Pet.query.order_by(Pet.created_at.desc()).all(),
        reminders=Reminder.query.order_by(Reminder.due_date.asc()).limit(20).all(),
        notifications=Notification.query.order_by(Notification.created_at.desc()).limit(30).all())

def ok(data=None,status=200): return jsonify({"success":True,"data":data if data is not None else {}}),status
def err(code,msg,status): return jsonify({"success":False,"error":{"code":code,"message":msg}}),status
def user():
    try:return db.session.get(User,int(get_jwt_identity()))
    except:return None
def owned(pid):
    u=user(); return (u,Pet.query.filter_by(id=pid,owner_id=u.id).first()) if u else (None,None)
def pd(p):
    return {"id":p.id,"name":p.name,"species":p.species,"breed":p.breed,"gender":p.gender,"date_of_birth":p.date_of_birth.isoformat() if p.date_of_birth else None,"weight":p.weight,"weight_unit":p.weight_unit,"color":p.color,"microchip_id":p.microchip_id,"allergies":p.allergies,"conditions":p.conditions,"diet":p.diet,"behavior_notes":p.behavior_notes,"emergency_notes":p.emergency_notes}
def pdate(v):
    if not v:return None
    try:return datetime.strptime(str(v),"%Y-%m-%d").date()
    except ValueError:raise ValueError("Date must use YYYY-MM-DD.")

@api.post("/auth/register")
@limiter.limit("10 per minute")
def register():
    d=request.get_json(silent=True) or {}; name=str(d.get("full_name","")).strip(); email=str(d.get("email","")).strip().lower(); password=d.get("password","")
    if len(name)<2 or "@" not in email or len(password)<8:return err("VALIDATION_ERROR","Name, valid email and password of at least 8 characters are required.",422)
    phone=str(d.get("phone","")).strip() or None
    if phone and not re.fullmatch(r"\+?[1-9]\d{7,14}",phone):return err("VALIDATION_ERROR","Use a valid mobile number in international E.164 format, for example +919876543210.",422)
    if User.query.filter_by(email=email).first():return err("CONFLICT","An account with that email already exists.",409)
    u=User(full_name=name,email=email,phone=phone,password_hash=generate_password_hash(password));db.session.add(u);db.session.commit()
    return ok({"id":u.id,"email":u.email},201)

@api.post("/auth/login")
@limiter.limit("10 per minute")
def login():
    d=request.get_json(silent=True) or {}; u=User.query.filter_by(email=str(d.get("email","")).strip().lower()).first()
    if not u or not u.is_active or not check_password_hash(u.password_hash,d.get("password","")):return err("AUTHENTICATION_FAILED","Invalid email or password.",401)
    token=create_access_token(identity=str(u.id),additional_claims={"role":u.role,"email":u.email})
    r,s=ok({"user":{"id":u.id,"name":u.full_name,"role":u.role,"email":u.email}});set_access_cookies(r,token);return r,s

@api.post("/auth/logout")
def logout():r,s=ok({"message":"Logged out"});unset_jwt_cookies(r);return r,s

@api.get("/dashboard")
@jwt_required(locations=["cookies"])
def dashboard_api():
    u=user(); process_due_reminders(owner_id=u.id)
    return ok({"user":{"id":u.id,"name":u.full_name,"email":u.email,"role":u.role,"phone":u.phone},
        "pets":[pd(p) for p in Pet.query.filter_by(owner_id=u.id).all()],
        "reminders":[{"id":r.id,"title":r.title,"due_date":r.due_date.isoformat(),"status":r.status,"type":r.reminder_type} for r in Reminder.query.join(Pet).filter(Pet.owner_id==u.id).order_by(Reminder.due_date.asc()).limit(20).all()]})

@api.post("/pets")
@jwt_required(locations=["cookies"])
def pet_create():
    u=user();d=request.get_json(silent=True) or {}
    if not str(d.get("name","")).strip() or not str(d.get("species","")).strip():return err("VALIDATION_ERROR","Pet name and species are required.",422)
    try:w=float(d["weight"]) if d.get("weight") not in (None,"") else None
    except:return err("VALIDATION_ERROR","Weight must be numeric.",422)
    owner_phone=str(d.get("owner_phone",d.get("phone",""))).strip() or None
    if owner_phone and not re.fullmatch(r"\+?[1-9]\d{7,14}",owner_phone):return err("VALIDATION_ERROR","Use a valid owner mobile number in international E.164 format, for example +919876543210.",422)
    if owner_phone:u.phone=owner_phone
    p=Pet(owner_id=u.id,name=str(d["name"]).strip(),species=str(d["species"]).strip(),breed=d.get("breed"),gender=d.get("gender"),date_of_birth=pdate(d.get("date_of_birth")),weight=w,weight_unit=d.get("weight_unit","kg"),color=d.get("color"),microchip_id=d.get("microchip_id"),allergies=d.get("allergies"),conditions=d.get("conditions"),diet=d.get("diet"),behavior_notes=d.get("behavior_notes"),emergency_notes=d.get("emergency_notes"))
    db.session.add(p);db.session.commit();return ok({**pd(p),"owner_phone":u.phone},201)

@api.get("/pets")
@jwt_required(locations=["cookies"])
def pets_list():return ok([pd(p) for p in Pet.query.filter_by(owner_id=user().id).order_by(Pet.name).all()])

@api.post("/pets/<int:pid>/vaccinations")
@jwt_required(locations=["cookies"])
def vac_create(pid):
    u,p=owned(pid)
    if not p:return err("NOT_FOUND","Pet not found.",404)
    d=request.get_json(silent=True) or {};name=str(d.get("vaccine_name","")).strip()
    if not name:return err("VALIDATION_ERROR","Vaccine name is required.",422)
    try:given=pdate(d.get("given_date")) or date.today();due=pdate(d.get("next_due_date"))
    except ValueError as e:return err("VALIDATION_ERROR",str(e),422)
    v=Vaccination(pet_id=p.id,vaccine_name=name,vaccine_type=d.get("vaccine_type"),given_date=given,next_due_date=due,batch_number=d.get("batch_number"),veterinarian=d.get("veterinarian"),clinic=d.get("clinic"),notes=d.get("notes"))
    db.session.add(v)
    if due:db.session.add(Reminder(pet_id=p.id,title=f"{name} vaccination due",reminder_type="vaccination",due_date=due))
    db.session.commit();notify_owner(u,f"{p.name}: vaccination saved",f"{name} has been added to {p.name}'s health passport.",event="vaccination",sms=False);return ok({"id":v.id},201)

@api.post("/pets/<int:pid>/medications")
@jwt_required(locations=["cookies"])
def med_create(pid):
    u,p=owned(pid)
    if not p:return err("NOT_FOUND","Pet not found.",404)
    d=request.get_json(silent=True) or {};name=str(d.get("name","")).strip()
    if not name:return err("VALIDATION_ERROR","Medication name is required.",422)
    try:start=pdate(d.get("start_date")) or date.today();end=pdate(d.get("end_date"))
    except ValueError as e:return err("VALIDATION_ERROR",str(e),422)
    m=Medication(pet_id=p.id,name=name,dosage=d.get("dosage"),frequency=d.get("frequency"),start_date=start,end_date=end,administration_instructions=d.get("administration_instructions"),veterinarian=d.get("veterinarian"),reason=d.get("reason"),notes=d.get("notes"))
    db.session.add(m);db.session.commit();notify_owner(u,f"{p.name}: medication added",f"{name} is now in the medication plan.",event="medication",sms=False);return ok({"id":m.id},201)

@api.post("/pets/<int:pid>/appointments")
@jwt_required(locations=["cookies"])
def appt_create(pid):
    u,p=owned(pid)
    if not p:return err("NOT_FOUND","Pet not found.",404)
    d=request.get_json(silent=True) or {}
    try:ad=pdate(d.get("appointment_date")) or date.today()
    except ValueError as e:return err("VALIDATION_ERROR",str(e),422)
    at=None
    if d.get("appointment_time"):
        try:at=datetime.strptime(str(d.get("appointment_time")),"%H:%M").time()
        except ValueError:return err("VALIDATION_ERROR","Appointment time must use HH:MM.",422)
    a=Appointment(pet_id=p.id,vet_name=d.get("vet_name"),clinic=d.get("clinic"),appointment_date=ad,appointment_time=at,reason=d.get("reason"),notes=d.get("notes"))
    db.session.add(a);db.session.flush()
    db.session.add(Reminder(pet_id=p.id,title=f"Vet appointment for {p.name}",reminder_type="appointment",due_date=ad,due_time=at,notes=a.reason))
    db.session.commit();notify_owner(u,f"{p.name}: appointment added",f"Vet appointment scheduled for {ad.isoformat()}.",event="appointment",sms=False);return ok({"id":a.id},201)

@api.post("/pets/<int:pid>/medical-records")
@jwt_required(locations=["cookies"])
def medical_create(pid):
    u,p=owned(pid)
    if not p:return err("NOT_FOUND","Pet not found.",404)
    d=request.get_json(silent=True) or {}
    try:rd=pdate(d.get("record_date")) or date.today();follow=pdate(d.get("follow_up_date"))
    except ValueError as e:return err("VALIDATION_ERROR",str(e),422)
    r=MedicalRecord(pet_id=p.id,record_date=rd,veterinarian=d.get("veterinarian"),clinic=d.get("clinic"),reason=d.get("reason"),symptoms=d.get("symptoms"),diagnosis=d.get("diagnosis"),treatment=d.get("treatment"),prescription=d.get("prescription"),notes=d.get("notes"),follow_up_date=follow)
    db.session.add(r)
    if follow:db.session.add(Reminder(pet_id=p.id,title=f"{p.name}: medical follow-up",reminder_type="follow_up",due_date=follow))
    db.session.commit();notify_owner(u,f"{p.name}: medical record saved","A new medical record was added to the health passport.",event="medical",sms=False);return ok({"id":r.id},201)

@api.route("/pets/<int:pid>/reminders",methods=["GET","POST"])
@jwt_required(locations=["cookies"])
def reminders(pid):
    u,p=owned(pid)
    if not p:return err("NOT_FOUND","Pet not found.",404)
    if request.method=="GET":
        rows=Reminder.query.filter_by(pet_id=p.id).order_by(Reminder.due_date.asc()).all()
        return ok([{"id":r.id,"title":r.title,"type":r.reminder_type,"due_date":r.due_date.isoformat(),"status":r.status,"recurrence":r.recurrence,"notes":r.notes} for r in rows])
    d=request.get_json(silent=True) or {}
    if not str(d.get("title","")).strip():return err("VALIDATION_ERROR","Reminder title is required.",422)
    try:due=pdate(d.get("due_date")) or date.today()
    except ValueError as e:return err("VALIDATION_ERROR",str(e),422)
    rt=d.get("reminder_type","custom")
    due_time=None
    if d.get("due_time"):
        try:due_time=datetime.strptime(str(d.get("due_time")),"%H:%M").time()
        except ValueError:return err("VALIDATION_ERROR","Reminder time must use HH:MM.",422)
    r=Reminder(pet_id=p.id,title=str(d["title"]).strip(),reminder_type=rt,due_date=due,due_time=due_time,recurrence=d.get("recurrence","none"),notes=d.get("notes"))
    db.session.add(r);db.session.commit();notify_owner(u,f"{p.name}: reminder created",f"{r.title} is due on {r.due_date.isoformat()}.",event="reminder_created",sms=False);return ok({"id":r.id},201)

@api.get("/notifications")
@jwt_required(locations=["cookies"])
def notifications():
    u=user();process_due_reminders(owner_id=u.id)
    rows=Notification.query.filter_by(user_id=u.id).order_by(Notification.created_at.desc()).limit(50).all()
    return ok([{"id":n.id,"title":n.title,"message":n.message,"channel":n.channel,"status":n.status,"is_read":n.is_read,"created_at":n.created_at.isoformat()} for n in rows])

@api.post("/notifications/<int:nid>/read")
@jwt_required(locations=["cookies"])
def notification_read(nid):
    u=user();n=Notification.query.filter_by(id=nid,user_id=u.id).first()
    if not n:return err("NOT_FOUND","Notification not found.",404)
    n.is_read=True;db.session.commit();return ok({"id":n.id,"is_read":True})

@api.route("/profile",methods=["GET","PATCH"])
@jwt_required(locations=["cookies"])
def profile():
    u=user()
    if request.method=="GET":return ok({"id":u.id,"full_name":u.full_name,"email":u.email,"phone":u.phone,"role":u.role})
    d=request.get_json(silent=True) or {}
    if "full_name" in d and len(str(d["full_name"]).strip())>=2:u.full_name=str(d["full_name"]).strip()
    if "phone" in d:
        phone=str(d["phone"]).strip() or None
        if phone and not re.fullmatch(r"\+?[1-9]\d{7,14}",phone): return err("VALIDATION_ERROR","Use a valid mobile number, preferably in international E.164 format such as +919876543210.",422)
        u.phone=phone
    db.session.commit();return ok({"id":u.id,"full_name":u.full_name,"email":u.email,"phone":u.phone,"role":u.role})

@api.post("/notifications/test-sms")
@jwt_required(locations=["cookies"])
def test_sms():
    u=user()
    if not u.phone:return err("PHONE_REQUIRED","Save the owner mobile number first.",422)
    import os
    configured=bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and (os.getenv("TWILIO_FROM_NUMBER") or os.getenv("TWILIO_MESSAGING_SERVICE_SID")))
    if not configured:return err("SMS_NOT_CONFIGURED","Twilio SMS is not configured on this environment.",503)
    sent,detail=send_sms(u.phone,"PetCare test SMS: your owner alert number is connected successfully.")
    if not sent:return err("SMS_SEND_FAILED",detail or "Twilio could not send the test message.",502)
    db.session.add(Notification(user_id=u.id,title="PetCare test SMS",message="Your owner alert number is connected successfully.",channel="sms",status="sent"));db.session.commit()
    return ok({"sent":True,"phone":u.phone})

@api.get("/notifications/preferences")
@jwt_required(locations=["cookies"])
def notification_preferences():
    u=user();import os
    return ok({"sms_configured":bool(os.getenv("TWILIO_ACCOUNT_SID") and os.getenv("TWILIO_AUTH_TOKEN") and os.getenv("TWILIO_FROM_NUMBER")),"phone_configured":bool(u.phone),"phone":u.phone})

@api.post("/admin/process-reminders")
@jwt_required(locations=["cookies"])
def admin_process_reminders():
    if get_jwt().get("role")!="admin":return err("FORBIDDEN","Admin access required.",403)
    return ok(process_due_reminders())

@api.post("/reminders/<int:rid>/complete")
@jwt_required(locations=["cookies"])
def complete(rid):
    u=user();r=Reminder.query.join(Pet).filter(Reminder.id==rid,Pet.owner_id==u.id).first()
    if not r:return err("NOT_FOUND","Reminder not found.",404)
    r.status="completed";db.session.add(Notification(user_id=u.id,title="Reminder completed",message=f"{r.title} marked complete.",status="sent",channel="in_app"));db.session.commit();return ok({"id":r.id,"status":"completed"})

@api.get("/admin/stats")
@jwt_required(locations=["cookies"])
def stats():
    if get_jwt().get("role")!="admin":return err("FORBIDDEN","Admin access required.",403)
    return ok({"users":User.query.count(),"pets":Pet.query.count(),"reminders":Reminder.query.count(),"notifications":Notification.query.count(),"medical_records":MedicalRecord.query.count()})
