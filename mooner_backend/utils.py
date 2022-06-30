import os

from django.db.models import Q
from rest_framework.permissions import AllowAny
from twilio.rest import Client
from .settings import ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO, API_KEY_TWILIO, \
    SECRET_KEY_TWILIO, CHAT_SERVICE_ID_TWILIO, SYNC_SERVICE_ID_TWILIO,\
    AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME, Gcm_Or_Fcm_Credential_Sid
from rest_framework.authentication import SessionAuthentication
from mooner_backend.settings import EMAIL_HOST_USER
from django.core.mail import EmailMessage
from rest_framework.authtoken.models import Token
from rest_framework.response import Response
import re
import datetime
from datetime import timezone
from user.models import UserProfile
import logging
import boto3
from botocore.exceptions import ClientError
from rest_framework.views import APIView
from rest_framework.pagination import PageNumberPagination
from twilio.jwt.access_token import AccessToken
from twilio.jwt.access_token.grants import (
    SyncGrant,
    ChatGrant
)
from twilio_chat.models import *
from django.apps import apps
from django.template.loader import get_template


def send_otp(to, body):
    try:
        # ACCOUNT_SID_TWILIO = 'ACff118afb4a2fd8e551c39ac7ce10275a'
        # AUTH_TOKEN_TWILIO ='e61e69bce711ac8621a835ee3141d8aa'
        client = Client(ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO)
        verify = client.verify.services('VA5fc4d4318853af1887d8de9dbd9242dd')
        msg_sent = verify.verifications.create(to=to, channel='sms')
        # from_='+12057515885'
        # client = Client(ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO)
        # message = client.messages.create(
        #     # from_=str(from_num),
        #     from_="+12254389571",
        #     body=body,
        #     to=to,
        # )
        e = "sent"
        return e
    except Exception as e:
        return e.msg

def verify_otp(to, code):
    e=''
    try:
        # ACCOUNT_SID_TWILIO = 'ACff118afb4a2fd8e551c39ac7ce10275a'
        # AUTH_TOKEN_TWILIO ='e61e69bce711ac8621a835ee3141d8aa'
        client = Client(ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO)
        verify = client.verify.services('VA5fc4d4318853af1887d8de9dbd9242dd')
        result = verify.verification_checks.create(to=to, code=code)
        # msg_sent = verify.verifications.create(to=to, channel='sms')
        # from_='+12057515885'
        # client = Client(ACCOUNT_SID_TWILIO, AUTH_TOKEN_TWILIO)
        # message = client.messages.create(
        #     # from_=str(from_num),
        #     from_="+12254389571",
        #     body=body,
        #     to=to,
        # )
        if result.status == 'approved':
            e = "approved"
            return e
    except Exception as e:
        return e.msg

class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


def send_email(body, url, users):
    email_from = EMAIL_HOST_USER
    message_body = "Please Confirm Your Email! " + '\n' + url
    email1 = EmailMessage("Email Confirmation Request",
                          message_body, email_from, [users.email])
    email1.content_subtype = 'html'
    email1.send()


def get_token(token):
    if token:
        token_check = Token.objects.filter(key=token).exists()
        if token_check:
            user = Token.objects.filter(key=token).first().user
            if user.is_superuser:
                return Response({"status": True})
            else:
                return Response({"status": False, "Response": "Only Admin is allowed to access."})
        else:
            return Response({"status": False, "Response": "Invalid Token"})
    else:
        return Response({"status": False, "Response": "Please Enter the token"})

def admin_send_email(url, users):
    email_from = EMAIL_HOST_USER
    message_body = "Please click {} to update your password".format(url)
    email1 = EmailMessage("Password Rest Request",
                          message_body, email_from, [users.email])
    email1.content_subtype = 'html'
    email1.send()


def email_validator(email):
    regex = '^[a-z0-9]+[\._]?[a-z0-9]+[@]\w+[.]\w{2,3}$'
    email_validation = re.search(regex, email)
    return email_validation


def get_otp_time(user_id):
    get_user = UserProfile.objects.get(user=user_id)
    user_otp_time = get_user.reset_code_time
    add_3_minutes = user_otp_time + datetime.timedelta(minutes=3)
    dt = datetime.datetime.now()
    difference = dt.replace(tzinfo=timezone.utc) - add_3_minutes
    minutes = difference.total_seconds() / 60
    if minutes > 1.0:
        return False
    else:
        return True


