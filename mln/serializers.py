from rest_framework import serializers
from .models import Referral, LevelsPercentage, TokenHistory


class ReferralSerializer(serializers.ModelSerializer):

    class Meta:
        model = Referral
        fields = '__all__'


class LevelsPercentageSerializer(serializers.ModelSerializer):

    class Meta:
        model = LevelsPercentage
        fields = '__all__'

    def update(self, instance, validated_data):
        level_0 = validated_data.get('level_0')
        level_1 = validated_data.get('level_1')
        level_2 = validated_data.get('level_2')
        level_3 = validated_data.get('level_3')
        level_4 = validated_data.get('level_4')
        if not level_0 or not level_1 or not level_2 or not level_3 or not level_4:
            raise serializers.ValidationError({'error': ['Please enter a valid number.']})
        total_sum = level_0 + level_1 + level_2 + level_3 + level_4
        if total_sum != 100:
            raise serializers.ValidationError({'error': ['Total sum of levels amount should be equal to 100.']})
        instance.level_0 = level_0
        instance.level_1 = level_1
        instance.level_2 = level_2
        instance.level_3 = level_3
        instance.level_4 = level_4
        instance.save()
        return instance


class TokenHistorySerializer(serializers.ModelSerializer):

    class Meta:
        model = TokenHistory
        fields = '__all__'

    def create(self, validated_data):
        earned_by = validated_data.get('earned_by')
        earned_from = validated_data.get('earned_from')
        earn_tokens = validated_data.get('earn_tokens')

        history = TokenHistory.objects.filter(earned_by=earned_by, earned_from=earned_from).exists()
        if history:
            obj = TokenHistory.objects.get(earned_by=earned_by, earned_from=earned_from)
            previous_tokens = obj.earn_tokens
            obj.earn_tokens = previous_tokens + earn_tokens
            obj.save()
            return obj
        else:
            return TokenHistory.objects.create(earned_by=earned_by, earned_from=earned_from, earn_tokens=earn_tokens)
