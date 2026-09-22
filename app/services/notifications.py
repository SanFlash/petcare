import os
from datetime import date,timedelta
from ..extensions import db
from ..models import Notification,Reminder,Pet,User

def _sms(to, body):
    sid=os.getenv("TWILIO_ACCOUNT_SID"); token=os.getenv("TWILIO_AUTH_TOKEN"); sender=os.getenv("TWILIO_FROM_NUMBER")
    if not all([sid,token,sender,to]): return False
    try:
        from twilio.rest import Client
        Client(sid,token).messages.create(body=body,from_=sender,to=to)
        return True
    except Exception:
        return False

def notify_owner(owner,title,message,event="general",sms=True):
    db.session.add(Notification(user_id=owner.id,title=title,message=message,channel="in_app",status="sent"))
    if sms and owner.phone:
        sent=_sms(owner.phone,f"{title}: {message}")
        db.session.add(Notification(user_id=owner.id,title=title,message=message,channel="sms",status="sent" if sent else "failed"))
    db.session.commit()

def process_due_reminders(owner_id=None):
    today=date.today(); tomorrow=today+timedelta(days=1)
    q=Reminder.query.join(Pet).filter(Reminder.status.notin_(["completed","cancelled"]),Reminder.due_date<=tomorrow)
    if owner_id:q=q.filter(Pet.owner_id==owner_id)
    processed=0
    for r in q.all():
        owner=r.pet.owner
        exists=Notification.query.filter_by(user_id=owner.id,channel="sms",title=f"Reminder: {r.title}").first()
        if exists: continue
        when="today" if r.due_date==today else "tomorrow" if r.due_date==tomorrow else r.due_date.isoformat()
        notify_owner(owner,f"Reminder: {r.title}",f"{r.pet.name} has a {r.reminder_type} reminder due {when}.",event="due_reminder")
        processed+=1
    return {"processed":processed}
