from flask import Blueprint, request, jsonify
from flask_login import login_required, current_user
import os
import requests

chatbot = Blueprint('chatbot', __name__)

GROQ_API_URL = 'https://api.groq.com/openai/v1/chat/completions'
GROQ_MODEL = os.getenv('GROQ_MODEL', 'openai/gpt-oss-20b')
GEMINI_API_URL = 'https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent'
GEMINI_MODEL = os.getenv('GEMINI_MODEL', 'gemini-3.6-flash')


def build_openai_messages(system_prompt, history, user_message):
    messages = [{'role': 'system', 'content': system_prompt}]
    for msg in history[-10:]:
        role = 'assistant' if msg.get('role') == 'assistant' else 'user'
        content = str(msg.get('content', '')).strip()
        if content:
            messages.append({'role': role, 'content': content})
    messages.append({'role': 'user', 'content': user_message})
    return messages


def build_gemini_contents(system_prompt, history, user_message):
    """Convert app chat history into Gemini's user/model content format."""
    contents = [{
        'role': 'user',
        'parts': [{'text': system_prompt}]
    }]

    for msg in history[-10:]:
        role = 'model' if msg.get('role') == 'assistant' else 'user'
        content = str(msg.get('content', '')).strip()
        if content:
            contents.append({
                'role': role,
                'parts': [{'text': content}]
            })

    contents.append({
        'role': 'user',
        'parts': [{'text': user_message}]
    })
    return contents


def extract_gemini_reply(response_data):
    candidates = response_data.get('candidates', [])
    if not candidates:
        return None
    parts = candidates[0].get('content', {}).get('parts', [])
    return ''.join(part.get('text', '') for part in parts).strip()


def get_groq_reply(system_prompt, history, user_message):
    groq_api_key = os.getenv('GROQ_API_KEY')
    if not groq_api_key:
        return None

    response = requests.post(
        GROQ_API_URL,
        headers={
            'Authorization': f'Bearer {groq_api_key}',
            'Content-Type': 'application/json',
        },
        json={
            'model': GROQ_MODEL,
            'messages': build_openai_messages(system_prompt, history, user_message),
            'max_tokens': 500,
            'temperature': 0.7,
            'reasoning_effort': 'low',
        },
        timeout=15,
    )
    response.raise_for_status()
    choices = response.json().get('choices', [])
    if not choices:
        return None
    return choices[0].get('message', {}).get('content', '').strip()


def get_gemini_reply(system_prompt, history, user_message):
    gemini_api_key = os.getenv('GEMINI_API_KEY')
    if not gemini_api_key:
        return None

    response = requests.post(
        GEMINI_API_URL.format(model=GEMINI_MODEL),
        params={'key': gemini_api_key},
        headers={'Content-Type': 'application/json'},
        json={
            'contents': build_gemini_contents(system_prompt, history, user_message),
            'generationConfig': {
                'maxOutputTokens': 500,
                'temperature': 0.7,
            },
        },
        timeout=30,
    )
    response.raise_for_status()
    return extract_gemini_reply(response.json())

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

    try:
        reply = get_groq_reply(system_prompt, history, user_message)
        if not reply:
            reply = get_gemini_reply(system_prompt, history, user_message)
        if not reply:
            reply = 'I could not generate a response right now. Please try again.'
        return jsonify({'reply': reply})

    except Exception as e:
        print(f"Chatbot API error: {e}")
        return jsonify({
            'reply': 'I am having trouble connecting right now. Please try again or contact the clinic directly.'
        })
