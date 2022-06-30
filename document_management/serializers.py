from rest_framework import serializers
from .models import Document, KycAnswer
from django.contrib.auth.models import User


class DocumentSerializer(serializers.ModelSerializer):

    class Meta:
        model = Document
        fields = '__all__'


class KycAnswerSerializer(serializers.ModelSerializer):
    # user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id')
    document = serializers.SlugRelatedField(queryset=Document.objects.all(), slug_field='id')
    answer = serializers.ListField(child=serializers.CharField())

    class Meta:
        model = KycAnswer

        fields = ['id', 'document', 'user', 'answer_text', 'answer',
                  'status', 'disapproval_reason']

