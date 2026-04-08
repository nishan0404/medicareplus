from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
from groq import Groq
import os

chatbot = Blueprint('chatbot', __name__)

@chatbot.route('/api/chat', methods=['POST'])
@login_required
def chat():
    data = request.get_json()
    user_message = data.get('message', '').strip()
    history = data.get('history', [])

    if not user_message:
        return jsonify({'error': 'No message provided'}), 400

    # Build system prompt
    system_prompt = f"""You are MediCare+ Assistant, a helpful AI chatbot for the 
MediCare+ healthcare management system. You are talking to {current_user.full_name}.

You help users with:
- Navigating the MediCare+ system
- Understanding appointments and medical records
- General health questions and guidance
- Explaining how to use features

Available pages:
- /patient/dashboard - Patient dashboard
- /patient/book - Book an appointment
- /patient/appointments - View appointments
- /patient/records - View medical records
- /patient/symptoms - AI Symptom Checker
- /patient/profile - Edit profile

Important rules:
- Always remind users you are NOT a substitute for professional medical advice
- For serious symptoms, recommend seeing a doctor or calling 000 in emergencies
- Be friendly, helpful, and professional
- Keep responses concise and clear
- Never provide specific medical diagnoses"""

    # Build messages
    messages = [{'role': 'system', 'content': system_prompt}]

    # Add conversation history (last 10 messages)
    for msg in history[-10:]:
        messages.append({
            'role': msg['role'],
            'content': msg['content']
        })

    # Add current message
    messages.append({
        'role': 'user',
        'content': user_message
    })

    try:
        # Call Groq API
        client = Groq(api_key=os.getenv('GROQ_API_KEY'))
        response = client.chat.completions.create(
            model='llama-3.3-70b-versatile',
            messages=messages,
            max_tokens=500,
            temperature=0.7
        )
        reply = response.choices[0].message.content
        return jsonify({'reply': reply})

    except Exception as e:
        print(f"Groq API error: {e}")
        return jsonify({
            'reply': 'I am having trouble connecting right now. Please try again or contact the clinic directly.'
        })