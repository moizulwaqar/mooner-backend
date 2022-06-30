from django.contrib import admin
from django.urls import path, include
from .views import *

urlpatterns = [
    path('device_register/', DeviceRegister.as_view(), name="device_register"),
    path('all_devices/', AllDevices.as_view(), name="all_devices"),
    path('remove_devices/', RemoveDevice.as_view(), name="remove_devices"),
    path('all_notification/', AllNotification.as_view(), name="all_notification"),
    path('update_notification/<int:pk>/', UpdateNotification.as_view(), name="update_notification"),
    path('notification_for_chat/', MessagesNotification.as_view(), name='notification_for_chat'),
    path('live_tracking/', SpLiveTracking.as_view(), name='live_tracking')
    ]