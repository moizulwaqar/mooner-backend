import json

import stripe
from django.db.models import F, Q, Sum
from django.db.models.functions import Cast
from django.db.models import FloatField
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from mooner_backend.settings import BLOCK_CHAIN_BASE_URL, STRIPE_API_KEY
import requests
from .models import *



# Create your views here.
from .utils import send_token


class UserWallet(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def get_queryset(self):
        return None

    def post(self, request, *args, **kwargs):
        if CreateWallet.objects.filter(user=request.user).exists():
            return Response({"status": False, 'msg': "wallet already created"})
        else:
            func_response = call_wallet_api('create_wallet')
            if func_response:
                created_wallet = CreateWallet.objects.create(user=request.user, wallet_public_key=func_response.get('address'))
                url = "{}sendBNB".format(BLOCK_CHAIN_BASE_URL)
                bnb_amount = 0.01
                bnb_load = {'topublicAddress': created_wallet.wallet_public_key, 'amount': bnb_amount}
                json_data = json.dumps(bnb_load)
                headers = {
                    'Content-Type': 'application/json'
                }
                response = requests.request("POST", url, headers=headers, data=json_data)
                if response.status_code == 200:
                    response_data = json.loads(response.text)
                    if response_data.get('success'):
                        if UserBnb.objects.filter(user=request.user).exists():
                            pass
                        else:
                            UserBnb.objects.create(user=request.user, bnb=bnb_amount)
                    else:
                        print("bnb not loaded")

                user_token = MLNTokenPandingHistory.objects.filter(user=request.user
                                                                   ).annotate(as_float=Cast('token', FloatField())
                                                                              ).aggregate(Sum('as_float'))
                if user_token.get('as_float__sum'):
                    if user_token.get('as_float__sum') > 0:
                        send_token(user_token.get('as_float__sum'), created_wallet.wallet_public_key)
            return Response({"status": True, "message": "wallet created successfully",
                             "private_key_address": func_response.get('privateKey')[2:]
                             })

    def get(self, request, *args, **kwargs):
        stripe.api_key = STRIPE_API_KEY
        verification = None
        requirements = None
        if CreateWallet.objects.filter(user=request.user).exists():
            user_wallet = CreateWallet.objects.filter(user=request.user).first()
            public_key = user_wallet.wallet_public_key
            data = call_wallet_api('get_balance', public_key)
            # account_status = stripe.Account.retrieve("acct_1JiFYSPPyqiVTwyc")
            connect_account = StripeConnectAccount.objects.filter(user=request.user)
            if connect_account.exists():
                connect_obj = connect_account.first().stripe_connect_account
                account_status = stripe.Account.retrieve(connect_obj)
            # json.dumps(account_status.individual.verification)
                verification = account_status.individual.verification
                requirements = account_status.requirements
            return Response({"status": True, 'msg': "wallet already created",
                             "mnr_balance": data.get('MNR').get('balance'),
                             'crypto_wallet_status': True, 'public_key_address': public_key,
                             'verification': verification, 'requirements': requirements
                             })

        else:

            user_token = MLNTokenPandingHistory.objects.filter(user=request.user
                                                  ).annotate(as_float=Cast('token', FloatField())
                                                             ).aggregate(Sum('as_float'))
            if user_token.get('as_float__sum'):
                return Response({"status": False, "msg": "wallet does not exists", "mnr_balance":
                    user_token.get('as_float__sum'),
                                 "crypto_wallet_status": False,
                                 'verification': verification,
                                 'requirements': requirements
                                 })
            else:
                return Response({"status": False, "msg": "wallet does not exists", "mnr_balance": 0,
                                 "crypto_wallet_status": False,
                                 'verification': verification,
                                 'requirements': requirements

                                 })


def call_wallet_api(attr, public_key=None, from_private_key=None, to_public_key=None, amount=None):
    if attr == 'create_wallet':
        data = wallet_apis(key='createAccount')
        return data
    elif attr == 'get_balance':
        data = wallet_apis(key='getBalance?publicaddress={}'.format(public_key))
        return data
    elif attr == 'sendToken':
        data = wallet_apis(key='sendToken',
                           fromprivateKey=from_private_key,
                           frompublicAddress=public_key, topublicAddress=
                           to_public_key, amount=amount)

        return data

    else:
        return None


def wallet_apis(**kwargs):
    url = "{}{}".format(BLOCK_CHAIN_BASE_URL, kwargs['key'])
    payload = {}
    headers = {}
    if kwargs['key'] == 'createAccount' or 'getBalance' in kwargs['key']:
        if 'getBalance' in kwargs['key']:
            response = requests.request("GET", url, headers=headers, data=payload)
        else:
            response = requests.request("POST", url, headers=headers, data=payload)
        if response.status_code == 201 or response.status_code == 200:
            api_data = json.loads(response.text)
            if api_data.get('data'):
                data = api_data.get('data')
                return data
            else:
                return None
    if kwargs['key'] == 'sendToken':
        payload = {
            'frompublicAddress': kwargs['frompublicAddress'],
            'fromprivateKey': kwargs['fromprivateKey'],
            'topublicAddress': kwargs['topublicAddress'],
            'amount': kwargs['amount']
        }
        json_data = json.dumps(payload)
        headers = {
            'Content-Type': 'application/json'
        }

        response = requests.request("POST", url, headers=headers, data=json_data)
        data = json.loads(response.text)
        print(response.text)
        if response.status_code == 200:
            api_data = json.loads(response.text)
            if api_data:
                return api_data
        else:
            return data
    else:
        return None


class CryptoWallet(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):

        if CreateWallet.objects.filter(user=request.user).exists():
            user_wallet = CreateWallet.objects.filter(user=request.user).first()
            public_key = user_wallet.wallet_public_key
            data = call_wallet_api('get_balance', public_key)
            transaction_history = WalletHistory.objects.filter(Q(to_public_address=public_key)
                                                               | Q(frompublic_address=public_key))\
                .values('transaction_hash', profile_image=F('user__profile__profile_image'),
                        from_public_address=F('frompublic_address'), to_public_addres=F('to_public_address')).order_by\
                ('-id')

            return Response({"status": True, 'msg': "crypto wallet details",
                             "mnr_balance": data.get('MNR').get('balance'),
                             "bnb_balance": data.get('BNB').get('balance'),
                             'crypto_wallet_status': True, 'public_key_address': public_key,
                             'transaction_history': transaction_history
                             })
        else:
            return Response({"status": False, "msg": "wallet does not exists", "mnr_balance": 0,
                             'bnb_balance': 0,
                             "crypto_wallet_status": False,
                             'transaction_history': []
                             })


class ShareCryptoTokens(generics.CreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        from_public_address = request.data.get('frompublicAddress')
        from_private_key = request.data.get('fromprivateKey')
        to_public_address = request.data.get('topublicAddress')
        amount = int(request.data.get('amount'))
        if from_public_address and from_private_key and to_public_address and amount:
            if CreateWallet.objects.filter(user=request.user).exists():
                user_wallet = CreateWallet.objects.filter(user=request.user).first()
                # public_key = user_wallet.wallet_public_key
                data = call_wallet_api('sendToken', from_public_address, from_private_key, to_public_address, amount)
                if data:
                    if data.get('success'):
                        WalletHistory.objects.create(user=request.user, transaction_hash=data.get('msg'),
                                                     wallet=user_wallet,
                                                     frompublic_address=from_public_address,
                                                     to_public_address=to_public_address)
                        return Response({"status": True, 'msg': "Transaction successful"})

                    elif not data.get('success') and 'invalid address' in data.get('msg'):
                        return Response({"status": False, 'msg': "Invalid Public Address"})

                    elif not data.get('success') and 'Returned error' in data.get('msg'):
                        return Response({"status": False, 'msg': "Private key is wrong"})

                    # elif not data.get('success') and 'length 32' in data.get('msg'):
                    #     return Response({"status": False, 'msg': "Private key address length should be  32"})

                    elif not data.get('success') and 'Insufficient token balance' in data.get('msg'):
                        return Response({"status": False, 'msg': "Insufficient token balance"})
                    else:
                        return Response({"status": False, 'msg': "Invalid Public/Private key"})
            else:
                return Response({"status": False, "msg": "wallet does not exists"
                                 })
        else:
            return Response({"status": False, "msg": "All fields are required"})



