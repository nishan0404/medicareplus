from flask import Blueprint, render_template, request, redirect, url_for, flash, jsonify, session
from flask_login import login_required, current_user
from app import db
from app.models import Appointment, Doctor, DoctorAvailability, Patient, CallSession, Cancellation
from datetime import datetime, date, timedelta
import stripe
import os
import uuid

appointment = Blueprint('appointment', __name__)

stripe.api_key = os.getenv('STRIPE_SECRET_KEY')
STRIPE_PUBLISHABLE_KEY = os.getenv('STRIPE_PUBLISHABLE_KEY')
CONSULTATION_FEE = 7500


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


@appointment.route('/patient/book', methods=['GET', 'POST'])
@login_required
def book():
    doctors = Doctor.query.filter_by(is_active=True).all()
    specialisations = list(set([d.specialisation for d in doctors]))

    if request.method == 'POST':
        doctor_id        = request.form.get('doctor_id')
        appointment_date = request.form.get('appointment_date')
        appointment_time = request.form.get('appointment_time')
        reason           = request.form.get('reason', '').strip()
        appointment_type = request.form.get('appointment_type', 'In-person')

        if not doctor_id or not appointment_date or not appointment_time:
            flash('Please select a doctor, date and time.', 'danger')
            return redirect(url_for('appointment.book'))

        # Validate date is not in the past
        try:
            appt_date_obj = datetime.strptime(appointment_date, '%Y-%m-%d').date()
        except ValueError:
            flash('Invalid date format.', 'danger')
            return redirect(url_for('appointment.book'))

        if appt_date_obj < date.today():
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

    upcoming = Appointment.query.filter_by(
        patient_id=current_user.id, status='Upcoming'
    ).order_by(Appointment.appointment_date.asc()).all()

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
        chat_available=chat_available
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
        return redirect(url_for('call.room', room_id=existing.room_id))
    new_call = create_call_session(appt, call_type)
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
        return redirect(url_for('call.room', room_id=existing.room_id))
    new_call = create_call_session(appt, call_type)
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