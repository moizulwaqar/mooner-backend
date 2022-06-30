from django.db import models
from django.contrib.auth.models import User
import datetime


# Create your models here.
class TwilioChat(models.Model):
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ss_in_twilio_chat", null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sp_in_twilio_chat", null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.today)
    last_chat = models.DateTimeField(auto_now_add=True)
    channel_id = models.CharField(max_length=50, null=True, blank=True)
    twilio_channel_sid = models.CharField(max_length=50, unique=True, null=True, blank=True)
    ss_twilio_user_sid = models.CharField(max_length=50, null=True, blank=True)
    sp_twilio_user_sid = models.CharField(max_length=50, null=True, blank=True)

    def __str__(self):
        return self.channel_id
