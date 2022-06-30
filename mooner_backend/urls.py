"""mooner_backend URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .utils import UploadFile, DeleteFile, UrlConcat, TwilioToken

urlpatterns = [
    path('admin/', admin.site.urls),
    path('account/', include('user.urls')),
    path('user_management/', include('user_management.urls')),
    path('category_management/', include('category_management.urls')),
    path('ticket_management/', include('ticket_management.urls')),
    path('document_management/', include('document_management.urls')),
    path('api/token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),
    path('api/refresh/', TokenRefreshView.as_view(), name='token_refresh'),


    ############ Booking app Url ##################
    path('booking/', include('booking.urls')),
    path('service_provider/', include('service_provider.urls')),
    path('mooner_faqs/', include('faqs.urls')),
    path('upload_file/', UploadFile.as_view(), name='upload_file'),
    path('delete_file/', DeleteFile.as_view(), name='delete_file'),
    path('url_concat/', UrlConcat.as_view(), name='url_concat'),
    path('twilio_token/', TwilioToken.as_view(), name='twilio_token'),
    path('twilio_chat/', include('twilio_chat.urls')),
    path('payments/', include('payments.urls')),
    path('notification/', include('notification.urls')),
    path('mln/', include('mln.urls')),
    path('privacy/', include('privacy_policy.urls')),
    path('category_kyc/', include('category_kyc.urls'))

] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
