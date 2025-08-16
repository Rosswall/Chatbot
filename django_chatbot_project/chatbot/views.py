import json
import google.generativeai as genai
from django.conf import settings
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_exempt
from .models import ChatMessage
import uuid
import jwt
from django.conf import settings
from django.core.cache import cache
import requests
# Configure Gemini API
genai.configure(api_key=settings.GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-2.0-flash")

def get_conversation_history(session_id, limit=10):
    """Get conversation history from database"""
    if not session_id:
        return []
    
    messages = ChatMessage.objects.filter(
        session_id=session_id
    ).order_by('timestamp')[:limit]
    
    history = []
    for msg in messages:
        history.extend([
            {"role": "user", "parts": [msg.user_message]},
            {"role": "model", "parts": [msg.bot_reply]}
        ])
    
    return history

def extract_user_from_jwt(token):
    """Extract user ID from JWT token"""
    try:
        if not hasattr(settings, 'JWT_SECRET_KEY'):
            print("JWT_SECRET_KEY not configured")
            return None
            
        payload = jwt.decode(
            token, 
            settings.JWT_SECRET_KEY, 
            algorithms=[settings.JWT_ALGORITHM],
            options={"verify_aud": False}  # Skip audience verification for now
        )
        
        user_id = (
            payload.get('sub') or
            payload.get('user_id') or
            payload.get('nameid') or
            payload.get('userId') or
            payload.get('id')
        )
        
        return {
            'user_id': user_id,
            'username': payload.get('name') or payload.get('username'),
            'email': payload.get('email'),
            'roles': payload.get('role') or payload.get('roles', [])
        }
    except jwt.ExpiredSignatureError:
        print("JWT token has expired")
        return None
    except jwt.InvalidTokenError as e:
        print(f"Invalid JWT token: {e}")
        return None
    except Exception as e:
        print(f"Error in extract_user_from_jwt: {e}")
        return None

@csrf_exempt
def chat(request):
    if request.method == 'OPTIONS':
        response = JsonResponse({})
        response['Access-Control-Allow-Origin'] = '*'
        response['Access-Control-Allow-Methods'] = 'POST, OPTIONS'
        response['Access-Control-Allow-Headers'] = 'Content-Type, Authorization'
        return response
    
    if request.method == 'POST':
        try:
            data = json.loads(request.body)
            user_message = data.get("message")
            session_id = data.get("session_id")
            
            if not user_message:
                error_response = JsonResponse({"error": "Message is required"}, status=400)
                error_response['Access-Control-Allow-Origin'] = '*'
                return error_response
            
            # Extract user info from JWT token
            user_info = None
            auth_header = request.headers.get('Authorization')
            if auth_header and auth_header.startswith('Bearer '):
                token = auth_header.split(' ')[1]
                user_info = extract_user_from_jwt(token)
            
            # Determine session identifier
            if user_info and user_info.get('user_id'):
                session_id = f"user_{user_info['user_id']}"
            elif not session_id:
                session_id = str(uuid.uuid4())

            # Get conversation history
            history = get_conversation_history(session_id)
            
            # Create chat session with history
            chat_session = model.start_chat(history=history)
            
            # Send message and get response
            response = chat_session.send_message(user_message)
            chatbot_reply = response.text

            # Save to database
            chat_message = ChatMessage.objects.create(
                user_message=user_message, 
                bot_reply=chatbot_reply,
                session_id=session_id
            )

            json_response = JsonResponse({
                "reply": chatbot_reply,
                "session_id": session_id,
                "message_id": chat_message.id,
                "user_id": user_info['user_id'] if user_info else None,
                "username": user_info['username'] if user_info else None
            })
            json_response['Access-Control-Allow-Origin'] = '*'
            return json_response
            
        except json.JSONDecodeError as e:
            print(f"JSON decode error: {e}")
            error_response = JsonResponse({"error": "Invalid JSON"}, status=400)
            error_response['Access-Control-Allow-Origin'] = '*'
            return error_response
        except Exception as e:
            print(f"Error in chat view: {e}")
            import traceback
            print(f"Traceback: {traceback.format_exc()}")
            error_response = JsonResponse({"error": f"Server error: {str(e)}"}, status=500)
            error_response['Access-Control-Allow-Origin'] = '*'
            return error_response
    
    return JsonResponse({"error": "Method not allowed"}, status=405)

def chat_history(request):
    session_id = request.GET.get('session_id')
    
    if session_id:
        messages = ChatMessage.objects.filter(session_id=session_id).order_by('-timestamp')
    elif request.user.is_authenticated:
        messages = ChatMessage.objects.filter(user=request.user).order_by('-timestamp')
    else:
        messages = ChatMessage.objects.none()
    
    return render(request, 'chatbot/history.html', {'messages': messages})

def chatbot_page(request):
    return render(request, 'chatbot/chat.html')