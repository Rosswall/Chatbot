from django.db import models
from django.contrib.auth.models import User

class ChatMessage(models.Model):
    user_message = models.TextField()
    bot_reply = models.TextField()
    timestamp = models.DateTimeField(auto_now_add=True)
    session_id = models.CharField(max_length=255, null=True, blank=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)  # Django users
    
    
    def __str__(self):
        
        if self.session_id and self.session_id.startswith('user_'):
            user_id = self.session_id.replace('user_', '')
            return f"{self.timestamp} - User {user_id}: {self.user_message}"
        return f"{self.timestamp} - Session {self.session_id}: {self.user_message}"

    class Meta:
        ordering = ['-timestamp']