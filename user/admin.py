from django.contrib import admin
from .models import UserProfile, Role, UserAddresses
# Register your models here.

admin.site.register(UserProfile)
admin.site.register(Role)
admin.site.register(UserAddresses)