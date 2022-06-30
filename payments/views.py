from django.core.exceptions import ObjectDoesNotExist
from django.db import transaction
from django.db.models import F
from rest_framework import generics
from mooner_backend.utils import pagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.views import APIView
from rest_framework.response import Response
import stripe
from mooner_backend.settings import STRIPE_API_KEY, BLOCK_CHAIN_BASE_URL, ToBublicAddress
from .crypto_integrations import wallet_apis
from .serializers import *
from .utils import create_charge, load_mnr, load_usd, amount_transfer
import time
from datetime import datetime
import requests
import json
from .payments_decoraters import *
from user.models import UserProfile
# Create your views here.


class LoadMNR(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = CustomerCardSerializer

    @staticmethod
    @exception_handler
    def post(request):
        status_msg = ''
        try:
            with transaction.atomic():
                serializer = CustomerCardSerializer(data=request.data)
                if CreateWallet.objects.filter(user=request.user).exists():
                    if serializer.is_valid(raise_exception=True):
                        stripe.api_key = STRIPE_API_KEY
                        if StripeCustomer.objects.filter(user=request.user).exists():
                            customer = StripeCustomer.objects.get(user=request.user)
                            card = stripe.Customer.create_source(
                                customer.stripe_customer,
                                source=serializer.data.get('token'),
                            )
                            amount = create_charge(amount=serializer.data.get('amount'), source=card.id,
                                                   customer=customer.stripe_customer)
                            to_public_address = CreateWallet.objects.filter(user=request.user).first().wallet_public_key
                            status_msg = load_mnr(to_public_address=to_public_address, amount=amount)
                            return Response(status_msg)
                        else:
                            customer = stripe.Customer.create(
                                email=serializer.data.get('email'),
                                description="Mooner Customer ID is {}".format(request.user.id)
                            )
                            card = stripe.Customer.create_source(
                                customer.id,
                                source=serializer.data.get('token'),
                            )
                            amount = create_charge(amount=serializer.data.get('amount'), source=card.id,
                                                   customer=customer.id)
                            StripeCustomer.objects.create(user=request.user, stripe_customer=customer.id, )
                            to_public_address = CreateWallet.objects.filter(user=request.user).first().wallet_public_key
                            status_msg = load_mnr(to_public_address=to_public_address, amount=amount)
                            return Response(status_msg)
                else:
                    return Response({"status": True, "message": "wallet does not exist!"})
                    # return Response({"status": True, "message": status_msg})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class ConnectAccount(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = StripeConnectAccountSerializer

    @staticmethod
    @exception_handler
    def post(request):
        try:
            with transaction.atomic():
                serializer = StripeConnectAccountSerializer(data=request.data)
                if serializer.is_valid(raise_exception=True):
                    if StripeConnectAccount.objects.filter(user=request.user).exists():
                        return Response({"status": True, "message": "Connected Account Already Exists!"})
                    stripe.api_key = STRIPE_API_KEY
                    data = stripe.Account.create(
                        type="custom",
                        country="SG",
                        email=serializer.data.get('email'),
                        capabilities={
                            "card_payments": {"requested": True},
                            "transfers": {"requested": True},
                        },
                        business_type="individual",
                        individual={
                            "dob": {
                                "day": int(serializer.data.get('day')),
                                "month": int(serializer.data.get('month')),
                                "year": int(serializer.data.get('year'))},
                            "first_name": serializer.data.get('first_name'),
                            "last_name": serializer.data.get('last_name'),
                            "address": {
                                "line1": serializer.data.get('address'),
                                "postal_code": serializer.data.get('postal_code')
                            },
                        },
                        tos_acceptance={
                            "date": int(time.time()),
                            "ip": "192.168.1.240",
                        },
                    )
                    front_pic_token = stripe.File.create(
                        purpose='identity_document',
                        file=request.FILES.get('front_pic_national_id'),
                        stripe_account=data.id,
                      )
                    back_pic_token = stripe.File.create(
                        purpose='identity_document',
                        file=request.FILES.get('back_pic_national_id'),
                        stripe_account=data.id,
                    )
                    stripe.Account.modify_person(
                      data.id,
                        data.individual.id,
                        id_number=serializer.data.get('id_number'),
                        verification={
                         'document': {
                          'front': front_pic_token.id,
                          'back': back_pic_token.id
                        },
                      },
                    )
                    StripeConnectAccount.objects.create(user=request.user, stripe_connect_account=data.stripe_id, )
                    return Response({"status": True, "message": "Stripe Connected Account Created Successfully!",
                                     'data': data})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})

    @staticmethod
    @exception_handler
    def get(request):
        stripe.api_key = STRIPE_API_KEY
        connect_account = StripeConnectAccount.objects.filter(user=request.user)
        if connect_account.exists():
            connect_obj = connect_account.first().stripe_connect_account
        # connect_details = stripe.Account.retrieve(connect_account.stripe_connect_account)
            connect_details = stripe.Account.retrieve(connect_obj)
            person_details = connect_details.individual
            stripe_details = dict()
            stripe_details["email"] = connect_details.email
            stripe_details["day"] = person_details.dob.day
            stripe_details["month"] = person_details.dob.month
            stripe_details["year"] = person_details.dob.year
            stripe_details["first_name"] = person_details.first_name
            stripe_details["last_name"] = person_details.last_name
            stripe_details["address"] = person_details.address.line1
            stripe_details["postal_code"] = person_details.address.postal_code
            account_verification = connect_details.individual.verification
            account_requirements = connect_details.requirements

            stripe_details['verification'] = account_verification
            stripe_details['requirements'] = account_requirements
            # front = stripe.File.retrieve(
            #     person_details.verification.document.front,
            # )
            # back = stripe.File.retrieve(
            #
            #     person_details.verification.document.back,
            # )
            # stripe_details["front_pic_national_id"] = front.links.data.url
            # stripe_details["back_pic_national_id"] = back.links.data.url

            return Response({'status': True, "msg": "account details", "data": stripe_details})

        else:
            return Response({'status': False, "msg": "connect account doesn't exists"})

    @staticmethod
    @exception_handler
    def put(request):
        stripe.api_key = STRIPE_API_KEY
        individual = request.data.get('individual')
        ind_id_number = request.data.get('id_number')
        front_file = request.FILES.get('front_pic_national_id')
        back_file = request.FILES.get('back_pic_national_id')
        connect_account = StripeConnectAccount.objects.filter(user=request.user)
        if connect_account.exists():
            connect_obj = connect_account.first().stripe_connect_account
            connect_details = stripe.Account.retrieve(connect_obj)
            person_details = connect_details.individual
            if individual:
                individual_json = json.loads(individual)
                stripe.Account.modify(
                    connect_details.id,
                    individual=individual_json
                )
            if ind_id_number:
                stripe.Account.modify_person(
                  connect_details.id,
                    person_details.id,
                    id_number=ind_id_number,
                )
            if front_file:
                front_pic_token = stripe.File.create(
                    purpose='identity_document',
                    file=front_file,
                    stripe_account=connect_details.id,
                )
                stripe.Account.modify_person(
                    connect_details.id,
                    person_details.id,
                    verification={
                        'document': {
                            'front': front_pic_token.id,
                        },
                    },
                )
            if back_file:
                back_pic_token = stripe.File.create(
                    purpose='identity_document',
                    file=back_file,
                    stripe_account=connect_details.id,
                )
                stripe.Account.modify_person(
                    connect_details.id,
                    person_details.id,
                    verification={
                        'document': {
                            'back': back_pic_token.id,
                        },
                    },
                )

            return Response({'status': True, "msg": "updated succesffully"})

        else:
            return Response({'status': False, "msg": "connect account doesn't exists"})


