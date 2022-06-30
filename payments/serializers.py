from rest_framework import serializers
from django.contrib.auth.models import User
from .models import *


class DeviceRegistrationSerializer(serializers.ModelSerializer):
    class Meta:
        model = StripeCustomer
        fields = ('email', 'serial_no')
        extra_kwargs = {'device_id': {'required': True}, 'serial_no': {'required': True}}


class CustomerCardSerializer(serializers.ModelSerializer):
    amount = serializers.CharField(required=True)
    token = serializers.CharField(required=True)
    title = serializers.CharField(required=True)
    email = serializers.CharField(required=True)

    class Meta:
        model = CustomerCardInfo
        fields = ('title', 'amount', 'token', 'email',)
        read_only_fields = ('amount', 'token', 'email')


class StripeConnectAccountSerializer(serializers.ModelSerializer):
    email = serializers.CharField(required=True)
    month = serializers.CharField(required=True)
    day = serializers.CharField(required=True)
    year = serializers.CharField(required=True)
    first_name = serializers.CharField(required=True)
    last_name = serializers.CharField(required=True)
    id_number = serializers.CharField(required=True)
    address = serializers.CharField(required=True)
    postal_code = serializers.CharField(required=True)
    front_pic_national_id = serializers.FileField(required=True)
    back_pic_national_id = serializers.FileField(required=True)

    class Meta:
        model = StripeConnectAccount
        fields = ('email', 'month', 'day', 'year', 'first_name', 'last_name', 'id_number', 'address', 'postal_code',
                  "front_pic_national_id", "back_pic_national_id")
        read_only_fields = ('email', 'month', 'day', 'year', 'first_name', 'last_name',
                            'id_number', 'address', 'postal_code', "front_pic_national_id", "back_pic_national_id")


class ExternalBankSerializer(serializers.ModelSerializer):
    account_holder_name = serializers.CharField(required=True)
    routing_number = serializers.CharField(required=True)
    account_number = serializers.CharField(required=True)

    class Meta:
        model = StripeConnectAccount
        fields = ('account_holder_name', 'routing_number', 'account_number',)
        read_only_fields = ('account_holder_name', 'routing_number', 'account_number',)


class CreateTokenPriceSerializer(serializers.ModelSerializer):
    admin = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id')
    set_rate = serializers.DecimalField(required=True, max_digits=10, decimal_places=2)

    class Meta:
        model = TokenRate
        fields = ('admin', 'set_rate')


class PayoutSerializer(serializers.ModelSerializer):
    token = serializers.CharField(required=True)
    bank_id = serializers.CharField(required=True)
    private_key = serializers.CharField(required=True)

    class Meta:
        model = WalletHistory
        fields = ('token', 'bank_id', 'private_key',)
        # read_only_fields = ('token', 'bank_id', 'private_key',)