def password_check(passwd):
    SpecialSym = ['$', '@', '#', '%']
    val_string = "Password updated successfully!"
    if len(passwd) < 8:
        val_string = 'length should be at least 8'
        return val_string

    elif len(passwd) > 20:
        val_string = 'length should be not be greater than 20'
        return val_string
    elif not any(char.isdigit() for char in passwd):
        val_string = 'Password should have at least one numeral'
        return val_string

    elif not any(char.isupper() for char in passwd):
        val_string = 'Password should have at least one uppercase letter'
        return val_string

    elif not any(char.islower() for char in passwd):
        return val_string

    elif not any(char in SpecialSym for char in passwd):
        val_string = 'Password should have at least one of the symbols like "$@#%"'
        return val_string
    else:
        return val_string


class UploadFile(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        file = request.FILES['file']
        file_for = request.data['file_for']
        client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        bucket = AWS_BUCKET_NAME
        split_filename = request.FILES['file'].name.split(".")
        current_time = str(datetime.datetime.now()).replace(' ', '')
        file_name = "{}{}{}{}".format(split_filename[0], current_time, ".", split_filename[-1])
        clean_f_name = file_name
        upload_file_key = file_for + clean_f_name
        if file:
            try:
                client.put_object(Bucket=bucket, Key=upload_file_key, Body=file, ACL='public-read')
                return Response({"status": True, "message": "File uploaded successfully", "url": upload_file_key})
            except ClientError as e:
                logging.error(e)
                return Response({"status": False, "message": "File not uploaded"})


class DeleteFile(APIView):
    permission_classes = (AllowAny,)

    @staticmethod
    def post(request):
        delete_file = request.data['del_file']
        client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        bucket = AWS_BUCKET_NAME
        key = delete_file
        if delete_file:
            try:
                client.delete_object(Bucket=bucket, Key=key)
                return Response({"status": False, "message": "File deleted"})
            except ClientError as e:
                logging.error(e)
                return Response({"status": False, "message": "File not deleted"})


class UrlConcat(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):

        file_key = request.data.get('file_key')
        if file_key:
            bucket_url = 'https://mooner-staging-files.s3-us-west-2.amazonaws.com/'
            new_url = ["{}{}".format(bucket_url, i) for i in file_key]
            return Response({"status": True, "url": new_url})
        else:
            return Response({"status": False, "message": "Please enter file_key"})


def pagination(all_records, request):
    paginator = PageNumberPagination()
    paginator.page_size = 10
    result_page = paginator.paginate_queryset(all_records, request)
    return paginator.get_paginated_response(result_page)


class TwilioToken(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # identity = ss_id
        name = self.request.POST.get('identity')
        sp = self.request.POST.get('sp_id')
        if name and sp:
            service_sid = CHAT_SERVICE_ID_TWILIO
            sync_service_sid = SYNC_SERVICE_ID_TWILIO
            token = AccessToken(ACCOUNT_SID_TWILIO, API_KEY_TWILIO, SECRET_KEY_TWILIO, identity=name)
            if sync_service_sid:
                sync_grant = SyncGrant(service_sid=sync_service_sid)
                token.add_grant(sync_grant)
            if service_sid:
                chat_grant = ChatGrant(service_sid=service_sid, push_credential_sid=Gcm_Or_Fcm_Credential_Sid)
                token.add_grant(chat_grant)
            # print(token.to_jwt().decode('utf-8'))

            sp_token = AccessToken(ACCOUNT_SID_TWILIO, API_KEY_TWILIO, SECRET_KEY_TWILIO, identity=sp)
            if sync_service_sid:
                sp_sync_grant = SyncGrant(service_sid=sync_service_sid)
                token.add_grant(sp_sync_grant)
            if service_sid:
                sp_chat_grant = ChatGrant(service_sid=service_sid, push_credential_sid=Gcm_Or_Fcm_Credential_Sid)
                sp_token.add_grant(sp_chat_grant)

            # twilio_channel = TwilioChat.objects.filter(ss_id=name, sp_id=sp)
            twilio_channel = TwilioChat.objects.filter(Q(ss_id=name, sp_id=sp) | Q(ss_id=sp, sp_id=name))
            channel_name = ''
            if twilio_channel.exists():
                channel_name = twilio_channel.first().channel_id
            provider_name = User.objects.filter(id=sp).first().first_name
            return Response({'status': True, 'message': 'Token generated successfully',
                             'identity': name,
                             'ss_token': token.to_jwt().decode('utf-8'),
                             'sp_token': sp_token.to_jwt().decode('utf-8'),
                             'provider_name': provider_name,
                             'channel_name': channel_name})
        else:
            return Response({'status': False, 'message': 'identity and sp  are required'})


# email function

def email_function(**kwargs):
    email_from = EMAIL_HOST_USER
    message_body = kwargs['body']
    subject = kwargs['subject']
    email = kwargs['email']
    email1 = EmailMessage(subject,
                          message_body, email_from, [email])
    email1.content_subtype = 'html'
    email1.send()


def soft_delete(**kwargs):
    if kwargs['user_modal'] == 'Category':
        modal = apps.get_model('category_management', kwargs.get('user_modal'))
        if modal.all_objects.filter(tn_parent=kwargs['id']).exists():
            # var_ids = modal.all_objects.get(id=kwargs['id'])
            # decendents = var_ids.tn_descendants_pks
            ids = modal.all_objects.filter(tn_parent=kwargs['id']).values_list('id', flat=True)
            if len(ids) > 0:
                for i in ids:
                    idss = modal.all_objects.filter(tn_parent=i).values_list('id', flat=True)
                    modal.all_objects.filter(id__in=idss).delete()
            # ids = decendents.split(',')
            modal.all_objects.filter(id__in=ids).delete()
            category = modal.all_objects.filter(id=kwargs['id']).delete()
            if category:
                return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
            else:
                return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})
        else:
            if modal.all_objects.filter(id=kwargs['id']).exists():
                modal.all_objects.filter(id=kwargs['id']).delete()
                return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
            else:
                return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})
    else:
        if kwargs['user_modal'].all_objects.filter(id=kwargs['id']).exists():
            kwargs['user_modal'].all_objects.filter(id=kwargs['id']).delete()
            return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
        else:
            return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})


