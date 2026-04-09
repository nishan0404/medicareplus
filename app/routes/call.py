"""
app/routes/call.py
──────────────────
Telehealth call module for MediCarePlus.

Stack:
  • Flask blueprint  — serves the call room HTML page
  • Flask-SocketIO   — relays WebRTC signalling messages between peers
  • WebRTC (browser) — actual peer-to-peer audio/video stream

How it works:
  1. Patient clicks Audio/Video Call → appointment.start_call creates a
     CallSession row with a unique room_id UUID, then redirects here.
  2. Doctor opens the same URL from their dashboard.
  3. Both browsers join the same SocketIO room (room_id).
  4. JS on each side exchanges WebRTC offer / answer / ICE candidates
     through SocketIO events (all relayed by this file).
  5. Once both peers have exchanged SDP + ICE, the browser-level
     RTCPeerConnection establishes a direct P2P media stream.
  6. When either party clicks "End Call" the ended event fires,
     CallSession is marked ended, and both are redirected home.

Registration in your app factory (app/__init__.py):
──────────────────────────────────────────────────
  from app.routes.call import call as call_blueprint, register_socketio_events
  app.register_blueprint(call_blueprint)
  register_socketio_events(socketio)   # pass your SocketIO instance
"""

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user
from flask_socketio import join_room, leave_room, emit
from app import db
from app.models import CallSession, Appointment
from datetime import datetime

call = Blueprint('call', __name__)


# ─────────────────────────────────────
# HTTP — Call Room Page
# ─────────────────────────────────────

@call.route('/call/room/<room_id>')
@login_required
def room(room_id):
    """
    Serve the call room page.
    Both patient and doctor land here with the same room_id.
    The template handles audio-only vs video UI based on call_type.
    """
    session = CallSession.query.filter_by(room_id=room_id).first_or_404()
    appt    = Appointment.query.get_or_404(session.appointment_id)

    # Only the patient or the assigned doctor may enter
    user_role = current_user.role   # 'patient' | 'doctor'
    allowed   = (
        (user_role == 'patient' and appt.patient_id == current_user.id) or
        (user_role == 'doctor'  and appt.doctor_id  == current_user.id)
    )
    if not allowed:
        flash('You are not authorised to join this call.', 'danger')
        return redirect(url_for('appointment.my_appointments'))

    if session.status == 'ended':
        flash('This call has already ended.', 'info')
        return redirect(url_for('appointment.my_appointments'))

    return render_template(
        'call/room.html',
        title      = 'Telehealth Consultation',
        call       = session,
        appt       = appt,
        user_role  = user_role,
        room_id    = room_id,
    )


# ─────────────────────────────────────
# HTTP — End Call (POST from button)
# ─────────────────────────────────────

@call.route('/call/end/<room_id>', methods=['POST', 'GET'])
@login_required
def end_call(room_id):
    """Mark the CallSession as ended and record duration."""
    call_session = CallSession.query.filter_by(room_id=room_id).first_or_404()

    if call_session.status != 'ended':
        call_session.status   = 'ended'
        call_session.ended_at = datetime.utcnow()
        if call_session.started_at:
            delta = call_session.ended_at - call_session.started_at
            call_session.duration_secs = int(delta.total_seconds())
        db.session.commit()

    flash('Call ended.', 'info')
    if current_user.role == 'doctor':
        return redirect(url_for('doctor.dashboard'))
    return redirect(url_for('appointment.my_appointments'))


# ─────────────────────────────────────
# SocketIO Event Handlers
# ─────────────────────────────────────

def register_socketio_events(socketio):
    """
    Call this once from your app factory after creating the SocketIO object:
        register_socketio_events(socketio)

    All events are namespaced under /call so they don't clash with other
    SocketIO usage in your app.
    """

    @socketio.on('join', namespace='/call')
    def on_join(data):
        """
        Fired by both peers when they open the call room page.
        data = { room_id: '...', user_role: 'patient'|'doctor' }
        """
        room_id   = data.get('room_id')
        user_role = data.get('user_role')

        join_room(room_id)

        # Tell the *other* peer someone joined so they can initiate the offer
        emit('peer_joined', {'user_role': user_role},
             room=room_id, include_self=False)

        # Mark call as active when doctor joins (doctor joins second)
        if user_role == 'doctor':
            call_session = CallSession.query.filter_by(room_id=room_id).first()
            if call_session and call_session.status == 'waiting':
                call_session.status     = 'active'
                call_session.started_at = datetime.utcnow()
                db.session.commit()

    @socketio.on('offer', namespace='/call')
    def on_offer(data):
        """
        WebRTC offer SDP from the initiating peer.
        data = { room_id: '...', sdp: { type: 'offer', sdp: '...' } }
        Relay to the other peer in the room.
        """
        room_id = data.get('room_id')
        emit('offer', {'sdp': data.get('sdp')},
             room=room_id, include_self=False)

    @socketio.on('answer', namespace='/call')
    def on_answer(data):
        """
        WebRTC answer SDP from the receiving peer.
        data = { room_id: '...', sdp: { type: 'answer', sdp: '...' } }
        Relay to the other peer.
        """
        room_id = data.get('room_id')
        emit('answer', {'sdp': data.get('sdp')},
             room=room_id, include_self=False)

    @socketio.on('ice_candidate', namespace='/call')
    def on_ice_candidate(data):
        """
        ICE candidate from either peer.
        data = { room_id: '...', candidate: { ... } }
        Relay to the other peer.
        """
        room_id = data.get('room_id')
        emit('ice_candidate', {'candidate': data.get('candidate')},
             room=room_id, include_self=False)

    @socketio.on('end_call', namespace='/call')
    def on_end_call(data):
        """
        Either peer clicked End Call.
        Notify the other peer so their page redirects automatically.
        data = { room_id: '...' }
        """
        room_id = data.get('room_id')

        # Persist ended status
        call_session = CallSession.query.filter_by(room_id=room_id).first()
        if call_session and call_session.status != 'ended':
            call_session.status   = 'ended'
            call_session.ended_at = datetime.utcnow()
            if call_session.started_at:
                delta = call_session.ended_at - call_session.started_at
                call_session.duration_secs = int(delta.total_seconds())
            db.session.commit()

        # Tell the other peer to redirect
        emit('call_ended', {}, room=room_id, include_self=False)
        leave_room(room_id)

    @socketio.on('toggle_media', namespace='/call')
    def on_toggle_media(data):
        """
        Relay mute/camera-off notifications to the other peer so their
        UI can show a 'mic muted' or 'camera off' indicator.
        data = { room_id: '...', type: 'audio'|'video', enabled: true|false }
        """
        room_id = data.get('room_id')
        emit('peer_media_toggle',
             {'type': data.get('type'), 'enabled': data.get('enabled')},
             room=room_id, include_self=False)

    @socketio.on('disconnect', namespace='/call')
    def on_disconnect():
        """
        Browser closed or network dropped.
        SocketIO handles room cleanup automatically; we just notify the peer.
        """
        # We don't have room_id on disconnect — the peer will detect via
        # RTCPeerConnection.oniceconnectionstatechange === 'disconnected'
        pass