class ExternalBank(APIView):
    permission_classes = (AllowAny,)
    serializer_class = ExternalBankSerializer

    @staticmethod
    @exception_handler
    def post(request):
        try:
            serializer = ExternalBankSerializer(data=request.data)
            user_account = StripeConnectAccount.objects.get(user=request.user)
            if serializer.is_valid(raise_exception=True):
                stripe.api_key = STRIPE_API_KEY
                # "routing_number": serializer.data.get('routing_number'),
                data = stripe.Token.create(
                  bank_account={
                    "country": "SG",
                    "currency": "sgd",
                    "account_holder_name": serializer.data.get('account_holder_name'),
                    "account_holder_type": "individual",
                    "routing_number": serializer.data.get('routing_number'),
                    "account_number": serializer.data.get('account_number'),
                  },
                )
                stripe.Account.create_external_account(
                    user_account.stripe_connect_account,
                    external_account=data.id
                )
                return Response({"status": True, "message": "Bank Account Attached Successfully!",
                                 'data': data})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class BankAccounts(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    @exception_handler
    def get(request):
        try:
            with transaction.atomic():
                if StripeConnectAccount.objects.filter(user=request.user).exists():
                    user_account = StripeConnectAccount.objects.get(user=request.user)
                    stripe.api_key = STRIPE_API_KEY
                    data = stripe.Account.list_external_accounts(
                        user_account.stripe_connect_account,
                        object="bank_account",
                        limit=10,
                    )
                    bank_list = {}
                    bank_detail = []
                    for i in data:
                        bank_list.update({'bank_id': i.id, 'bank_name': i.bank_name, 'last4': i.last4})
                        bank_detail.append(bank_list.copy())
                    result = pagination(bank_detail, request)
                    return Response({"status": True, "data": result.data})
                else:
                    return Response({"status": False, "message": "Connected Account Does not exists!"})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class TransferAmount(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    @exception_handler
    def post(request):
        try:
            amount = request.data.get('amount')
            account_id = request.data.get('account_id')
            stripe.api_key = STRIPE_API_KEY
            data = stripe.Transfer.create(
                amount=amount,
                currency='sgd',
                destination=account_id,
            )
            return Response({"status": True, "message": "Amount Transfer Successfully!",
                             'data': data})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class AmountPayout(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = PayoutSerializer

    @staticmethod
    @exception_handler
    def post(request):
        try:
            serializer = PayoutSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                token = serializer.data.get('token')
                if CreateWallet.objects.filter(user=request.user).exists():
                    public_key = CreateWallet.objects.get(user=request.user)
                    data = wallet_apis(key='sendToken', fromprivateKey=serializer.data.get('private_key'),
                                frompublicAddress=public_key.wallet_public_key,
                                topublicAddress=ToBublicAddress, amount=token)
                    if data.get('success'):
                        rate = TokenRate.objects.get()
                        # token_amount = float(token) * float(rate.set_price)
                        token_amount = float(token)
                        if StripeConnectAccount.objects.filter(user=request.user).exists():
                            user_account = StripeConnectAccount.objects.get(user=request.user)
                            amount = load_usd(token=token_amount)
                            url = "https://api.binance.com/api/v3/ticker/price?symbol=BNBUSDT"
                            response = requests.request("GET", url)
                            bnb_price = json.loads(response.text)
                            # if 'price' in bnb_price:
                            #     bnb_usd = bnb_price.get('price')
                            # else:
                            #     bnb_usd = 0
                            user_bnb = UserBnb.objects.filter(user=request.user)
                            total_amount = 0
                            if user_bnb.exists():
                                if not user_bnb.first().is_payment:
                                    bnb_obj = user_bnb.first()
                                    bnb = bnb_obj.bnb
                                    bnb_price = float(bnb_price.get('price')) * float(bnb)

                                    if float(bnb_price) >= amount:
                                        return Response({"status": False, "message":
                                            "You need atleast $"+ str(bnb_price) + " worth MNR tokens in your Wallet to make a withdrawal" })
                                    total_amount = amount - bnb_price
                                    bnb_obj.is_payment = True
                                    bnb_obj.save()
                                else:
                                    total_amount = amount


                            # bnb_deduction = amount-bnb_amount
                            amount_cents = amount_transfer(amount=total_amount, account_id=user_account.stripe_connect_account)
                            if amount_cents.get('status'):
                                stripe.api_key = STRIPE_API_KEY
                                balance = stripe.Balance.retrieve(
                                    stripe_account=user_account.stripe_connect_account
                                )
                                connect_account = stripe.Account.retrieve(user_account.stripe_connect_account)
                                account_ids = []
                                for ids in connect_account.external_accounts.data:
                                    account_ids.append(ids.id)
                                sgd_balance = None
                                for bal in balance["available"]:
                                    if bal.get('currency') == "sgd":
                                        sgd_balance = bal.get('amount')
                                if amount_cents.get('cents') <= sgd_balance:
                                    if serializer.data.get('bank_id') in account_ids:
                                        stripe.api_key = STRIPE_API_KEY
                                        data = stripe.Payout.create(
                                                currency='sgd',
                                                amount=amount_cents.get('cents'),
                                                stripe_account=user_account.stripe_connect_account,
                                                destination=serializer.data.get('bank_id')
                                            )
                                        return Response({"status": True, "message": "Amount Withdraw Successfully!",
                                                         'data': data})
                                    else:
                                        return Response({"status": False, "message": "Bank ID does not exist!"})
                                else:
                                    return Response({"status": False, "message": "Insufficient fund in stripe account!"})
                            else:
                                return Response({"status": False, "message": "Insufficient fund in stripe platform account!"})
                        else:
                            return Response({"status": False, "message": "Connected Account Does not exist!"})
                    else:
                        return Response({"status": False, "message": "Insufficient Tokens in your Wallet!"})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class PayoutList(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    @exception_handler
    def get(request):
        try:
            if StripeConnectAccount.objects.filter(user=request.user).exists():
                stripe_user = StripeConnectAccount.objects.get(user=request.user)
                stripe.api_key = STRIPE_API_KEY
                payout_data = stripe.Payout.list(stripe_account=stripe_user.stripe_connect_account, limit=10)

                bank_list = {}
                bank_detail = []
                for data in payout_data:
                    bank_list.update({
                                     'username': request.user.username,
                                      'arrival_date': datetime.utcfromtimestamp(data.arrival_date),
                                      'created_date': datetime.utcfromtimestamp(data.created),
                                      'amount': data.amount / 100,
                                      'status': data.status,
                                      'mnr': ''})
                    bank_detail.append(bank_list.copy())
                result = pagination(bank_detail, request)
                return Response({"status": True, "total_mnr": "", "data": result.data})
            else:
                return Response({"status": False, "message": "Connected Account Does not exists!"})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class DeleteExternalBank(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    @exception_handler
    def post(request):
        try:
            bank_id = request.data.get('bank_id')
            if not bank_id:
                return Response({"status": False, "message": "Bank ID is Required!"})
            if StripeConnectAccount.objects.filter(user=request.user).exists():
                stripe_user = StripeConnectAccount.objects.get(user=request.user)
                stripe.api_key = STRIPE_API_KEY
                stripe.Account.delete_external_account(
                                  stripe_user.stripe_connect_account,
                                  bank_id
                                )
                return Response({"status": True, "message": "Bank Deleted Successfully!"})
            else:
                return Response({"status": False, "message": "Connected Account Does not exists!"})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class SetTokenPrice(generics.ListAPIView):
    permission_classes = (IsAdminUser,)

    @staticmethod
    def post(request):
            amount = request.data.get('set_rate')
            float_amount = float(amount)
            headers = {
                'Content-Type': 'application/json'
            }
            url = "{}setRate".format(BLOCK_CHAIN_BASE_URL)
            payload = {'rate': float_amount}
            json_data = json.dumps(payload)
            response = requests.request("POST", url, headers=headers, data=json_data)
            if response.status_code == 200:
                api_data = json.loads(response.text)
                if api_data:
                    set_rate = api_data.get('data').get('tokenrate')
                    TokenRate.objects.create(admin=request.user, set_price=set_rate)
                    return Response({"status": True, "message": "Token rate set successfully"})

            else:
                return Response({"status": False, "message": "some thing went wrong"})


    @staticmethod
    def get(request):
        rate_id = request.query_params.get('rate_id')
        if TokenRate.objects.filter(id=rate_id).exists():
            amount = TokenRate.objects.filter(id=rate_id).values('id', rate=F('set_price'))
            return Response({"status": True, "data": amount})
        else:
            return Response({"status": False, "message": "Rate does not exists"})


class UpdateTokenPrice(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAdminUser,)

    def put(self, request, *args, **kwargs):
            amount = request.data.get('set_rate')
            float_amount = float(amount)
            headers = {
                'Content-Type': 'application/json'
            }
            url = "{}setRate".format(BLOCK_CHAIN_BASE_URL)
            payload = {'rate': float_amount}
            json_data = json.dumps(payload)
            response = requests.request("POST", url, headers=headers, data=json_data)
            if response.status_code == 200:
                api_data = json.loads(response.text)
                if api_data:
                    set_rate = api_data.get('data').get('tokenrate')
                    TokenRate.objects.update(id=kwargs.get('pk'), admin=request.user, set_price=set_rate)
                    return Response({"status": True, "message": "Token rate update successfully"})

            else:
                return Response({"status": False, "message": "some thing went wrong"})


class CommisionHistory(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def get(request):
        if MLNTokensEarn.objects.filter(recevier=request.user).exists():
            token_data = MLNTokensEarn.objects.filter(recevier=request.user).values('id', 'token', profile_image
            =F('sender__profile__profile_image'), user_name=F('sender__first_name')).order_by('-id')
            result = pagination(token_data, request)
            return Response({"status": True,  "data": result.data})
        else:
            return Response({"status": False, "message": "Commision does not exists!"})


