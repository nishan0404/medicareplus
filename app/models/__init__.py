from app import db, login_manager
from flask_login import UserMixin
from datetime import datetime


# ─────────────────────────────────────
# LOGIN MANAGER
# ─────────────────────────────────────
@login_manager.user_loader
def load_user(user_id):
    try:
        if user_id.startswith('patient_'):
            return Patient.query.get(int(user_id.split('_')[1]))
        elif user_id.startswith('doctor_'):
            return Doctor.query.get(int(user_id.split('_')[1]))
        elif user_id.startswith('admin_'):
            return Admin.query.get(int(user_id.split('_')[1]))
    except (ValueError, IndexError):
        pass
    return None


# ─────────────────────────────────────
# SIJAN — PATIENT MODULE
# ─────────────────────────────────────
class Patient(db.Model, UserMixin):
    __tablename__ = 'patients'
    id              = db.Column(db.Integer, primary_key=True)
    full_name       = db.Column(db.String(100), nullable=False)
    date_of_birth   = db.Column(db.Date, nullable=False)
    email           = db.Column(db.String(150), unique=True, nullable=False)
    phone           = db.Column(db.String(20), nullable=False)
    password_hash   = db.Column(db.String(255), nullable=False)
    is_verified     = db.Column(db.Boolean, default=False)
    is_active       = db.Column(db.Boolean, default=True)
    failed_attempts = db.Column(db.Integer, default=0)
    role            = db.Column(db.String(20), default='patient')
    created_at      = db.Column(db.DateTime, default=datetime.utcnow)

    profile         = db.relationship('PatientProfile', backref='patient', uselist=False)
    appointments    = db.relationship('Appointment', backref='patient', lazy=True)
    symptom_logs    = db.relationship('SymptomLog', backref='patient', lazy=True)

    def get_id(self):
        return f"patient_{self.id}"


class PatientProfile(db.Model):
    __tablename__ = 'patient_profiles'
    id              = db.Column(db.Integer, primary_key=True)
    patient_id      = db.Column(db.Integer, db.ForeignKey('patients.id'), unique=True, nullable=False)
    home_address    = db.Column(db.String(255))
    emergency_name  = db.Column(db.String(100))
    emergency_phone = db.Column(db.String(20))
    updated_at      = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class PasswordResetToken(db.Model):
    __tablename__ = 'password_reset_tokens'
    id          = db.Column(db.Integer, primary_key=True)
    user_id     = db.Column(db.Integer, nullable=False)
    user_role   = db.Column(db.String(20), nullable=False)
    token       = db.Column(db.String(100), unique=True, nullable=False)
    expires_at  = db.Column(db.DateTime, nullable=False)
    used        = db.Column(db.Boolean, default=False)
    created_at  = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────
# ANISHA — APPOINTMENT MODULE
# ─────────────────────────────────────
class Appointment(db.Model):
    __tablename__ = 'appointments'
    id                = db.Column(db.Integer, primary_key=True)
    patient_id        = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False, index=True)
    doctor_id         = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False, index=True)
    appointment_date  = db.Column(db.Date, nullable=False)
    appointment_time  = db.Column(db.Time, nullable=False)
    reason            = db.Column(db.String(255))
    appointment_type  = db.Column(db.String(20), default='In-person')
    status            = db.Column(db.String(20), default='Upcoming')
    reminder_sent     = db.Column(db.Boolean, default=False)
    completed_at      = db.Column(db.DateTime)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)
    payment_intent_id = db.Column(db.String(255), nullable=True)
    payment_status    = db.Column(db.String(50), default='Unpaid')
    amount_paid       = db.Column(db.Numeric(10, 2), default=0.00)

    notes             = db.relationship('ConsultationNote', backref='appointment', uselist=False)
    prescriptions     = db.relationship('Prescription', backref='appointment', lazy=True)
    call_session      = db.relationship('CallSession', backref='appointment', uselist=False)
    chat_messages     = db.relationship('ChatMessage', backref='appointment', lazy=True)


