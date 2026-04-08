from flask import Blueprint, render_template, request, redirect, url_for, flash, send_file
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import Admin, Patient, Doctor, Appointment, ConsultationNote, Prescription, AuditLog, SymptomLog, PatientProfile
from datetime import datetime, date
from functools import wraps

admin = Blueprint('admin', __name__)


# ── Admin Required Decorator ──
def admin_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated or current_user.role != 'admin':
            flash('Access denied. Admins only.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function


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


# ── Dashboard ──
@admin.route('/admin/dashboard')
@login_required
@admin_required
def dashboard():
    total_patients     = Patient.query.count()
    total_doctors      = Doctor.query.count()
    total_appointments = Appointment.query.count()
    this_month = Appointment.query.filter(
        db.extract('month', Appointment.appointment_date) == date.today().month,
        db.extract('year',  Appointment.appointment_date) == date.today().year
    ).count()
    cancelled = Appointment.query.filter_by(status='Cancelled').count()
    cancellation_rate = round((cancelled / total_appointments * 100), 1) if total_appointments > 0 else 0
    total_symptom_checks = SymptomLog.query.count()
    recent_appointments = Appointment.query.order_by(
        Appointment.created_at.desc()
    ).limit(5).all()

    return render_template('admin/dashboard.html',
        title='Admin Dashboard',
        total_patients=total_patients,
        total_doctors=total_doctors,
        total_appointments=total_appointments,
        this_month=this_month,
        cancellation_rate=cancellation_rate,
        total_symptom_checks=total_symptom_checks,
        recent_appointments=recent_appointments
    )


# ── Manage Patients ──
@admin.route('/admin/patients')
@login_required
@admin_required
def patients():
    search = request.args.get('search', '')
    page   = request.args.get('page', 1, type=int)
    q = Patient.query
    if search:
        q = q.filter(
            Patient.full_name.like(f'%{search}%') |
            Patient.email.like(f'%{search}%')
        )
    pagination  = q.order_by(Patient.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    all_patients = pagination.items

    return render_template('admin/patients.html',
        title='Manage Patients',
        patients=all_patients,
        search=search,
        pagination=pagination,
    )


# ── Edit Patient ──
@admin.route('/admin/patients/<int:patient_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    ip      = request.remote_addr or '127.0.0.1'

    if request.method == 'POST':
        full_name    = request.form.get('full_name', '').strip()
        dob_str      = request.form.get('date_of_birth', '').strip()
        email        = request.form.get('email', '').strip().lower()
        phone        = request.form.get('phone', '').strip()
        is_active    = request.form.get('is_active') == '1'
        new_password = request.form.get('new_password', '').strip()
        confirm_pw   = request.form.get('confirm_password', '').strip()

        if not full_name or not email or not phone:
            flash('Full name, email and phone are required.', 'danger')
            return render_template('admin/edit_patient.html',
                                   title='Edit Patient', patient=patient)

        # Check email not taken by another patient
        existing = Patient.query.filter(
            Patient.email == email, Patient.id != patient_id
        ).first()
        if existing:
            flash('Another patient already uses this email address.', 'danger')
            return render_template('admin/edit_patient.html',
                                   title='Edit Patient', patient=patient)

        patient.full_name = full_name
        patient.email     = email
        patient.phone     = phone
        patient.is_active = is_active

        if dob_str:
            patient.date_of_birth = datetime.strptime(dob_str, '%Y-%m-%d').date()

        # Optional password reset
        if new_password:
            if new_password != confirm_pw:
                flash('Passwords do not match.', 'danger')
                return render_template('admin/edit_patient.html',
                                       title='Edit Patient', patient=patient)
            patient.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

        db.session.commit()
        log_event(current_user.id, 'admin', 'Patient_Edited', patient_id, 'patients', ip)
        flash(f'{patient.full_name} updated successfully.', 'success')
        return redirect(url_for('admin.patients'))

    return render_template('admin/edit_patient.html',
                           title='Edit Patient', patient=patient)


# ── Activate / Deactivate Patient ──
@admin.route('/admin/patients/<int:patient_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = False
    db.session.commit()
    log_event(current_user.id, 'admin', 'Patient_Deactivated', patient_id, 'patients')
    flash(f'{patient.full_name} has been deactivated.', 'success')
    return redirect(url_for('admin.patients'))


@admin.route('/admin/patients/<int:patient_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_patient(patient_id):
    patient = Patient.query.get_or_404(patient_id)
    patient.is_active = True
    db.session.commit()
    log_event(current_user.id, 'admin', 'Patient_Activated', patient_id, 'patients')
    flash(f'{patient.full_name} has been activated.', 'success')
    return redirect(url_for('admin.patients'))


# ── Manage Doctors ──
@admin.route('/admin/doctors')
@login_required
@admin_required
def doctors():
    page       = request.args.get('page', 1, type=int)
    pagination = Doctor.query.order_by(Doctor.created_at.desc()).paginate(page=page, per_page=20, error_out=False)
    return render_template('admin/doctors.html',
        title='Manage Doctors',
        doctors=pagination.items,
        pagination=pagination,
    )


# ── Add Doctor ──
@admin.route('/admin/doctors/add', methods=['GET', 'POST'])
@login_required
@admin_required
def add_doctor():
    if request.method == 'POST':
        full_name      = request.form.get('full_name', '').strip()
        specialisation = request.form.get('specialisation', '').strip()
        email          = request.form.get('email', '').strip().lower()
        phone          = request.form.get('phone', '').strip()
        bio            = request.form.get('bio', '').strip()
        password       = request.form.get('password', '').strip()

        if not full_name or not specialisation or not email or not phone or not password:
            flash('All fields are required.', 'danger')
            return redirect(url_for('admin.add_doctor'))

        existing = Doctor.query.filter_by(email=email).first()
        if existing:
            flash('A doctor with this email already exists.', 'danger')
            return redirect(url_for('admin.add_doctor'))

        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        new_doctor = Doctor(
            full_name      = full_name,
            specialisation = specialisation,
            email          = email,
            phone          = phone,
            bio            = bio,
            password_hash  = hashed,
            is_active      = True,
            role           = 'doctor'
        )
        db.session.add(new_doctor)
        db.session.commit()
        log_event(current_user.id, 'admin', 'Doctor_Created', new_doctor.id, 'doctors')
        flash(f'Dr. {full_name} added successfully!', 'success')
        return redirect(url_for('admin.doctors'))

    return render_template('admin/add_doctor.html', title='Add Doctor')


# ── Edit Doctor ──
@admin.route('/admin/doctors/<int:doctor_id>/edit', methods=['GET', 'POST'])
@login_required
@admin_required
def edit_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    ip     = request.remote_addr or '127.0.0.1'

    if request.method == 'POST':
        full_name      = request.form.get('full_name', '').strip()
        specialisation = request.form.get('specialisation', '').strip()
        email          = request.form.get('email', '').strip().lower()
        phone          = request.form.get('phone', '').strip()
        bio            = request.form.get('bio', '').strip()
        is_active      = request.form.get('is_active') == '1'
        new_password   = request.form.get('new_password', '').strip()
        confirm_pw     = request.form.get('confirm_password', '').strip()

        if not full_name or not specialisation or not email or not phone:
            flash('Name, specialisation, email and phone are required.', 'danger')
            return render_template('admin/edit_doctor.html',
                                   title='Edit Doctor', doctor=doctor)

        existing = Doctor.query.filter(
            Doctor.email == email, Doctor.id != doctor_id
        ).first()
        if existing:
            flash('Another doctor already uses this email address.', 'danger')
            return render_template('admin/edit_doctor.html',
                                   title='Edit Doctor', doctor=doctor)

        doctor.full_name      = full_name
        doctor.specialisation = specialisation
        doctor.email          = email
        doctor.phone          = phone
        doctor.bio            = bio
        doctor.is_active      = is_active

        if new_password:
            if new_password != confirm_pw:
                flash('Passwords do not match.', 'danger')
                return render_template('admin/edit_doctor.html',
                                       title='Edit Doctor', doctor=doctor)
            doctor.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')

        db.session.commit()
        log_event(current_user.id, 'admin', 'Doctor_Edited', doctor_id, 'doctors', ip)
        flash(f'{doctor.full_name} updated successfully.', 'success')
        return redirect(url_for('admin.doctors'))

    return render_template('admin/edit_doctor.html',
                           title='Edit Doctor', doctor=doctor)


# ── Activate / Deactivate Doctor ──
@admin.route('/admin/doctors/<int:doctor_id>/deactivate', methods=['POST'])
@login_required
@admin_required
def deactivate_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_active = False
    db.session.commit()
    log_event(current_user.id, 'admin', 'Doctor_Deactivated', doctor_id, 'doctors')
    flash(f'{doctor.full_name} has been deactivated.', 'success')
    return redirect(url_for('admin.doctors'))


@admin.route('/admin/doctors/<int:doctor_id>/activate', methods=['POST'])
@login_required
@admin_required
def activate_doctor(doctor_id):
    doctor = Doctor.query.get_or_404(doctor_id)
    doctor.is_active = True
    db.session.commit()
    log_event(current_user.id, 'admin', 'Doctor_Activated', doctor_id, 'doctors')
    flash(f'{doctor.full_name} has been activated.', 'success')
    return redirect(url_for('admin.doctors'))


# ── All Appointments ──
@admin.route('/admin/appointments')
@login_required
@admin_required
def appointments():
    status_filter = request.args.get('status', '')
    page = request.args.get('page', 1, type=int)
    q = Appointment.query
    if status_filter:
        q = q.filter_by(status=status_filter)
    pagination       = q.order_by(Appointment.appointment_date.desc()).paginate(page=page, per_page=25, error_out=False)
    all_appointments = pagination.items

    return render_template('admin/appointments.html',
        title='All Appointments',
        appointments=all_appointments,
        status_filter=status_filter,
        pagination=pagination,
    )


# ── PDF: Doctor Report ──
@admin.route('/admin/doctors/<int:doctor_id>/pdf')
@login_required
@admin_required
def doctor_pdf(doctor_id):
    from app.pdf_reports import generate_doctor_pdf
    doctor = Doctor.query.get_or_404(doctor_id)
    appointments = Appointment.query.filter_by(
        doctor_id=doctor_id
    ).order_by(Appointment.appointment_date.desc()).all()

    buf = generate_doctor_pdf(doctor, appointments)
    filename = f"doctor_{doctor.full_name.replace(' ', '_')}_{date.today()}.pdf"
    log_event(current_user.id, 'admin', 'Doctor_PDF_Downloaded', doctor_id, 'doctors',
              request.remote_addr or '127.0.0.1')
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


# ── PDF: Patient Report ──
@admin.route('/admin/patients/<int:patient_id>/pdf')
@login_required
@admin_required
def patient_pdf(patient_id):
    from app.pdf_reports import generate_patient_pdf
    patient      = Patient.query.get_or_404(patient_id)
    profile      = PatientProfile.query.filter_by(patient_id=patient_id).first()
    appointments = Appointment.query.filter_by(
        patient_id=patient_id
    ).order_by(Appointment.appointment_date.desc()).all()
    symptom_logs = SymptomLog.query.filter_by(
        patient_id=patient_id
    ).order_by(SymptomLog.checked_at.desc()).all()

    buf = generate_patient_pdf(patient, appointments, profile, symptom_logs)
    filename = f"patient_{patient.full_name.replace(' ', '_')}_{date.today()}.pdf"
    log_event(current_user.id, 'admin', 'Patient_PDF_Downloaded', patient_id, 'patients',
              request.remote_addr or '127.0.0.1')
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


# ── PDF: All Appointments Report ──
@admin.route('/admin/appointments/pdf')
@login_required
@admin_required
def appointments_pdf():
    from app.pdf_reports import generate_appointments_pdf
    status_filter = request.args.get('status', '')
    if status_filter:
        all_appointments = Appointment.query.filter_by(
            status=status_filter
        ).order_by(Appointment.appointment_date.desc()).all()
    else:
        all_appointments = Appointment.query.order_by(
            Appointment.appointment_date.desc()
        ).all()

    buf = generate_appointments_pdf(all_appointments, status_filter)
    filename = f"appointments_{date.today()}.pdf"
    log_event(current_user.id, 'admin', 'Appointments_PDF_Downloaded', None, 'appointments',
              request.remote_addr or '127.0.0.1')
    return send_file(buf, mimetype='application/pdf',
                     as_attachment=True, download_name=filename)


# ── Audit Log ──
@admin.route('/admin/audit-log')
@login_required
@admin_required
def audit_log():
    page        = request.args.get('page', 1, type=int)
    role_filter = request.args.get('role', '')
    action_filter = request.args.get('action', '')

    q = AuditLog.query
    if role_filter:
        q = q.filter_by(user_role=role_filter)
    if action_filter:
        q = q.filter(AuditLog.action_type.like(f'%{action_filter}%'))

    pagination = q.order_by(AuditLog.event_timestamp.desc()).paginate(page=page, per_page=30, error_out=False)

    return render_template('admin/audit_log.html',
        title='Audit Log',
        logs=pagination.items,
        pagination=pagination,
        role_filter=role_filter,
        action_filter=action_filter,
    )