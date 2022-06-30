from django.contrib import admin
from .models import Document, KycAnswer

# Register your models here.
admin.site.register(Document)
admin.site.register(KycAnswer)
