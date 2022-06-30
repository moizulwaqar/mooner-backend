from django.urls import path, include
from .views import *

urlpatterns = [
    path('faqs/', Faq.as_view()),
    path('faqs/<int:pk>', GetFaq.as_view()),
    path('search_faqs/', SearchFaqs.as_view())
]