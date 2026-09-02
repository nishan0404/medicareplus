from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from flask_mail import Message
from app import db, mail, socketio
from app.models import Appointment, Doctor, DoctorAvailability, Patient, CallSession, Cancellation, EmailLog
from datetime import datetime, date, timedelta
import stripe
import os
import uuid

appointment = Blueprint('appointment', __name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
CONSULTATION_FEE = 7500
DEFAULT_TIME_SLOTS = [
    '09:00', '09:30', '10:00', '10:30', '11:00', '11:30',
    '13:00', '13:30', '14:00', '14:30', '15:00', '15:30',
    '16:00', '16:30',
]


def build_email_card_html(title, greeting, intro, details, footer_note):
    rows = ''.join(
        f"""
        <tr>
          <td style="padding:10px 0;color:#64748b;font-size:14px;border-bottom:1px solid #e2e8f0;">{label}</td>
          <td style="padding:10px 0;color:#0f172a;font-size:14px;font-weight:700;text-align:right;border-bottom:1px solid #e2e8f0;">{value}</td>
        </tr>
        """
        for label, value in details
    )
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
                    <p style="margin:0 0 22px;font-size:15px;line-height:1.6;color:#334155;">{intro}</p>
                    <table role="presentation" width="100%" cellspacing="0" cellpadding="0" style="background:#f8fafc;border:1px solid #e2e8f0;border-radius:10px;padding:6px 16px;margin-bottom:20px;">
                      {rows}
                    </table>
                    <p style="margin:0;font-size:13px;line-height:1.6;color:#64748b;">{footer_note}</p>
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


def send_appointment_email(appt, recipient_email, email_type, subject,
                           html_body, text_body):
    status = 'Sent'
    try:
        msg = Message(
            subject=subject,
            sender=os.getenv('MAIL_USERNAME'),
            recipients=[recipient_email],
            body=text_body,
            html=html_body,
        )
        mail.send(msg)
    except Exception:
        status = 'Failed'

    email_log = EmailLog(
        appointment_id=appt.id,
        recipient_email=recipient_email,
        email_type=email_type,
        status=status,
    )
    db.session.add(email_log)
    db.session.commit()
    return status == 'Sent'


def send_booking_confirmation_email(appt):
    patient = appt.patient
    doctor = appt.doctor
    common_details = [
        ('Doctor', doctor.full_name),
        ('Specialisation', doctor.specialisation),
        ('Patient', patient.full_name),
        ('Date', appt.appointment_date.strftime('%A, %d %B %Y')),
        ('Time', appt.appointment_time.strftime('%I:%M %p')),
        ('Appointment Type', appt.appointment_type),
        ('Payment Status', appt.payment_status),
        ('Amount Paid', f'${float(appt.amount_paid):.2f} AUD'),
    ]
    if appt.reason:
        common_details.append(('Reason', appt.reason))

    patient_html = build_email_card_html(
        title='Appointment confirmed',
        greeting=f'Hi {patient.full_name},',
        intro='Your MediCare+ appointment has been booked successfully and your payment has been received.',
        details=common_details,
        footer_note='You can view or manage this appointment from your MediCare+ dashboard.'
    )
    patient_text = (
        f"Hi {patient.full_name},\n\n"
        f"Your MediCare+ appointment has been confirmed.\n\n"
        f"Doctor: {doctor.full_name}\n"
        f"Specialisation: {doctor.specialisation}\n"
        f"Date: {appt.appointment_date.strftime('%A, %d %B %Y')}\n"
        f"Time: {appt.appointment_time.strftime('%I:%M %p')}\n"
        f"Type: {appt.appointment_type}\n"
        f"Payment Status: {appt.payment_status}\n"
        f"Amount Paid: ${float(appt.amount_paid):.2f} AUD\n\n"
        f"You can view this appointment from your MediCare+ dashboard.\n\n"
        f"- MediCare+ Team"
    )
    patient_sent = send_appointment_email(
        appt,
        patient.email,
        'Appointment_Confirmation_Patient',
        'MediCare+ Appointment Confirmation',
        patient_html,
        patient_text,
    )

    doctor_html = build_email_card_html(
        title='New appointment booked',
        greeting=f'Hi {doctor.full_name},',
        intro='A patient has booked and paid for a MediCare+ appointment with you.',
        details=common_details,
        footer_note='Please review your doctor dashboard before the consultation time.'
    )
    doctor_text = (
        f"Hi {doctor.full_name},\n\n"
        f"A patient has booked and paid for a MediCare+ appointment with you.\n\n"
        f"Patient: {patient.full_name}\n"
        f"Date: {appt.appointment_date.strftime('%A, %d %B %Y')}\n"
        f"Time: {appt.appointment_time.strftime('%I:%M %p')}\n"
        f"Type: {appt.appointment_type}\n"
        f"Reason: {appt.reason or 'Not provided'}\n"
        f"Payment Status: {appt.payment_status}\n\n"
        f"Please review your doctor dashboard before the consultation time.\n\n"
        f"- MediCare+ Team"
    )
    doctor_sent = send_appointment_email(
        appt,
        doctor.email,
        'Appointment_Confirmation_Doctor',
        'MediCare+ New Appointment Booked',
        doctor_html,
        doctor_text,
    )
    return patient_sent and doctor_sent


def is_call_available(appt):
    """Call available all day on appointment date for Video Call appointments only."""
    appt_type = getattr(appt, 'appointment_type', None) or 'In-person'
    if appt_type != 'Video Call':
        return False
    if appt.status == 'Cancelled':
        return False
    return appt.appointment_date == date.today()


def is_chat_available(appt):
    """Chat available all day on appointment date (and day after for completed ones)."""
    if appt.status == 'Cancelled':
        return False
    today = date.today()
    # Allow chat on the appointment day, and the day after if completed
    if appt.appointment_date == today:
        return True
    if appt.status == 'Completed' and appt.appointment_date == today - timedelta(days=1):
        return True
    return False


def create_call_session(appt, call_type):
    old = CallSession.query.filter_by(appointment_id=appt.id).first()
    if old:
        db.session.delete(old)
        db.session.flush()
    new_call = CallSession(
        appointment_id=appt.id,
        patient_id=appt.patient_id,
        doctor_id=appt.doctor_id,
        room_id=str(uuid.uuid4()),
        call_type=call_type,
        status='waiting',
    )
    db.session.add(new_call)
    db.session.commit()
    return new_call


def notify_incoming_call(appt, call_session, caller_role):
    """Send a real-time incoming call notification to the other appointment user."""
    if caller_role == 'patient':
        target_room = f'user:doctor:{appt.doctor_id}'
        caller_name = appt.patient.full_name if appt.patient else 'Patient'
    else:
        target_room = f'user:patient:{appt.patient_id}'
        caller_name = appt.doctor.full_name if appt.doctor else 'Doctor'

    socketio.emit(
        'incoming_call',
        {
            'room_id': call_session.room_id,
            'appointment_id': appt.id,
            'call_type': call_session.call_type,
            'caller_role': caller_role,
            'caller_name': caller_name,
            'join_url': url_for('call.room', room_id=call_session.room_id),
        },
        room=target_room,
        namespace='/call',
    )


def get_booking_slot_maps(doctors):
    doctor_ids = [doctor.id for doctor in doctors]
    availability_map = {}
    booked_slots = {}
    custom_doctor_ids = []

    if doctor_ids:
        custom_doctor_ids = [
            str(row[0]) for row in db.session.query(DoctorAvailability.doctor_id)
            .filter(
                DoctorAvailability.doctor_id.in_(doctor_ids),
                DoctorAvailability.slot_date >= date.today(),
                DoctorAvailability.is_available == True,
            )
            .distinct()
            .all()
        ]

        available_slots = DoctorAvailability.query.filter(
            DoctorAvailability.doctor_id.in_(doctor_ids),
            DoctorAvailability.slot_date >= date.today(),
            DoctorAvailability.is_available == True,
            DoctorAvailability.is_booked == False,
        ).order_by(DoctorAvailability.slot_date.asc(), DoctorAvailability.slot_time.asc()).all()

        for slot in available_slots:
            doctor_key = str(slot.doctor_id)
            date_key = slot.slot_date.strftime('%Y-%m-%d')
            availability_map.setdefault(doctor_key, {}).setdefault(date_key, []).append(
                slot.slot_time.strftime('%H:%M')
            )

        current_bookings = Appointment.query.filter(
            Appointment.doctor_id.in_(doctor_ids),
            Appointment.appointment_date >= date.today(),
            Appointment.status != 'Cancelled',
        ).all()

        for appt in current_bookings:
            doctor_key = str(appt.doctor_id)
            date_key = appt.appointment_date.strftime('%Y-%m-%d')
            booked_slots.setdefault(doctor_key, {}).setdefault(date_key, []).append(
                appt.appointment_time.strftime('%H:%M')
            )

    return availability_map, booked_slots, custom_doctor_ids


def update_availability_booking(appt, is_booked):
    slot = DoctorAvailability.query.filter_by(
        doctor_id=appt.doctor_id,
        slot_date=appt.appointment_date,
        slot_time=appt.appointment_time,
    ).first()
    if slot:
        slot.is_booked = is_booked
        slot.appointment_id = appt.id if is_booked else None


@appointment.route('/patient/book', methods=['GET', 'POST'])
@login_required
def book():
    doctors = Doctor.query.filter_by(is_active=True).all()
    specialisations = list(set([d.specialisation for d in doctors]))
    availability_map, booked_slots, custom_doctor_ids = get_booking_slot_maps(doctors)

    if request.method == 'POST':
        doctor_id        = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason           = request.form.get('reason', '').strip()
        appointment_type = request.form.get('appointment_type', 'In-person')

        if not doctor_id or not appointment_date or not appointment_time:
            flash('Please select a doctor, date and time.', 'danger')
            return redirect(url_for('appointment.book'))

        # Validate date/time is not in the past
        try:
            appt_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
            appt_time_obj = datetime.strptime(appointment_time, '%H:%M').time()
        except ValueError:
            flash('Invalid date or time format.', 'danger')
            return redirect(url_for('appointment.book'))

        selected_datetime = datetime.combine(appt_date_obj, appt_time_obj)
        if selected_datetime <= datetime.now():
            flash('You cannot book an appointment in the past.', 'danger')
            return redirect(url_for('appointment.book'))

        # Validate reason length
        if len(reason) > 300:
            flash('Reason must be 300 characters or fewer.', 'danger')
            return redirect(url_for('appointment.book'))

        # Validate doctor exists and is active
        doctor_obj = Doctor.query.filter_by(id=doctor_id, is_active=True).first()
        if not doctor_obj:
            flash('Selected doctor is not available.', 'danger')
            return redirect(url_for('appointment.book'))

        existing = Appointment.query.filter_by(
            doctor_id=doctor_id,
            appointment_date=appointment_date,
            appointment_time=appointment_time
        ).filter(Appointment.status != 'Cancelled').first()

        if existing:
            flash('This time slot is no longer available.', 'danger')
            return redirect(url_for('appointment.book'))

        doctor_slots_for_date = availability_map.get(str(doctor_id), {}).get(appointment_date, [])
        doctor_has_custom_availability = str(doctor_id) in custom_doctor_ids
        if doctor_has_custom_availability and appointment_time not in doctor_slots_for_date:
            flash('Please choose one of the doctor’s available time slots.', 'danger')
            return redirect(url_for('appointment.book'))

        session['pending_booking'] = {
            'doctor_id': int(doctor_id),
            'appointment_date': appointment_date,
            'appointment_time': appointment_time,
            'reason': reason,
            'appointment_type': appointment_type
        }
        return redirect(url_for('appointment.checkout'))

    return render_template('patient/book.html',
        title='Book Appointment',
        doctors=doctors,
        specialisations=sorted(specialisations),
        availability_map=availability_map,
        booked_slots=booked_slots,
        default_slots=DEFAULT_TIME_SLOTS,
        custom_doctor_ids=custom_doctor_ids,
        today=date.today().strftime('%Y-%m-%d')
    )


@appointment.route('/patient/checkout')
@login_required
def checkout():
    booking = session.get('pending_booking')
    if not booking:
        flash('No pending booking found.', 'danger')
        return redirect(url_for('appointment.book'))
    doctor    = Doctor.query.get_or_404(booking['doctor_id'])
    appt_date = datetime.strptime(booking['appointment_date'], '%Y-%m-%d').date()
    appt_time = datetime.strptime(booking['appointment_time'], '%H:%M').time()
    if datetime.combine(appt_date, appt_time) <= datetime.now():
        session.pop('pending_booking', None)
        flash('This appointment time has already passed. Please choose a future time.', 'danger')
        return redirect(url_for('appointment.book'))
    return render_template('patient/checkout.html',
        title='Payment', doctor=doctor,
        appt_date=appt_date, appt_time=appt_time,
        reason=booking.get('reason', ''),
        fee=CONSULTATION_FEE / 100,
        stripe_publishable_key=STRIPE_PUBLISHABLE_KEY
    )


@appointment.route('/patient/create-payment-intent', methods=['POST'])
@login_required
def create_payment_intent():
    booking = session.get('pending_booking')
    if not booking:
        return jsonify({'error': 'No pending booking'}), 400
    try:
        doctor = Doctor.query.get(booking['doctor_id'])
        intent = stripe.PaymentIntent.create(
            amount=CONSULTATION_FEE, currency='aud',
            metadata={
                'patient_id': current_user.id,
                'patient_name': current_user.full_name,
                'doctor_id': booking['doctor_id'],
                'doctor_name': doctor.full_name if doctor else '',
                'appt_date': booking['appointment_date'],
                'appt_time': booking['appointment_time'],
            }
        )
        return jsonify({'clientSecret': intent['client_secret']})
    except stripe.error.StripeError as e:
        return jsonify({'error': str(e)}), 400


@appointment.route('/patient/payment-success', methods=['POST'])
@login_required
def payment_success():
    booking           = session.get('pending_booking')
    payment_intent_id = request.form.get('payment_intent_id')
    if not booking:
        flash('Session expired.', 'danger')
        return redirect(url_for('appointment.book'))
    try:
        intent = stripe.PaymentIntent.retrieve(payment_intent_id)
        if intent['status'] != 'succeeded':
            flash('Payment not completed.', 'danger')
            return redirect(url_for('appointment.checkout'))
    except stripe.error.StripeError as e:
        flash(f'Payment failed: {str(e)}', 'danger')
        return redirect(url_for('appointment.checkout'))

    existing = Appointment.query.filter_by(
        doctor_id=booking['doctor_id'],
        appointment_date=booking['appointment_date'],
        appointment_time=booking['appointment_time']
    ).filter(Appointment.status != 'Cancelled').first()

    if existing:
        flash('Slot just taken. Please contact us for a refund.', 'danger')
        session.pop('pending_booking', None)
        return redirect(url_for('appointment.book'))

    appt_date = datetime.strptime(booking['appointment_date'], '%Y-%m-%d').date()
    appt_time = datetime.strptime(booking['appointment_time'], '%H:%M').time()

    new_appointment = Appointment(
        patient_id=current_user.id,
        doctor_id=booking['doctor_id'],
        appointment_date=appt_date,
        appointment_time=appt_time,
        reason=booking.get('reason', ''),
        appointment_type=booking.get('appointment_type', 'In-person'),
        status='Upcoming',
        payment_intent_id=payment_intent_id,
        payment_status='Paid',
        amount_paid=CONSULTATION_FEE / 100
    )
    db.session.add(new_appointment)
    db.session.commit()
    update_availability_booking(new_appointment, True)
    db.session.commit()
    send_booking_confirmation_email(new_appointment)
    session.pop('pending_booking', None)
    flash('Appointment booked!', 'success')
    return redirect(url_for('appointment.booking_confirmation', appointment_id=new_appointment.id))


@appointment.route('/patient/booking-confirmation/<int:appointment_id>')
@login_required
def booking_confirmation(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.patient_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('appointment.my_appointments'))
    return render_template('patient/booking_confirmation.html',
        title='Booking Confirmed', appt=appt, fee=CONSULTATION_FEE / 100)


@appointment.route('/patient/appointments')
@login_required
def my_appointments():
    from flask import current_app
    try:
        current_app.auto_expire_appointments()
    except Exception:
        pass

    today = date.today()

    upcoming = Appointment.query.filter(
        Appointment.patient_id == current_user.id,
        Appointment.status.in_(['Upcoming', 'In-Progress'])
    ).order_by(Appointment.appointment_date.asc(), Appointment.appointment_time.asc()).all()

    past = Appointment.query.filter_by(
        patient_id=current_user.id
    ).filter(Appointment.status.in_(['Completed', 'Cancelled', 'No-Show'])
    ).order_by(Appointment.appointment_date.desc()).all()

    # Both call and chat availability — only today's appointments can have these
    call_available = {appt.id: is_call_available(appt) for appt in upcoming}
    chat_available = {appt.id: is_chat_available(appt) for appt in upcoming}

    return render_template('patient/appointments.html',
        title='My Appointments',
        upcoming=upcoming, past=past,
        today=today,
        call_available=call_available,
        chat_available=chat_available,
        default_slots=DEFAULT_TIME_SLOTS,
    )


@appointment.route('/patient/appointments/cancel/<int:appointment_id>', methods=['POST'])
@login_required
def cancel(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.patient_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('appointment.my_appointments'))
    appt_datetime = datetime.combine(appt.appointment_date, appt.appointment_time)
    if (appt_datetime - datetime.now()).total_seconds() < 7200:
        flash('Cannot cancel within 2 hours.', 'danger')
        return redirect(url_for('appointment.my_appointments'))
    hours_notice = (appt_datetime - datetime.now()).total_seconds() / 3600
    reason = request.form.get('cancellation_reason', '').strip()[:255]

    appt.status = 'Cancelled'
    update_availability_booking(appt, False)

    cancellation = Cancellation(
        appointment_id      = appt.id,
        cancelled_by        = current_user.id,
        cancellation_reason = reason or None,
        hours_notice_given  = round(hours_notice, 2),
    )
    db.session.add(cancellation)
    db.session.commit()
    flash('Appointment cancelled.', 'success')
    return redirect(url_for('appointment.my_appointments'))


@appointment.route('/patient/appointments/reschedule/<int:appointment_id>', methods=['POST'])
@login_required
def reschedule(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.patient_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('appointment.my_appointments'))
    if appt.status not in ('Upcoming', 'In-Progress'):
        flash('Only active appointments can be rescheduled.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    old_datetime = datetime.combine(appt.appointment_date, appt.appointment_time)
    if (old_datetime - datetime.now()).total_seconds() < 7200:
        flash('Cannot reschedule within 2 hours of the scheduled time.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    new_date = request.form.get('appointment_date')
    new_time = request.form.get('appointment_time')
    reason = request.form.get('reschedule_reason', '').strip()[:255]

    try:
        new_date_obj = datetime.strptime(new_date, '%Y-%m-%d').date()
        new_time_obj = datetime.strptime(new_time, '%H:%M').time()
    except (ValueError, TypeError):
        flash('Invalid reschedule date or time.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    if datetime.combine(new_date_obj, new_time_obj) <= datetime.now():
        flash('Please choose a future appointment time.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    existing = Appointment.query.filter_by(
        doctor_id=appt.doctor_id,
        appointment_date=new_date_obj,
        appointment_time=new_time_obj,
    ).filter(
        Appointment.id != appt.id,
        Appointment.status != 'Cancelled',
    ).first()
    if existing:
        flash('This time slot is already booked.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    available_slot = DoctorAvailability.query.filter_by(
        doctor_id=appt.doctor_id,
        slot_date=new_date_obj,
        slot_time=new_time_obj,
        is_available=True,
        is_booked=False,
    ).first()
    custom_slots_exist = DoctorAvailability.query.filter_by(
        doctor_id=appt.doctor_id,
        is_available=True,
    ).first()
    if custom_slots_exist and not available_slot:
        flash('Please choose one of the doctor’s available time slots.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    update_availability_booking(appt, False)
    appt.appointment_date = new_date_obj
    appt.appointment_time = new_time_obj
    if reason:
        appt.reason = f"{appt.reason or ''} | Rescheduled: {reason}"[:255]
    update_availability_booking(appt, True)
    db.session.commit()
    flash('Appointment rescheduled successfully.', 'success')
    return redirect(url_for('appointment.my_appointments'))


# ── PATIENT START CALL ──
@appointment.route('/patient/appointments/<int:appointment_id>/start-call/<call_type>')
@login_required
def start_call(appointment_id, call_type):
    if call_type not in ('audio', 'video'):
        flash('Invalid call type.', 'danger')
        return redirect(url_for('appointment.my_appointments'))
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.patient_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('appointment.my_appointments'))
    if not is_call_available(appt):
        flash('Call is only available on the day of your appointment.', 'warning')
        return redirect(url_for('appointment.my_appointments'))
    existing = CallSession.query.filter_by(appointment_id=appointment_id).first()
    if existing and existing.status in ('waiting', 'active'):
        notify_incoming_call(appt, existing, 'patient')
        return redirect(url_for('call.room', room_id=existing.room_id))
    new_call = create_call_session(appt, call_type)
    notify_incoming_call(appt, new_call, 'patient')
    return redirect(url_for('call.room', room_id=new_call.room_id))


# ── DOCTOR START CALL ──
@appointment.route('/doctor/appointments/<int:appointment_id>/start-call/<call_type>')
@login_required
def doctor_start_call(appointment_id, call_type):
    if call_type not in ('audio', 'video'):
        flash('Invalid call type.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    if not is_call_available(appt):
        flash('Call is only available on the day of the appointment.', 'warning')
        return redirect(url_for('doctor.dashboard'))
    existing = CallSession.query.filter_by(appointment_id=appointment_id).first()
    if existing and existing.status in ('waiting', 'active'):
        notify_incoming_call(appt, existing, 'doctor')
        return redirect(url_for('call.room', room_id=existing.room_id))
    new_call = create_call_session(appt, call_type)
    notify_incoming_call(appt, new_call, 'doctor')
    return redirect(url_for('call.room', room_id=new_call.room_id))


# ── DOCTOR JOIN CALL ──
@appointment.route('/doctor/appointments/<int:appointment_id>/join-call')
@login_required
def doctor_join_call(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    if appt.doctor_id != current_user.id:
        flash('Unauthorised.', 'danger')
        return redirect(url_for('doctor.dashboard'))
    call = CallSession.query.filter_by(appointment_id=appointment_id).first()
    if call is None or call.status == 'ended':
        flash('No active call found.', 'warning')
        return redirect(url_for('doctor.dashboard'))
    return redirect(url_for('call.room', room_id=call.room_id))
