from django.db import models
from django.contrib.auth.models import User
from booking.models import Booking
# from django.contrib.gis.db import models as gis_model


# Create your models here.
class Role(models.Model):
    ROLE = (
        ('Super_Admin', 'Super_Admin'),
        ('Sub_Admin', 'Sub_Admin'),
        ('Finance_Head', 'Finance_Head'),
        ('Finance_Junior', 'Finance_Junior'),
        ('Customer_Service', 'Customer_Service'),
        ('Customer_Service_Junior', 'Customer_Service_Junior'),
        ('Auditor', 'Auditor'),
        ('Sub_Auditor', 'Sub_Auditor'),
        ('HR_Head', 'HR_Head'),
        ('HR_Junior', 'HR_Junior'),
        ('Technical', 'Technical'),
        ('Technical_Junior', 'Technical_Junior'),
        ('Content', 'Content'),
        ('Content_Junior', 'Content_Junior'),
        ('IT_Head', 'IT_Head'),
        ('IT_Junior', 'IT_Junior'),
        ('user', 'user')
    )
    role_name = models.CharField(max_length=50, choices=ROLE, default='User')

    def __str__(self):
        return self.role_name

    class Meta:
        verbose_name_plural = 'Role'


class Permissions(models.Model):
    user_management = models.BooleanField(default=True)
    sp_management = models.BooleanField(default=True)
    questionnaires = models.BooleanField(default=True)
    document_management = models.BooleanField(default=True)
    margin_management = models.BooleanField(default=True)
    wallet_management = models.BooleanField(default=True)
    report_management = models.BooleanField(default=True)
    change_password = models.BooleanField(default=True)
    ticket_management = models.BooleanField(default=True)
    category_management = models.BooleanField(default=True)
    admin_management = models.BooleanField(default=True)
    role_management = models.BooleanField(default=True)
    country_management = models.BooleanField(default=True)
    radius_management = models.BooleanField(default=True)
    subscription_management = models.BooleanField(default=True)
    merchandise_management = models.BooleanField(default=True)
    tips_management = models.BooleanField(default=True)
    announcement_management = models.BooleanField(default=True)
    ad_management = models.BooleanField(default=True)
    faq_management = models.BooleanField(default=True)
    Dispute_management = models.BooleanField(default=True)
    cancelation_management = models.BooleanField(default=True)


USER_CHOICE = (
    ('SS', 'SS'),
    ('SP', 'SP')
)
LOGIN_TYPE = (
    ('Local', 'Local'),
    ('Facebook', 'Facebook'),
    ('Google', 'Google')
)
USER_STATUS = (
    ('Active', 'Active'),
    ('Inactive', 'Inactive'),
    ('Onhold', 'Onhold')
)

ADDRESSES_TYPE = (
    ('Home', 'Home'),
    ('Work', 'Work'),
    ('Other', 'Other')
)


class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    cell_phone = models.CharField(max_length=15, blank=True, default="", null=True)
    country = models.CharField(max_length=50, blank=True, default="", null=True)
    state = models.CharField(max_length=50, blank=True, default="", null=True)
    profile_image = models.FileField(upload_to='user_images/', default='', blank=True)
    postal_code = models.CharField(max_length=50, blank=True, default="", null=True)
    registration_id = models.CharField(max_length=200, null=True, blank=True, default=None)
    active = models.BooleanField(default=True)
    roles = models.ForeignKey(Role, null=True, on_delete=models.CASCADE, related_name='role', blank=True)
    user_type = models.CharField(max_length=50, choices=USER_CHOICE, null=True, blank=True)
    login_type = models.CharField(max_length=40, choices=LOGIN_TYPE, default='local')
    reset_pass = models.BooleanField(default=False)
    confirmed_email = models.BooleanField(default=False)
    remember_me = models.BooleanField(default=False)
    reset_code = models.CharField(max_length=200, null=True, blank=True, default="")
    reset_code_time = models.DateTimeField(auto_now_add=True, blank=True)
    longitude = models.DecimalField(max_digits=80, decimal_places=10, default=0.00)
    latitude = models.DecimalField(max_digits=80, decimal_places=10, default=0.00)
    r_code = models.CharField(max_length=15, null=True, blank=True)
    refer_user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True, related_name="user_refer")
    referred = models.ManyToManyField(User, related_name="user_referred")
    otp = models.CharField(max_length=6, blank=True, default="", null=True)
    permission = models.OneToOneField(Permissions, on_delete=models.CASCADE, null=True, blank=True)

    # ========================= added level, earnings and spending & booking ======================= #

    level = models.CharField(max_length=25, null=True, blank=True)
    earning = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    spending = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="user_booking", null=True, blank=True, )
    user_status = models.CharField(max_length=10, choices=USER_STATUS, null=True, blank=True, default='Active')
    reference_id = models.UUIDField(null=True, blank=True, editable=False)

    def __str__(self):
        return self.user.username


class UserAddresses(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, null=True, blank=True)
    label = models.CharField(max_length=250, null=True, blank=True)
    address = models.CharField(max_length=250, null=True, blank=True)
    floor_no = models.CharField(max_length=50, null=True, blank=True)
    unit_no = models.CharField(max_length=50, null=True, blank=True)
    longitude = models.FloatField(null=True, blank=True)
    latitude = models.FloatField(null=True, blank=True)
    # location = gis_model.PointField(null=True, blank=True)
    address_type = models.CharField(max_length=50, choices=ADDRESSES_TYPE, null=True, blank=True)

    def __str__(self):
        return self.label
