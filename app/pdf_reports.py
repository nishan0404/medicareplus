"""
app/pdf_reports.py
──────────────────
PDF report generation for MediCare+ admin panel.
Uses reportlab (already installed).
"""

from io import BytesIO
from datetime import date
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle,
    HRFlowable, KeepTogether
)
from reportlab.lib.enums import TA_LEFT, TA_CENTER, TA_RIGHT

# ── Brand colours ──
DARK_BLUE  = colors.HexColor('#1A5276')
GREEN      = colors.HexColor('#1A8A4A')
LIGHT_BLUE = colors.HexColor('#D6EAF8')
LIGHT_GREEN= colors.HexColor('#D5F5E3')
LIGHT_GREY = colors.HexColor('#F4F6F7')
MID_GREY   = colors.HexColor('#95A5A6')
RED        = colors.HexColor('#C0392B')
ORANGE     = colors.HexColor('#E67E22')
WHITE      = colors.white
BLACK      = colors.black

W, H = A4   # 595.27 x 841.89 pt


def _styles():
    base = getSampleStyleSheet()
    return {
        'title':    ParagraphStyle('title',    fontSize=20, textColor=WHITE,   alignment=TA_LEFT,   fontName='Helvetica-Bold', leading=24),
        'subtitle': ParagraphStyle('subtitle', fontSize=10, textColor=WHITE,   alignment=TA_LEFT,   fontName='Helvetica',      leading=13),
        'h2':       ParagraphStyle('h2',       fontSize=13, textColor=DARK_BLUE, alignment=TA_LEFT, fontName='Helvetica-Bold', spaceAfter=4, leading=16),
        'h3':       ParagraphStyle('h3',       fontSize=11, textColor=GREEN,    alignment=TA_LEFT,  fontName='Helvetica-Bold', spaceAfter=2, leading=14),
        'body':     ParagraphStyle('body',     fontSize=9,  textColor=BLACK,    alignment=TA_LEFT,  fontName='Helvetica',      leading=13),
        'small':    ParagraphStyle('small',    fontSize=8,  textColor=MID_GREY, alignment=TA_LEFT,  fontName='Helvetica',      leading=11),
        'label':    ParagraphStyle('label',    fontSize=8,  textColor=MID_GREY, fontName='Helvetica-Bold', leading=11),
        'footer':   ParagraphStyle('footer',   fontSize=8,  textColor=MID_GREY, alignment=TA_CENTER, fontName='Helvetica'),
        'cell':     ParagraphStyle('cell',     fontSize=8,  textColor=BLACK,    fontName='Helvetica', leading=11),
        'cell_bold':ParagraphStyle('cell_bold',fontSize=8,  textColor=BLACK,    fontName='Helvetica-Bold', leading=11),
    }


def _header_table(title_text, subtitle_text, generated_by='Admin'):
    """Returns a full-width coloured header block."""
    S = _styles()
    data = [[
        Paragraph(title_text,    S['title']),
        Paragraph(
            f"<b>MediCare+</b><br/>Generated: {date.today().strftime('%d %b %Y')}<br/>By: {generated_by}",
            ParagraphStyle('hdr_right', fontSize=8, textColor=WHITE,
                           alignment=TA_RIGHT, fontName='Helvetica', leading=12)
        )
    ]]
    if subtitle_text:
        data.append([
            Paragraph(subtitle_text, S['subtitle']), ''
        ])

    t = Table(data, colWidths=[W * 0.65 - 36, W * 0.35 - 36])
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), DARK_BLUE),
        ('VALIGN',     (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, -1), 14),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 14),
        ('LEFTPADDING',   (0, 0), (-1, -1), 16),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 16),
        ('SPAN',       (0, 1), (-1, 1)),
        ('TOPPADDING', (0, 1), (-1, 1), 4),
        ('BOTTOMPADDING', (0, 1), (-1, 1), 10),
    ]))
    return t


