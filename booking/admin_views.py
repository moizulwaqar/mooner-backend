from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from .serializers import *
from rest_framework.response import Response
from django.db.models import F, Q
from mooner_backend.utils import pagination


class GetBookingList(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Booking.objects.filter(category__is_deleted=False)
    serializer_class = BookingAdminSerializer

    def post(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        data = Booking.objects.filter(Q(sp=user_id) | Q(ss=user_id), category__is_deleted=False).values('id', 'start_date', 'budget', 'order_status',
                                                         seeker=F('ss__username'),
                                                         category_name=F('category__name')
                                                         )
        result = pagination(data, request)
        return Response({"status": True, "data": result.data})


class ChangeBookingStatus(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer

    def put(self, request, *args, **kwargs):
        order_status = request.data.get('order_status')
        booking = Booking.objects.get(id=kwargs['pk'])
        booking.order_status = order_status
        booking.save()

        return Response({"status": True, "message": "Order status has been changed successfully"})


class DeleteBooking(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Booking.objects.all()
    serializer_class = BookingSerializer


class UserManagementView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Booking.objects.filter(category__is_deleted=False).order_by('-id')
    serializer_class = BookingAdminSerializer

    def get(self, request, *args, **kwargs):
        user_details = User.objects.filter(id=kwargs['pk']).values('id', 'username', 'email', 'first_name', 'last_name',
                                                                   phone=F('profile__cell_phone'),
                                                                   reference_id=F('profile__reference_id'),
                                                                   level=F('profile__level'),
                                                                   status=F('is_active'))
        user_bookings = Booking.objects.filter(ss=kwargs['pk'], ss__is_active=True, category__is_deleted=False).values(
            'id', 'start_date', 'budget', 'order_status', seeker=F('ss__username'),
            category_name=F('category__name')).order_by('-id')[:2]

        return Response({"status": True, "user_details": user_details, "user_bookings": user_bookings})
