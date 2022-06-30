import json
import stripe
from django.db import transaction

from mooner_backend.settings import STRIPE_API_KEY, BLOCK_CHAIN_BASE_URL
from .models import *
import requests
from .payments_decoraters import *


def create_charge(**kwargs):
    """
         try to use stripe token second time.
         'You cannot use a Stripe token more than once: tok_1JJug4AhGa8et5ygDLTGv3s5.'
         if customer does not exists:
            No such customer: 'fasfafasffasfasfas'
         if customer card id is wrong:
            Customer cus_JqorgRV14gv2qi does not have a linked source with ID card_1JJug4AhGa8et5yg4wLD5r.
         if amount value in float:
            Invalid integer: 20.0
         if amount is less than 0.50:
            Amount must be at least $0.50 sgd
    """

    generic_msg = "There was some issue processing your request, Please try again later!"
    try:
        stripe.api_key = STRIPE_API_KEY
        dollar_amount = float(kwargs['amount'])
        cents = round(int(dollar_amount * 100))
        charge = stripe.Charge.create(
            amount=cents,
            currency='sgd',
            source=kwargs['source'],
            customer=kwargs['customer']
        )
        transaction_id = charge.balance_transaction
        if charge.status == 'succeeded':
            transaction_details = stripe.BalanceTransaction.retrieve(
                transaction_id,
            )
            net_amount = transaction_details.net
            amount = convert_dollars(net_amount)
            return amount
        elif charge.status == 'pending':
            return ({'status': False,
                     'message': 'Transaction  Pending!'})
        else:
            return ({'status': False,
                     'message': 'Transaction  failed!'})

    except stripe.error.CardError as e:
        stripe_msg = e.json_body.get('error').get('message')
        return ({'status': False, 'message': generic_msg,
                 'stripe_msg': stripe_msg})

    except stripe.error.InvalidRequestError as e:
        stripe_msg = e.json_body.get('error').get('message')
        return ({'status': False, 'message': generic_msg,
                 'stripe_msg': stripe_msg})

    except Exception as e:
        stripe_msg = e.json_body.get('error').get('message')
        return ({'status': False, 'message': generic_msg,
                 'stripe_msg': stripe_msg})


def convert_dollars(amount):
    net_amount = amount / 100
    return net_amount


def load_mnr(amount, to_public_address):
    url = "{}USDtoMNR".format(BLOCK_CHAIN_BASE_URL)
    payload = {'fiatAmount': amount}
    json_data = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json_data)
    print(response.text)
    if response.status_code == 201:
        api_data = json.loads(response.text)
        if api_data:
            bal_token = api_data.get('data').get('MNR').get('balance')
            url = "{}adminsendToken".format(BLOCK_CHAIN_BASE_URL)
            mnr_load = {'topublicAddress': to_public_address, 'amount': bal_token}
            json_data = json.dumps(mnr_load)
            headers = {
                'Content-Type': 'application/json'
            }
            response = requests.request("POST", url, headers=headers, data=json_data)
            if response.status_code == 200:
                response_data = json.loads(response.text)
                if response_data.get('success'):
                    return ({'status': True, 'message': 'Mnr loaded successfully'
                             })
                else:
                    return ({'status': False, 'message': 'Mnr not loaded'
                             })


@exception_handler
def attach_card(**kwargs):
    with transaction.atomic():
        if StripeCustomer.objects.filter(user_id=kwargs['user']).exists():
            customer = StripeCustomer.objects.get(user_id=kwargs['user'])
            stripe.api_key = STRIPE_API_KEY
            stripe.Customer.create_source(
                customer.stripe_customer,
                source=kwargs['token'],
            )
            return True
        else:
            stripe.api_key = STRIPE_API_KEY
            customer = stripe.Customer.create(
                email=kwargs['email'],
                description="Mooner Customer register")
            stripe.Customer.create_source(
                customer.id,
                source=kwargs['token'],
            )
            StripeCustomer.objects.create(user_id=kwargs['user'], stripe_customer=customer.id, )
            return True


@exception_handler
def get_card(**kwargs):
    stripe.api_key = STRIPE_API_KEY
    data = stripe.Token.retrieve(
        kwargs['token']
    )
    card = data.card.id
    return card


