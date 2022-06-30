from django.db import transaction

from notification.models import DeviceRegistration
from notification.utils import send_notification
from .models import Booking
from mln.models import LevelsPercentage
from mln.utils import sp_user_levels
from payments.models import StripeConnectAccount, StripeBooking, CreateWallet, MLNTokensEarn, MLNTokenPandingHistory, \
    RefundBooking
from payments.utils import load_mnr_token, send_token, referral_mnr_token
from .serializers import *
from rest_framework.response import Response
from datetime import timezone
from mooner_backend.settings import STRIPE_API_KEY
import stripe


def ss_booking_cancel(**kwargs):
    if kwargs['user_modal'].objects.filter(id=kwargs['booking_id'], ss=kwargs['ss_id']).exists():
        booking = kwargs['user_modal'].objects.get(id=kwargs['booking_id'], ss=kwargs['ss_id'])
        stripe_booking = StripeBooking.objects.get(booking_id=booking.id)
        stripe.api_key = STRIPE_API_KEY
        # stripe.Charge.capture(stripe_booking.charge_id)
        refund_data = stripe.Refund.create(
            charge=stripe_booking.charge_id
        )
        RefundBooking.objects.create(stripe_booking=stripe_booking, refund_id=refund_data.id, cancelled_by='SS')
        return Response({"status": True, "message": "SS Booking Cancelled"})
        # if not StripeConnectAccount.objects.filter(user=booking.sp).exists():
        #     return Response({"status": False, "message": "Please add your connect account first than you will cancel the job!"})
        # sp_account = StripeConnectAccount.objects.filter(user=booking.sp).exists()
        # booking_time = booking.start_date
        # current_time = datetime.now()
        # difference = current_time.replace(tzinfo=timezone.utc) - booking_time
        # mintues = int(difference.total_seconds() / 60)
        # if mintues <= 30:
        #     booking.order_status = "Cancelled"
        #     booking.cancelled_by = 'SS'
        #     booking.save()
            # stripe.api_key = STRIPE_API_KEY
            # stripe.Charge.capture(stripe_booking.charge_id)
            # balance = stripe.Balance.retrieve()
            # sgd_balance = None
            # for bal in balance["available"]:
            #     if bal.get('currency') == "sgd":
            #         sgd_balance = bal.get('amount')
            # amount_for_sp = booking.budget / 2
            # cents = round(int(amount_for_sp * 100))
            # if cents <= sgd_balance:
            #     stripe.Transfer.create(
            #         amount=cents,
            #         currency='sgd',
            #         destination=sp_account.stripe_connect_account,
            #     )
        #     device_list = list(DeviceRegistration.objects.filter(user=booking.sp).
        #                        values_list('device_id', flat=True).distinct())
        #     if len(device_list) != 0:
        #         payload = dict()
        #         payload['type'] = 'Booking'
        #         payload['type_id'] = booking.job_id
        #         send_notification(sender=Booking, message_title='Mooner',
        #                           message_body='your order has been Cancelled',
        #                           extra_notification_kwargs=payload, user=booking.sp.id, user_type='SP',
        #                           list_of_devices=device_list)

        #     # else:
        #     #     return Response({"status": True, "message": "Insufficient fund in stripe platform account!"})
        # else:
        #     return Response({"status": False, "message": "You can not Cancel Booking"})
    else:
        return Response({"status": False, "message": "Booking ID does not exist"})


def sp_booking_cancel(**kwargs):
    if kwargs['user_modal'].objects.filter(id=kwargs['booking_id'], sp=kwargs['sp_id']).exists():
        booking = kwargs['user_modal'].objects.get(id=kwargs['booking_id'], sp=kwargs['sp_id'])
        stripe_booking = StripeBooking.objects.get(booking_id=booking.id)
        stripe.api_key = STRIPE_API_KEY
        # stripe.Charge.capture(stripe_booking.charge_id)
        refund_data = stripe.Refund.create(
            charge=stripe_booking.charge_id
        )
        RefundBooking.objects.create(stripe_booking=stripe_booking, refund_id=refund_data.id, cancelled_by='SP')
        return Response({"status": True, "message": "SP Booking Cancelled"})
        # booking_time = booking.start_date
        # current_time = datetime.now()
        # difference = current_time.replace(tzinfo=timezone.utc) - booking_time
        # mintues = int(difference.total_seconds() / 60)
        # if mintues <= 30:
        #     booking.order_status = "Cancelled"
        #     booking.cancelled_by = 'SP'
        #     booking.save()
        #     # stripe.api_key = STRIPE_API_KEY
        #     # charge = stripe.Charge.capture(stripe_booking.charge_id)
        #     # amount_for_ss = booking.budget / 2
        #     # cents = round(int(amount_for_ss * 100))
        #     # refund = stripe.Refund.create(
        #     #     amount=cents,
        #     #     charge=charge.id,
        #     # )
        #     device_list = list(DeviceRegistration.objects.filter(user=booking.ss).
        #                        values_list('device_id', flat=True).distinct())
        #     if len(device_list) != 0:
        #         payload = dict()
        #         payload['type'] = 'Booking'
        #         payload['type_id'] = booking.job_id
        #         send_notification(sender=Booking, message_title='Mooner',
        #                           message_body='your order has been Cancelled',
        #                           extra_notification_kwargs=payload, user=booking.ss.id, user_type='SS',
        #                           list_of_devices=device_list)
        #
        #     # if refund.status == "succeeded":
        #     return Response({"status": True, "message": "Payment will be awarded 50% to SS & 50% to the Company!"})
        # else:
        #     return Response({"status": False, "message": "You can not Cancel Booking"})
    else:
        return Response({"status": False, "message": "Booking ID does not exist"})


