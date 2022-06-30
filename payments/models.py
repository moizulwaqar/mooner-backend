from django.db import models
from django.contrib.auth.models import User
# Create your models here.
from booking.models import Booking

CANCELLED_BY = (
    ('SS', 'SS'),
    ('SP', 'SP'),
)

class CreateWallet(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_wallet", null=True, blank=True)
    wallet_public_key = models.CharField(max_length=50, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.wallet_public_key


class WalletHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_wallet_history",
                             null=True, blank=True)
    wallet = models.ForeignKey(CreateWallet, on_delete=models.CASCADE, related_name='wallet_in_wallet_history',
                               null=True, blank=True)
    to_public_address = models.CharField(max_length=250, null=True, blank=True)
    frompublic_address = models.CharField(max_length=250, null=True, blank=True)
    transaction_hash = models.CharField(max_length=250, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    earn_tokens = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)


# stripe models
class StripeCustomer(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_in_stripe_customer",
                                null=True, blank=True)
    stripe_customer = models.CharField(max_length=255, unique=True, null=True, blank=True)
    stripe_email = models.EmailField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.stripe_customer


class StripeConnectAccount(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name="user_in_connect_account",
                                null=True, blank=True)
    stripe_connect_account = models.CharField(max_length=255, unique=True, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.stripe_connect_account


class CustomerCardInfo(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='user_in_customercardinfo')
    card_no = models.CharField(max_length=250, unique=True)
    title = models.CharField(max_length=250, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.card_no


class StripeBooking(models.Model):
    ss = models.ForeignKey(User, on_delete=models.CASCADE, related_name="ss_in_stripe_booking",
                           null=True, blank=True)
    sp = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sp_in_stripe_booking",
                           null=True, blank=True)
    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name="booking_stripe_booking", null=True,
                                blank=True)
    amount = models.CharField(max_length=255)
    charge_id = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class TokenRate(models.Model):
    admin = models.ForeignKey(User, on_delete=models.CASCADE, related_name="admin_in_tokenRate",
                           null=True, blank=True)
    set_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class MLNTokensEarn(models.Model):
    sender = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender_in_mlnTokensEarn",
                               null=True, blank=True)
    recevier = models.ForeignKey(User, on_delete=models.CASCADE, related_name="recevier_in_mlnTokensEarn",
                                 null=True, blank=True)
    token = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class MLNTokenPandingHistory(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sender_in_mlnTokenPandingHistory",
                               null=True, blank=True)
    token = models.CharField(max_length=255,null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class RefundBooking(models.Model):
    stripe_booking = models.ForeignKey(StripeBooking, on_delete=models.CASCADE, related_name="stripebooking_in_"
                                                                                             "refundbooking",
                                       null=True, blank=True)
    refund_id = models.CharField(max_length=255)
    cancelled_by = models.CharField(max_length=50, choices=CANCELLED_BY, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)


class UserBnb(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="user_in_UserBnb",
                               null=True, blank=True)
    bnb = models.CharField(max_length=255,null=True, blank=True)
    is_payment = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now_add=True)