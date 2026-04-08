from dotenv import load_dotenv
load_dotenv()

from app import create_app, db, socketio
from app.models import (
    Patient, PatientProfile, PasswordResetToken,
    Appointment, Cancellation, DoctorAvailability, EmailLog,
    Doctor, ConsultationNote, Prescription,
    Admin, SymptomLog, Condition, AuditLog,
    CallSession                              # ← NEW: import CallSession
)

app = create_app()

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        print("✅ All database tables created!")
    socketio.run(app, host='0.0.0.0', port=5000, debug=False)  # ← CHANGED: socketio.run instead of app.run