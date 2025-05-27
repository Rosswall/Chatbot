import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import ChatMessage

# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")  # Use the appropriate model

@csrf_exempt
def chat(request):
    if request.method == 'POST':
        data = json.loads(request.body)
        user_message = data.get("message")

        try:
            response = model.generate_content(user_message)
            chatbot_reply = response.text

            # Save to database
            ChatMessage.objects.create(user_message=user_message, bot_reply=chatbot_reply)

            return JsonResponse({"reply": chatbot_reply})
        except Exception as e:
            return JsonResponse({"error": str(e)}, status=500)

def chatbot_page(request):
    return render(request, 'chatbot/chat.html')

def chat_history(request):
    messages = ChatMessage.objects.all().order_by('-timestamp')
    return render(request, 'chatbot/history.html', {'messages': messages})