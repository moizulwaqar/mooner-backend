from rest_framework.response import Response
import datetime
from datetime import datetime as dt
from django.db.models import F, Value, When, Case, ImageField
from django.db.models.functions import Concat
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from booking.models import Booking
from .serializers import *


class OverallStates(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):
        try:
            current = datetime.date.today()
            date = request.data.get('date')
            today = dt.strptime(date, '%Y-%m-%d').date()
            if today > current:
                return Response({"status": False, "message": "Only available till current date."})
            startDate = today - datetime.timedelta(days=6)
            endDate = today + datetime.timedelta(days=1)
            users = User.objects.filter(date_joined__range=[startDate, endDate]).count()
            admin_team = User.objects.filter(is_superuser=True).values('profile__profile_image')
            total_admin_users = admin_team.count()
            admin_users_images = admin_team.annotate(
                image=Case(
                    When(profile__profile_image='', then=Value('', output_field=ImageField())),
                    default=Concat(Value('/media/'), F('profile__profile_image')), output_field=ImageField()),
                ).values('image').order_by('-id')[:8]

            active_orders = Booking.objects.filter(order_status='Active',
                                                   start_date__date=today).count()
            completed_orders = Booking.objects.filter(order_status='Completed',
                                                      end_date__date=today).count()

            data = {
                "date": date,
                "weekly_sign_ups": users,
                "user_images": admin_users_images,
                "total_admin_count": total_admin_users,
                "active_orders": active_orders,
                "completed_orders": completed_orders
            }
            return Response({"status": True, "data": data})
        except:
            return Response({"status": False, "Response": "Images are not provided"})
