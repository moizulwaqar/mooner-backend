from django.db import models
from django.contrib.auth.models import User
import datetime
# Create your models here.

TICKET_STATUS = (
    ('Active', 'Active'),
    ('Pending', 'Pending'),
    ('Closed', 'Closed'),
)

CATEGORY_CHOICES = (
    ('Accounts', 'Accounts'),
    ('Bugs Reporting', 'Bugs Reporting'),
    ('General', 'General'),
)


class Tickets(models.Model):
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sp_in_tickets", null=True,
                           blank=True)
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ss_in_tickets", null=True,
                           blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="admin_in_tickets", null=True,
                              blank=True)
    name = models.CharField(max_length=30, null=True, blank=True)
    email = models.EmailField(null=True, blank=True)
    status = models.CharField(max_length=50, choices=TICKET_STATUS, null=True, blank=True, default='Active')
    category = models.CharField(max_length=50, choices=CATEGORY_CHOICES, null=True, blank=True, default='General')
    company_details = models.CharField(max_length=500, null=True, blank=True)
    message = models.CharField(max_length=500, null=True, blank=True)
    comments = models.CharField(max_length=500, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.today)
    updated_at = models.DateTimeField(auto_now_add=True)
