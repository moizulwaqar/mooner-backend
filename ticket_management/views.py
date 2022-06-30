from django.db.models import Q
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from .serializers import *
from mooner_backend.utils import email_function, pagination
from faqs.models import Faqs
from django.contrib.auth.models import User
from booking.models import Spservices, Booking, Rating


# APIs For mobile side.

class CreateTicket(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TicketSerializer

    def post(self, request, *args, **kwargs):

        serializer = TicketSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            body = '<strong>Your message:</strong> ' + serializer.data['message'] +\
                   '<br><strong>Ticket status:</strong> ' + serializer.data['status']
            email_function(body=body, email=serializer.data['email'], subject="Ticket generation")
            return Response({"status": True, "message": "Ticket has been created successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


# APIs For admin side

class GetTicket(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = TicketSerializer

    def list(self, request, *args, **kwargs):

        result = Tickets.objects.all().order_by('-id').values('id', 'name', 'category', 'message', 'comments', 'status')
        ticket = pagination(result, request)
        return Response({"status": True, "data": ticket.data})


class EditTicket(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = TicketSerializer

    def get_queryset(self):
        ticket = Tickets.objects.filter(id=self.kwargs['pk']).all()
        return ticket

    def put(self, request, *args, **kwargs):
        try:
            serializer = self.update(request)
            body = '<strong>Your message:</strong> ' + serializer.data['message'] + \
                   '<br><strong>Admin comments:</strong> ' + serializer.data['comments'] + \
                   '<br><strong>Ticket status:</strong> ' + serializer.data['status']
            email_function(body=body, subject="Ticket response", email=serializer.data['email'])
            return Response({"status": True, "message": "Ticket has been updated successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)

    def get(self, request, *args, **kwargs):
        ticket = self.get_object()
        data = Tickets.objects.filter(id=ticket.id).values('id', 'name', 'category', 'comments', 'status',
                                                           'message', 'email')
        return Response({"status": True, "data": data})

    def post(self, request, *args, **kwargs):
        ticket = self.get_object()
        obj = Faqs.objects.filter(question=ticket.message).exists()
        if not obj:
            Faqs.objects.create(question=ticket.message, answer=ticket.comments)
            return Response({"status": True, "message": "Added to FAQs successfully."})
        else:
            return Response({"status": False, "message": "Already added to FAQs."})


class SearchTicket(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        if self.request.query_params.get('search'):
            string_value = self.request.query_params.get('search')
            result = Tickets.objects.filter(Q(name__icontains=string_value) | Q(category__icontains=string_value))\
                .order_by('-id').values('id', 'name', 'category', 'message', 'comments', 'status')
            tickets = pagination(result, request)
            return Response({"status": True, "data": tickets.data})
        else:
            return Response(
                {"status": False, "Response": "Please enter the search value."})


# APIs For Report management admin side

class GetReport(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):

        service_seeker = User.objects.filter(is_superuser=False).count()
        service_provider = Spservices.objects.all().values('s_user__id').distinct().count()
        bookings = Booking.objects.all().count()
        completed_bookings = Booking.objects.filter(order_status='Completed').count()
        tickets = Tickets.objects.all().count()
        pending_tickets = Tickets.objects.filter(status='Pending').count()
        completed_tickets = Tickets.objects.filter(status='Closed').count()
        bookings_canceled = Booking.objects.filter(order_status='Cancelled').count()
        reviews = Rating.objects.all().count()
        data = {
            "service_seeker": service_seeker,
            "service_provider": service_provider,
            "bookings": bookings,
            "completed_services": completed_bookings,
            "complains": tickets,
            "pending_complains": pending_tickets,
            "completed_complains": completed_tickets,
            "bookings_canceled": bookings_canceled,
            "review": reviews
        }
        return Response({"status": True, "data": data})
