import random
import requests
from django.conf import settings
from .models import Question

def get_random_question(topic, asked_ids):
    remaining_questions = Question.objects.filter(topic=topic).exclude(id__in=asked_ids)
    if remaining_questions.exists():
        return random.choice(remaining_questions)
    return None


def send_whatsapp_message(phone_number, message_payload):
    url = f"https://graph.facebook.com/v23.0/{settings.META_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {settings.META_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": phone_number,
        **message_payload
        
    }
    
    response = requests.post(url, headers=headers, json=payload)
    # return response.status_code, response.text
    print("📤 WhatsApp API response:", response.status_code, response.text)
