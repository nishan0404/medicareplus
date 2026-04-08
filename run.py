from dotenv import load_dotenv
load_dotenv()
from app import create_app, db, socketio
from app.models import (
    Patient, PatientProfile, PasswordResetToken,
    Appointment, Cancellation, DoctorAvailability, EmailLog,
    Doctor, ConsultationNote, Prescription,
    Admin, SymptomLog, Condition, AuditLog,
    CallSession,
    ChatMessage, ChatAttachment,
)

app = create_app()

with app.app_context():
    try:
        db.create_all()
        print("✅ All database tables created!")
    except Exception as e:
        print(f"⚠️ DB init skipped: {e}")

if __name__ == '__main__':
    socketio.run(app, host='0.0.0.0', port=10000, debug=False)