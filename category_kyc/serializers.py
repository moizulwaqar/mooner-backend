from rest_framework import serializers
from .models import *
from category_management.models import Category
from django.db import transaction


class CategoryKycSerializer(serializers.ModelSerializer):
    DOC_TYPE = (
        ('Public', 'Public'),
        ('Private', 'Private'),
    )

    DOC_FILE_TYPE = (
        ('Image', 'Image'),
        ('File', 'File'),
    )

    DOC_FOR = (
        ('SS', 'SS'),
        ('SP', 'SP')
    )

    CATEGORY_KYC_TYPE = (
        ('Common', 'Common'),
        ('Specific', 'Specific'),
    )

    QUESTION_TYPE = (
        ('Optional', 'Optional'),
        ('Mandatory', 'Mandatory'),
    )

    label = serializers.CharField(max_length=255, required=True)
    category_kyc_type = serializers.ChoiceField(choices=CATEGORY_KYC_TYPE, required=True)
    doc_file_type = serializers.ChoiceField(choices=DOC_FILE_TYPE, required=True)
    doc_for = serializers.ChoiceField(choices=DOC_FOR, required=False)
    doc_type = serializers.ChoiceField(choices=DOC_TYPE, required=True)
    question_type = serializers.ChoiceField(choices=QUESTION_TYPE, required=True)
    category = serializers.IntegerField(write_only=True, required=False)
    sub_category = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    sub_category_child = serializers.IntegerField(write_only=True, required=False, allow_null=True)
    common_questions = serializers.ListField(write_only=True, required=False)
    expiration_date_required = serializers.BooleanField(default=False)

    class Meta:
        model = CategoryKyc
        fields = ['id', 'label', 'category_kyc_type', 'doc_file_type', 'doc_for', 'doc_type', 'question_type',
                  'category', 'sub_category', 'sub_category_child', 'common_questions', 'expiration_date_required']

    def validate(self, attrs):

        if attrs['category_kyc_type'] == 'Specific' and self.context['request'].method == 'POST':

            # validate doc_for field
            if 'doc_for' not in attrs:
                raise serializers.ValidationError({"doc_for": "This field is required."})

            # validate category field
            if 'category' not in attrs:
                raise serializers.ValidationError({"category": "This field is required."})

            # validate common_questions field
            if 'common_questions' not in attrs:
                raise serializers.ValidationError({"common_questions": "This field is required."})

            return attrs

        return attrs

    def create(self, validated_data):
        with transaction.atomic():
            category = validated_data.pop('category', None)
            sub_category = validated_data.pop('sub_category', None)
            sub_category_child = validated_data.pop('sub_category_child', None)
            common_questions = validated_data.pop('common_questions', None)
            if validated_data.get('category_kyc_type') == 'Specific':
                if category and not sub_category and not sub_category_child:
                    check_category = Category.objects.filter(id=category)
                    if not check_category.exists():
                        raise serializers.ValidationError({"category": "Object with id={} does not exist."
                                                          .format(category)})
                    cat_kyc = CategoryKyc.objects.create(**validated_data)
                    existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=None,
                                                                     sub_category_child=None)
                    if existed_obj.exists():
                        existed_obj.first().specific_doc.add(cat_kyc)
                    else:
                        created_obj = CategorySpecificKyc.objects.create(category_id=category)
                        created_obj.specific_doc.add(cat_kyc)
                if category and sub_category and not sub_category_child:
                    check_category = Category.objects.filter(id=category)
                    if not check_category.exists():
                        raise serializers.ValidationError({"category": "Object with id={} does not exist."
                                                          .format(category)})
                    check_sub_category = Category.objects.filter(id=sub_category)
                    if not check_sub_category.exists():
                        raise serializers.ValidationError({"sub_category": "Object with id={} does not exist."
                                                          .format(sub_category)})
                    cat_kyc = CategoryKyc.objects.create(**validated_data)
                    existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                     sub_category_child=None)
                    if existed_obj.exists():
                        existed_obj.first().specific_doc.add(cat_kyc)
                    else:
                        created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                         sub_category_id=sub_category)
                        created_obj.specific_doc.add(cat_kyc)
                if category and sub_category and sub_category_child:
                    check_category = Category.objects.filter(id=category)
                    if not check_category.exists():
                        raise serializers.ValidationError({"category": "Object with id={} does not exist."
                                                          .format(category)})
                    check_sub_category = Category.objects.filter(id=sub_category)
                    if not check_sub_category.exists():
                        raise serializers.ValidationError({"sub_category": "Object with id={} does not exist."
                                                          .format(sub_category)})
                    check_sub_category_child = Category.objects.filter(id=sub_category_child)
                    if not check_sub_category_child.exists():
                        raise serializers.ValidationError({"sub_category_child": "Object with id={} does not exist."
                                                          .format(sub_category_child)})
                    cat_kyc = CategoryKyc.objects.create(**validated_data)
                    existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                     sub_category_child=sub_category_child)
                    if existed_obj.exists():
                        existed_obj.first().specific_doc.add(cat_kyc)
                    else:
                        created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                         sub_category_id=sub_category,
                                                                         sub_category_child_id=sub_category_child)
                        created_obj.specific_doc.add(cat_kyc)
            else:
                cat_kyc = CategoryKyc.objects.create(**validated_data)
                return cat_kyc
            if common_questions:
                if category and not sub_category and not sub_category_child:
                    for question in common_questions:
                        existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=None,
                                                                         sub_category_child=None)
                        obj = CategoryKyc.objects.filter(id=question)
                        if not obj.exists():
                            raise serializers.ValidationError({"common_questions": "Object with id={} does not exist."
                                                              .format(question)})
                        if existed_obj.exists():
                            existed_obj.first().specific_doc.add(obj.first())
                        else:
                            created_obj = CategorySpecificKyc.objects.create(category_id=category)
                            created_obj.specific_doc.add(obj.first())

                    # remove questions
                    selected_cat = CategorySpecificKyc.objects.filter(category=category, sub_category=None,
                                                                      sub_category_child=None)
                    selected_questions = selected_cat.first().specific_doc \
                        .filter(category_kyc_type='Common').values_list('id', flat=True)
                    remove_questions = list(set(common_questions) ^ set(selected_questions))
                    remove_obj = CategoryKyc.objects.filter(id__in=remove_questions)
                    selected_cat.first().specific_doc.remove(*remove_obj)

                if category and sub_category and not sub_category_child:
                    for question in common_questions:
                        existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                         sub_category_child=None)
                        obj = CategoryKyc.objects.filter(id=question)
                        if not obj.exists():
                            raise serializers.ValidationError({"common_questions": "Object with id={} does not exist."
                                                              .format(question)})
                        if existed_obj.exists():
                            existed_obj.first().specific_doc.add(obj.first())
                        else:
                            created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                             sub_category_id=sub_category)
                            created_obj.specific_doc.add(obj.first())

                    # remove questions
                    selected_cat = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                      sub_category_child=None)
                    selected_questions = selected_cat.first().specific_doc \
                        .filter(category_kyc_type='Common').values_list('id', flat=True)
                    remove_questions = list(set(common_questions) ^ set(selected_questions))
                    remove_obj = CategoryKyc.objects.filter(id__in=remove_questions)
                    selected_cat.first().specific_doc.remove(*remove_obj)

                if category and sub_category and sub_category_child:
                    for question in common_questions:
                        existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                         sub_category_child=sub_category_child)
                        obj = CategoryKyc.objects.filter(id=question)
                        if not obj.exists():
                            raise serializers.ValidationError({"common_questions": "Object with id={} does not exist."
                                                              .format(question)})
                        if existed_obj.exists():
                            existed_obj.first().specific_doc.add(obj.first())
                        else:
                            created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                             sub_category_id=sub_category,
                                                                             sub_category_child_id=sub_category_child)
                            created_obj.specific_doc.add(obj.first())

                    # remove questions
                    selected_cat = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                      sub_category_child=sub_category_child)
                    selected_questions = selected_cat.first().specific_doc \
                        .filter(category_kyc_type='Common').values_list('id', flat=True)
                    remove_questions = list(set(common_questions) ^ set(selected_questions))
                    remove_obj = CategoryKyc.objects.filter(id__in=remove_questions)
                    selected_cat.first().specific_doc.remove(*remove_obj)
            return cat_kyc

    def update(self, instance, validated_data):
        category = validated_data.pop('category', None)
        sub_category = validated_data.pop('sub_category', None)
        sub_category_child = validated_data.pop('sub_category_child', None)
        common_questions = validated_data.pop('common_questions', None)
        with transaction.atomic():
            if validated_data.get('category_kyc_type') == 'Specific':
                if category and not sub_category and not sub_category_child:
                    check_category = Category.objects.filter(id=category)
                    if not check_category.exists():
                        raise serializers.ValidationError({"category": "Object with id={} does not exist."
                                                          .format(category)})
                    cat_kyc = instance
                    specific_instance_id = instance.specific_doc_in_category_kyc.values_list('id', flat=True)
                    selected_cat = CategorySpecificKyc.objects.filter(id__in=specific_instance_id)
                    selected_cat.first().specific_doc.remove(cat_kyc)
                    existed_obj = CategorySpecificKyc.objects.filter(category=category,
                                                                     sub_category=None, sub_category_child=None)
                    if existed_obj.exists():
                        existed_obj.first().specific_doc.add(cat_kyc)
                    else:
                        created_obj = CategorySpecificKyc.objects.create(category_id=category)
                        created_obj.specific_doc.add(cat_kyc)
                if category and sub_category and not sub_category_child:
                    check_category = Category.objects.filter(id=category)
                    if not check_category.exists():
                        raise serializers.ValidationError({"category": "Object with id={} does not exist."
                                                          .format(category)})
                    check_sub_category = Category.objects.filter(id=sub_category)
                    if not check_sub_category.exists():
                        raise serializers.ValidationError({"sub_category": "Object with id={} does not exist."
                                                          .format(sub_category)})
                    cat_kyc = instance
                    specific_instance_id = instance.specific_doc_in_category_kyc.values_list('id', flat=True)
                    selected_cat = CategorySpecificKyc.objects.filter(id__in=specific_instance_id)
                    selected_cat.first().specific_doc.remove(cat_kyc)
                    existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                     sub_category_child=None)
                    if existed_obj.exists():
                        existed_obj.first().specific_doc.add(cat_kyc)
                    else:
                        created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                         sub_category_id=sub_category)
                        created_obj.specific_doc.add(cat_kyc)
                if category and sub_category and sub_category_child:
                    check_category = Category.objects.filter(id=category)
                    if not check_category.exists():
                        raise serializers.ValidationError({"category": "Object with id={} does not exist."
                                                          .format(category)})
                    check_sub_category = Category.objects.filter(id=sub_category)
                    if not check_sub_category.exists():
                        raise serializers.ValidationError({"sub_category": "Object with id={} does not exist."
                                                          .format(sub_category)})
                    check_sub_category_child = Category.objects.filter(id=sub_category_child)
                    if not check_sub_category_child.exists():
                        raise serializers.ValidationError({"sub_category_child": "Object with id={} does not exist."
                                                          .format(sub_category_child)})
                    cat_kyc = instance
                    specific_instance_id = instance.specific_doc_in_category_kyc.values_list('id', flat=True)
                    selected_cat = CategorySpecificKyc.objects.filter(id__in=specific_instance_id)
                    selected_cat.first().specific_doc.remove(cat_kyc)
                    existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                     sub_category_child=sub_category_child)
                    if existed_obj.exists():
                        existed_obj.first().specific_doc.add(cat_kyc)
                    else:
                        created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                         sub_category_id=sub_category,
                                                                         sub_category_child_id=sub_category_child)
                        created_obj.specific_doc.add(cat_kyc)
            else:
                cat_kyc = super().update(instance, validated_data)
                return cat_kyc
            if common_questions:
                if category and not sub_category and not sub_category_child:
                    for question in common_questions:
                        existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=None,
                                                                         sub_category_child=None)
                        obj = CategoryKyc.objects.filter(id=question)
                        if not obj.exists():
                            raise serializers.ValidationError({"common_questions": "Object with id={} does not exist."
                                                              .format(question)})
                        if existed_obj.exists():
                            existed_obj.first().specific_doc.add(obj.first())
                        else:
                            created_obj = CategorySpecificKyc.objects.create(category_id=category)
                            created_obj.specific_doc.add(obj.first())

                    # remove questions
                    selected_cat = CategorySpecificKyc.objects.filter(category=category, sub_category=None,
                                                                      sub_category_child=None)
                    selected_questions = selected_cat.first().specific_doc \
                        .filter(category_kyc_type='Common').values_list('id', flat=True)
                    remove_questions = list(set(common_questions) ^ set(selected_questions))
                    remove_obj = CategoryKyc.objects.filter(id__in=remove_questions)
                    selected_cat.first().specific_doc.remove(*remove_obj)

                if category and sub_category and not sub_category_child:
                    for question in common_questions:
                        existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                         sub_category_child=None)
                        obj = CategoryKyc.objects.filter(id=question)
                        if not obj.exists():
                            raise serializers.ValidationError({"common_questions": "Object with id={} does not exist."
                                                              .format(question)})
                        if existed_obj.exists():
                            existed_obj.first().specific_doc.add(obj.first())
                        else:
                            created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                             sub_category_id=sub_category)
                            created_obj.specific_doc.add(obj.first())

                    # remove questions
                    selected_cat = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                      sub_category_child=None)
                    selected_questions = selected_cat.first().specific_doc \
                        .filter(category_kyc_type='Common').values_list('id', flat=True)
                    remove_questions = list(set(common_questions) ^ set(selected_questions))
                    remove_obj = CategoryKyc.objects.filter(id__in=remove_questions)
                    selected_cat.first().specific_doc.remove(*remove_obj)

                if category and sub_category and sub_category_child:
                    for question in common_questions:
                        existed_obj = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                         sub_category_child=sub_category_child)
                        obj = CategoryKyc.objects.filter(id=question)
                        if not obj.exists():
                            raise serializers.ValidationError({"common_questions": "Object with id={} does not exist."
                                                              .format(question)})
                        if existed_obj.exists():
                            existed_obj.first().specific_doc.add(obj.first())
                        else:
                            created_obj = CategorySpecificKyc.objects.create(category_id=category,
                                                                             sub_category_id=sub_category,
                                                                             sub_category_child_id=sub_category_child)
                            created_obj.specific_doc.add(obj.first())

                    # remove questions
                    selected_cat = CategorySpecificKyc.objects.filter(category=category, sub_category=sub_category,
                                                                      sub_category_child=sub_category_child)
                    selected_questions = selected_cat.first().specific_doc \
                        .filter(category_kyc_type='Common').values_list('id', flat=True)
                    remove_questions = list(set(common_questions) ^ set(selected_questions))
                    remove_obj = CategoryKyc.objects.filter(id__in=remove_questions)
                    selected_cat.first().specific_doc.remove(*remove_obj)
            cat_kyc = super().update(instance, validated_data)
            return cat_kyc


class CategorySpecificSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id', required=False)
    sub_category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id', required=False)
    sub_category_child = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id', required=False)
    specific_doc = CategoryKycSerializer(many=True)

    class Meta:
        model = CategorySpecificKyc
        fields = ['category', 'sub_category', 'sub_category_child', 'specific_doc']


class CategoryKycAnswerFileSerializer(serializers.ModelSerializer):
    answer = serializers.SlugRelatedField(queryset=CategoryKycAnswer.objects.all(), slug_field='id', required=False)
    answer_url = serializers.CharField(max_length=1000, required=True)

    class Meta:
        model = CategoryKycAnswerFile
        fields = ['id', 'answer', 'answer_url']


class CategoryKycAnswerSerializer(serializers.ModelSerializer):

    ANSWER_STATUS = (
        ('Inactive', 'Inactive'),
        ('Pending', 'Pending'),
        ('Approve', 'Approve'),
        ('Disapprove', 'Disapprove')
    )

    user = serializers.SlugRelatedField(queryset=User.objects.all(), slug_field='id', required=False)
    category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id', required=True)
    sub_category = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id', required=False,
                                                allow_null=True)
    sub_category_child = serializers.SlugRelatedField(queryset=Category.objects.all(), slug_field='id', required=False,
                                                      allow_null=True)
    category_name = serializers.CharField(source='category.name', read_only=True)
    sub_category_name = serializers.CharField(source='sub_category.name', read_only=True)
    sub_category_child_name = serializers.CharField(source='sub_category_child.name', read_only=True)
    user_name = serializers.CharField(source='user.first_name', read_only=True)
    doc_file_type = serializers.CharField(source='document.doc_file_type', read_only=True)
    category_kyc_type = serializers.CharField(source='document.category_kyc_type', read_only=True)
    document = serializers.SlugRelatedField(queryset=CategoryKyc.objects.all(), slug_field='id', required=True)
    answer_text = serializers.CharField(max_length=250, required=False)
    status = serializers.ChoiceField(choices=ANSWER_STATUS, default='Pending')
    disapproval_reason = serializers.CharField(max_length=500, required=False)
    expiration_date = serializers.DateField(required=False, allow_null=True)
    file_in_cat_kyc_answer = CategoryKycAnswerFileSerializer(many=True, required=True)

    class Meta:
        model = CategoryKycAnswer
        fields = ['id', 'user', 'document', 'answer_text', 'status', 'disapproval_reason', 'expiration_date',
                  'category', 'sub_category', 'sub_category_child', 'user_name', 'doc_file_type', 'category_kyc_type',
                  'category_name', 'sub_category_name', 'sub_category_child_name', 'file_in_cat_kyc_answer']

    def validate(self, attrs):
        if not self.partial:
            document = attrs.get('document')
            expiration_date = attrs.get('expiration_date')
            category = attrs.get('category')
            if document.expiration_date_required and not expiration_date:
                raise serializers.ValidationError({"expiration_date": "This field is required."})
            if document.category_kyc_type == 'Specific' and not category:
                raise serializers.ValidationError({"category": "This field is required."})
            return attrs
        return attrs

    def create(self, validated_data):
        answer = validated_data.pop('file_in_cat_kyc_answer')
        cat_ans = CategoryKycAnswer.objects.create(**validated_data)
        for ans in answer:
            CategoryKycAnswerFile.objects.create(answer=cat_ans, **ans)
        return cat_ans

