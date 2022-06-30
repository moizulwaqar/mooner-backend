from rest_framework import serializers
from .models import *


# class CategorySerializer(serializers.ModelSerializer):
#
#     class Meta:
#         model = Categories
#         fields = '__all__'

def age_restriction(value):
    if not value:
        raise serializers.ValidationError(value + "is required")


class CategoriesSerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        # fields = '__all__'
        fields = ['id', 'name', 'cat_icon', 'category_image', 'category_heading_text', 'category_heading_text2',
                  'tn_parent', 'behaviour']


class QuestionsSerializer(serializers.ModelSerializer):
    sub_category_name = serializers.CharField(source="sub_category.name", read_only=True)
    parent_category_name = serializers.CharField(source="parent_category.name", read_only=True)
    sub_child_name = serializers.CharField(source="sub_category_child.name", read_only=True)
    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id')
    sub_category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id')

    class Meta:
        model = CategoryQuestions

        fields = ['id', 'parent_category', 'sub_category', 'sub_category_child', 'parent_category_name',
                  'sub_category_name',
                  'sub_child_name','question_text', 'question_type', 'question_for', 'r_question_text', 'r_text_one',
                  'r_text_two', 'r_text_three', 'r_text_four', 'r_text_five', 'r_text_six', 'user']
    # def validate(self, data):
    #     if self.context['request'].stream.method == 'POST':
    #         user_id = self.initial_data.get('user')
    #         p_category = self.initial_data.get('sub_category')
    #         if not user_id and not p_category:
    #             msg = {'user': ['this field is required'], 'sub_category': ['this field is required']}
    #             raise serializers.ValidationError(msg)
    #         if not user_id:
    #             msg = {'user': ['this field is required']}
    #             raise serializers.ValidationError(msg)
    #         # if not p_category:
    #         #     msg = {'sub_category': ['this field is required']}
    #         #     raise serializers.ValidationError(msg)
    #         return data
    #     else:
    #         return data
