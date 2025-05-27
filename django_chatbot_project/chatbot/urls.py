from django.urls import path
from .views import chat, chatbot_page, chat_history

urlpatterns = [
    path("chat/", chat, name="chat"),
    path("history/", chat_history, name="chat_history"),
    path("", chatbot_page, name="chat_page"),
]
