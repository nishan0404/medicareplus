from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import Doctor, Appointment, Patient, ConsultationNote, Prescription, ChatMessage, DoctorAvailability
from datetime import datetime, date, timedelta

doctor = Blueprint('doctor', __name__)

DOCTOR_SLOT_OPTIONS = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30',
]


@doctor.route('/doctor/dashboard')
@login_required
def dashboard():
    if current_user.role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    from flask import current_app
    try:
        current_app.auto_expire_appointments()
    except Exception:
        pass

    today     = date.today()
    today_str = today.strftime('%A, %d %B %Y')
    week_end  = today + timedelta(days=7)

    # Today's appointments
    todays_appts = Appointment.query.filter_by(
        doctor_id        = current_user.id,
        appointment_date = today,
    ).order_by(Appointment.appointment_time.asc()).all()

    # Upcoming appointments (next 7 days, excluding today)
    upcoming_appts = Appointment.query.filter(
        Appointment.doctor_id        == current_user.id,
        Appointment.appointment_date >  today,
        Appointment.appointment_date <= week_end,
        Appointment.status.in_(['Upcoming']),
    ).order_by(Appointment.appointment_date.asc(),
               Appointment.appointment_time.asc()).all()

    total_today     = len(todays_appts)
    upcoming_today  = sum(1 for a in todays_appts if a.status == 'Upcoming')
    in_progress_today = sum(1 for a in todays_appts if a.status == 'In-Progress')
    completed_today = sum(1 for a in todays_appts if a.status == 'Completed')

    from app.routes.appointment import is_call_available, is_chat_available
    call_available = {a.id: is_call_available(a) for a in todays_appts}
    chat_available = {a.id: is_chat_available(a) for a in todays_appts}

    # This week's stats (Mon–Sun of current week)
    week_start = today - timedelta(days=today.weekday())
    week_appts = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.appointment_date >= week_start,
        Appointment.appointment_date <= today,
    ).all()
    week_total     = len(week_appts)
    week_completed = sum(1 for a in week_appts if a.status == 'Completed')
    week_cancelled = sum(1 for a in week_appts if a.status == 'Cancelled')
    week_rescheduled = 0  # placeholder — no reschedule concept yet

    # Appointments with no notes yet (completed but missing ConsultationNote)
    pending_notes = Appointment.query.filter(
        Appointment.doctor_id == current_user.id,
        Appointment.status == 'Completed',
    ).filter(
        ~Appointment.notes.has()
    ).order_by(Appointment.appointment_date.desc()).limit(5).all()

    return render_template('doctor/dashboard.html',
        title             = 'Doctor Dashboard',
        today             = today_str,
        today_date        = today,
        appointments      = todays_appts,
        upcoming_appts    = upcoming_appts,
        total_today       = total_today,
        upcoming_today    = upcoming_today,
        in_progress_today = in_progress_today,
        completed_today   = completed_today,
        call_available    = call_available,
        chat_available    = chat_available,
        week_total        = week_total,
        week_completed    = week_completed,
        week_cancelled    = week_cancelled,
        week_rescheduled  = week_rescheduled,
        pending_notes     = pending_notes,
    )


