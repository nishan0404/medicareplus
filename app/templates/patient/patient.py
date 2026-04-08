from flask import Blueprint, render_template, request, redirect, url_for, flash
from flask_login import login_required, current_user
from app import db, bcrypt
from app.models import Patient, PatientProfile, Appointment, ConsultationNote, Prescription
from datetime import datetime

patient = Blueprint('patient', __name__)


# ── Dashboard ──
@patient.route('/patient/dashboard')
@login_required
def dashboard():
    # Count upcoming appointments
    upcoming = Appointment.query.filter_by(
        patient_id=current_user.id,
        status='Upcoming'
    ).count()

    # Count prescriptions
    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).count()

    # Count medical records
    records = ConsultationNote.query.filter_by(
        patient_id=current_user.id
    ).count()

    return render_template('patient/dashboard.html',
        title='Dashboard',
        upcoming=upcoming,
        prescriptions=prescriptions,
        records=records
    )


# ── Profile ──
@patient.route('/patient/profile', methods=['GET', 'POST'])
@login_required
def profile():
    patient_profile = PatientProfile.query.filter_by(
        patient_id=current_user.id
    ).first()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'update_profile':
            phone         = request.form.get('phone', '').strip()
            home_address  = request.form.get('home_address', '').strip()
            emergency_name  = request.form.get('emergency_name', '').strip()
            emergency_phone = request.form.get('emergency_phone', '').strip()

            # Update phone on patient
            current_user.phone = phone
            db.session.commit()

            # Update profile
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

            current_user.password_hash = bcrypt.generate_password_hash(new_password).decode('utf-8')
            db.session.commit()
            flash('Password changed successfully!', 'success')
            return redirect(url_for('patient.profile'))

    return render_template('patient/profile.html',
        title='My Profile',
        profile=patient_profile
    )


# ── Medical Records ──
@patient.route('/patient/records')
@login_required
def records():
    # Get all completed appointments with notes
    appointments = Appointment.query.filter_by(
        patient_id=current_user.id,
        status='Completed'
    ).order_by(Appointment.appointment_date.desc()).all()

    # Get all prescriptions
    prescriptions = Prescription.query.filter_by(
        patient_id=current_user.id
    ).order_by(Prescription.issued_at.desc()).all()

    return render_template('patient/records.html',
        title='Medical Records',
        appointments=appointments,
        prescriptions=prescriptions
    )