from django.db import models
from django.contrib.auth.models import User
from category_management.models import Category, CategoryQuestions
# from django.contrib.gis.db.models import GeoManager
# from django.contrib.gis.db import models as gis_model
import datetime
from django.contrib.postgres.fields import ArrayField
from django_softdelete.models import SoftDeleteModel
# Create your models here.


ORDER_STATUS = (
    ('Pending', 'Pending'),
    ('Active', 'Active'),
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
    ('Anytime Now', 'Anytime Now'),
    ('At Your Doorstep', 'At Your Doorstep')
)

JOB_STATUS = (
    ('Active', 'Active'),
    ('InActive', 'InActive'),
    ('Pending', 'Pending'),
    ('Hired', 'Hired')
)

CANCELLED_BY = (
    ('SS', 'SS'),
    ('SP', 'SP'),
)
UPDATE_BY = (
    ('Admin', 'Admin'),
    ('SP', 'SP'),
)
ADDRESSES_TYPE = (
    ('Home', 'Home'),
    ('Work', 'Work'),
    ('Other', 'Other')
)

DISPUTE_STATUS = (
    ('Pending', 'Pending'),
    ('Approved', 'Approved'),
    ('Rejected', 'Rejected'),

    )

PAYMENT_STATUS = (
    ('Accept', 'Accept'),
    ('Reject', 'Reject'),
    ('Pending', 'Pending')
)


class Jobs(SoftDeleteModel):
    ssid = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ss_id", null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sp_in_jobs", null=True, blank=True)
    created_at = models.DateTimeField(default=datetime.datetime.today)
    updated_at = models.DateTimeField(auto_now_add=True)
    job_status = models.CharField(max_length=50, choices=JOB_STATUS, null=True, blank=True, default='Active')
    job_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="job_category_id", null=True,
                                     blank=True)
    job_cat_child = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="job_cat_child_id", null=True,
                                      blank=True)
    budget = models.IntegerField(default=0, null=True, blank=True)

    time = models.CharField(max_length=50, null=True, blank=True, default="")
    booking_date = models.CharField(max_length=50, null=True, blank=True, default="")
    job_description = models.CharField(max_length=500, null=True, blank=True)
    schedule = models.DateTimeField(default=datetime.datetime.today)
    image_urls = ArrayField(models.CharField(max_length=1000), blank=True, null=True)
    ss_stripe_token = models.CharField(max_length=100, null=True, blank=True)
    ss_stripe_email = models.EmailField(max_length=255, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    floor_no = models.CharField(max_length=50, null=True, blank=True)
    unit_no = models.CharField(max_length=50, null=True, blank=True)


class Booking(SoftDeleteModel):
    start_date = models.DateTimeField(default=datetime.datetime.today)
    end_date = models.DateTimeField(default=datetime.datetime.today)
    modified_data = models.DateTimeField(auto_now_add=True)
    order_status = models.CharField(max_length=50, choices=ORDER_STATUS, null=True, blank=True, default='Active')
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name="booking_job_id", null=True, blank=True)
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_ss_id", null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="booking_sp_id", null=True, blank=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="booking_category_id", null=True,
                                 blank=True)
    cat_child_id = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="cat_child_id", null=True,
                                     blank=True)
    budget = models.IntegerField(default=0, null=True, blank=True)
    time = models.CharField(max_length=50, null=True, blank=True, default="")
    booking_date = models.CharField(max_length=50, null=True, blank=True, default="")
    cancelled_by = models.CharField(max_length=50, choices=CANCELLED_BY, null=True, blank=True)
    is_payment = models.BooleanField(default=False)
    is_tip_request = models.BooleanField(default=False)
    tip_request_count = models.IntegerField(default=0)
    again_tip_request = models.BooleanField(default=True)