@doctor.route('/doctor/appointment/<int:appointment_id>/status', methods=['POST'])
@login_required
def update_status(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    new_status = request.form.get('status')
    if new_status in ('In-Progress', 'Completed', 'No-Show'):
        appt.status = new_status
        if new_status == 'Completed':
            appt.completed_at = datetime.now()
        db.session.commit()
        flash(f'Appointment marked as {new_status}.', 'success')

    return redirect(url_for('doctor.dashboard'))


@doctor.route('/doctor/appointment/<int:appointment_id>/notes', methods=['GET', 'POST'])
@login_required
def write_notes(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    existing_note = ConsultationNote.query.filter_by(appointment_id=appointment_id).first()

    if request.method == 'POST':
        diagnosis  = request.form.get('diagnosis', '').strip()
        notes_text = request.form.get('notes', '').strip()
        follow_up  = request.form.get('follow_up_date') or None
        no_notes   = request.form.get('no_notes') == 'on'

        if not no_notes and not diagnosis:
            flash('Diagnosis is required unless marking as no notes recorded.', 'danger')
            return render_template('doctor/notes.html', title='Write Notes',
                                   appt=appt, existing_note=existing_note)

        if existing_note:
            existing_note.diagnosis         = diagnosis
            existing_note.notes             = notes_text
            existing_note.follow_up_date    = follow_up
            existing_note.no_notes_recorded = no_notes
        else:
            new_note = ConsultationNote(
                appointment_id    = appointment_id,
                doctor_id         = current_user.id,
                patient_id        = appt.patient_id,
                diagnosis         = diagnosis,
                notes             = notes_text,
                follow_up_date    = follow_up,
                no_notes_recorded = no_notes,
            )
            db.session.add(new_note)

        appt.status       = 'Completed'
        appt.completed_at = datetime.now()
        db.session.commit()
        flash('Notes saved and appointment completed.', 'success')
        return redirect(url_for('doctor.dashboard'))

    return render_template('doctor/notes.html',
        title         = 'Write Notes',
        appt          = appt,
        existing_note = existing_note,
    )


@doctor.route('/doctor/appointment/<int:appointment_id>/prescriptions', methods=['GET', 'POST'])
@login_required
def prescribe(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('doctor.dashboard'))

    prescriptions = Prescription.query.filter_by(appointment_id=appointment_id).all()

    if request.method == 'POST':
        medication   = request.form.get('medication_name', '').strip()[:150]
        dosage       = request.form.get('dosage', '').strip()[:100]
        frequency    = request.form.get('frequency', '').strip()[:100]
        instructions = request.form.get('instructions', '').strip()[:500]

        try:
            duration = int(request.form.get('duration_days', 0))
            if duration < 1 or duration > 365:
                raise ValueError
        except (ValueError, TypeError):
            flash('Duration must be between 1 and 365 days.', 'danger')
            return redirect(url_for('doctor.prescribe', appointment_id=appointment_id))

        if not medication or not dosage or not frequency:
            flash('Medication name, dosage, and frequency are required.', 'danger')
            return redirect(url_for('doctor.prescribe', appointment_id=appointment_id))

        new_rx = Prescription(
            appointment_id  = appointment_id,
            doctor_id       = current_user.id,
            patient_id      = appt.patient_id,
            medication_name = medication,
            dosage          = dosage,
            frequency       = frequency,
            duration_days   = duration,
            instructions    = instructions,
        )
        db.session.add(new_rx)
        db.session.commit()
        flash('Prescription added.', 'success')
        return redirect(url_for('doctor.prescribe', appointment_id=appointment_id))

    return render_template('doctor/prescribe.html',
        title         = 'Prescriptions',
        appt          = appt,
        prescriptions = prescriptions,
    )


@doctor.route('/doctor/chats')
@login_required
def chat_inbox():
    if current_user.role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    from app.routes.chat import is_chat_open

    # All non-cancelled appointments for this doctor, newest first
    appointments = Appointment.query.filter_by(
        doctor_id=current_user.id
    ).filter(
        Appointment.status != 'Cancelled'
    ).order_by(Appointment.appointment_date.desc()).all()

    unread_counts = {}
    last_messages = {}
    for appt in appointments:
        unread_counts[appt.id] = ChatMessage.query.filter_by(
            appointment_id=appt.id,
            sender_role='patient',
            is_read=False
        ).count()
        last_messages[appt.id] = ChatMessage.query.filter_by(
            appointment_id=appt.id
        ).order_by(ChatMessage.sent_at.desc()).first()

    chat_open_map = {appt.id: is_chat_open(appt) for appt in appointments}
    total_unread  = sum(unread_counts.values())

    return render_template('chat/doctor_inbox.html',
        title        = 'Patient Chats',
        appointments = appointments,
        unread_counts= unread_counts,
        last_messages= last_messages,
        chat_open_map= chat_open_map,
        total_unread = total_unread,
        today        = date.today(),
    )


@doctor.route('/doctor/prescription/<int:rx_id>/delete', methods=['POST'])
@login_required
def delete_prescription(rx_id):
    rx = Prescription.query.get_or_404(rx_id)
    if rx.doctor_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    appt_id = rx.appointment_id
    db.session.delete(rx)
    db.session.commit()
    flash('Prescription removed.', 'success')
    return redirect(url_for('doctor.prescribe', appointment_id=appt_id))


@doctor.route('/doctor/patient/<int:patient_id>/history')
@login_required
def patient_history(patient_id):
    if current_user.role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    patient = Patient.query.get_or_404(patient_id)

    # Only show appointments where this doctor was involved
    appointments = Appointment.query.filter_by(
        patient_id = patient_id,
        doctor_id  = current_user.id,
    ).order_by(Appointment.appointment_date.desc()).all()

    if not appointments:
        flash('No appointments found between you and this patient.', 'info')
        return redirect(url_for('doctor.dashboard'))

    notes = ConsultationNote.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id,
    ).order_by(ConsultationNote.created_at.desc()).all()

    prescriptions = Prescription.query.filter_by(
        patient_id=patient_id,
        doctor_id=current_user.id,
    ).order_by(Prescription.issued_at.desc()).all()

    return render_template('doctor/patient_history.html',
        title        = f'History — {patient.full_name}',
        patient      = patient,
        appointments = appointments,
        notes        = notes,
        prescriptions= prescriptions,
    )


@doctor.route('/doctor/profile', methods=['GET', 'POST'])
@login_required
def profile():
    if current_user.role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            full_name      = request.form.get('full_name', '').strip()
            specialisation = request.form.get('specialisation', '').strip()
            phone          = request.form.get('phone', '').strip()
            bio            = request.form.get('bio', '').strip()

            if not full_name or not specialisation:
                flash('Name and specialisation are required.', 'danger')
                return redirect(url_for('doctor.profile'))

            current_user.full_name      = full_name[:100]
            current_user.specialisation = specialisation[:100]
            current_user.phone          = phone[:20]
            current_user.bio            = bio[:1000]
            db.session.commit()
            flash('Profile updated successfully.', 'success')

        elif action == 'change_password':
            current_pw = request.form.get('current_password', '')
            new_pw     = request.form.get('new_password', '')
            confirm_pw = request.form.get('confirm_password', '')

            if not bcrypt.check_password_hash(current_user.password_hash, current_pw):
                flash('Current password is incorrect.', 'danger')
                return redirect(url_for('doctor.profile'))

            if len(new_pw) < 8:
                flash('New password must be at least 8 characters.', 'danger')
                return redirect(url_for('doctor.profile'))

            if new_pw != confirm_pw:
                flash('New passwords do not match.', 'danger')
                return redirect(url_for('doctor.profile'))

            current_user.password_hash = bcrypt.generate_password_hash(new_pw).decode('utf-8')
            db.session.commit()
            flash('Password changed successfully.', 'success')

        return redirect(url_for('doctor.profile'))

    total_patients = db.session.query(Appointment.patient_id).filter_by(
        doctor_id=current_user.id
    ).distinct().count()

    total_appointments = Appointment.query.filter_by(doctor_id=current_user.id).count()
    availability_slots = DoctorAvailability.query.filter(
        DoctorAvailability.doctor_id == current_user.id,
        DoctorAvailability.slot_date >= date.today(),
    ).order_by(
        DoctorAvailability.slot_date.asc(),
        DoctorAvailability.slot_time.asc(),
    ).limit(20).all()

    return render_template('doctor/profile.html',
        title             = 'My Profile',
        total_patients    = total_patients,
        total_appointments= total_appointments,
        availability_slots= availability_slots,
        slot_options      = DOCTOR_SLOT_OPTIONS,
        today             = date.today().strftime('%Y-%m-%d'),
    )


@doctor.route('/doctor/availability', methods=['POST'])
@login_required
def availability():
    if current_user.role != 'doctor':
        flash('Access denied.', 'danger')
        return redirect(url_for('auth.login'))

    action = request.form.get('action')

    if action == 'add_slots':
        slot_date = request.form.get('slot_date')
        slot_times = request.form.getlist('slot_times')

        try:
            slot_date_obj = datetime.strptime(slot_date, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            flash('Please choose a valid availability date.', 'danger')
            return redirect(url_for('doctor.profile'))

        if slot_date_obj < date.today():
            flash('Availability cannot be added for a past date.', 'danger')
            return redirect(url_for('doctor.profile'))

        if not slot_times:
            flash('Please select at least one time slot.', 'danger')
            return redirect(url_for('doctor.profile'))

        added_count = 0
        for slot_time in slot_times:
            if slot_time not in DOCTOR_SLOT_OPTIONS:
                continue
            slot_time_obj = datetime.strptime(slot_time, '%H:%M').time()
            existing = DoctorAvailability.query.filter_by(
                doctor_id=current_user.id,
                slot_date=slot_date_obj,
                slot_time=slot_time_obj,
            ).first()
            if existing:
                if not existing.is_booked:
                    existing.is_available = True
                continue
            db.session.add(DoctorAvailability(
                doctor_id=current_user.id,
                slot_date=slot_date_obj,
                slot_time=slot_time_obj,
                is_available=True,
                is_booked=False,
            ))
            added_count += 1

        db.session.commit()
        flash(f'Availability saved. {added_count} new slot(s) added.', 'success')

    elif action == 'remove_slot':
        slot_id = request.form.get('slot_id')
        slot = DoctorAvailability.query.filter_by(
            id=slot_id,
            doctor_id=current_user.id,
        ).first()
        if not slot:
            flash('Availability slot not found.', 'danger')
            return redirect(url_for('doctor.profile'))
        if slot.is_booked:
            flash('Booked slots cannot be removed. Reschedule or cancel the appointment first.', 'danger')
            return redirect(url_for('doctor.profile'))
        db.session.delete(slot)
        db.session.commit()
        flash('Availability slot removed.', 'success')

    return redirect(url_for('doctor.profile'))
