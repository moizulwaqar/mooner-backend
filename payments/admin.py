from django.contrib import admin
from .models import *
# Register your models here.

admin.site.register(CreateWallet)
admin.site.register(WalletHistory)
admin.site.register(StripeCustomer)
admin.site.register(StripeConnectAccount)
admin.site.register(StripeBooking)
admin.site.register(CustomerCardInfo)
admin.site.register(TokenRate)
admin.site.register(MLNTokensEarn)
admin.site.register(MLNTokenPandingHistory)
admin.site.register(UserBnb)