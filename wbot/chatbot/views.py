import json
from django.views.decorators.csrf import csrf_exempt
from django.http import HttpResponse, JsonResponse
from .models import Topic, Question, UserSession
from .utils import get_random_question, send_whatsapp_message
from django.conf import settings


@csrf_exempt
def whatsAppWebhook(request):
    # --- META VERIFICATION ---
    if request.method == 'GET':
        verify_token = request.GET.get("hub.verify_token")
        challenge = request.GET.get("hub.challenge")

        if verify_token == settings.META_VERIFY_TOKEN:
            return HttpResponse(challenge)
        return HttpResponse("Invalid verification token", status=403)
    
    
    if request.method == 'POST':
        payload = json.loads(request.body.decode('utf-8'))
        # Nimeongeza hii function kwa ajili ya debugging
        print("📩 Incoming message payload:", json.dumps(payload, indent=2))

        try:
            entry = payload['entry'][0]
            change = entry['changes'][0]
            value = change['value']
            messages = value.get('messages')
           
            
            if not messages:
                return JsonResponse({'status': 'no messages to handle'})
            
            message = messages[0]
            phone = message.get('from')
            
            # msg_text = message.get('text', {}).get('body')
            msg_text = None
            # if not msg_text:
            #     return JsonResponse({"status": "no text message found"})
            
            if 'text' in message:
                text = message.get("text", {})
                msg_text = text.get("body", "").strip()

                
            if 'interactive' in message:
                interactive = message['interactive']
                button_reply =interactive.get('button_reply', {})
                msg_text = button_reply.get('id') or button_reply.get('title', '').strip()
            
            # Hii function ipo hapa kwa ajili ya debugging    
            print("📝 Parsed message text:", msg_text)
            if not msg_text:
                print("⚠️ No message text found, skipping response.")

            
            # interactive = message.get('interactive', {})
            # if interactive:
            #     msg_text = interactive.get("button_reply", {}).get("id") or interactive.get("button_reply", {}).get("title")
            user_session, _ = UserSession.objects.get_or_create(phone_number=phone)
            
        except (KeyError, IndexError, TypeError) as e:
            return JsonResponse({"error": f"Invalid payload structure: {str(e)}"}, status=400)
        
        

        if msg_text and msg_text.lower() in ["hi", "hello", "karibu", "habari", "salama", "hey", "mambo", "sasa", "salamu", "nikofiti"]:
            print("👋 Greeting detected, sending topic buttons.")
            
            #Add this for paginated buttons, lakini bado haijakaa sawa hivyo nitai-comment kwa muda
            #-------------------------------------------------#
            # user_session.topic_page = 1
            # user_session.save()
            # send_whatsapp_message(phone, greeting_page_1())
            #-------------------------------------------------#
            
            
            # I'll comment for a while so as to test paginated buttons
            send_whatsapp_message(phone, greeting_message())
            return JsonResponse({'status': 'ok'})
            # return JsonResponse(greeting_message())
            
            
        
        #Ninaongeza navigation logic hapa kwa ajili ya kuhama miongoni mwa kurasa mbili zenye mada 3 kila mojawapo
        #--------------------------------------------------------#
        # I'll comment for a while before refining my logic that includes more than 3 topics
        # if msg_text.lower() == "zaidi":
        #     user_session.topic_page = 2
        #     user_session.save()
        #     send_whatsapp_message(phone, greeting_page_2())
        #     return JsonResponse({"status": "ok"})
        
        # if msg_text.lower() == "rudi":
        #     user_session.topic_page = 1
        #     user_session.save()
        #     send_whatsapp_message(phone, greeting_page_1())
        #     return JsonResponse({"status": "ok"})
        #----------------------------------------------------------#    
        
        
        # To do:-Wakati naongeza topic tatu za ziada, itanibidi kuongeza hizi topic hapa kwenye Topic_Map
        TOPIC_MAP = {
        "akiba": "kuweka akiba",
        "wekeza": "kuwekeza",
        "bajeti": "kupangilia bajeti"
        }

        if msg_text and msg_text.lower() in TOPIC_MAP:
            topic_name = TOPIC_MAP[msg_text]
            topic = Topic.objects.filter(name=topic_name).first()
            if not topic:
                return JsonResponse({"status": "topic not found"}, status=404)
            # topic = Topic.objects.filter(name=msg_text).first()
            user_session.current_topic = topic
            user_session.question_index = 0
            user_session.answered_questions.clear()
            user_session.save()
            # question = Question.objects.filter(topic=topic).exclude(id__in=user_session.answered_questions.all()).first()
            question = get_random_question(topic, user_session.answered_questions.values_list('id', flat=True))
            if question is not None:
                try:
                    send_whatsapp_message(phone, send_question(question))
                except Exception as e:
                    print(f"❌ Error sending question: {e}")
            else:
                send_whatsapp_message(phone, prompt_continue_or_switch())

            # This commented code solve the same problem as the above code (not to send the same question twice)
            # if question:
            #     print(f"✅ Sending first question for topic '{topic_name}' to user {phone}")
            #     send_whatsapp_message(phone, send_question(question))
            # else:
            #     print("⚠️ No questions found, sending continue/switch prompt.")
            #     send_whatsapp_message(phone, prompt_continue_or_switch())

            # # send_whatsapp_message(phone, send_question(question))
            return JsonResponse({"status": "question sent"})

        if msg_text in ["Ndiyo", "Hapana", "yes", "no"]:
            topic = user_session.current_topic
            unanswered_qs = Question.objects.filter(topic=topic).exclude(id__in=user_session.answered_questions.all())

            if unanswered_qs.exists():
                current_q = unanswered_qs.first()
                user_session.answered_questions.add(current_q)
                
                # ✅ 1. Tuma jibu as a text message (so line breaks work)
                answer = current_q.answer_yes if msg_text == "Ndiyo" else current_q.answer_no
                send_whatsapp_message(phone, {
                    "type": "text",
                    "text": {"body": answer}
                    }
                    )
                remaining_qs = unanswered_qs.exclude(id=current_q.id)
                
                # ✅ 2. Send next question (as interactive)
                if remaining_qs.exists():
                    next_q = remaining_qs.first()
                    send_whatsapp_message(phone, send_question(next_q))
                else:
                    #Comment for a while, kwa ajili ya testing
                    # send_whatsapp_message(phone, prompt_continue_or_switch())
                    return [
                        {
                            "type": "text",
                            "text": {"body": answer}
                            },
                        prompt_continue_or_switch()
                        ]

            else:
                send_whatsapp_message(phone, prompt_continue_or_switch())
            return JsonResponse({"status": "answered"})


            # The commented code below works fine but hinders listed answers, so I've decided to separate answers and next questions by using the above code.
            #     answer = current_q.answer_yes if msg_text == "Ndiyo" else current_q.answer_no
            #     remaining_qs = unanswered_qs.exclude(id=current_q.id)
            #     if remaining_qs.exists():
            #         next_q = remaining_qs.first()
            #         send_whatsapp_message(phone, send_answer_and_question(answer, next_q))
            #     else:
            #         send_whatsapp_message(phone, send_answer_and_question(answer, None))
            # else:
            #     send_whatsapp_message(phone, prompt_continue_or_switch())
            # return JsonResponse({"status": "answered"})
            
            

        if msg_text in ["Endelea", "Badilisha Mada", "continue", "switch"]:
            if msg_text in ["Continue", "Endelea"]:
                topic = user_session.current_topic
                user_session.question_index = 0
                user_session.save()
                question = Question.objects.filter(topic=topic).exclude(id__in=user_session.answered_questions.all()).first()
                send_whatsapp_message(phone, send_question(question))
            else:
                send_whatsapp_message(phone, greeting_message())
            return JsonResponse({"status": "topic handled"})
        
        # 🧲 Fallback: treat unknown input as greeting, hii itasaidia kama user wa Bot ataandika text ambayo haipo kwa list.
        if msg_text:
            print("💬 Unrecognized input, treating as greeting.")
            send_whatsapp_message(phone, greeting_message())
            return JsonResponse({"status": "fallback greeting sent"})

    return JsonResponse({"status": "ignored"})