def _info_table(rows, col_widths=None):
    """Two-column label/value info table."""
    S = _styles()
    data = [
        [Paragraph(label, S['label']), Paragraph(str(value), S['body'])]
        for label, value in rows
    ]
    w = col_widths or [80, W - 80 - 72]
    t = Table(data, colWidths=w)
    t.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), LIGHT_GREY),
        ('ROWBACKGROUNDS', (0, 0), (-1, -1), [WHITE, LIGHT_GREY]),
        ('GRID',       (0, 0), (-1, -1), 0.4, colors.HexColor('#DDE')),
        ('VALIGN',     (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 8),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 8),
    ]))
    return t


def _section_header(text):
    S = _styles()
    return [
        Spacer(1, 8),
        HRFlowable(width='100%', thickness=1, color=DARK_BLUE),
        Spacer(1, 3),
        Paragraph(text, S['h2']),
        Spacer(1, 4),
    ]


def _stat_row(stats):
    """Horizontal stats strip: list of (label, value, colour) tuples."""
    S = _styles()
    data = [[
        [Paragraph(str(v),
                   ParagraphStyle('sv', fontSize=18, fontName='Helvetica-Bold',
                                  textColor=WHITE, alignment=TA_CENTER, leading=22)),
         Paragraph(lbl,
                   ParagraphStyle('sl', fontSize=8, fontName='Helvetica',
                                  textColor=WHITE, alignment=TA_CENTER, leading=10))]
        for lbl, v, _ in stats
    ]]
    col_w = (W - 72) / len(stats)
    t = Table(data, colWidths=[col_w] * len(stats))
    bg_commands = [('BACKGROUND', (i, 0), (i, 0), c) for i, (_, __, c) in enumerate(stats)]
    t.setStyle(TableStyle([
        ('VALIGN',        (0, 0), (-1, -1), 'MIDDLE'),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('TOPPADDING',    (0, 0), (-1, -1), 10),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ('ROUNDEDCORNERS', [4]),
        *bg_commands,
    ]))
    return t


def _appt_table(appointments, show_patient=True, show_doctor=True):
    """Reusable appointments table."""
    S = _styles()
    headers = []
    if show_patient: headers.append('Patient')
    if show_doctor:  headers.append('Doctor')
    headers += ['Date', 'Time', 'Reason', 'Status', 'Payment']

    head_row = [Paragraph(h, ParagraphStyle('th', fontSize=8, fontName='Helvetica-Bold',
                                             textColor=WHITE, alignment=TA_CENTER))
                for h in headers]
    rows = [head_row]

    for a in appointments:
        status_colour = {
            'Completed':   GREEN,
            'Upcoming':    DARK_BLUE,
            'Cancelled':   RED,
            'In-Progress': ORANGE,
            'No-Show':     MID_GREY,
        }.get(a.status, BLACK)

        row = []
        if show_patient:
            row.append(Paragraph(a.patient.full_name, S['cell']))
        if show_doctor:
            row.append(Paragraph(a.doctor.full_name,  S['cell']))
        row += [
            Paragraph(a.appointment_date.strftime('%d %b %Y'), S['cell']),
            Paragraph(a.appointment_time.strftime('%I:%M %p'), S['cell']),
            Paragraph(a.reason or '—', S['cell']),
            Paragraph(a.status,
                      ParagraphStyle('status', fontSize=8, fontName='Helvetica-Bold',
                                     textColor=status_colour)),
            Paragraph(a.payment_status or '—', S['cell']),
        ]
        rows.append(row)

    n_cols = len(headers)
    avail  = W - 72
    if show_patient and show_doctor:
        col_widths = [75, 75, 52, 45, 90, 55, 45][:n_cols]
    elif show_patient:
        col_widths = [80, 52, 45, 110, 55, 45][:n_cols]
    else:
        col_widths = [80, 52, 45, 120, 55, 45][:n_cols]

    # Normalise to fit
    scale = avail / sum(col_widths)
    col_widths = [c * scale for c in col_widths]

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ('BACKGROUND',    (0, 0), (-1, 0), DARK_BLUE),
        ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor('#CCC')),
        ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
        ('ALIGN',         (0, 0), (-1, -1), 'CENTER'),
        ('ALIGN',         (0, 1), (0 + (1 if show_patient else 0), -1), 'LEFT'),
        ('TOPPADDING',    (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING',   (0, 0), (-1, -1), 5),
        ('RIGHTPADDING',  (0, 0), (-1, -1), 5),
    ]))
    return t


