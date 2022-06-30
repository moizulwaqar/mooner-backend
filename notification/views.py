from django.shortcuts import render
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from .serializers import *
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from mooner_backend.utils import pagination
from rest_framework import generics
from pyfcm import FCMNotification
from mooner_backend.settings import NOTIFICATION_API_KEY
# Create your views here.


class DeviceRegister(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = DeviceRegistrationSerializer

    def post(self, request):
        try:
            if request.data:
                if User.objects.filter(id=request.user.id).exists():
                    serializer = DeviceRegistrationSerializer(data=request.data)
                    if serializer.is_valid(raise_exception=True):
                        serializer.save(user=request.user)
                        return Response({"status": True, "message": "Device registered Successfully!",
                                         'data': serializer.data})
                else:
                    return Response({"status": False, "message": "User Does not exist!"})
        except ObjectDoesNotExist:
            return Response(
                {"status": False,
                 "message": "There are some error!"})


class AllDevices(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AllDevicesSerializer

    def get(self, request):
        try:
            all_records = DeviceRegistration.objects.all().order_by('-id')\
                .values('id', 'user', 'device_id', 'serial_no')
            document = pagination(all_records, request)
            return Response({"status": True, "data": document.data})
        except ObjectDoesNotExist:
            return Response(
                {"status": False,
                 "message": "There are some error!"})


class RemoveDevice(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            device_id = request.data.get('device_id')
            if DeviceRegistration.objects.filter(device_id=device_id).exists():
                DeviceRegistration.objects.filter(device_id=device_id).delete()
                return Response({"status": True, "message": "Device Deleted Successfully!"})
            else:
                return Response({"status": False, "message": "Device ID does not exist"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class AllNotification(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = AllNotificationSerializer

    def get(self, request):
        try:
            all_records = Notification.objects.filter(user=request.user).order_by('-id')\
                .values('id', 'user', 'message_title', 'message_body', 'type', 'type_id', 'user_type', 'read_status',
                        'created_at')
            document = pagination(all_records, request)
            return Response({"status": True, "data": document.data})
        except ObjectDoesNotExist:
            return Response(
                {"status": False,
                 "message": "There are some error!"})


class UpdateNotification(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UpdateNotificationSerializer

    def get_queryset(self):
        notification = Notification.objects.filter(id=self.kwargs['pk']).all()
        return notification

    def put(self, request, *args, **kwargs):
        try:
            self.update(request)
            return Response({"status": True, "message": "Notification has been updated successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class MessagesNotification(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):

        if request.data:
            if request.data.get('user_id') and request.data.get('title') and request.data.get('message'):
                device_id = DeviceRegistration.objects.filter(user_id=request.data.get('user_id')).values_list('device_id', flat=True).distinct()
                devices = list(device_id)
                push_service = FCMNotification(api_key=NOTIFICATION_API_KEY)
                push_service.notify_multiple_devices(registration_ids=devices,
                                                     message_title=request.data.get('title'),
                                                     message_body=request.data.get('message'),
                                                     )
                return Response({"status": True, "message": "Notifications has been sent successfully"})
            else:
                return Response({"status": False, "message": "All params required user_id, title, message "})


class SpLiveTracking(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        serializer = LiveTracking(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            ss = serializer.data.get("seeker_id")
            payload = dict()
            payload["type"] = 'Location'
            payload["type_id"] = serializer.data.get('job_id')
            payload["location"] = serializer.data.get('location')
            devices = list(DeviceRegistration.objects.filter(user_id=ss).values_list('device_id', flat=True).distinct())
            push_service = FCMNotification(api_key=NOTIFICATION_API_KEY)
            # message_title=request.data.get('title'),
            # message_body="SP Live location",
            push_service.multiple_devices_data_message(registration_ids=devices,
                                                       low_priority=False,
                                                       content_available=True,
                                                       data_message=payload
                                                       )
            return Response({'status': True, 'message': "Live location sent"})
        except Exception as e:
            if 'error' in e.args[-1]:
                return Response({'status': False, 'message': e.args[-1].get('error')[0]})
            else:
                return Response({'status': False, 'message': 'data is not in correct format'})


