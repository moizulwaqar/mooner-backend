from django.db import models
from django.contrib.auth.models import User
from category_management.models import Category
from django.contrib.postgres.fields import ArrayField
import datetime

# Create your models here.

DOCUMENT_STATUS = (
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Disapproved', 'Disapproved')
)

DOCUMENT_TYPE = (
    ('Default', 'Default'),
    ('Certificate', 'Certificate'),
    ('Educational', 'Educational'),
    ('Government', 'Government'),
    ('KYC', 'KYC'),
    ('ID CARD', 'ID CARD'),
    ('Driving License', 'Driving License')
)

OCCUPATION_TYPE = (
    ('Default', 'Default'),
    ('Driver', 'Driver'),
)

DOCUMENT_FOR = (
    ('SS', 'SS'),
    ('SP', 'SP'),
)

DOC_QUESTION_TYPE = (
    ('File', 'File'),
    ('Image', 'Image'),
    ('Text', 'Text')
)


Answer_Status = (
    ('Inactive', 'Inactive'),
    ('Pending', 'Pending'),
    ('Approve', 'Approve'),
    ('Disapprove', 'Disapprove')
)


class Document(models.Model):
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sp_in_document", null=True,
                           blank=True)
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ss_in_document", null=True,
                           blank=True)
    admin = models.ForeignKey(User, on_delete=models.SET_NULL, related_name="admin_in_document", null=True,
                              blank=True)
    parent_category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                        related_name='parent_category_in_document')
    sub_category = models.ForeignKey(Category, on_delete=models.CASCADE, null=True, blank=True,
                                     related_name='sub_category_in_document')
    doc_label = models.CharField(max_length=30, null=True, blank=True)
    status = models.CharField(max_length=50, choices=DOCUMENT_STATUS, null=True, blank=True, default='Pending')
    doc_type = models.CharField(max_length=50, choices=DOCUMENT_TYPE, null=True, blank=True, default='Default')
    occupation = models.CharField(max_length=50, choices=OCCUPATION_TYPE, null=True, blank=True, default='Default')
    experience = models.CharField(max_length=500, null=True, blank=True)
    expiration_date = models.DateField(null=True, blank=True)  # default format yyyy-mm-dd
    vehicle_number = models.CharField(max_length=50, null=True, blank=True)
    vehicle_year = models.CharField(max_length=50, null=True, blank=True)
    disapproval_reason = models.CharField(max_length=500, null=True, blank=True)
    image_urls = ArrayField(models.CharField(max_length=1000), blank=True, null=True)
    doc_for = models.CharField(max_length=50, choices=DOCUMENT_FOR, null=True, blank=True, default='SS')
    id_card_number = models.CharField(max_length=50, null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.today)
    updated_at = models.DateTimeField(auto_now_add=True)
    doc_question_type = models.CharField(max_length=50, choices=DOC_QUESTION_TYPE, null=True, blank=True,
                                         default='Image')


class KycAnswer(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_KycAnswer")
    document = models.ForeignKey(Document, on_delete=models.CASCADE, related_name="document_in_KycAnswer")
    answer_text = models.CharField(max_length=250, null=True, blank=True)
    answer = ArrayField(models.CharField(max_length=1000), blank=True, null=True)
    status = models.CharField(max_length=50, choices=Answer_Status, default='Pending')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
    disapproval_reason = models.CharField(max_length=500, null=True, blank=True)