def create_booking(**kwargs):
    with transaction.atomic():
        generic_msg = 'There was some issue processing your request, Please try again later!'
        stripe.api_key = STRIPE_API_KEY
        dollar_amount = float(kwargs['amount'])
        cents = round(int(dollar_amount * 100))
        try:
            charge = stripe.Charge.create(
                amount=cents,
                currency='sgd',
                source=kwargs['payment_method_id'],
                customer=kwargs['customer_id'],
                capture=False,
            )
            StripeBooking.objects.create(ss_id=kwargs['ss'], sp_id=kwargs['sp'],
                                         booking_id=kwargs['booking_id'], amount=kwargs['amount'], charge_id=charge.id)

        except stripe.error.CardError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return ({'status': False, 'message': generic_msg,
                     'stripe_msg': stripe_msg})
        except stripe.error.InvalidRequestError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return ({'status': False, 'message': generic_msg,
                     'stripe_msg': stripe_msg})
        except Exception as e:
            stripe_msg = e.json_body.get('error').get('message')
            return ({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg
                     })
        return True


def amount_transfer(**kwargs):
    """
    if stripe connect account does not exists:
        No such destination: 'connect_account'
    if platform account has insufficient funds:
        You have insufficient funds in your Stripe account. One likely reason you have insufficient funds is
        that your funds are automatically being paid out; try enabling manual payouts by going to
        https://dashboard.stripe.com/account/payouts.
    if amount in float:
        Invalid integer: 20.0
    if amount is less than 0.50:
        Amount must be at least $0.50 sgd
    """
    generic_msg = 'Insufficient fund in stripe platform account'
    stripe.api_key = STRIPE_API_KEY
    balance = stripe.Balance.retrieve()
    sgd_balance = None
    for bal in balance["available"]:
        if bal.get('currency') == "sgd":
            sgd_balance = bal.get('amount')

    cents = round(int(kwargs['amount'] * 100))
    if cents <= sgd_balance:
        try:
            stripe.Transfer.create(
                amount=cents,
                currency='sgd',
                destination=kwargs['account_id'],
            )
            return ({'status': True,
                     'cents': cents})

        except stripe.error.InvalidRequestError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return ({'status': False, 'message': generic_msg,
                     'stripe_msg': stripe_msg})
        except Exception as e:
            stripe_msg = e.json_body.get('error').get('message')
            return ({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg
                     })

    else:
        return ({'status': False, 'message': 'Insufficient fund in stripe platform account'})


def load_usd(token):
    url = "{}MNRtoUSD".format(BLOCK_CHAIN_BASE_URL)
    payload = {'tokenAmount': token}
    json_data = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json_data)
    print(response.text)
    api_data = json.loads(response.text)
    if api_data:
        balance = int(api_data.get('data').get('USD').get('balance'))
        return balance
    else:
        return False


def load_mnr_token(amount):
    url = "{}USDtoMNR".format(BLOCK_CHAIN_BASE_URL)
    amount_usd = amount/100
    payload = {'fiatAmount': amount_usd}
    json_data = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json_data)
    if response.status_code == 201:
        api_data = json.loads(response.text)
        if api_data:
            balance = api_data.get('data').get('MNR').get('balance')
            return balance
        else:
            return False

def referral_mnr_token(amount):
    url = "{}USDtoMNR".format(BLOCK_CHAIN_BASE_URL)
    # amount_usd = amount/100
    payload = {'fiatAmount': amount}
    json_data = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json_data)
    if response.status_code == 201:
        api_data = json.loads(response.text)
        if api_data:
            balance = api_data.get('data').get('MNR').get('balance')
            return balance
        else:
            return False


def send_token(amount, to_public_address):
    url = "{}adminsendToken".format(BLOCK_CHAIN_BASE_URL)
    mnr_load = {'topublicAddress': to_public_address, 'amount': amount}
    json_data = json.dumps(mnr_load)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json_data)
    if response.status_code == 200:
        response_data = json.loads(response.text)
        if response_data.get('success'):
            return ({'status': True,
                     'message': 'Mnr loaded successfully'})
        else:
            return ({'status': False,
                     'message': 'Mnr not loaded'})
