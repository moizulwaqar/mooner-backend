from rest_framework import serializers

from category_management.serializers import CategoriesSerializer
from booking.models import *
from user.models import UserProfile
from .models import SpItems, SpItemImages


class SpServiceSerializer(serializers.ModelSerializer):

    class Meta:
        model = Spservices
        fields = ['id', 'portfolio', 'about', 's_question', 's_cat_parent', 's_answers', 's_user']


class SpItemsSerializer(serializers.ModelSerializer):
    # category = CategoriesSerializer()
    opening = serializers.TimeField(format='%I:%M %p')
    closing = serializers.TimeField(format='%I:%M %p')
    user = serializers.HiddenField(default=serializers.CurrentUserDefault())

    class Meta:
        model = SpItems
        # fields = '__all__'
        fields = ["id", "category", "user", "name", "quantity", "weight", "method", "description", "opening", "closing",
                  "monday", "tuesday", "wednesday", "thursday", "friday", "saturday", "sunday", "price"]


class GetSpItemsSerializer(serializers.ModelSerializer):
    category = CategoriesSerializer()
    opening = serializers.TimeField(format='%I:%M %p')
    closing = serializers.TimeField(format='%I:%M %p')

    class Meta:
        model = SpItems
        fields = ['id', 'opening', 'closing', 'user', 'name', 'quantity', 'weight', 'method', 'description', 'monday',
                  'tuesday', 'wednesday', 'thursday', 'friday', 'saturday', 'sunday', 'category', 'price']


class SpImagesSerializer(serializers.ModelSerializer):

    class Meta:
        model = SpItemImages
        fields = '__all__'


class SPProfileSerializer(serializers.ModelSerializer):

    class Meta:
        model = UserProfile
        fields = ['cell_phone']


class SPSerializer(serializers.ModelSerializer):
    profile = SPProfileSerializer()

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'is_active', 'profile']
        extra_kwargs = {
            'username': {'read_only': True}
        }

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
        return super(SPSerializer, self).update(instance, validated_data)


class SpFilterJobsSerializer(serializers.ModelSerializer):
    categories_list = serializers.ListField(required=True)

    class Meta:
        model = Spservices
        fields = ['categories_list']

    def validate(self, attrs):
        categories_id = attrs.get('categories_list')
        if not Spservices.objects.filter(s_user=self.context['user'], s_cat_parent__in=categories_id,
                                         s_cat_parent__is_deleted=False):
            raise serializers.ValidationError({'error': ['you are not registered in these categories']})
        return attrs