#----------------------------------------------------------------------------------------------------------------#
# This approch should be refined so as kuweka mada zaidi ya 3 lakini iwe na presentation nzuri kuliko hii ya sasa
#Hivyo nitai-comment kwa muda
#Create the Greeting Pages (greeting_page_1 & greeting_page_2)

# def greeting_page_1():
#     return {
#         "type": "interactive",
#         "interactive": {
#             "type": "button",
#             "header": {"type": "text", "text": "Karibu kwenye Nikofiti chatbot!"},
#             "body": {"text": "Habari👋, chagua mojawapo ya mada hizi kujifunza:"},
#             "footer": {"text": "Mada 1 ya 2"},
#             "action": {
#                 "buttons": [
#                     {"type": "reply", "reply": {"id": "akiba", "title": "kuweka akiba"}},
#                     {"type": "reply", "reply": {"id": "wekeza", "title": "kuwekeza"}},
#                     {"type": "reply", "reply": {"id": "zaidi", "title": "Zaidi..."}}
#                 ]
#             }
#         }
#     }

# def greeting_page_2():
#     return {
#         "type": "interactive",
#         "interactive": {
#             "type": "button",
#             "header": {"type": "text", "text": "Ziada ya Mada"},
#             "body": {"text": "Hizi ni mada nyingine unazoweza kujifunza:"},
#             "footer": {"text": "Mada 2 ya 2"},
#             "action": {
#                 "buttons": [
#                     {"type": "reply", "reply": {"id": "bajeti", "title": "kupangilia bajeti"}},
#                     {"type": "reply", "reply": {"id": "mikopo", "title":  "mikopo"}},
#                     {"type": "reply", "reply": {"id": "rudi", "title": "Rudi nyuma"}}
#                 ]
#             }
#         }
#     }

