from pyfcm import FCMNotification
from mooner_backend.settings import NOTIFICATION_API_KEY
from .models import *


# def send_notification_group(sender, instance, **kwargs):
#     push_service = FCMNotification(api_key=NOTIFICATION_API_KEY)
#     registration_id = instance
#     push_service.notify_single_device(registration_id=registration_id, message_title=kwargs['message_title'],
#                                       message_body=kwargs['message_body'])


def send_notification(**kwargs):
    push_service = FCMNotification(api_key=NOTIFICATION_API_KEY)
    registration_ids = kwargs.get('list_of_devices')
    # registration_ids = ['d8kD3SDCSaiie2BZPkUDps:APA91bGzPtkE7rNl5VBd-Nfus7NFTNfXL07TdKOC-tYr4U9AnPCU7yMf_1IKjYu30z1mdzpISfGNoqzmyzjrxB7LDjWGDUq-PkdxHsA6Uq5Lu_lpLi-uvAlGl0JcOR8xwGdvYKB9XOM8']
    message_title = kwargs['message_title']
    message_body = kwargs['message_body']
    user_type = kwargs['user_type']
    result = push_service.notify_multiple_devices(registration_ids=registration_ids,
                                                  message_title=message_title,
                                                  message_body=message_body,
                                                  extra_notification_kwargs=kwargs['extra_notification_kwargs'])
    type_model = kwargs.get('extra_notification_kwargs').get('type')
    type_id = kwargs.get('extra_notification_kwargs').get('type_id')
    create_notification(type_model=type_model, type_id=type_id, message_title=message_title,
                        user_type=user_type, message_body=message_body, user=kwargs.get('user'))

    print(result)
    return True


def create_notification(**kwargs):
    if kwargs.get('user'):
        Notification.objects.create(user_id=kwargs.get('user'), message_title=kwargs.get('message_title'),
                                    message_body=kwargs.get('message_body'),
                                    type=kwargs.get('type_model'), type_id=kwargs.get('type_id'),
                                    user_type=kwargs.get('user_type'))
    return True