class Cancellation(db.Model):
    __tablename__ = 'cancellations'
    id                  = db.Column(db.Integer, primary_key=True)
    appointment_id      = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    cancelled_by        = db.Column(db.Integer, nullable=False)
    cancellation_reason = db.Column(db.String(255))
    cancelled_at        = db.Column(db.DateTime, default=datetime.utcnow)
    hours_notice_given  = db.Column(db.Float)
    new_appointment_id  = db.Column(db.Integer)


class DoctorAvailability(db.Model):
    __tablename__ = 'doctor_availability'
    __table_args__ = (
        db.UniqueConstraint('doctor_id', 'slot_date', 'slot_time', name='uq_doctor_slot'),
    )
    id             = db.Column(db.Integer, primary_key=True)
    doctor_id      = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False, index=True)
    slot_date      = db.Column(db.Date, nullable=False)
    slot_time      = db.Column(db.Time, nullable=False)
    is_available   = db.Column(db.Boolean, default=True)
    is_booked      = db.Column(db.Boolean, default=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'))


class EmailLog(db.Model):
    __tablename__ = 'email_logs'
    id              = db.Column(db.Integer, primary_key=True)
    appointment_id  = db.Column(db.Integer, db.ForeignKey('appointments.id'))
    recipient_email = db.Column(db.String(150), nullable=False)
    email_type      = db.Column(db.String(50), nullable=False)
    sent_at         = db.Column(db.DateTime, default=datetime.utcnow)
    status          = db.Column(db.String(20), default='Sent')


# ─────────────────────────────────────
# ANISHA — TELEHEALTH CALL SESSION
# ─────────────────────────────────────
class CallSession(db.Model):
    __tablename__ = 'call_sessions'
    id             = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)
    patient_id     = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    doctor_id      = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    room_id        = db.Column(db.String(64), unique=True, nullable=False)
    call_type      = db.Column(db.String(10), nullable=False)
    status         = db.Column(db.String(20), default='waiting')
    started_at     = db.Column(db.DateTime)
    ended_at       = db.Column(db.DateTime)
    duration_secs  = db.Column(db.Integer)
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    patient        = db.relationship('Patient', foreign_keys=[patient_id])
    doctor         = db.relationship('Doctor',  foreign_keys=[doctor_id])


# ─────────────────────────────────────
# ANISHA — LIVE CHAT TABLES (NEW)
# ─────────────────────────────────────
class ChatMessage(db.Model):
    """
    Stores every chat message for an appointment.
    Chat window opens 30 min before appointment and closes 30 min after completion.
    sender_role: 'patient' | 'doctor'
    msg_type:    'text' | 'file' | 'image'
    is_read:     True once the other party has seen it
    """
    __tablename__ = 'chat_messages'

    id             = db.Column(db.Integer, primary_key=True)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False, index=True)
    sender_id      = db.Column(db.Integer, nullable=False)
    sender_role    = db.Column(db.String(10), nullable=False)   # 'patient' | 'doctor'
    sender_name    = db.Column(db.String(100), nullable=False)
    message        = db.Column(db.Text)
    msg_type       = db.Column(db.String(10), default='text')   # 'text' | 'file' | 'image'
    file_url       = db.Column(db.String(500))                  # path for attachments
    file_name      = db.Column(db.String(255))                  # original filename
    is_read        = db.Column(db.Boolean, default=False)
    sent_at        = db.Column(db.DateTime, default=datetime.utcnow)


class ChatAttachment(db.Model):
    """
    Stores metadata for file/image attachments sent in chat.
    """
    __tablename__ = 'chat_attachments'

    id             = db.Column(db.Integer, primary_key=True)
    message_id     = db.Column(db.Integer, db.ForeignKey('chat_messages.id'), nullable=False)
    appointment_id = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    file_name      = db.Column(db.String(255), nullable=False)
    file_path      = db.Column(db.String(500), nullable=False)
    file_type      = db.Column(db.String(50))                   # 'image/png', 'application/pdf' etc
    file_size      = db.Column(db.Integer)                      # bytes
    uploaded_at    = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────
