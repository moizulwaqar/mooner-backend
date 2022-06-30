from rest_framework import serializers
from django.contrib.auth.models import User
from .models import UserProfile, Role, UserAddresses
from django.utils.translation import gettext_lazy as _

ADDRESS_TYPE = (
        ("Home", "Home"),
        ("Work", "Work"),
        ("Other", "Other"),
    )


class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = '__all__'


class RoleSerializer(serializers.ModelSerializer):
    class Meta:
        model = Role
        fields = '__all__'


class UserSerializer(serializers.ModelSerializer):
    profile = UserProfileSerializer()
    # role = RoleSerializer()

    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'is_active', 'profile']


class SeekerProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserProfile
        fields = ['cell_phone', 'country', 'state', 'profile_image', 'postal_code']


class SeekerSerializer(serializers.ModelSerializer):
    profile = SeekerProfileSerializer()
    # role = RoleSerializer()

    class Meta:
        model = User
        fields = ['id', 'email', 'first_name', 'is_active', 'profile']

    def update(self, instance, validated_data):
        email = validated_data.get('email', '')
        cell_phone = validated_data.get('profile', 'cell_phone')
        if User.objects.exclude(pk=instance.pk).filter(email=email):
            raise serializers.ValidationError({'error': ['User with that email already exists.']})
        if UserProfile.objects.exclude(user=instance).filter(cell_phone=cell_phone['cell_phone']):
            raise serializers.ValidationError({'error': ['User with that cell_phone already exists.']})
        if not cell_phone['cell_phone'].startswith("+"):
            raise serializers.ValidationError({'error': ['Phone Number must starts with +.']})
        elif len(cell_phone['cell_phone']) < 9 or len(cell_phone['cell_phone']) > 15:
            raise serializers.ValidationError(
                {'error': ['Length of Phone number should not be less than 9 or greater than 15.']})
        profile_data = validated_data.pop('profile', {})
        profile = instance.profile
        for attr, value in profile_data.items():
            setattr(profile, attr, value)
        profile.save()
        return super(SeekerSerializer, self).update(instance, validated_data)


class UserAddressSerializer(serializers.ModelSerializer):
    label = serializers.CharField(required=False)
    address = serializers.CharField(required=False)
    latitude = serializers.FloatField(required=False)
    longitude = serializers.FloatField(required=False)
    location = serializers.CharField(required=False, write_only=True)
    address_type = serializers.ChoiceField(choices=ADDRESS_TYPE, required=False)

    class Meta:
        model = UserAddresses
        fields = ['id', 'label', 'address', 'floor_no', 'unit_no', 'location', 'address_type', 'latitude', 'longitude',
                  'user']

    def validate(self, attrs):
        label = attrs.get('label')
        if label:
            label = label.title()
        address = attrs.get('address')
        lat = attrs.get('latitude')
        long = attrs.get('longitude')
        address_type = attrs.get('address_type', '')

        if not self.partial:
            user_address = UserAddresses.objects.filter(label=label, user=self.context['user'])
            if user_address.exists():
                raise serializers.ValidationError({'error': _("label already exists")})
            if not label:
                raise serializers.ValidationError({'error': _("label is required")})
            if not address:
                raise serializers.ValidationError({'error': _("address is required")})
            if not lat:
                raise serializers.ValidationError({'error': _('latitude is required')})
            if not long:
                raise serializers.ValidationError({'error': _('longitude is required')})
            if not address_type:
                raise serializers.ValidationError({'error': _('address_type is required')})
            return attrs
        else:
            user_address = UserAddresses.objects.filter(label=label, user=self.context['request'].user)
            if user_address.exists():
                raise serializers.ValidationError({'error': _("label already exists")})
            return attrs

    def create(self, validated_data):
        user = self.context['user']
        validated_data['label'] = validated_data["label"].title()
        create_address = UserAddresses.objects.create(
            user=user,
            **validated_data
        )
        return create_address

    def update(self, instance, validated_data):
        if 'label' in validated_data:
            validated_data['label'] = validated_data["label"].title()
            UserAddresses.objects.filter(pk=instance.id) \
                .update(**validated_data)
            address = UserAddresses.objects.get(pk=instance.id)
        else:
            UserAddresses.objects.filter(pk=instance.id) \
                .update(**validated_data)
            address = UserAddresses.objects.get(pk=instance.id)

        return address