#----------------------------------------------------------------------------------------------------------------#



def greeting_message():
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "header": {
                "type": "text",
                "text": "Karibu kwenye Nikofiti chatbot!"
            },
            "body": {"text": "Habari👋, naitwa Nikofiti chatbot. Je, ni mambo gani unataka kujifunza leo?\t\n✅Chagua mada:"},
            "footer": {"text": "Powered by TBA ©️2025\nDeveloped by TBA Team"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "akiba", "title": "kuweka akiba"}},
                    {"type": "reply", "reply": {"id": "wekeza", "title": "kuwekeza"}},
                    {"type": "reply", "reply": {"id": "bajeti", "title": "kupangilia bajeti"}}
                ]
            }
        }
    }


def send_question(question):
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": question.question_text},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "yes", "title": "Ndiyo"}},
                    {"type": "reply", "reply": {"id": "no", "title": "Hapana"}}
                ]
            }
        }
    }

# I've commented for a while to test my bot if it works fine!
# def send_answer_and_question(answer, question):
#     if question:
#         return {
#             "type": "interactive",
#             "interactive": {
#                 "type": "button",
#                 "body": {"text": f"{answer}\n\n{question.question_text}"},
#                 "action": {
#                     "buttons": [
#                         {"type": "reply", "reply": {"id": "yes", "title": "Ndiyo"}},
#                         {"type": "reply", "reply": {"id": "no", "title": "Hapana"}}
#                     ]
#                 }
#             }
#         }
#     else:
#         return prompt_continue_or_switch()

def prompt_continue_or_switch():
    return {
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {"text": "Je, ungependa kuendelea na mada hii au kuchagua nyingine?"},
            "action": {
                "buttons": [
                    {"type": "reply", "reply": {"id": "continue", "title": "Endelea"}},
                    {"type": "reply", "reply": {"id": "switch", "title": "Badilisha Mada"}}
                ]
            }
        }
    }
