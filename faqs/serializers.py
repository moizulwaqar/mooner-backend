from rest_framework import serializers
from .models import *


class FaqsSerializer(serializers.ModelSerializer):
    question = serializers.CharField(required=True)
    answer = serializers.CharField(required=True)

    class Meta:
        model = Faqs
        fields = ['id', 'question', 'answer']