def permanent_delete(**kwargs):
    if kwargs['user_modal'] == 'Category':
        modal = apps.get_model('category_management', kwargs.get('user_modal'))
        if modal.all_objects.filter(tn_parent=kwargs['id']).exists():
            # var_ids = modal.all_objects.get(id=kwargs['id'])
            # decendents = var_ids.tn_descendants_pks
            ids = modal.all_objects.filter(tn_parent=kwargs['id']).values_list('id', flat=True)
            # ids = decendents.split(',')
            modal.all_objects.filter(id__in=ids).hard_delete()
            category = modal.all_objects.filter(id=kwargs['id']).hard_delete()
            if category:
                return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
            else:
                return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})
        else:
            if modal.all_objects.filter(id=kwargs['id']).exists():
                modal.all_objects.filter(id=kwargs['id']).hard_delete()
                return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
            else:
                return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})
    else:
        if kwargs['user_modal'].all_objects.filter(id=kwargs['id']).exists():
            kwargs['user_modal'].all_objects.filter(id=kwargs['id']).hard_delete()
            return Response({"status": True, "message": "{} Deleted Successfully!".format(kwargs['msg'])})
        else:
            return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})


def restore_from_softdelete(**kwargs):
    if kwargs['user_modal'] == 'Category':
        modal = apps.get_model('category_management', kwargs.get('user_modal'))
        if modal.all_objects.filter(tn_parent=kwargs['id']).exists():
            # var_ids = modal.all_objects.get(id=kwargs['id'])
            ids = modal.all_objects.filter(tn_parent=kwargs['id']).values_list('id', flat=True)
            if len(ids) > 0:
                for i in ids:
                    idss = modal.all_objects.filter(tn_parent=i).values_list('id', flat=True)
                    modal.all_objects.filter(id__in=idss).restore()
            # decendents = var_ids.tn_descendants_pks
            # ids = decendents.split(',')
            modal.all_objects.filter(id__in=ids).restore()
            category = modal.all_objects.filter(id=kwargs['id']).restore()
            if category:
                return Response({"status": True, "message": "{} Restore Successfully!".format(kwargs['msg'])})
            else:
                return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})
        else:
            if modal.all_objects.filter(id=kwargs['id']).exists():
                modal.all_objects.filter(id=kwargs['id']).restore()
                return Response({"status": True, "message": "{} Restore Successfully!".format(kwargs['msg'])})
            else:
                return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})
    else:
        if kwargs['user_modal'].all_objects.filter(id=kwargs['id']).exists():
            kwargs['user_modal'].all_objects.filter(id=kwargs['id']).restore()
            return Response({"status": True, "message": "{} Restore Successfully!".format(kwargs['msg'])})
        else:
            return Response({"status": False, "message": "{} ID does not exist".format(kwargs['msg'])})


def admin_softdelete_record(self, request):
    qs = self.model.all_objects
    ordering = self.get_ordering(request)
    if ordering:
        qs = qs.order_by(*ordering)
    return qs


def send_email_template(**kwargs):

    """
    Send email template to mooner app  user.
    """

    temp_path = kwargs.get('template_name')
    data = kwargs.get('data')
    subject_msg = kwargs.get('subject_msg')
    email = kwargs.get('email')
    try:
        message = get_template(temp_path).render(data)
        mail = EmailMessage(
            subject=subject_msg,
            body=message,
            from_email=EMAIL_HOST_USER,
            to=[email]
        )
        mail.content_subtype = "html"
        mail.send()
        return True
    except Exception:
        return False