def _notes_block(note, prescriptions, S):
    """Render consultation note + prescriptions for one appointment."""
    items = []
    if note:
        items.append(Paragraph(f"<b>Diagnosis:</b> {note.diagnosis or '—'}", S['body']))
        items.append(Paragraph(f"<b>Notes:</b> {note.notes or '—'}", S['body']))
        if note.follow_up_date:
            items.append(Paragraph(f"<b>Follow-up:</b> {note.follow_up_date.strftime('%d %b %Y')}", S['body']))
    if prescriptions:
        items.append(Spacer(1, 4))
        items.append(Paragraph('<b>Prescriptions:</b>', S['body']))
        rx_data = [[
            Paragraph(h, ParagraphStyle('rxh', fontSize=7, fontName='Helvetica-Bold', textColor=WHITE))
            for h in ['Medication', 'Dosage', 'Frequency', 'Days', 'Instructions']
        ]]
        for rx in prescriptions:
            rx_data.append([
                Paragraph(rx.medication_name, S['cell']),
                Paragraph(rx.dosage,          S['cell']),
                Paragraph(rx.frequency,       S['cell']),
                Paragraph(str(rx.duration_days), S['cell']),
                Paragraph(rx.instructions or '—', S['cell']),
            ])
        avail = W - 72 - 20   # indented
        rx_t = Table(rx_data, colWidths=[avail*0.22, avail*0.15, avail*0.18,
                                          avail*0.08, avail*0.37], repeatRows=1)
        rx_t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), GREEN),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT_GREEN]),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor('#BDC')),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ]))
        items.append(rx_t)
    return items


