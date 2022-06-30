import stripe
from rest_framework.response import Response


def exception_handler(func):
    """
        exception handling of server and stripe
        """
    def inner_function(*args, **kwargs):
        generic_msg = 'There was some issue processing your request, Please try again later!'
        try:
            return func(*args, **kwargs)
        except stripe.error.CardError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return Response({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg
                             })
        except stripe.error.InvalidRequestError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return Response({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg
                             })
        except stripe.error.AuthenticationError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return Response({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg})

        except stripe.error.APIConnectionError as e:
            stripe_msg = e.json_body.get('error').get('message')
            return Response({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg})

        except Exception as e:
            if hasattr(e, 'json_body'):
                stripe_msg = e.json_body.get('error').get('message')
                return Response({'status': False, 'message': generic_msg, 'stripe_msg': stripe_msg
                                 })
            else:
                return Response({'status': False, 'message': generic_msg, 'server_msg': e.args[-1]
                                 })
    return inner_function
