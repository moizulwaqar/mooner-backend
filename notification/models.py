from django.db import models
from django.contrib.auth.models import User
# Create your models here.

NOTIFICATION_TYPE = (
    ('Job', 'Job'),
    ('Bid', 'Bid'),
    ('Booking', 'Booking'),
    ('User', 'User'),
    ('Category', 'Category'),
    ('SpServices', 'SpServices'),
    ('Payment', 'Payment'),
    ('Ticket', 'Ticket'),
    ('Document', 'Document'),
)

USER_CHOICE = (
    ('SS', 'SS'),
    ('SP', 'SP')
)


class DeviceRegistration(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_in_device_registration')
    device_id = models.CharField(max_length=250)
    serial_no = models.CharField(max_length=250, null=True, blank=True)

    def __str__(self):
        return self.device_id


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_in_notification')
    message_title = models.CharField(max_length=250, null=True, blank=True)
    message_body = models.CharField(max_length=250, null=True, blank=True)
    type = models.CharField(max_length=20, choices=NOTIFICATION_TYPE, null=True, blank=True)
    type_id = models.TextField(null=True, blank=True)
    read_status = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    user_type = models.CharField(max_length=50, choices=USER_CHOICE, null=True, blank=True)

    def __str__(self):
        return self.message_title
