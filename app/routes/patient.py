from flask import Blueprint, render_template, request, redirect, url_for, flash, make_response
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import Patient, PatientProfile, Appointment, ConsultationNote, Prescription, ChatMessage, SymptomLog
from datetime import datetime, date
from app.ai_engine.symptom_checker import predict_disease, classify_urgency, get_all_symptoms

patient = Blueprint('patient', __name__)


@patient.route('/patient/dashboard')
@login_required
def dashboard():
    from flask import current_app
    # Expire any overdue appointments before showing the dashboard
    try:
        current_app.auto_expire_appointments()
    except Exception:
        pass

    today = date.today()

    upcoming_appointments = Appointment.query.filter_by(
        patient_id=current_user.id,
        status='Upcoming'
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).count()

    records = ConsultationNote.query.filter_by(
        patient_id=current_user.id
    ).count()

    from app.routes.appointment import is_call_available
    call_available = {appt.id: is_call_available(appt) for appt in upcoming_appointments}

    return render_template('patient/dashboard.html',
        title='Dashboard',
        upcoming_appointments=upcoming_appointments,
        upcoming=len(upcoming_appointments),
        prescriptions=prescriptions,
        records=records,
        today=today,
        call_available=call_available
    )


@patient.route('/patient/profile', methods=['GET', 'POST'])
@login_required
def profile():
    patient_profile = PatientProfile.query.filter_by(
        patient_id=current_user.id
    ).first()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            phone           = request.form.get('phone', '').strip()
            home_address    = request.form.get('home_address', '').strip()
            emergency_name  = request.form.get('emergency_name', '').strip()
            emergency_phone = request.form.get('emergency_phone', '').strip()

            current_user.phone = phone
            db.session.commit()

            if patient_profile:
                patient_profile.home_address    = home_address
                patient_profile.emergency_name  = emergency_name
                patient_profile.emergency_phone = emergency_phone
            else:
                patient_profile = PatientProfile(
                    patient_id      = current_user.id,
                    home_address    = home_address,
                    emergency_name  = emergency_name,
                    emergency_phone = emergency_phone
                )
                db.session.add(patient_profile)

            db.session.commit()
            flash('Profile updated successfully!', 'success')
            return redirect(url_for('patient.profile'))

        elif action == 'change_password':
            current_password = request.form.get('current_password', '')
            new_password     = request.form.get('new_password', '')
            confirm_password = request.form.get('confirm_password', '')

            if not bcrypt.check_password_hash(current_user.password_hash, current_password):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('patient.profile'))

            if len(new_password) < 8:
                flash('New password must be at least 8 characters.', 'danger')
                return redirect(url_for('patient.profile'))

            if new_password != confirm_password:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('patient.profile'))

            current_user.password_hash = bcrypt.generate_password_hash(
                new_password).decode('utf-8')
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('patient.profile'))

    return render_template('patient/profile.html',
        title='My Profile',
        profile=patient_profile
    )


@patient.route('/patient/records')
@login_required
def records():
    appointments = Appointment.query.filter_by(
        patient_id=current_user.id,
        status='Completed'
    ).order_by(Appointment.appointment_date.desc()).all()

    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).order_by(Prescription.issued_at.desc()).all()

    return render_template('patient/records.html',
        title='Medical Records',
        appointments=appointments,
        prescriptions=prescriptions
    )


@patient.route('/patient/symptoms', methods=['GET', 'POST'])
@login_required
def symptoms():
    all_symptoms = get_all_symptoms()

    if request.method == 'POST':
        selected_symptoms = request.form.getlist('symptoms')
        free_text = request.form.get('free_text', '').strip()

        if free_text:
            words = free_text.lower().replace(' ', '_').split(',')
            selected_symptoms.extend([w.strip() for w in words])

        if not selected_symptoms:
            flash('Please enter or select at least one symptom.', 'danger')
            return redirect(url_for('patient.symptoms'))

        predictions = predict_disease(selected_symptoms)
        urgency = classify_urgency(predictions, selected_symptoms)

        if not predictions:
            flash('Could not identify symptoms. Please try different symptom names.', 'warning')
            return redirect(url_for('patient.symptoms'))

        from app.models import SymptomLog
        log = SymptomLog(
            patient_id           = current_user.id,
            input_text           = ', '.join(selected_symptoms),
            predicted_conditions = predictions,
            urgency_level        = urgency,
            booked_after         = False
        )
        db.session.add(log)
        db.session.commit()

        return render_template('patient/symptom_results.html',
            title='Symptom Check Results',
            predictions=predictions,
            urgency=urgency,
            symptoms=selected_symptoms,
            log_id=log.id
        )

    return render_template('patient/symptoms.html',
        title='AI Symptom Checker',
        all_symptoms=all_symptoms
    )


# ─────────────────────────────────────
# NISHAN — LIVE CHAT INBOX
# ─────────────────────────────────────

@patient.route('/patient/chats')
@login_required
def chat_inbox():
    from app.routes.chat import is_chat_open

    # All non-cancelled appointments, newest first
    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).filter(
        Appointment.status != 'Cancelled'
    ).order_by(Appointment.appointment_date.desc()).all()

    # Count unread messages from doctor per appointment
    unread_counts = {}
    last_messages = {}
    for appt in appointments:
        unread_counts[appt.id] = ChatMessage.query.filter_by(
            appointment_id=appt.id,
            sender_role='doctor',
            is_read=False
        ).count()
        last_messages[appt.id] = ChatMessage.query.filter_by(
            appointment_id=appt.id
        ).order_by(ChatMessage.sent_at.desc()).first()

    # Check if chat window is open per appointment
    chat_open_map = {appt.id: is_chat_open(appt) for appt in appointments}

    total_unread = sum(unread_counts.values())

    return render_template('chat/patient_inbox.html',
        title='My Chats',
        appointments=appointments,
        unread_counts=unread_counts,
        last_messages=last_messages,
        chat_open_map=chat_open_map,
        total_unread=total_unread,
    )


@patient.route('/patient/records/pdf')
@login_required
def download_records_pdf():
    from app.pdf_reports import generate_patient_pdf

    appointments = Appointment.query.filter_by(
        patient_id=current_user.id
    ).order_by(Appointment.appointment_date.desc()).all()

    profile = PatientProfile.query.filter_by(patient_id=current_user.id).first()

    symptom_logs = SymptomLog.query.filter_by(
        patient_id=current_user.id
    ).order_by(SymptomLog.checked_at.desc()).limit(20).all()

    pdf_bytes = generate_patient_pdf(current_user, appointments, profile, symptom_logs)

    response = make_response(pdf_bytes)
    response.headers['Content-Type'] = 'application/pdf'
    filename = f"MediCarePlus_Records_{current_user.full_name.replace(' ', '_')}.pdf"
    response.headers['Content-Disposition'] = f'attachment; filename="{filename}"'
    return response