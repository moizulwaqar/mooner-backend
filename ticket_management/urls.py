from django.urls import path
from .views import *

urlpatterns = [
    path('create_ticket/', CreateTicket.as_view()),
    path('edit_ticket/<int:pk>/', EditTicket.as_view()),
    path('get_ticket/', GetTicket.as_view()),
    path('search_ticket/', SearchTicket.as_view()),

    # Report management URL
    path('get_report/', GetReport.as_view()),

]