# ABIN — DOCTOR MODULE
# ─────────────────────────────────────
class Doctor(db.Model, UserMixin):
    __tablename__ = 'doctors'
    id             = db.Column(db.Integer, primary_key=True)
    full_name      = db.Column(db.String(100), nullable=False)
    specialisation = db.Column(db.String(100), nullable=False)
    email          = db.Column(db.String(150), unique=True, nullable=False)
    password_hash  = db.Column(db.String(255), nullable=False)
    phone          = db.Column(db.String(20), nullable=False)
    bio            = db.Column(db.Text)
    is_active      = db.Column(db.Boolean, default=True)
    role           = db.Column(db.String(20), default='doctor')
    created_at     = db.Column(db.DateTime, default=datetime.utcnow)

    appointments   = db.relationship('Appointment', backref='doctor', lazy=True)
    availability   = db.relationship('DoctorAvailability', backref='doctor', lazy=True)

    def get_id(self):
        return f"doctor_{self.id}"


class ConsultationNote(db.Model):
    __tablename__ = 'consultation_notes'
    id                = db.Column(db.Integer, primary_key=True)
    appointment_id    = db.Column(db.Integer, db.ForeignKey('appointments.id'), unique=True, nullable=False)
    doctor_id         = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id        = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    diagnosis         = db.Column(db.String(255), nullable=False)
    notes             = db.Column(db.Text, nullable=False)
    follow_up_date    = db.Column(db.Date)
    no_notes_recorded = db.Column(db.Boolean, default=False)
    created_at        = db.Column(db.DateTime, default=datetime.utcnow)


class Prescription(db.Model):
    __tablename__ = 'prescriptions'
    id              = db.Column(db.Integer, primary_key=True)
    appointment_id  = db.Column(db.Integer, db.ForeignKey('appointments.id'), nullable=False)
    doctor_id       = db.Column(db.Integer, db.ForeignKey('doctors.id'), nullable=False)
    patient_id      = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    medication_name = db.Column(db.String(150), nullable=False)
    dosage          = db.Column(db.String(100), nullable=False)
    frequency       = db.Column(db.String(100), nullable=False)
    duration_days   = db.Column(db.Integer, nullable=False)
    instructions    = db.Column(db.Text)
    issued_at       = db.Column(db.DateTime, default=datetime.utcnow)


# ─────────────────────────────────────
# NISHAN — AI + ADMIN MODULE
# ─────────────────────────────────────
class Admin(db.Model, UserMixin):
    __tablename__ = 'admins'
    id            = db.Column(db.Integer, primary_key=True)
    full_name     = db.Column(db.String(100), nullable=False)
    email         = db.Column(db.String(150), unique=True, nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    last_login    = db.Column(db.DateTime)
    role          = db.Column(db.String(20), default='admin')
    created_at    = db.Column(db.DateTime, default=datetime.utcnow)

    def get_id(self):
        return f"admin_{self.id}"


class SymptomLog(db.Model):
    __tablename__ = 'symptom_logs'
    id                   = db.Column(db.Integer, primary_key=True)
    patient_id           = db.Column(db.Integer, db.ForeignKey('patients.id'), nullable=False)
    input_text           = db.Column(db.Text, nullable=False)
    predicted_conditions = db.Column(db.JSON, nullable=False)
    urgency_level        = db.Column(db.String(10), nullable=False)
    booked_after         = db.Column(db.Boolean, default=False)
    checked_at           = db.Column(db.DateTime, default=datetime.utcnow)


class Condition(db.Model):
    __tablename__ = 'conditions'
    id                     = db.Column(db.Integer, primary_key=True)
    condition_name         = db.Column(db.String(150), unique=True, nullable=False)
    description            = db.Column(db.Text, nullable=False)
    recommended_specialist = db.Column(db.String(100), nullable=False)
    default_urgency        = db.Column(db.String(10), nullable=False)
    red_flag_keywords      = db.Column(db.JSON)


class AuditLog(db.Model):
    __tablename__ = 'audit_logs'
    id                 = db.Column(db.Integer, primary_key=True)
    user_id            = db.Column(db.Integer, nullable=False)
    user_role          = db.Column(db.String(20), nullable=False)
    action_type        = db.Column(db.String(100), nullable=False)
    affected_record_id = db.Column(db.Integer)
    affected_table     = db.Column(db.String(50))
    ip_address         = db.Column(db.String(45), nullable=False)
    event_timestamp    = db.Column(db.DateTime, default=datetime.utcnow)