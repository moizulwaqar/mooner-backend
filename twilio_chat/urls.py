from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('chat/', TwilioChats.as_view()),
    path('user_channel/', UserChannel.as_view())
]
