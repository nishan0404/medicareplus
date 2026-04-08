import eventlet
eventlet.monkey_patch()

from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from flask_socketio import SocketIO
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from dotenv import load_dotenv
from apscheduler.schedulers.background import BackgroundScheduler
from datetime import timedelta
import os

load_dotenv()

db           = SQLAlchemy()
login_manager = LoginManager()
bcrypt       = Bcrypt()
mail         = Mail()
scheduler    = BackgroundScheduler()
socketio     = SocketIO()
limiter      = Limiter(key_func=get_remote_address, default_limits=[])


def create_app():
    app = Flask(__name__, template_folder='templates', static_folder='static')

    app.config['SECRET_KEY'] = os.getenv('SECRET_KEY')
    app.config['SQLALCHEMY_DATABASE_URI'] = (
        os.getenv('DATABASE_URL') or
        f"mysql+pymysql://{os.getenv('DB_USER')}:{os.getenv('DB_PASSWORD')}@{os.getenv('DB_HOST')}/{os.getenv('DB_NAME')}"
    )
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ENGINE_OPTIONS'] = {
        'pool_pre_ping': True,
        'pool_recycle':  1800,
    }

    # ── Session security ──
    app.config['PERMANENT_SESSION_LIFETIME']    = timedelta(minutes=60)
    app.config['SESSION_REFRESH_EACH_REQUEST']  = True
    app.config['SESSION_COOKIE_HTTPONLY']       = True
    app.config['SESSION_COOKIE_SAMESITE']       = 'Lax'
    app.config['MAIL_SERVER']   = os.getenv('MAIL_SERVER')
    app.config['MAIL_PORT']     = int(os.getenv('MAIL_PORT', 587))
    app.config['MAIL_USE_TLS']  = os.getenv('MAIL_USE_TLS') == 'True'
    app.config['MAIL_USERNAME'] = os.getenv('MAIL_USERNAME')
    app.config['MAIL_PASSWORD'] = os.getenv('MAIL_PASSWORD')

    db.init_app(app)
    login_manager.init_app(app)
    bcrypt.init_app(app)
    mail.init_app(app)
    limiter.init_app(app)

    # SocketIO — supports WebRTC calls AND live chat
    socketio.init_app(
        app,
        cors_allowed_origins='*',
        async_mode='eventlet',
        ping_timeout=60,
        ping_interval=25
    )

    login_manager.login_view         = 'auth.login'
    login_manager.login_message      = 'Please log in to access this page.'
    login_manager.login_message_category = 'info'

    with app.app_context():
        from app.models import (
            Patient, PatientProfile, PasswordResetToken,
            Appointment, Cancellation, DoctorAvailability, EmailLog,
            Doctor, ConsultationNote, Prescription,
            Admin, SymptomLog, Condition, AuditLog,
            CallSession,
            ChatMessage, ChatAttachment,
        )

        from app.routes.auth        import auth
        from app.routes.patient     import patient
        from app.routes.doctor      import doctor
        from app.routes.admin       import admin
        from app.routes.appointment import appointment
        from app.routes.chatbot     import chatbot
        from app.routes.call        import call,      register_socketio_events
        from app.routes.chat        import chat as chat_blueprint, register_chat_events

        app.register_blueprint(auth)
        app.register_blueprint(patient)
        app.register_blueprint(doctor)
        app.register_blueprint(admin)
        app.register_blueprint(appointment)
        app.register_blueprint(chatbot)
        app.register_blueprint(call)
        app.register_blueprint(chat_blueprint)

        register_socketio_events(socketio)
        register_chat_events(socketio)

        def auto_expire_appointments():
            from datetime import datetime, timedelta, date as date_type, time as time_type
            from app.models import Appointment

            now      = datetime.now()
            today    = now.date()
            cutoff   = (now - timedelta(hours=1)).time()

            stale = Appointment.query.filter(
                Appointment.status.in_(['Upcoming', 'In-Progress']),
                Appointment.appointment_date < today,
            ).all()

            stale += Appointment.query.filter(
                Appointment.status.in_(['Upcoming', 'In-Progress']),
                Appointment.appointment_date == today,
                Appointment.appointment_time < cutoff,
            ).all()

            for appt in stale:
                appt.status = 'No-Show'
            if stale:
                db.session.commit()

        app.auto_expire_appointments = auto_expire_appointments

        try:
            auto_expire_appointments()
        except Exception:
            pass

        def _scheduled_job():
            with app.app_context():
                auto_expire_appointments()

        if not scheduler.running:
            scheduler.add_job(
                func=_scheduled_job,
                trigger='interval',
                hours=1,
                id='auto_expire_appointments',
                replace_existing=True,
            )
            scheduler.start()

    return app