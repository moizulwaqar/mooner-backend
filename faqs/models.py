from django.db import models

# Create your models here.


class Faqs(models.Model):
    question = models.CharField(max_length=250, default="", null=True, blank=True)
    answer = models.CharField(max_length=250, default="", null=True, blank=True)
