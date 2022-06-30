from rest_framework import serializers
from .models import *


class PrivacyPolicySerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    policy_content = serializers.CharField()

    class Meta:
        model = PrivacyPolicy
        # fields = "__all__"
        fields = ["id", "policy_content", "user"]

    def validate(self, attrs):
        if not self.partial:
            if PrivacyPolicy.objects.exists() and self.context['request'].method == 'POST':
                raise serializers.ValidationError(
                    {'error': "Privacy Policy content already exists!"})
            return attrs
        else:
            return attrs


class AboutContentSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    about_content = serializers.CharField()

    class Meta:
        model = AboutContent
        # fields = "__all__"
        fields = ["id", "about_content", "user"]

    def validate(self, attrs):
        if AboutContent.objects.exists() and self.context['request'].method == 'POST':
            raise serializers.ValidationError(
                {'error': "About Content already exists!"})
        return attrs


class TermsAndConditionSerializer(serializers.ModelSerializer):
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    terms_and_condition = serializers.CharField()

    class Meta:
        model = TermsAndCondition
        # fields = "__all__"
        fields = ["id", "terms_and_condition", "user"]

    def validate(self, attrs):
        if TermsAndCondition.objects.exists() and self.context['request'].method == 'POST':
            raise serializers.ValidationError(
                {'error': "Terms and condition already exists!"})
        return attrs