def sp_booked_or_not(**kwargs):
    if kwargs['user_modal'].objects.filter(id=kwargs['booking_id'], sp=kwargs['sp_id']).exists():
        booking = kwargs['user_modal'].objects.get(id=kwargs['booking_id'], sp=kwargs['sp_id'])
        booking_time = booking.start_date
        current_time = datetime.datetime.now()
        if not booking_time == current_time:
            return Response({"status": False, "message": "Service Provider is not available!"})
        else:
            pass
    else:
        return Response({"status": False, "message": "Booking ID does not exist"})


def send_referrals_earnings(amount, booking):
    with transaction.atomic():
        booking = Booking.objects.get(id=booking)
        tokens = referral_mnr_token(amount=amount)
        value = LevelsPercentage.objects.get(id=1)
        admin_user = User.objects.filter(is_superuser=True).first()
        fee_obj = AdminConvenienceFee.objects.first()
        total_fees = fee_obj.admin_fees + fee_obj.convenience_fees
        company_incentive = tokens / 100 * total_fees
        total_amount = company_incentive / 100 * 20
        admin_fee_amount = company_incentive - total_amount
        remaining_amount = tokens - company_incentive
        level_zero = total_amount / 100 * int(value.level_0)
        level_one = total_amount / 100 * int(value.level_1)
        level_two = total_amount / 100 * int(value.level_2)
        level_three = total_amount / 100 * int(value.level_3)
        level_four = total_amount / 100 * int(value.level_4)
        sp_levels = sp_user_levels(sp_id=booking.sp_id, ss_id=booking.ss_id, admin_id=admin_user.id,
                                   level_0=level_zero, level_1=level_one, level_2=level_two,
                                   level_3=level_three, level_4=level_four)
        if sp_levels[0] != 'No parent available':
            for sp_user in sp_levels[0]:

                if CreateWallet.objects.filter(user_id=sp_user['provider_id']).exists():
                    sp_account = CreateWallet.objects.get(user_id=sp_user['provider_id'])
                    mnr = send_token(amount=sp_user['incentives'], to_public_address=sp_account.wallet_public_key)
                    if mnr:
                        MLNTokensEarn.objects.create(sender_id=booking.sp_id, recevier_id=sp_user['provider_id'],
                                                     token=sp_user['incentives'])
                else:
                    MLNTokenPandingHistory.objects.create(user_id=sp_user['provider_id'],
                                                          token=sp_user['incentives'])
                    MLNTokensEarn.objects.create(sender_id=booking.sp_id, recevier_id=sp_user['provider_id'],
                                                 token=sp_user['incentives'])
        if sp_levels[1] != 'No parent available':
            for ss_user in sp_levels[1]:
                if CreateWallet.objects.filter(user_id=ss_user['seeker_id']).exists():
                    ss_account = CreateWallet.objects.get(user_id=ss_user['seeker_id'])
                    mnr = send_token(amount=ss_user['incentives'], to_public_address=ss_account.wallet_public_key)
                    if mnr:
                        MLNTokensEarn.objects.create(sender_id=booking.ss_id, recevier_id=ss_user['seeker_id'],
                                                     token=ss_user['incentives'])
                else:
                    MLNTokenPandingHistory.objects.create(user_id=ss_user['seeker_id'], token=ss_user['incentives'])
                    MLNTokensEarn.objects.create(sender_id=booking.ss_id, recevier_id=ss_user['seeker_id'],
                                                 token=ss_user['incentives'])
        if CreateWallet.objects.filter(user_id=booking.sp_id).exists():
            sp_account = CreateWallet.objects.get(user_id=booking.sp_id)
            send_token(amount=remaining_amount, to_public_address=sp_account.wallet_public_key)
        else:
            MLNTokenPandingHistory.objects.create(user_id=booking.sp_id, token=remaining_amount)
        AdminTransactionList.objects.create(admin=admin_user, earn_tokens=admin_fee_amount, booking=booking)
        return True
