import json

import requests
from django.db.models import F
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response

from mooner_backend.utils import pagination
from .models import TwilioChat
from django.contrib.auth.models import User
from mooner_backend.settings import ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO
from twilio.rest import Client
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.permissions import AllowAny
from rest_framework.pagination import PageNumberPagination

# Create your views here.


class TwilioChats(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            ss_id = self.request.data.get('seeker_id')
            sp_id = self.request.data.get('provider_id')
            channel_name = self.request.data.get('channel_id')
            channel_sid = self.request.data.get('channel_sid')
            ss_twilio_id = self.request.data.get('ss_twilio_user_id')
            sp_twilio_id = self.request.data.get('sp_twilio_user_id')
            if sp_twilio_id and ss_twilio_id and ss_id and sp_id and channel_name and channel_sid:
                if User.objects.filter(id=ss_id).exists() and User.objects.filter(id=sp_id).exists():
                    get_user_ss = User.objects.get(id=ss_id)
                    get_user_sp = User.objects.get(id=sp_id)
                    chat_obj = TwilioChat.objects.filter(ss=ss_id, sp=sp_id)
                    # if TwilioChat.objects.filter(channel_id=channel_name).exists():
                    if chat_obj.exists():
                        chat_data = chat_obj.values('id', 'channel_id', seeker_id=F('ss'), provider_id=F('sp'))
                        return Response({"status": False, "message": "channel already exists", "data": chat_data})
                    # return Response({'status': False, 'message': 'channel already exists with this id'})
                    else:
                        channel = TwilioChat.objects.create(
                            ss=get_user_ss,
                            sp=get_user_sp,
                            channel_id=channel_name,
                            twilio_channel_sid=channel_sid,
                            ss_twilio_user_sid=ss_twilio_id,
                            sp_twilio_user_sid=sp_twilio_id

                        )
                        channel_data = TwilioChat.objects.filter(id=channel.id).values('id', 'channel_id',
                                                                                       seeker_id=F('ss'),
                                                                                       provider_id=F('sp'))
                        return Response({"status": True, "message": "Channel saved  successfully!",
                                         'data': channel_data})
                else:
                    return Response({"status": False, "message": "User id does not exist!"})
            else:
                return Response({"status": False,
                                 'message': "These fields are required! seeker_id, provider_id, channel_id, "
                                            "channel_sid, ss_twilio_user_id, sp_twilio_user_id"})
        except:
            return Response({"status": False, "message": "There are some error"})

    def get(self, request):
        chat_for = self.request.query_params.get('chat_for')
        # Q(sp=user_id) | Q(ss=user_id, job__is_deleted=False)
        sp = False
        ss = False
        if chat_for:
            if chat_for.lower() == 'service_seeker':
                twilio_user_sid = TwilioChat.objects.filter(ss=request.user.id,).first()
                if not twilio_user_sid:
                    twilio_user_sid = TwilioChat.objects.filter(sp=request.user.id).first()
                    twilio_user_sid = twilio_user_sid.sp_twilio_user_sid
                    channels_data = get_user_twilio_channels(twilio_user_sid)
                    sp = True
                else:
                    twilio_user_sid = twilio_user_sid.ss_twilio_user_sid
                    channels_data = get_user_twilio_channels(twilio_user_sid)
                if twilio_user_sid:
                    # twilio_user_sid = twilio_user_sid.ss_twilio_user_sid
                    # channels_data = get_user_twilio_channels(twilio_user_sid)
                    data = []
                    if channels_data:
                        for i in channels_data:
                            if sp:
                                user_chat = TwilioChat.objects.filter(sp=request.user.id,
                                                                      sp_twilio_user_sid=i['user_sid'],
                                                                      twilio_channel_sid=i['channel_sid']). \
                                    values('id', 'channel_id', channel_sid=F('twilio_channel_sid'), seeker_id=F('ss'),
                                           provider_id=F('sp'), user_name=F('ss__first_name'),
                                           profile_image=F('ss__profile__profile_image'))
                            else:
                                user_chat = TwilioChat.objects.filter(ss=request.user.id, ss_twilio_user_sid=i['user_sid'],
                                                                      twilio_channel_sid=i['channel_sid']).\
                                    values('id', 'channel_id', channel_sid=F('twilio_channel_sid'), seeker_id=F('ss'),
                                           provider_id=F('sp'), user_name=F('sp__first_name'),
                                           profile_image=F('sp__profile__profile_image'))
                            convert_query = list(user_chat)
                            chat_data = None
                            message = None
                            if convert_query:
                                chat_data = convert_query.pop()
                            # message = get_channel_messages(chat_data.get('channel_id'))
                                message = get_message(chat_data.get('channel_sid'))
                            if message:
                                chat_data['last_message'] = message.get('body')
                                chat_data['last_message_time'] = message.get('date_created')
                                # # chat_data['last_message'] = message.pop().get('body')
                                # chat_data['last_message_time'] = message.pop().get('date_created')

                                chat_data['unread_messages_count'] = i['unread_messages_count']
                                # data.append(chat_data)
                                data.append(chat_data)
                                data.sort(key=lambda x: x.get('last_message_time'), reverse=True)
                else:
                    return Response({"status": False, "message": "data does not exist!",
                                     })

            elif chat_for.lower() == 'service_provider':
                twilio_user_sid = TwilioChat.objects.filter(sp=request.user.id).first()
                data = []
                if not twilio_user_sid:
                    twilio_user_sid = TwilioChat.objects.filter(ss=request.user.id).first()
                    twilio_user_sid = twilio_user_sid.ss_twilio_user_sid
                    channels_data = get_user_twilio_channels(twilio_user_sid)
                    ss = True
                else:
                    twilio_user_sid = twilio_user_sid.sp_twilio_user_sid
                    channels_data = get_user_twilio_channels(twilio_user_sid)
                if twilio_user_sid:
                    # twilio_user_sid = twilio_user_sid.sp_twilio_user_sid
                    # channels_data = get_user_twilio_channels(twilio_user_sid)
                    if channels_data:
                        for i in channels_data:
                            if ss:
                                user_chat = TwilioChat.objects.filter(ss=request.user.id,
                                                                      ss_twilio_user_sid=i['user_sid'],
                                                                      twilio_channel_sid=i['channel_sid']). \
                                    values('id', 'channel_id', channel_sid=F('twilio_channel_sid'), seeker_id=F('ss'),
                                           provider_id=F('sp'), user_name=F('sp__first_name'),
                                           profile_image=F('sp__profile__profile_image'))
                            else:
                                user_chat = TwilioChat.objects.filter(sp=request.user.id,
                                                                      sp_twilio_user_sid=i['user_sid'],
                                                                      twilio_channel_sid=i['channel_sid']). \
                                    values('id', 'channel_id', channel_sid=F('twilio_channel_sid'), seeker_id=F('ss'),
                                           provider_id=F('sp'), user_name=F('ss__first_name'),
                                           profile_image=F('ss__profile__profile_image'))

                            convert_query = list(user_chat)
                            chat_data = None
                            message = None
                            if convert_query:
                                chat_data = convert_query.pop()
                                # message = get_channel_messages(chat_data.get('channel_id'))
                                message = get_message(chat_data.get('channel_sid'))
                            if message:
                                chat_data['last_message'] = message.get('body')
                                chat_data['last_message_time'] = message.get('date_created')

                                # msg_data = message.pop()
                                # chat_data['last_message'] = msg_data.get('body')
                                # chat_data['last_message_time'] = msg_data.get('date_created')

                                # chat_data['last_message'] = message.pop().get('body')
                                # chat_data['last_message_time'] = message.pop().get('date_created')
                                chat_data['unread_messages_count'] = i['unread_messages_count']
                                data.append(chat_data)
                                data.sort(key=lambda x: x.get('last_message_time'), reverse=True)
                else:
                    return Response({"status": False, "message": "data doses not exist!",
                                     })
            result = pagination(data, request)
            return Response({"status": True, "data": result.data})
            # return Response({"status": True, "message": "successfully  get the chat list  of login user!",
            #                  'data': data})
        return Response({'status': False, "message": "chat_for should be service_seeker or service_provider required!"})


def get_message(channel_sid):

    client = Client(ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO)
    channel = client.chat.v1 \
        .services('IS876299b7684b4c3cb16a67fec904e74d') \
        .channels(channel_sid) \
        .fetch()
    data_dict = {}
    if channel:
        if channel.messages.list():
            message = channel.messages.list()[-1].body
            date = channel.messages.list()[0].date_created
            data_dict['body'] = channel.messages.list()[-1].body
            data_dict['date_created'] = channel.messages.list()[-1].date_created
            return data_dict
        # return Response({'status': True, 'message': 'your data is here', 'body': message, 'date': date})


def get_channel_messages(channel_id):
    url = "https://chat.twilio.com/v2/Services/IS876299b7684b4c3cb16a67fec904e74d/" \
          "Channels/{}/Messages".format(channel_id)
    payload = {}
    headers = {
        'Authorization':
            'Basic QUNmZjExOGFmYjRhMmZkOGU1NTFjMzlhYzdjZTE'
            'wMjc1YTplNjFlNjliY2U3MTFhYzg2MjFhODM1ZWUzMTQxZDhhYQ=='
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    messages_api = json.loads(response.text)
    if response.status_code == 200:
        message = messages_api['messages']
        return message
    else:
        return None


def get_user_twilio_channels(twilio_user_id):
    url = "https://chat.twilio.com/v2/Services/IS876299b7684b4c3cb16a67fec904e74d/Users/" \
          "{}/Channels".format(twilio_user_id)
    payload = {}
    headers = {
        'Authorization':
            'Basic QUNmZjExOGFmYjRhMmZkOGU1NTFjMzlhYzdjZTEwMjc1YTplNjFlNjliY2U3MTFhYzg2MjFhODM1ZWUzMTQxZDhhYQ=='
    }
    response = requests.request("GET", url, headers=headers, data=payload)
    json_data = json.loads(response.text)
    if response.status_code == 200:
        channels_data = json_data['channels']
        return channels_data
    else:
        return None


class UserChannel(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({"status": False, "message": "Please Provide User SID"})
            chanel = []
            channel_dict = {}
            user_channels = get_user_channels(user_id)
            for record in user_channels:
                channel_dict["user_id"] = record.user_sid
                channel_dict["channel_id"] = record.channel_sid
                channel_dict["account_id"] = record.account_sid
                channel_dict["last_consumed_message_index"] = record.last_consumed_message_index
                channel_dict["unread_messages_count"] = record.unread_messages_count
                message_data = get_message(record.channel_sid)
                channel_dict['body'] = message_data['body']
                channel_dict['date_created'] = message_data['date_created']
                chanel.append(channel_dict.copy())
                chanel.sort(key=lambda x: x.get('date_created'), reverse=True)
            result = pagination(chanel, request)
            return Response({"status": True, "channels": result.data})
            # return Response({"channels": chanel})
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error"})


def get_user_channels(user_id):
    account_sid = ACCOUNT_SID_TWILIO
    auth_token = AUTH_TOKEN_TWILIO
    client = Client(account_sid, auth_token)
    user_channels = client.chat \
        .services('IS876299b7684b4c3cb16a67fec904e74d') \
        .users(user_id) \
        .user_channels \
        .list(limit=10)
    return user_channels