class Answer(SoftDeleteModel):
    question_id = models.ForeignKey(CategoryQuestions, on_delete=models.CASCADE, related_name='questions_answers',
                                    null=True, blank=True)
    booking_id = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="ss_booking", null=True, blank=True)
    jobs_id = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name="ss_job", null=True, blank=True)
    cat_parent_id = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="cat_parent_answers", null=True,
                                      blank=True)
    child_category = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="cat_child_answers", null=True,
                                       blank=True)
    answer = models.CharField(max_length=250, null=True, blank=True)
    answer_file = models.FileField(upload_to="answers/", null=True, blank=True)
    sp_services = models.ForeignKey("Spservices", on_delete=models.CASCADE, related_name="sp_service_ans", null=True,
                                    blank=True)


class Spservices(models.Model):
    s_question = models.ForeignKey(CategoryQuestions, on_delete=models.CASCADE, related_name='squestions',
                                   null=True, blank=True)
    s_cat_parent = models.ForeignKey(Category, on_delete=models.CASCADE, related_name="scat_parent", null=True,
                                     blank=True)
    s_answers = models.ForeignKey(Answer, on_delete=models.CASCADE, related_name="cat_parent_answers", null=True,
                                  blank=True)
    s_user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="s_user_in_spservices", null=True,
                               blank=True)
    portfolio = models.CharField(max_length=250, null=True, blank=True)
    about = models.CharField(max_length=250, null=True, blank=True)
    budget = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True, default=0)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    # location = gis_model.PointField(null=True, blank=True)
    image_urls = ArrayField(models.CharField(max_length=1000), blank=True, null=True)
    # objects = GeoManager()
    is_active = models.BooleanField(default=True)
    in_active_by = models.CharField(max_length=50, choices=UPDATE_BY, null=True, blank=True)


class Bids(models.Model):
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name="bd_job_id", null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="bid_sip_id", null=True, blank=True)
    price = models.IntegerField(default=0, null=True, blank=True)
    time = models.DateTimeField(auto_now_add=True)
    status = models.CharField(max_length=50, choices=JOB_STATUS, null=True, blank=True, default='Active')


class Rating(models.Model):
    rated_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rated_by_in_rating')
    rated_to = models.ForeignKey(User, on_delete=models.CASCADE, related_name='rated_to_in_rating')
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking')
    feedback = models.CharField(max_length=400, null=True)
    star = models.FloatField(default=0.0)
    created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    updated_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)


class JobFiles(models.Model):
    job = models.ForeignKey(Jobs, on_delete=models.CASCADE, related_name="Job_files")
    file = models.FileField(upload_to="job_post_files/")


class SpServiceImages(models.Model):
    sp_service = models.ForeignKey(Spservices, on_delete=models.CASCADE, related_name="sp_service_files")
    file = models.FileField(upload_to="sp_files/")


class Dispute(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_in_dispute')
    reason = models.CharField(max_length=400, null=True, blank=True)
    dispute_status = models.CharField(max_length=50, choices=DISPUTE_STATUS, null=True, blank=True)
    ss_created_at = models.DateTimeField(auto_now_add=True, null=True, blank=True)
    admin_updated_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ['-id']
        indexes = [
            models.Index(fields=['dispute_status'], name='dispute_status_idx')

        ]


class SPAddPrice(models.Model):

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_in_spaddprice')
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name='sp_in_spaddprice')
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name='ss_in_spaddprice')
    description = models.CharField(max_length=250, null=True, blank=True)
    add_amount = models.IntegerField(default=0, null=True, blank=True)
    stripe_token = models.CharField(max_length=50, null=True, blank=True)
    charge_id = models.CharField(max_length=50, null=True, blank=True)
    payment_status = models.CharField(max_length=50, choices=PAYMENT_STATUS, default='Pending')
    add_price_is_payment = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-id']


class Tip(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_in_tips', null=True,
                                blank=True)
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    status = models.BooleanField(default=False)
    charge_id = models.CharField(max_length=50, null=True, blank=True)
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ss_id_tips", null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sp_id_tips", null=True, blank=True)


class AdminConvenienceFee(models.Model):
    admin_fees = models.IntegerField(default=0, null=True, blank=True)
    convenience_fees = models.IntegerField(default=0, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class AdminTransactionList(models.Model):
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='booking_in_admin_fee_list', null=True,
                                blank=True)
    earn_tokens = models.CharField(max_length=255, null=True, blank=True)
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name='admin_in_fee_list')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)
