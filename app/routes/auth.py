from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from app import db, bcrypt, mail, limiter
from app.models import Patient, PatientProfile, Doctor, Admin, AuditLog, PasswordResetToken
from datetime import datetime, timedelta
from flask_mail import Message
from urllib.parse import urlencode
import re, secrets, os, requests

auth = Blueprint('auth', __name__)

GOOGLE_AUTH_URL = 'https://accounts.google.com/o/oauth2/v2/auth'
GOOGLE_TOKEN_URL = 'https://oauth2.googleapis.com/token'
GOOGLE_USERINFO_URL = 'https://openidconnect.googleapis.com/v1/userinfo'


def build_email_button_html(title, greeting, intro, button_text, button_url, note):
    return f"""
    <!doctype html>
    <html>
      <body style="margin:0;padding:0;background:#f1f5f9;font-family:Arial,Helvetica,sans-serif;color:#0f172a;">
        <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f1f5f9;padding:28px 12px;">
          <tr>
            <td align="center">
              <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="max-width:560px;background:#ffffff;border-radius:14px;overflow:hidden;border:1px solid #e2e8f0;">
                <tr>
                  <td style="background:#0B2545;padding:22px 28px;color:#ffffff;">
                    <div style="font-size:24px;font-weight:700;letter-spacing:.2px;">MediCare+</div>
                    <div style="font-size:13px;color:#bfdbfe;margin-top:4px;">AI-Powered Healthcare Management</div>
                  </td>
                </tr>
                <tr>
                  <td style="padding:30px 28px;">
                    <h1 style="margin:0 0 16px;font-size:22px;line-height:1.3;color:#0B2545;">{title}</h1>
                    <p style="margin:0 0 14px;font-size:15px;line-height:1.6;">{greeting}</p>
                    <p style="margin:0 0 24px;font-size:15px;line-height:1.6;color:#334155;">{intro}</p>
                    <table role="presentation" cellspacing="0" cellpadding="0" style="margin:0 0 24px;">
                      <tr>
                        <td style="background:#1A8A4A;border-radius:8px;">
                          <a href="{button_url}" style="display:inline-block;padding:13px 22px;color:#ffffff;text-decoration:none;font-weight:700;font-size:15px;">{button_text}</a>
                        </td>
                      </tr>
                    </table>
                    <p style="margin:0 0 14px;font-size:13px;line-height:1.6;color:#64748b;">{note}</p>
                    <p style="margin:0;font-size:12px;line-height:1.6;color:#64748b;word-break:break-all;">If the button does not work, copy and paste this link into your browser:<br>{button_url}</p>
                  </td>
                </tr>
                <tr>
                  <td style="background:#f8fafc;padding:18px 28px;border-top:1px solid #e2e8f0;color:#64748b;font-size:12px;line-height:1.6;">
                    This is an automated email from MediCare+. Please do not reply to this message.
                  </td>
                </tr>
              </table>
            </td>
          </tr>
        </table>
      </body>
    </html>
    """


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


@auth.route('/login/google')
def google_login():
    client_id = os.getenv('GOOGLE_CLIENT_ID')
    if not client_id:
        flash('Google sign-in is not configured yet.', 'warning')
        return redirect(url_for('auth.login'))

    state = secrets.token_urlsafe(32)
    session['google_oauth_state'] = state
    params = {
        'client_id': client_id,
        'redirect_uri': url_for('auth.google_callback', _external=True),
        'response_type': 'code',
        'scope': 'openid email profile',
        'state': state,
        'prompt': 'select_account',
    }
    return redirect(f'{GOOGLE_AUTH_URL}?{urlencode(params)}')


