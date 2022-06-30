from django.db import models
from django.contrib.auth.models import User
from category_management.models import Category
from django.contrib.postgres.fields import ArrayField

# Create your models here.

DOC_TYPE = (
    ('Public', 'Public'),
    ('Private', 'Private')
)

DOC_FILE_TYPE = (
    ('Image', 'Image'),
    ('File', 'File')
)

DOC_FOR = (
    ('SS', 'SS'),
    ('SP', 'SP')
)

CATEGORY_KYC_TYPE = (
    ('Common', 'Common'),
    ('Specific', 'Specific')
)

QUESTION_TYPE = (
    ('Optional', 'Optional'),
    ('Mandatory', 'Mandatory')
)

ANSWER_STATUS = (
    ('Inactive', 'Inactive'),
    ('Pending', 'Pending'),
    ('Approve', 'Approve'),
    ('Disapprove', 'Disapprove')
)


class CategoryKyc(models.Model):
    label = models.CharField(max_length=255, null=True, blank=True)
    category_kyc_type = models.CharField(max_length=50, choices=CATEGORY_KYC_TYPE, null=True, blank=True)
    doc_file_type = models.CharField(max_length=50, choices=DOC_FILE_TYPE, null=True, blank=True)
    doc_for = models.CharField(max_length=50, choices=DOC_FOR, null=True, blank=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_in_cat_kyc", null=True, blank=True)
    doc_type = models.CharField(max_length=50, choices=DOC_TYPE, null=True, blank=True)
    question_type = models.CharField(max_length=50, choices=QUESTION_TYPE, null=True, blank=True)
    expiration_date_required = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        indexes = [
            models.Index(fields=['category_kyc_type'], name='category_kyc_type_idx'),
            models.Index(fields=['doc_type'], name='doc_type_idx'),
            models.Index(fields=['doc_for'], name='doc_for_idx'),
        ]
        ordering = ['-id']


class CategorySpecificKyc(models.Model):
    specific_doc = models.ManyToManyField(CategoryKyc, related_name='specific_doc_in_category_kyc')
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_in_category_kyc', null=True,
                                 blank=True)
    sub_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_category_in_category_kyc',
                                     null=True, blank=True)
    sub_category_child = models.ForeignKey(Category, on_delete=models.CASCADE,
                                           related_name='sub_category_child_in_category_kyc',
                                           null=True, blank=True)


class CategoryKycAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_cat_kyc_answer")
    document = models.ForeignKey(CategoryKyc, on_delete=models.CASCADE, related_name="document_in_cat_kyc_answer")
    answer_text = models.CharField(max_length=250, null=True, blank=True)
    # answer = ArrayField(models.CharField(max_length=1000), blank=True, null=True)
    status = models.CharField(max_length=50, choices=ANSWER_STATUS, default='Pending')
    disapproval_reason = models.CharField(max_length=500, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='category_in_category_kyc_answer',
                                 null=True, blank=True)
    sub_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name='sub_category_in_category_kyc_answer',
                                     null=True, blank=True)
    sub_category_child = models.ForeignKey(Category, on_delete=models.CASCADE,
                                           related_name='sub_category_child_in_category_kyc_answer',
                                           null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class CategoryKycAnswerFile(models.Model):
    answer = models.ForeignKey(CategoryKycAnswer, on_delete=models.CASCADE, related_name="file_in_cat_kyc_answer",
                               null=True, blank=True)
    answer_url = models.CharField(max_length=1000, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)