# ══════════════════════════════════════════
#  1.  DOCTOR  REPORT
# ══════════════════════════════════════════
def generate_doctor_pdf(doctor, appointments):
    """
    Full report for one doctor:
    – Profile info
    – Appointment stats
    – All appointments table
    – Per-appointment: consultation notes + prescriptions
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
        title=f"Doctor Report — {doctor.full_name}"
    )
    S = _styles()
    story = []

    # ── Header ──
    story.append(_header_table(
        f"Doctor Report",
        f"{doctor.full_name}  ·  {doctor.specialisation}"
    ))
    story.append(Spacer(1, 10))

    # ── Profile ──
    story += _section_header("Doctor Profile")
    story.append(_info_table([
        ('Full Name',      doctor.full_name),
        ('Specialisation', doctor.specialisation),
        ('Email',          doctor.email),
        ('Phone',          doctor.phone),
        ('Status',         'Active' if doctor.is_active else 'Inactive'),
        ('Joined',         doctor.created_at.strftime('%d %b %Y') if doctor.created_at else '—'),
        ('Bio',            doctor.bio or '—'),
    ]))
    story.append(Spacer(1, 10))

    # ── Stats ──
    total     = len(appointments)
    completed = sum(1 for a in appointments if a.status == 'Completed')
    upcoming  = sum(1 for a in appointments if a.status == 'Upcoming')
    cancelled = sum(1 for a in appointments if a.status == 'Cancelled')
    story += _section_header("Appointment Statistics")
    story.append(_stat_row([
        ('Total',     total,     DARK_BLUE),
        ('Completed', completed, GREEN),
        ('Upcoming',  upcoming,  colors.HexColor('#2980B9')),
        ('Cancelled', cancelled, RED),
    ]))
    story.append(Spacer(1, 10))

    # ── All appointments table ──
    story += _section_header("All Appointments")
    if appointments:
        story.append(_appt_table(appointments, show_patient=True, show_doctor=False))
    else:
        story.append(Paragraph('No appointments on record.', S['small']))
    story.append(Spacer(1, 10))

    # ── Detailed notes per completed appointment ──
    completed_appts = [a for a in appointments if a.status == 'Completed' and (a.notes or a.prescriptions)]
    if completed_appts:
        story += _section_header("Consultation Notes & Prescriptions")
        for appt in completed_appts:
            block = [
                Paragraph(
                    f"<b>{appt.appointment_date.strftime('%d %b %Y')}  {appt.appointment_time.strftime('%I:%M %p')}"
                    f"</b>  ·  Patient: {appt.patient.full_name}",
                    S['h3']
                ),
            ]
            block += _notes_block(appt.notes, appt.prescriptions, S)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    doc.build(story)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════
#  2.  PATIENT  REPORT
# ══════════════════════════════════════════
def generate_patient_pdf(patient, appointments, profile=None, symptom_logs=None):
    """
    Full report for one patient:
    – Profile info
    – Appointment stats
    – All appointments table
    – Per-appointment: consultation notes + prescriptions
    – Symptom check history
    """
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
        title=f"Patient Report — {patient.full_name}"
    )
    S = _styles()
    story = []

    # ── Header ──
    story.append(_header_table(
        "Patient Report",
        f"{patient.full_name}  ·  DOB: {patient.date_of_birth.strftime('%d %b %Y') if patient.date_of_birth else '—'}"
    ))
    story.append(Spacer(1, 10))

    # ── Profile ──
    story += _section_header("Patient Profile")
    profile_rows = [
        ('Full Name',   patient.full_name),
        ('Email',       patient.email),
        ('Phone',       patient.phone),
        ('Date of Birth', patient.date_of_birth.strftime('%d %b %Y') if patient.date_of_birth else '—'),
        ('Status',      'Active' if patient.is_active else 'Inactive'),
        ('Registered',  patient.created_at.strftime('%d %b %Y') if patient.created_at else '—'),
    ]
    if profile:
        profile_rows += [
            ('Address',         profile.home_address    or '—'),
            ('Emergency Name',  profile.emergency_name  or '—'),
            ('Emergency Phone', profile.emergency_phone or '—'),
        ]
    story.append(_info_table(profile_rows))
    story.append(Spacer(1, 10))

    # ── Stats ──
    total     = len(appointments)
    completed = sum(1 for a in appointments if a.status == 'Completed')
    upcoming  = sum(1 for a in appointments if a.status == 'Upcoming')
    cancelled = sum(1 for a in appointments if a.status == 'Cancelled')
    rx_count  = sum(len(a.prescriptions) for a in appointments)
    story += _section_header("Summary Statistics")
    story.append(_stat_row([
        ('Appointments', total,     DARK_BLUE),
        ('Completed',    completed, GREEN),
        ('Upcoming',     upcoming,  colors.HexColor('#2980B9')),
        ('Cancelled',    cancelled, RED),
        ('Prescriptions',rx_count,  colors.HexColor('#8E44AD')),
    ]))
    story.append(Spacer(1, 10))

    # ── All appointments ──
    story += _section_header("Appointment History")
    if appointments:
        story.append(_appt_table(appointments, show_patient=False, show_doctor=True))
    else:
        story.append(Paragraph('No appointments on record.', S['small']))
    story.append(Spacer(1, 10))

    # ── Notes + Prescriptions ──
    completed_appts = [a for a in appointments if a.status == 'Completed' and (a.notes or a.prescriptions)]
    if completed_appts:
        story += _section_header("Consultation Notes & Prescriptions")
        for appt in completed_appts:
            block = [
                Paragraph(
                    f"<b>{appt.appointment_date.strftime('%d %b %Y')}  {appt.appointment_time.strftime('%I:%M %p')}"
                    f"</b>  ·  Dr. {appt.doctor.full_name}",
                    S['h3']
                ),
            ]
            block += _notes_block(appt.notes, appt.prescriptions, S)
            block.append(Spacer(1, 6))
            story.append(KeepTogether(block))

    # ── Symptom Logs ──
    if symptom_logs:
        story += _section_header("Symptom Check History")
        sym_data = [[
            Paragraph(h, ParagraphStyle('syh', fontSize=8, fontName='Helvetica-Bold', textColor=WHITE))
            for h in ['Date', 'Symptoms Entered', 'Top Prediction', 'Urgency', 'Booked After']
        ]]
        for log in symptom_logs:
            preds = log.predicted_conditions
            top   = preds[0]['condition'] if preds else '—'
            sym_data.append([
                Paragraph(log.checked_at.strftime('%d %b %Y %H:%M'), S['cell']),
                Paragraph(log.input_text[:80] + ('…' if len(log.input_text) > 80 else ''), S['cell']),
                Paragraph(top,  S['cell']),
                Paragraph(log.urgency_level, S['cell']),
                Paragraph('Yes' if log.booked_after else 'No', S['cell']),
            ])
        avail = W - 72
        sym_t = Table(sym_data,
                      colWidths=[avail*0.14, avail*0.32, avail*0.24, avail*0.12, avail*0.18],
                      repeatRows=1)
        sym_t.setStyle(TableStyle([
            ('BACKGROUND',    (0, 0), (-1, 0), DARK_BLUE),
            ('ROWBACKGROUNDS',(0, 1), (-1, -1), [WHITE, LIGHT_BLUE]),
            ('GRID',          (0, 0), (-1, -1), 0.3, colors.HexColor('#BCD')),
            ('VALIGN',        (0, 0), (-1, -1), 'TOP'),
            ('TOPPADDING',    (0, 0), (-1, -1), 4),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
            ('LEFTPADDING',   (0, 0), (-1, -1), 4),
        ]))
        story.append(sym_t)

    doc.build(story)
    buf.seek(0)
    return buf


# ══════════════════════════════════════════
#  3.  ALL-APPOINTMENTS REPORT
# ══════════════════════════════════════════
def generate_appointments_pdf(appointments, status_filter=''):
    """System-wide appointments report."""
    buf = BytesIO()
    doc = SimpleDocTemplate(
        buf, pagesize=A4,
        leftMargin=36, rightMargin=36, topMargin=36, bottomMargin=36,
        title="Appointments Report"
    )
    S = _styles()
    story = []

    subtitle = f"Status filter: {status_filter}" if status_filter else "All statuses"
    story.append(_header_table("Appointments Report", subtitle))
    story.append(Spacer(1, 10))

    # Stats
    total     = len(appointments)
    completed = sum(1 for a in appointments if a.status == 'Completed')
    upcoming  = sum(1 for a in appointments if a.status == 'Upcoming')
    cancelled = sum(1 for a in appointments if a.status == 'Cancelled')
    no_show   = sum(1 for a in appointments if a.status == 'No-Show')
    story += _section_header("Summary")
    story.append(_stat_row([
        ('Total',     total,     DARK_BLUE),
        ('Completed', completed, GREEN),
        ('Upcoming',  upcoming,  colors.HexColor('#2980B9')),
        ('Cancelled', cancelled, RED),
        ('No-Show',   no_show,   MID_GREY),
    ]))
    story.append(Spacer(1, 10))

    story += _section_header("Appointment List")
    if appointments:
        story.append(_appt_table(appointments, show_patient=True, show_doctor=True))
    else:
        story.append(Paragraph('No appointments found.', S['small']))

    doc.build(story)
    buf.seek(0)
    return buf