@auth.route('/login/google/callback')
def google_callback():
    if request.args.get('state') != session.pop('google_oauth_state', None):
        flash('Google sign-in could not be verified. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    code = request.args.get('code')
    if not code:
        flash('Google sign-in was cancelled or failed.', 'warning')
        return redirect(url_for('auth.login'))

    client_id = os.getenv('GOOGLE_CLIENT_ID')
    client_secret = os.getenv('GOOGLE_CLIENT_SECRET')
    if not client_id or not client_secret:
        flash('Google sign-in is not configured yet.', 'warning')
        return redirect(url_for('auth.login'))

    try:
        token_res = requests.post(
            GOOGLE_TOKEN_URL,
            data={
                'code': code,
                'client_id': client_id,
                'client_secret': client_secret,
                'redirect_uri': url_for('auth.google_callback', _external=True),
                'grant_type': 'authorization_code',
            },
            timeout=10,
        )
        token_res.raise_for_status()
        access_token = token_res.json().get('access_token')
        if not access_token:
            raise ValueError('Missing Google access token')

        user_res = requests.get(
            GOOGLE_USERINFO_URL,
            headers={'Authorization': f'Bearer {access_token}'},
            timeout=10,
        )
        user_res.raise_for_status()
        google_user = user_res.json()
    except Exception:
        flash('Google sign-in failed. Please try again.', 'danger')
        return redirect(url_for('auth.login'))

    email = (google_user.get('email') or '').strip().lower()
    full_name = (google_user.get('name') or '').strip()
    email_verified = google_user.get('email_verified')
    if not email or not email_verified:
        flash('Google account email must be verified before sign-in.', 'danger')
        return redirect(url_for('auth.login'))

    patient = Patient.query.filter_by(email=email).first()
    if patient:
        if not patient.is_active:
            flash('Your account has been deactivated.', 'danger')
            return redirect(url_for('auth.login'))
        patient.is_verified = True
        db.session.commit()
        login_user(patient)
        log_event(patient.id, 'patient', 'Google_Login_Success',
                  patient.id, 'patients', request.remote_addr or '127.0.0.1')
        flash(f'Welcome back, {patient.full_name}!', 'success')
        return redirect(url_for('patient.dashboard'))

    existing_staff = (Doctor.query.filter_by(email=email).first() or
                      Admin.query.filter_by(email=email).first())
    if existing_staff:
        flash('This Google email is already used by a staff account. Please use email and password login.', 'warning')
        return redirect(url_for('auth.login'))

    session['pending_google_patient'] = {
        'email': email,
        'full_name': full_name or email.split('@')[0],
    }
    return redirect(url_for('auth.google_complete_profile'))


@auth.route('/login/google/complete-profile', methods=['GET', 'POST'])
def google_complete_profile():
    google_patient = session.get('pending_google_patient')
    if not google_patient:
        flash('Please start Google sign-up again.', 'warning')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        full_name = request.form.get('full_name', '').strip()
        date_of_birth = request.form.get('date_of_birth', '').strip()
        phone = request.form.get('phone', '').strip()

        errors = []
        if not full_name:
            errors.append('Full name is required.')
        if not date_of_birth:
            errors.append('Date of birth is required.')
        if not re.match(r'^\d{10}$', phone):
            errors.append('Phone number must be exactly 10 digits.')
        if Patient.query.filter_by(email=google_patient['email']).first():
            errors.append('An account with this email already exists. Please log in.')

        try:
            dob = datetime.strptime(date_of_birth, '%Y-%m-%d').date()
        except ValueError:
            dob = None
            errors.append('Please enter a valid date of birth.')

        if errors:
            for error in errors:
                flash(error, 'danger')
            return render_template('patient/google_complete_profile.html',
                                   title='Complete Google Sign-Up',
                                   google_patient=google_patient)

        random_password = secrets.token_urlsafe(32)
        patient = Patient(
            full_name=full_name,
            date_of_birth=dob,
            email=google_patient['email'],
            phone=phone,
            password_hash=bcrypt.generate_password_hash(random_password).decode('utf-8'),
            is_verified=True,
        )
        db.session.add(patient)
        db.session.commit()

        profile = PatientProfile(patient_id=patient.id)
        db.session.add(profile)
        db.session.commit()

        session.pop('pending_google_patient', None)
        login_user(patient)
        log_event(patient.id, 'patient', 'Google_Account_Created',
                  patient.id, 'patients', request.remote_addr or '127.0.0.1')
        flash(f'Welcome to MediCare+, {patient.full_name}!', 'success')
        return redirect(url_for('patient.dashboard'))

    return render_template('patient/google_complete_profile.html',
                           title='Complete Google Sign-Up',
                           google_patient=google_patient)


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
                html_body = build_email_button_html(
                    title='Reset your password',
                    greeting=f'Hi {user.full_name},',
                    intro='We received a request to reset the password for your MediCare+ account. Use the secure button below to create a new password.',
                    button_text='Reset Password',
                    button_url=reset_url,
                    note='This secure reset link expires in 1 hour. If you did not request a password reset, you can safely ignore this email.'
                )
                msg = Message(
                    subject  = 'MediCare+ - Reset Your Password',
                    sender   = os.getenv('MAIL_USERNAME'),
                    recipients = [email],
                    body=(
                        f"Hi {user.full_name},\n\n"
                        f"We received a request to reset the password for your MediCare+ account.\n\n"
                        f"Reset your password using this secure link. It expires in 1 hour:\n\n"
                        f"{reset_url}\n\n"
                        f"If you did not request this, you can safely ignore this email.\n\n"
                        f"- MediCare+ Team"
                    ),
                    html=html_body
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
