import os
from datetime import date,timedelta,datetime
from zoneinfo import ZoneInfo
from ..extensions import db
from ..models import Notification,Reminder,Pet

def _now():
    tz=ZoneInfo(os.getenv("APP_TIMEZONE","Asia/Kolkata"))
    return datetime.now(tz)

def send_sms(to,body):
    sid=os.getenv("TWILIO_ACCOUNT_SID")
    token=os.getenv("TWILIO_AUTH_TOKEN")
    sender=os.getenv("TWILIO_FROM_NUMBER")
    messaging_service=os.getenv("TWILIO_MESSAGING_SERVICE_SID")
    if not all([sid,token,to]) or not (sender or messaging_service):
        return False,"Twilio credentials/sender are not configured."
    try:
        from twilio.rest import Client
        client=Client(sid,token)
        payload={"body":body,"to":to}
        if messaging_service:
            payload["messaging_service_sid"]=messaging_service
        else:
            payload["from_"]=sender
        msg=client.messages.create(**payload)
        print(f"[PetCare SMS] sent sid={msg.sid} to={to}")
        return True,msg.sid
    except Exception as exc:
        print(f"[PetCare SMS] failed to={to}: {exc}")
        return False,str(exc)

def notify_owner(owner,title,message,event="general",sms=True):
    db.session.add(Notification(user_id=owner.id,title=title,message=message,channel="in_app",status="sent"))
    if sms and owner.phone:
        sent,detail=send_sms(owner.phone,f"{title}: {message}")
        db.session.add(Notification(user_id=owner.id,title=title,message=message,channel="sms",status="sent" if sent else "failed"))
    db.session.commit()

def process_due_reminders(owner_id=None):
    today=_now().date()
    end_date=today+timedelta(days=2)
    q=Reminder.query.join(Pet).filter(
        Reminder.status.notin_(["completed","cancelled"]),
        Reminder.due_date>=today,
        Reminder.due_date<=end_date
    )
    if owner_id:q=q.filter(Pet.owner_id==owner_id)
    processed=0
    for r in q.order_by(Reminder.due_date.asc(),Reminder.id.asc()).all():
        days_until=(r.due_date-today).days
        stage={2:"2-day",1:"1-day",0:"event-day"}.get(days_until)
        if not stage:
            continue
        owner=r.pet.owner
        title=f"Reminder: {r.title}"
        when={2:"in 2 days",1:"tomorrow",0:"today"}[days_until]
        detail=f"{r.pet.name} has a {r.reminder_type.replace('_',' ')} scheduled {when}."
        if r.due_time:
            detail += f" Event time: {r.due_time.strftime('%I:%M %p').lstrip('0')}."
        message=f"{detail} This is the {stage} follow-up notification."
        already=Notification.query.filter_by(user_id=owner.id,channel="sms",title=title,message=message,status="sent").first()
        if already:
            continue
        notify_owner(owner,title,message,event=f"reminder_{stage}",sms=True)
        processed+=1
    return {"processed":processed,"today":today.isoformat()}
