from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, mail, limiter
from app.models import Patient, PatientProfile, Doctor, Admin, AuditLog, PasswordResetToken
from datetime import datetime, timedelta
from flask_mail import Message
import re, secrets, os

auth = Blueprint('auth', __name__)


# ── Helper: Log Event ──
def log_event(user_id, user_role, action_type, affected_record_id=None,
              affected_table=None, ip_address='127.0.0.1'):
    log = AuditLog(
        user_id            = user_id,
        user_role          = user_role,
        action_type        = action_type,
        affected_record_id = affected_record_id,
        affected_table     = affected_table,
        ip_address         = ip_address
    )
    db.session.add(log)
    db.session.commit()


@auth.route('/')
def home():
    return redirect(url_for('auth.login'))


@auth.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        full_name        = request.form.get('full_name', '').strip()
        date_of_birth    = request.form.get('date_of_birth', '').strip()
        email            = request.form.get('email', '').strip().lower()
        phone            = request.form.get('phone', '').strip()
        password         = request.form.get('password', '')
        confirm_password = request.form.get('confirm_password', '')

        errors = []

        if not full_name:
            errors.append('Full name is required.')
        if not date_of_birth:
            errors.append('Date of birth is required.')
        if not re.match(r'^[\w\.-]+@[\w\.-]+\.\w+$', email):
            errors.append('Please enter a valid email address.')
        if not re.match(r'^\d{10}$', phone):
            errors.append('Phone number must be exactly 10 digits.')
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one number.')
        if not re.search(r'[^a-zA-Z0-9]', password):
            errors.append('Password must contain at least one special character.')
        if password != confirm_password:
            errors.append('Passwords do not match.')

        existing = Patient.query.filter_by(email=email).first()
        if existing:
            errors.append('An account with this email already exists.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('patient/register.html', title='Register')

        hashed_password = bcrypt.generate_password_hash(password).decode('utf-8')
        dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()

        new_patient = Patient(
            full_name     = full_name,
            date_of_birth = dob,
            email         = email,
            phone         = phone,
            password_hash = hashed_password,
            is_verified   = True
        )
        db.session.add(new_patient)
        db.session.commit()

        profile = PatientProfile(patient_id=new_patient.id)
        db.session.add(profile)
        db.session.commit()

        # Log registration
        ip = request.remote_addr or '127.0.0.1'
        log_event(new_patient.id, 'patient', 'Patient_Registered',
                  new_patient.id, 'patients', ip)

        flash('Account created successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('patient/register.html', title='Register')


@auth.route('/login', methods=['GET', 'POST'])
@limiter.limit('10 per minute', methods=['POST'])
def login():
    if request.method == 'POST':
        email    = request.form.get('email', '').strip().lower()
        password = request.form.get('password', '')
        ip       = request.remote_addr or '127.0.0.1'

        # Check Patient
        user = Patient.query.filter_by(email=email).first()
        if user and bcrypt.check_password_hash(user.password_hash, password):
            if not user.is_active:
                flash('Your account has been deactivated.', 'danger')
                return render_template('patient/login.html', title='Login')
            user.failed_attempts = 0
            db.session.commit()
            login_user(user)
            log_event(user.id, 'patient', 'Login_Success',
                      user.id, 'patients', ip)
            flash(f'Welcome back, {user.full_name}!', 'success')
            return redirect(url_for('patient.dashboard'))

        # Check Doctor
        doctor = Doctor.query.filter_by(email=email).first()
        if doctor and bcrypt.check_password_hash(doctor.password_hash, password):
            if not doctor.is_active:
                flash('Your doctor account has been deactivated. Please contact admin.', 'danger')
                return render_template('patient/login.html', title='Login')
            login_user(doctor)
            log_event(doctor.id, 'doctor', 'Login_Success',
                      doctor.id, 'doctors', ip)
            flash(f'Welcome, {doctor.full_name}!', 'success')
            return redirect(url_for('doctor.dashboard'))

        # Check Admin
        admin_user = Admin.query.filter_by(email=email).first()
        if admin_user and bcrypt.check_password_hash(admin_user.password_hash, password):
            login_user(admin_user)
            admin_user.last_login = datetime.utcnow()
            db.session.commit()
            log_event(admin_user.id, 'admin', 'Login_Success',
                      admin_user.id, 'admins', ip)
            flash(f'Welcome, {admin_user.full_name}!', 'success')
            return redirect(url_for('admin.dashboard'))

        # Failed login
        if user:
            user.failed_attempts += 1
            db.session.commit()
            log_event(user.id, 'patient', 'Login_Failed',
                      user.id, 'patients', ip)

        flash('Incorrect email or password. Please try again.', 'danger')

    return render_template('patient/login.html', title='Login')


@auth.route('/logout')
@login_required
def logout():
    ip = request.remote_addr or '127.0.0.1'
    log_event(current_user.id, current_user.role, 'Logout',
              current_user.id, current_user.role + 's', ip)
    logout_user()
    flash('You have been logged out successfully.', 'success')
    return redirect(url_for('auth.login'))


# ── Forgot Password ──
@auth.route('/forgot-password', methods=['GET', 'POST'])
@limiter.limit('5 per minute', methods=['POST'])
def forgot_password():
    if request.method == 'POST':
        email = request.form.get('email', '').strip().lower()
        ip    = request.remote_addr or '127.0.0.1'

        # Find user across all roles
        user = (Patient.query.filter_by(email=email).first() or
                Doctor.query.filter_by(email=email).first() or
                Admin.query.filter_by(email=email).first())

        # Always show success to prevent email enumeration
        if user:
            # Invalidate old tokens
            PasswordResetToken.query.filter_by(
                user_id=user.id, user_role=user.role, used=False
            ).update({'used': True})
            db.session.commit()

            token      = secrets.token_urlsafe(48)
            expires_at = datetime.utcnow() + timedelta(hours=1)
            reset_tok  = PasswordResetToken(
                user_id    = user.id,
                user_role  = user.role,
                token      = token,
                expires_at = expires_at,
            )
            db.session.add(reset_tok)
            db.session.commit()

            reset_url = url_for('auth.reset_password', token=token, _external=True)
            try:
                msg = Message(
                    subject  = 'MediCare+ — Reset Your Password',
                    sender   = os.getenv('MAIL_USERNAME'),
                    recipients = [email],
                    body=(
                        f"Hi {user.full_name},\n\n"
                        f"Click the link below to reset your password. "
                        f"This link expires in 1 hour.\n\n"
                        f"{reset_url}\n\n"
                        f"If you did not request this, ignore this email.\n\n"
                        f"— MediCare+ Team"
                    )
                )
                mail.send(msg)
            except Exception:
                pass  # Don't reveal mail errors to user

            log_event(user.id, user.role, 'Password_Reset_Requested',
                      user.id, user.role + 's', ip)

        flash('If that email is registered, a reset link has been sent.', 'info')
        return redirect(url_for('auth.login'))

    return render_template('patient/forgot_password.html', title='Forgot Password')


# ── Reset Password ──
@auth.route('/reset-password/<token>', methods=['GET', 'POST'])
def reset_password(token):
    record = PasswordResetToken.query.filter_by(token=token, used=False).first()

    if not record or record.expires_at < datetime.utcnow():
        flash('This reset link is invalid or has expired.', 'danger')
        return redirect(url_for('auth.forgot_password'))

    if request.method == 'POST':
        password = request.form.get('password', '')
        confirm  = request.form.get('confirm_password', '')
        ip       = request.remote_addr or '127.0.0.1'

        errors = []
        if len(password) < 8:
            errors.append('Password must be at least 8 characters.')
        if not re.search(r'[0-9]', password):
            errors.append('Password must contain at least one number.')
        if not re.search(r'[^a-zA-Z0-9]', password):
            errors.append('Password must contain at least one special character.')
        if password != confirm:
            errors.append('Passwords do not match.')
        if errors:
            for e in errors:
                flash(e, 'danger')
            return render_template('patient/reset_password.html',
                                   title='Reset Password', token=token)

        # Find user by role
        role_map = {'patient': Patient, 'doctor': Doctor, 'admin': Admin}
        UserModel = role_map.get(record.user_role)
        user = UserModel.query.get(record.user_id) if UserModel else None
        if not user:
            flash('User not found.', 'danger')
            return redirect(url_for('auth.login'))

        user.password_hash = bcrypt.generate_password_hash(password).decode('utf-8')
        record.used = True
        db.session.commit()

        log_event(user.id, user.role, 'Password_Reset_Completed',
                  user.id, user.role + 's', ip)
        flash('Password reset successfully! Please log in.', 'success')
        return redirect(url_for('auth.login'))

    return render_template('patient/reset_password.html',
                           title='Reset Password', token=token)