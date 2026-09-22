from app import create_app
from app.services.notifications import process_due_reminders
app=create_app()
with app.app_context():
    print(process_due_reminders())
