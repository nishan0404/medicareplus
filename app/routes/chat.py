"""
app/routes/chat.py
──────────────────
Live chat module for MediCarePlus.
"""

import os
import uuid
from datetime import datetime, timedelta
from flask import (Blueprint, render_template, redirect, url_for,
                   flash, request, jsonify, current_app)
from flask_login import login_required, current_user
from flask_socketio import join_room, leave_room, emit
from werkzeug.utils import secure_filename
from app import db
from app.models import Appointment, ChatMessage, ChatAttachment

chat = Blueprint('chat', __name__)

ALLOWED_EXTENSIONS = {'png', 'jpg', 'jpeg', 'gif', 'pdf', 'doc', 'docx', 'txt'}
MAX_FILE_SIZE      = 5 * 1024 * 1024   # 5MB

online_users = {}


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def chat_room_key(appointment_id):
    return f"chat_{appointment_id}"


def is_chat_open(appt):
    from app.routes.appointment import is_chat_available
    return is_chat_available(appt)


def get_unread_count(appointment_id, viewer_role):
    return ChatMessage.query.filter_by(
        appointment_id = appointment_id,
        is_read        = False
    ).filter(ChatMessage.sender_role != viewer_role).count()


@chat.route('/chat/<int:appointment_id>')
@login_required
def room(appointment_id):
    appt      = Appointment.query.get_or_404(appointment_id)
    user_role = current_user.role

    allowed = (
        (user_role == 'patient' and appt.patient_id == current_user.id) or
        (user_role == 'doctor'  and appt.doctor_id  == current_user.id)
    )
    if not allowed:
        flash('You are not authorised to access this chat.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    if not is_chat_open(appt):
        flash('This chat room is not available for that appointment.', 'info')
        if user_role == 'doctor':
            return redirect(url_for('doctor.dashboard'))
        return redirect(url_for('appointment.my_appointments'))

    messages = ChatMessage.query.filter_by(
        appointment_id=appointment_id
    ).order_by(ChatMessage.sent_at.asc()).all()

    ChatMessage.query.filter_by(
        appointment_id = appointment_id,
        is_read        = False
    ).filter(ChatMessage.sender_role != user_role).update({'is_read': True})
    db.session.commit()

    room_key = chat_room_key(appointment_id)

    from app.routes.appointment import is_call_available
    from datetime import date
    call_available = is_call_available(appt)
    # Show voice call in chat header for ANY today's non-cancelled appointment
    chat_today = (appt.appointment_date == date.today() and appt.status != 'Cancelled')

    return render_template('chat/room.html',
        title          = 'Live Chat',
        appt           = appt,
        messages       = messages,
        user_role      = user_role,
        room_key       = room_key,
        chat_open      = True,
        call_available = call_available,
        chat_today     = chat_today,
    )


@chat.route('/chat/<int:appointment_id>/upload', methods=['POST'])
@login_required
def upload_file(appointment_id):
    appt      = Appointment.query.get_or_404(appointment_id)
    user_role = current_user.role

    allowed = (
        (user_role == 'patient' and appt.patient_id == current_user.id) or
        (user_role == 'doctor'  and appt.doctor_id  == current_user.id)
    )
    if not allowed:
        return jsonify({'error': 'Unauthorised'}), 403

    if not is_chat_open(appt):
        return jsonify({'error': 'Chat is closed'}), 403

    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not allowed_file(file.filename):
        return jsonify({'error': 'File type not allowed. Allowed: images, PDF, Word, TXT'}), 400

    file.seek(0, 2)
    size = file.tell()
    file.seek(0)
    if size > MAX_FILE_SIZE:
        return jsonify({'error': 'File too large. Maximum size is 5MB'}), 400

    upload_folder = os.path.join(current_app.static_folder, 'chat_uploads')
    os.makedirs(upload_folder, exist_ok=True)

    ext           = secure_filename(file.filename).rsplit('.', 1)[1].lower()
    unique_name   = f"{uuid.uuid4().hex}.{ext}"
    save_path     = os.path.join(upload_folder, unique_name)
    file.save(save_path)

    file_url      = f"/static/chat_uploads/{unique_name}"
    original_name = secure_filename(file.filename)
    is_image      = ext in {'png', 'jpg', 'jpeg', 'gif'}
    msg_type      = 'image' if is_image else 'file'

    new_msg = ChatMessage(
        appointment_id = appointment_id,
        sender_id      = current_user.id,
        sender_role    = user_role,
        sender_name    = current_user.full_name,
        message        = original_name,
        msg_type       = msg_type,
        file_url       = file_url,
        file_name      = original_name,
        is_read        = False,
    )
    db.session.add(new_msg)
    db.session.flush()

    attachment = ChatAttachment(
        message_id     = new_msg.id,
        appointment_id = appointment_id,
        file_name      = original_name,
        file_path      = save_path,
        file_type      = file.content_type,
        file_size      = size,
    )
    db.session.add(attachment)
    db.session.commit()

    return jsonify({
        'success'  : True,
        'msg_id'   : new_msg.id,
        'file_url' : file_url,
        'file_name': original_name,
        'msg_type' : msg_type,
        'sent_at'  : new_msg.sent_at.strftime('%I:%M %p'),
        'sender'   : current_user.full_name,
        'role'     : user_role,
    })


@chat.route('/chat/<int:appointment_id>/send', methods=['POST'])
@login_required
def send_message_http(appointment_id):
    """HTTP fallback for sending messages when WebSocket is unavailable."""
    appt      = Appointment.query.get_or_404(appointment_id)
    user_role = current_user.role

    allowed = (
        (user_role == 'patient' and appt.patient_id == current_user.id) or
        (user_role == 'doctor'  and appt.doctor_id  == current_user.id)
    )
    if not allowed:
        return jsonify({'error': 'Unauthorised'}), 403

    if not is_chat_open(appt):
        return jsonify({'error': 'Chat is closed'}), 403

    data    = request.get_json(silent=True) or {}
    message = (data.get('message') or '').strip()[:2000]
    if not message:
        return jsonify({'error': 'Empty message'}), 400

    new_msg = ChatMessage(
        appointment_id = appointment_id,
        sender_id      = current_user.id,
        sender_role    = user_role,
        sender_name    = current_user.full_name,
        message        = message,
        msg_type       = 'text',
        is_read        = False,
    )
    db.session.add(new_msg)
    db.session.commit()

    return jsonify({
        'success': True,
        'msg_id' : new_msg.id,
        'sent_at': new_msg.sent_at.strftime('%I:%M %p'),
    })


@chat.route('/chat/<int:appointment_id>/status')
@login_required
def chat_status(appointment_id):
    appt = Appointment.query.get_or_404(appointment_id)
    return jsonify({
        'open'         : is_chat_open(appt),
        'unread'       : get_unread_count(appointment_id, current_user.role),
        'appt_status'  : appt.status,
    })


def register_chat_events(socketio):

    @socketio.on('chat_join', namespace='/chat')
    def on_chat_join(data):
        room_key       = data.get('room_key')
        user_role      = data.get('user_role')
        user_name      = data.get('user_name')
        appointment_id = data.get('appointment_id')

        join_room(room_key)

        if room_key not in online_users:
            online_users[room_key] = set()
        online_users[room_key].add(f"{user_role}:{user_name}")

        emit('user_online', {
            'user_role': user_role,
            'user_name': user_name,
        }, room=room_key, include_self=False)

        emit('online_list', {
            'users': list(online_users.get(room_key, set()))
        })

        if appointment_id:
            ChatMessage.query.filter_by(
                appointment_id = appointment_id,
                is_read        = False,
            ).filter(ChatMessage.sender_role != user_role).update({'is_read': True})
            db.session.commit()

            emit('messages_read', {
                'reader_role': user_role
            }, room=room_key, include_self=False)

    @socketio.on('chat_message', namespace='/chat')
    def on_chat_message(data):
        room_key       = data.get('room_key')
        appointment_id = data.get('appointment_id')
        message        = data.get('message', '').strip()
        sender_id      = data.get('sender_id')
        sender_role    = data.get('sender_role')
        sender_name    = data.get('sender_name')
        msg_type       = data.get('msg_type', 'text')
        file_url       = data.get('file_url')
        file_name      = data.get('file_name')

        if not message:
            return

        appt = Appointment.query.get(appointment_id)
        if not appt or not is_chat_open(appt):
            emit('chat_closed', {'message': 'Chat room has closed.'})
            return

        # File/image messages are already saved to DB by the upload_file HTTP route.
        # Only save text messages here to avoid duplicates.
        if msg_type == 'text':
            new_msg = ChatMessage(
                appointment_id = appointment_id,
                sender_id      = sender_id,
                sender_role    = sender_role,
                sender_name    = sender_name,
                message        = message,
                msg_type       = 'text',
                is_read        = False,
            )
            db.session.add(new_msg)
            db.session.commit()
            msg_id   = new_msg.id
            sent_at  = new_msg.sent_at.strftime('%I:%M %p')
        else:
            # Fetch the already-saved record to get its id and timestamp
            existing = ChatMessage.query.filter_by(
                appointment_id = appointment_id,
                sender_id      = sender_id,
                msg_type       = msg_type,
                file_url       = file_url,
            ).order_by(ChatMessage.sent_at.desc()).first()
            msg_id  = existing.id   if existing else None
            sent_at = existing.sent_at.strftime('%I:%M %p') if existing else ''

        emit('new_message', {
            'msg_id'     : msg_id,
            'message'    : message,
            'msg_type'   : msg_type,
            'file_url'   : file_url,
            'file_name'  : file_name,
            'sender_role': sender_role,
            'sender_name': sender_name,
            'sent_at'    : sent_at,
            'is_read'    : False,
        }, room=room_key)

    @socketio.on('chat_typing', namespace='/chat')
    def on_typing(data):
        room_key = data.get('room_key')
        emit('typing_indicator', {
            'user_role': data.get('user_role'),
            'user_name': data.get('user_name'),
            'is_typing': data.get('is_typing'),
        }, room=room_key, include_self=False)

    @socketio.on('chat_read', namespace='/chat')
    def on_chat_read(data):
        appointment_id = data.get('appointment_id')
        reader_role    = data.get('reader_role')
        room_key       = data.get('room_key')

        if appointment_id and reader_role:
            ChatMessage.query.filter_by(
                appointment_id = appointment_id,
                is_read        = False,
            ).filter(ChatMessage.sender_role != reader_role).update({'is_read': True})
            db.session.commit()

            emit('messages_read', {
                'reader_role': reader_role
            }, room=room_key, include_self=False)

    @socketio.on('chat_leave', namespace='/chat')
    def on_chat_leave(data):
        room_key  = data.get('room_key')
        user_role = data.get('user_role')
        user_name = data.get('user_name')

        leave_room(room_key)

        key = f"{user_role}:{user_name}"
        if room_key in online_users:
            online_users[room_key].discard(key)

        emit('user_offline', {
            'user_role': user_role,
            'user_name': user_name,
        }, room=room_key, include_self=False)

    @socketio.on('disconnect', namespace='/chat')
    def on_disconnect():
        pass