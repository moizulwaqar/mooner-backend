from abc import ABC
from rest_framework import serializers
from .models import *
from booking.models import Booking
from django.utils.translation import gettext_lazy as _


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceRegistration
        fields = ('device_id', 'serial_no')
        extra_kwargs = {'device_id': {'required': True}, 'serial_no': {'required': True}}


class AllDevicesSerializer(serializers.ModelSerializer):
    class Meta:
        model = DeviceRegistration
        fields = '__all__'


class AllNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = '__all__'


class UpdateNotificationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Notification
        fields = ('read_status',)


class LiveTracking(serializers.Serializer):
    job_id = serializers.IntegerField(required=False)
    booking_id = serializers.IntegerField(required=False)
    seeker_id = serializers.IntegerField(required=False)
    location = serializers.JSONField(required=False)
    # lat = serializers.FloatField(required=True)
    # long = serializers.FloatField(required=True)

    def validate(self, data):
        job = data.get('job_id')
        booking = data.get('booking_id')
        seeker_id = data.get('seeker_id')
        id_booking = None
        id_seeker = None
        if job:
            job_booking = Booking.objects.filter(job_id=job)
            if not job_booking.exists():
                raise serializers.ValidationError({'error': _("Booking does not exists against this job")})
            booking_object = job_booking.first()
            id_booking = booking_object.id
            id_seeker = booking_object.ss.id

        else:
            raise serializers.ValidationError({'error': _("job_id is required")})
        if not booking:
            raise serializers.ValidationError({'error': _("Booking id is required")})
        else:
            if id_booking and booking:
                if id_booking != booking:
                    raise serializers.ValidationError({'error': _("Booking id is not correct")})
            else:
                raise serializers.ValidationError({'error': _("Booking does not exists against this job")})
        if id_seeker:
            pass
            # if id_seeker and seeker_id:
            #     if id_seeker != seeker_id:
            #         raise serializers.ValidationError({'error': _("seeker_id is not correct")})
        else:
            raise serializers.ValidationError({'error': _("seeker does exits")})

        return data
