import datetime
import functools
import random
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.hashers import make_password
from django.core.mail import EmailMessage
from django.db import transaction
from django.db.models import Avg, F, Case, When, Value, FloatField, Sum
from django.db.models.functions import Cast
from django.utils.encoding import force_bytes, force_text
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from rest_framework.authtoken.models import Token
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, AllowAny, IsAdminUser
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.tokens import RefreshToken

from booking.models import Spservices
from mooner_backend.utils import send_otp, send_email, admin_send_email, email_validator, get_otp_time, verify_otp, \
    password_check, pagination, send_email_template
from django.contrib.auth.tokens import PasswordResetTokenGenerator
from user.token import account_activation_token
from .models import UserAddresses
from .serializers import *
from geopy.geocoders import Nominatim
from django.core.exceptions import ObjectDoesNotExist
from rest_framework import generics
from django.db.models import CharField
from django.db.models import Q, Count
import uuid
from mln.utils import check_reference_id
from mln.models import Referral


class UserProfiles(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request, *args, **kwargs):
        try:
            userData = UserProfile.objects.filter(user=request.user.id).exists()
            if userData:
                userData = UserProfile.objects.get(user=request.user.id)
                serializer = UserProfileSerializer(userData, many=False)
                return Response({"status": True,
                                 "message": "User Profile Information!", "data": serializer.data})
            else:
                return Response({"status": False,
                                 "message": "Profile does not exist!"})
        except:
            return Response({"status": False,
                             "message": "There is some error!"})


class UserAdminRoleAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')
        email = request.data.get('email')
        username = request.data.get('username')
        password = request.data.get('password')
        role_name = request.data.get('role_name')

        if not UserProfile.objects.filter(roles__role_name__contains=role_name):
            return Response({"status": False,
                             "message": "Invalid Role Name"})
        data = {}
        if first_name and last_name and email and password and role_name:
            if User.objects.filter(first_name=first_name, last_name=last_name,
                                   email=email).exists() and UserProfile.objects.filter(
                roles__role_name__contains=role_name).exists():
                return Response({"status": False,
                                 "message": "User already exists!"})
            else:
                try:
                    pwd = make_password(password)
                    with transaction.atomic():
                        try:
                            roles = Role.objects.get(role_name='User')
                        except:

                            roles = Role.objects.create(role_name=role_name)
                            generated_otp = str(random.randint(1000, 9999))
                            user = User.objects.create(
                                first_name=first_name, last_name=last_name, username=username,
                                email=email, password=pwd, )
                            UserProfile.objects.create(
                                user=user,
                                roles=roles,
                                user_type=request.POST.get('user_type'),
                                otp=generated_otp
                            )
                            token, created = Token.objects.get_or_create(user=user)
                            data = {
                                "user_id": user.id,
                                "user_name": user.first_name,
                                "last_name": user.last_name,
                                "email": user.email,
                                "token": token.key,
                            }
                            return Response({"status": True,
                                             "message": "Registered successfully!", "OTP": generated_otp,
                                             "data": data})
                except:
                    return Response(
                        {"status": False,
                         "message": "Could Not Register User!", "data": data})
        return Response(
            {"status": False, "message": "Parameters are incomplete!"})


# ==================User Signup===================== #

class UserRegisterAPIView(APIView):
    permission_classes = (AllowAny,)

    @transaction.atomic
    def post(self, request):

        login_type = request.data.get('login_type')
        username = request.data.get('username')
        cell_phone = request.data.get('cell_phone')
        user_id = request.data.get('user_id')
        if not login_type and not username and not cell_phone:
            return Response({"status": False,
                             "message": "Please enter username, phone number and login type!"})

        if login_type:
            if login_type == 'local' or login_type == "LOCAL" or login_type == 'Local':
                # if User.objects.filter(username=request.data.get('username')).exists() and UserProfile.objects.filter(
                #         cell_phone=cell_phone).exists():
                    # generated_otp = str(random.randint(1000, 9999))
                    # UserProfile.objects.filter(cell_phone=cell_phone).update(otp=generated_otp,
                    #                                                          reset_code_time=datetime.datetime.now())
                    # send_otp(cell_phone, "Your Confirmation code is : " + generated_otp)
                    # send_otp(cell_phone, "Your Confirmation code is : ")
                    # user = UserProfile.objects.get(cell_phone=cell_phone)
                    # data = {
                    #     "user_id": user.user.id,
                    #     "username": user.user.username,
                    #     "cell_phone": user.cell_phone,
                    #     # "expire_otp_time": "3"
                    # }
                    # return Response({"status": True,
                    #                  "message": "User Profile OTP Reset!",
                    #                  "data": data})
                if not cell_phone:
                    return Response({"status": False,
                                     "message": "Please enter phone number!"})
                # if cell_phone:
                #     profile_phone_no = UserProfile.objects.filter(cell_phone=cell_phone).exists()
                #     if profile_phone_no:
                #         return Response({"status": False,
                #                          "message": "User already exist with this Phone Number!"})

                if len(cell_phone) < 9 or len(cell_phone) > 15:
                    return Response({"status": False,
                                     "message": "Phone Number Length should be 9 to 15 "})
                if not cell_phone.startswith('+'):
                    return Response({"status": False,
                                     "message": "Please enter phone number with Country code"})
                r_code = ""
                if request.data.get('r_code'):
                    if len(request.data.get('r_code')) == 10:
                        r_code = request.data.get('r_code')
                        if not UserProfile.objects.filter(r_code=r_code).exists():
                            return Response({"status": False,
                                             "message": "Referenced code does not exist!"})
                    else:
                        return Response({"status": False,
                                         "message": "Referenced code length must be 10!"})
                data = {}
                if user_id:
                    if UserProfile.objects.filter(user=user_id).exists():
                        instance_user_profile = UserProfile.objects.get(user=user_id)
                        if UserProfile.objects.filter(cell_phone=cell_phone).exclude(user=user_id):
                            return Response({"status": False,
                                             "message": "Phone Number already exist!"})
                        else:
                            instance_user_profile.cell_phone = cell_phone
                        instance_user_profile.save()
                        # generated_otp = str(random.randint(1000, 9999))
                        # UserProfile.objects.filter(cell_phone=cell_phone).update(otp=generated_otp,
                        #                                                          reset_code_time=datetime.datetime.now())
                        # send_otp(cell_phone, "Your Confirmation code is : " + generated_otp)
                        send_otp(cell_phone, "Your Confirmation code is : ")
                        user = UserProfile.objects.get(cell_phone=cell_phone)
                        data = {
                            "user_id": user.user.id,
                            "username": user.user.username,
                            "cell_phone": user.cell_phone,
                            # "expire_otp_time": "3"
                        }
                        return Response({"status": False,
                                         "message": "User Phone Number Update successfully!", "data": data})
                else:
                    try:
                        otp = request.data.get('otp')
                        if otp:
                            opt_status = verify_otp(cell_phone, otp)
                            if opt_status == 'approved':
                                roles, created = Role.objects.get_or_create(role_name='user')
                                # if created:
                                #     roles = created
                                # generated_otp = str(random.randint(1000, 9999))
                                generated_rcode = str(random.randint(2345609800, 9923459000))
                                user = User.objects.create(username=username, first_name=username)
                                # added for referal system
                                if request.data.get('reference_id'):
                                    check_ref = check_reference_id(User=User, user=user,
                                                       reference_id=request.data.get('reference_id'))
                                    if not check_ref:
                                        transaction.set_rollback(True)
                                        return Response({"status": False,
                                                         "message": "reference ID does not exist"})
                                else:
                                    if not Referral.objects.filter(user=user).exists():
                                        Referral.objects.create(user=user)
                                # added for referal system
                                user_get = UserProfile.objects.filter(r_code=r_code).first()
                                if user_get:
                                    created_profile = UserProfile.objects.create(
                                        user=user,
                                        roles=roles,
                                        cell_phone=cell_phone,
                                        r_code=generated_rcode,
                                        refer_user=user_get.user,
                                        user_type='SS',
                                        reference_id=uuid.uuid4()
                                    )
                                    user_get.referred.add(user)
                                    user_get.save()
                                    # if created_profile:
                                    #     send_otp(request.POST.get('cell_phone'), "Your Confirmation code is : ")
                                    login(request, user)
                                    refresh = RefreshToken.for_user(user)
                                else:
                                    created_profile = UserProfile.objects.create(
                                        user=user,
                                        roles=roles,
                                        cell_phone=cell_phone,
                                        r_code=generated_rcode,
                                        reset_code_time=datetime.datetime.now(),
                                        user_type='SS',
                                        reference_id=uuid.uuid4()
                                    )
                                    # if created_profile:
                                    #     send_otp(cell_phone, "Your Confirmation code is : ")
                                    login(request, user)
                                    refresh = RefreshToken.for_user(user)
                                user_address = UserAddresses.objects.filter(user_id=user.id).order_by('-id')
                                serialized_address = UserAddressSerializer(user_address, many=True)

                                data = {
                                    "user_id": user.id,
                                    "username": user.username,
                                    "email": user.email,
                                    "cell_phone": created_profile.cell_phone,
                                    "referral_code": generated_rcode,
                                    "reference_id": user.profile.reference_id,
                                    "login_type": "local",
                                    # "expire_otp_time": "3",
                                    'address': serialized_address.data,
                                    "access": str(refresh.access_token)
                                }
                                return Response({"status": True,
                                                 "message": "Registered successfully!",
                                                 "data": data})
                            else:
                                return Response({"status": False,
                                                 "message": "Wrong Otp!",
                                                 "data": "none"})
                        else:
                            username = request.data.get('username')
                            if not username:
                                return Response({"status": False,
                                                 "message": "Username is Required "})
                            # if User.objects.filter(username=username).exists():
                            #     return Response({"status": False,
                            #                      "message": "Username already exist "})
                            if UserProfile.objects.filter(cell_phone=cell_phone).exists():
                                return Response({"status": False,
                                                 "message": "User already registered!"})
                            send_otp(cell_phone, "Your Confirmation code is : ")
                            return Response({"status": True,
                                             "message": "OTP has been sent successfully on your phone number!"})
                    except:
                        transaction.set_rollback(True)
                        return Response(
                            {"status": False,
                             "message": "Could Not Register User!", "data": data})
            elif login_type == 'facebook' or login_type == "FACEBOOK" or login_type == "Facebook":
                facebook_name = request.data.get('facebook_name')
                facebook_id = request.data.get('facebook_id')
                r_code = ""
                if request.data.get('r_code'):
                    if len(request.data.get('r_code')) == 10:
                        r_code = request.data.get('r_code')
                        if not UserProfile.objects.filter(r_code=r_code).exists():
                            return Response({"status": False,
                                             "message": "Referenced code does not exist!"})
                    else:
                        return Response({"status": False,
                                         "message": "Referenced code length must be 10!"})
                if not facebook_name:
                    return Response({"status": False,
                                     "message": "Please Provide Facebook Name!"})
                if not facebook_id:
                    return Response({"status": False,
                                     "message": "Please Provide Facebook ID!"})
                if facebook_name and facebook_id:
                    user_object = UserProfile.objects.filter(registration_id=facebook_id, login_type="Facebook").first()
                    if user_object and User.objects.filter(username=facebook_id).exists():
                        user = User.objects.get(username=facebook_id)
                        login(request, user)
                        refresh = RefreshToken.for_user(user)
                        serializer = UserSerializer(user, many=False)
                        user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                        serialized_address = UserAddressSerializer(user_address, many=True)
                        data = {
                            "user_register": True,
                            "user": serializer.data,
                            'address': serialized_address.data,
                            "access": str(refresh.access_token)
                        }
                        if not Referral.objects.filter(user=user).exists():
                            Referral.objects.create(user=user)
                        # data = {
                        #     "user_id": user_object.user.id,
                        #     "user_name": user_object.user.first_name,
                        #     "email": user_object.user.email,
                        #     "login_type": user_object.login_type,
                        #     "user_type": user_object.user_type,
                        #     "referral_code": user_object.r_code,
                        #     "access": str(refresh.access_token),
                        # }
                        return Response(
                            {"status": True, 'message': 'user logged in successfully! ',
                             'data': data})
                    else:
                        try:
                            role, created = Role.objects.get_or_create(role_name='user')
                            if created:
                                role = created
                            if User.objects.filter(username=facebook_id).exists():
                                return Response(
                                    {"status": False,
                                     "message": "Facebook ID already exist!"})
                            user = User.objects.create(username=facebook_id, first_name=facebook_name)
                            generated_rcode = str(random.randint(2345609800, 9923459000))
                            user_get = UserProfile.objects.filter(r_code=r_code).first()
                            if user_get:
                                user_profile = UserProfile.objects.create(user=user, registration_id=facebook_id,
                                                                          roles=role, login_type="Facebook",
                                                                          refer_user=user_get.user,
                                                                          r_code=generated_rcode, user_type='SS',
                                                                          reference_id=uuid.uuid4())
                            else:
                                user_profile = UserProfile.objects.create(user=user, registration_id=facebook_id,
                                                                          roles=role, login_type="Facebook",
                                                                          r_code=generated_rcode, user_type='SS',
                                                                          reference_id=uuid.uuid4())
                            login(request, user)
                            refresh = RefreshToken.for_user(user)
                            serializer = UserSerializer(user, many=False)
                            user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                            serialized_address = UserAddressSerializer(user_address, many=True)

                            data = {
                                "user_register": False,
                                "user": serializer.data,
                                'address': serialized_address.data,
                                "access": str(refresh.access_token)
                            }
                            # data = {
                            #     "user_id": user_profile.user.id,
                            #     "user_name": user_profile.user.first_name,
                            #     "login_type": user_profile.login_type,
                            #     "user_type": user_profile.user_type,
                            #     "referral_code": user_profile.r_code,
                            #     "access": str(refresh.access_token),
                            # }
                            return Response(
                                {"status": True,
                                 "message": "User registered successfully!", "data": data})
                        except:
                            return Response({"status": False,
                                             "message": "Could Not Register User!"})
                else:
                    return Response(
                        {"status": False,
                         "message": "You should give social id!"})
            elif login_type == 'google' or login_type == "GOOGLE" or login_type == "Google":
                google_name = request.data.get('google_name')
                google_id = request.data.get('google_id')
                email = request.data.get('email')
                if not google_name:
                    return Response({"status": False,
                                     "message": "Please Provide Google Name!"})
                if not google_id:
                    return Response({"status": False,
                                     "message": "Please Provide Google ID!"})
                if not email:
                    return Response({"status": False,
                                     "message": "Please Provide Email!"})

                profile_image = ""
                if request.data.get('profile_image'):
                    profile_image = request.data.get('profile_image')
                r_code = ""
                if request.data.get('r_code'):
                    if len(request.data.get('r_code')) == 10:
                        r_code = request.data.get('r_code')
                        if not UserProfile.objects.filter(r_code=r_code).exists():
                            return Response({"status": False,
                                             "message": "Referenced code does not exist!"})
                    else:
                        return Response({"status": False,
                                         "message": "Referenced code length must be 10!"})
                if google_name and google_id and email:
                    if User.objects.filter(username=google_id).exists():
                        get_email = User.objects.get(username=google_id)
                        if not get_email.email == email:
                            return Response(
                                {"status": False, 'message': 'User Register with different email'})
                    user_object = UserProfile.objects.filter(registration_id=google_id, login_type="Google").first()
                    if user_object and User.objects.filter(username=google_id, email=email).exists():
                        user = User.objects.get(username=google_id)
                        login(request, user)
                        refresh = RefreshToken.for_user(user)
                        serializer = UserSerializer(user, many=False)
                        user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                        serialized_address = UserAddressSerializer(user_address, many=True)
                        data = {
                            "user_register": True,
                            "user": serializer.data,
                            'address': serialized_address.data,
                            "access": str(refresh.access_token)
                        }
                    if User.objects.filter(email=email).exists():
                        user = User.objects.get(email=email)
                        login(request, user)
                        refresh = RefreshToken.for_user(user)
                        serializer = UserSerializer(user, many=False)
                        user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                        serialized_address = UserAddressSerializer(user_address, many=True)
                        data = {
                            "user_register": True,
                            "user": serializer.data,
                            'address': serialized_address.data,
                            "access": str(refresh.access_token)
                        }
                        if not Referral.objects.filter(user=user).exists():
                            Referral.objects.create(user=user)

                        # data = {
                        #     "user_id": user_object.user.id,
                        #     "first_name": user_object.user.first_name,
                        #     "email": user_object.user.email,
                        #     "login_type": user_object.login_type,
                        #     "user_type": user_object.user_type,
                        #     "referral_code": user_object.r_code,
                        #     "access": str(refresh.access_token)
                        # }
                        return Response(
                            {"status": True, 'message': 'User logged in successfully!',
                             'data': data})
                    else:
                        try:
                            role, created = Role.objects.get_or_create(role_name='user')
                            if created:
                                role = created
                            if User.objects.filter(username=google_id).exists():
                                return Response(
                                    {"status": True,
                                     "message": "Google ID already exist!"})
                            if User.objects.filter(email=email).exists():
                                return Response({"status": False,
                                                 "message": "User Email already exists!"})
                            user = User.objects.create(username=google_id, first_name=google_name, email=email)
                            generated_rcode = str(random.randint(2345609800, 9923459000))
                            user_get = UserProfile.objects.filter(r_code=r_code).first()
                            if user_get:
                                user_profile = UserProfile.objects.create(user=user, registration_id=google_id,
                                                                          roles=role, login_type="Google",
                                                                          refer_user=user_get.user,
                                                                          profile_image=profile_image,
                                                                          r_code=generated_rcode, user_type='SS',
                                                                          reference_id=uuid.uuid4())
                            else:
                                user_profile = UserProfile.objects.create(user=user, registration_id=google_id,
                                                                          roles=role, login_type="Google",
                                                                          profile_image=profile_image,
                                                                          r_code=generated_rcode, user_type='SS',
                                                                          reference_id=uuid.uuid4())
                            login(request, user)
                            refresh = RefreshToken.for_user(user)
                            serializer = UserSerializer(user, many=False)
                            user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                            serialized_address = UserAddressSerializer(user_address, many=True)

                            data = {
                                "user_register": False,
                                "user": serializer.data,
                                'address': serialized_address.data,
                                "access": str(refresh.access_token)
                            }
                            data1 = {'username': request.user.first_name}
                            send_email_template(template_name='email_templates/singup.html',
                                                subject_msg="congratulations on successfully signup",
                                                email=user.email,
                                                data=data1)
                            # data = {
                            #     "user_id": user_profile.user.id,
                            #     "user_name": user_profile.user.first_name,
                            #     "login_type": user_profile.login_type,
                            #     "user_type": user_profile.user_type,
                            #     "referral_code": user_profile.r_code,
                            #     "access": str(refresh.access_token)
                            # }
                            return Response(
                                {"status": True,
                                 "message": "User Logged in successfully!", "data": data})
                        except:
                            return Response({"status": False,
                                             "message": "There's some error!"})
                else:
                    return Response(
                        {"status": False,
                         "message": "You should give Google id!"})
            else:
                return Response(
                    {"status": False,
                     "message": "Login type Should be Local, Facebook or Google"})
        else:
            return Response({"status": False, "message": "Please Provide Login Type!"})


# ==================User Update using Facebook or Google===================== #

class UserUpdateAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):
        # login_type = request.data.get('login_type')
        # if login_type:
        #     if login_type == 'facebook' or login_type == "FACEBOOK" or login_type == "Facebook":
        try:
            user_id = request.data.get('user_id')
            email = ""
            if request.data.get('email'):
                email = request.data.get('email')
                if User.objects.filter(email=email).exclude(id=user_id):
                    return Response({"status": False,
                                     "message": "User Email already exists!"})
            full_name = ""
            if request.data.get('full_name'):
                full_name = request.data.get('full_name')
            if not user_id:
                return Response({"status": False,
                                 "message": "user_id required"})
            if not User.objects.filter(id=user_id).exists():
                return Response({"status": False,
                                 "message": "User ID does not exist"})
            instance_user = User.objects.get(id=user_id)
            if request.data.get('reference_id'):
                check_ref = check_reference_id(User=User, user=instance_user,
                                   reference_id=request.data.get('reference_id'))
                if not check_ref:
                    return Response({"status": False,
                                     "message": "reference ID does not exist"})
            else:
                if not Referral.objects.filter(user=instance_user).exists():
                    Referral.objects.create(user=instance_user)
            if instance_user:
                if full_name:
                    instance_user.first_name = full_name
                if email:
                    instance_user.email = email
                instance_user.save()
                user_profile = UserProfile.objects.get(user=user_id)
                user = User.objects.get(id=user_id)
                serializer = UserSerializer(user, many=False)
                user_obj = User.objects.get(id=user_id)
                refresh = RefreshToken.for_user(user_obj)

                # users = User.objects.get(id=user_id)
                # refresh = RefreshToken.for_user(users)
                # user_obj = User.objects.filter(id=user_id)
                # serializer = UserSerializer(user_obj, many=False)
                data = {
                    "user": serializer.data,
                    "access": str(refresh.access_token)
                }

                # data = {
                #     "user_id": user.user.id,
                #     "full_name": user.user.first_name,
                #     "email": user.user.email,
                #     "Social_id": user.user.username,
                #     "login_type": user.login_type,
                #     "user_type": user.user_type,
                #     "referral_code": user.r_code,
                #     "expire_otp_time": "3"

                # }
                return Response({"status": True,
                                 "message": "Update successfully!",
                                 "data": data})
        except:
            return Response(
                {"status": False,
                 "message": "Could Not update User!", })
            # elif login_type == 'google' or login_type == "GOOGLE" or login_type == "Google":
            #     try:
            #         user_id = request.data.get('user_id')
            #         email = ""
            #         if request.data.get('email'):
            #             email = request.data.get('email')
            #             if User.objects.filter(email=email).exclude(id=user_id):
            #                 return Response({"status": False,
            #                                  "message": "User Email already exists!"})
            #         full_name = ""
            #         if request.data.get('full_name'):
            #             full_name = request.data.get('full_name')
            #         if not user_id:
            #             return Response({"status": False,
            #                              "message": "user_id required"})
            #         if not User.objects.filter(id=user_id).exists():
            #             return Response({"status": False,
            #                              "message": "User ID does not exist"})
            #         instance_user = User.objects.get(id=user_id)
            #         if instance_user:
            #             instance_user.first_name = full_name
            #             instance_user.email = email
            #             instance_user.save()
            #             user = UserProfile.objects.get(user=user_id)
            #             data = {
            #                 "user_id": user.user.id,
            #                 "full_name": user.user.first_name,
            #                 "email": user.user.email,
            #                 "google_id": user.user.username,
            #                 "login_type": user.login_type,
            #                 "user_type": user.user_type,
            #                 "referral_code": user.r_code,
            #                 "expire_otp_time": "3"
            #
            #             }
            #             return Response({"status": True,
            #                              "message": "Update successfully!",
            #                              "data": data})
            #     except:
            #         return Response(
            #             {"status": False,
            #              "message": "Could Not update User!", })
            # else:
            #     return Response(
            #         {"status": False,
            #          "message": "Login type Should be Facebook or Google"})
        # else:
        #     return Response({"status": False,
        #                      "message": "Please mention login type!"})


# ==================User Update using Phone===================== #

class UserUpdatePhoneAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def put(self, request):

        try:
            user_id = request.data.get('user_id')
            email = ""
            if request.data.get('email'):
                email = request.data.get('email').lower()
                if User.objects.filter(email=email).exclude(id=user_id):
                    return Response({"status": False,
                                     "message": "User Email already exists!"})
            password = ""
            if request.data.get('password'):
                password = request.data.get('password')
            if not User.objects.filter(id=user_id).exists():
                return Response({"status": False,
                                 "message": "User ID does not exist"})
            instance_user = User.objects.get(id=user_id)
            if instance_user:
                instance_user.email = email
                instance_user.password = make_password(password)
                instance_user.save()
                user = User.objects.get(id=user_id)
                data1 = {'username': request.user.first_name}
                send_email_template(template_name='email_templates/singup.html',
                                    subject_msg="congratulations on successfully signup",
                                    email=user.email,
                                    data=data1)
                # url = 'http://127.0.0.1:8000/user/activate/' + urlsafe_base64_encode(
                #     force_bytes(instance_user.pk)) + '/' + account_activation_token.make_token(
                #     instance_user) + '/'
                # send_email("Please Confirm Your Email! " + '\n' + url, url, instance_user)
                refresh = RefreshToken.for_user(user)
                serializer = UserSerializer(user, many=False)
                user_address = UserAddresses.objects.filter(user_id=user.id).order_by('-id')
                serialized_address = UserAddressSerializer(user_address, many=True)

                data = {
                    'user': serializer.data,
                    'address': serialized_address.data,
                    # "user_id": user.id,
                    # "first_name": user.first_name,
                    # "last_name": user.last_name,
                    # "email": user.email,
                    # "refresh": str(refresh),
                    "access": str(refresh.access_token),

                }

                # data = {
                #     "user_id": user.user.id,
                #     "email": user.user.email,
                #     "cell_phone": user.cell_phone,
                #     "username": user.user.username,
                #     "referral_code": user.r_code,
                #     "login_type": user.login_type,
                #     "user_type": user.user_type,
                #
                # }
                # serializer = UserProfileSerializer(user, many=True)
                return Response({"status": True,
                                 "message": "User Update successfully! Please Check your Email for Confirmation",
                                 "data": data})
            else:
                return Response(
                    {"status": False,
                     "message": "User ID does not exist"})
        except:
            return Response(
                {"status": False,
                 "message": "Could Not update User!", })


# ==================User Profile view using User ID and OTP===================== #

class UserProfileAPIView(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            otp = request.data.get('otp')
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({"status": False,
                                 "message": "User ID is Required"})
            if not otp:
                return Response({"status": False,
                                 "message": "otp is Required"})
            if not User.objects.filter(id=user_id).exists():
                return Response({"status": False,
                                 "message": "User ID does not exist"})
            # if not UserProfile.objects.filter(otp=otp).exists():
            #     return Response({"status": False,
            #                      "message": "otp does not exist"})
            # otp_time = get_otp_time(user_id)
            # if not otp_time:
            #     return Response({"status": False,
            #                      "message": "otp time expire please generate new one"})

            # if User.objects.filter(id=user_id).exists() and UserProfile.objects.filter(otp=otp).exists():

            if User.objects.filter(id=user_id).exists():
                users = User.objects.get(id=user_id)
                obj = UserProfile.objects.get(user=users)
                opt_status = verify_otp(obj.cell_phone, otp)
                if opt_status == 'approved':
                    user = UserProfile.objects.get(user=user_id)
                    users = User.objects.get(id=user_id)

                    url = 'http://127.0.0.1:8000/account/activate/' + urlsafe_base64_encode(
                        force_bytes(users.pk)) + '/' + account_activation_token.make_token(users) + '/'
                    send_email("Please Confirm Your Email! " + '\n' + url, url, users)
                    refresh = RefreshToken.for_user(users)
                    data = {
                        "user_id": user.user.id,
                        "email": user.user.email,
                        "cell_phone": user.cell_phone,
                        "username": user.user.username,
                        "referral_code": user.r_code,
                        "login_type": user.login_type,
                        "access": str(refresh.access_token),
                    }
                    return Response({"status": True,
                                     "message": "User Profile!",
                                     "Text": "Please Check your email for confirmation",
                                     "data": data})
                else:
                    return Response({"status": False,
                                     "message": "OTP has been expired"})

            else:
                return Response({"status": False,
                                 "message": "user id or OTP Code Does not Exist!"})
        except:
            return Response({"status": False,
                             "message": "Not Found!"})


# ==================User Phone Profile view ===================== #

class UserProfileOTP(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            otp = request.data.get('otp')
            user_id = request.data.get('user_id')
            if not user_id:
                return Response({"status": False,
                                 "message": "User ID is Required"})
            if not otp:
                return Response({"status": False,
                                 "message": "otp is Required"})
            if not User.objects.filter(id=user_id).exists():
                return Response({"status": False,
                                 "message": "User ID does not exist"})
            # if not UserProfile.objects.filter(otp=otp).exists():
            #     return Response({"status": False,
            #                      "message": "otp does not exist"})
            # otp_time = get_otp_time(user_id)
            # if not otp_time:
            #     return Response({"status": False,
            #                      "message": "otp time expire please generate new one"})

            # if User.objects.filter(id=user_id).exists() and UserProfile.objects.filter(otp=otp).exists():
            if User.objects.filter(id=user_id).exists():
                # user = UserProfile.objects.get(user=user_id)
                users = User.objects.get(id=user_id)
                obj = UserProfile.objects.get(user=users)
                opt_status = verify_otp(obj.cell_phone, otp)
                if opt_status == 'approved':
                    refresh = RefreshToken.for_user(users)
                    user_obj = User.objects.get(id=user_id)
                    serializer = UserSerializer(user_obj, many=False)
                    data = {
                        "user": serializer.data,
                        "access": str(refresh.access_token)
                    }

                    # data = {
                    #     "user_id": user.user.id,
                    #     "email": user.user.email,
                    #     "cell_phone": user.cell_phone,
                    #     "username": user.user.username,
                    #     "referral_code": user.r_code,
                    #     "login_type": user.login_type,
                    #     "user_type": user.user_type,
                    #     "access": str(refresh.access_token),
                    # }
                    return Response({"status": True,
                                     "message": "User Profile!",
                                     "data": data})
                else:
                    return Response({"status": False,
                                     "message": "Wrong Otp!"})
            else:
                return Response({"status": False,
                                 "message": "Wrong User ID!"})
        except:
            return Response({"status": False,
                             "message": "Not Found!"})


# ==================User Activation Email===================== #
@api_view(('POST', 'GET'))
@permission_classes([IsAuthenticated])
def activate(request, uidb64, token):
    try:
        uid = force_text(urlsafe_base64_decode(uidb64))
        user = User.objects.get(pk=uid)
    except:
        user = None
    if user is not None and account_activation_token.check_token(user, token):
        UserProfile.objects.filter(user=user).update(confirmed_email=True)
        return Response({"status": True,
                         "message": "Thank You successfully Confirm Your Email!"})
    else:
        return Response(
            {"status": False,
             "message": "Could Not Confirm Your Email!", })


# ==================User Toggle SS to Sp or Sp to SS===================== #

class UserToggleAPIView(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user_type = request.data.get('user_type')
            user_id = request.data.get('user_id')
            if not User.objects.filter(id=user_id).exists():
                return Response({"status": False,
                                 "message": "User ID does not exist"})
            user_exist = User.objects.get(id=user_id)
            role = UserProfile.objects.get(user=user_id).roles
            if user_exist:
                if role.role_name == "User" or role.role_name == "user":
                    if user_type == 'SP' or user_type == 'SS':
                        UserProfile.objects.filter(user=user_id).update(user_type=user_type)
                        user = UserProfile.objects.get(user=user_id)
                        data = {
                            "user_id": user.user.id,
                            "email": user.user.email,
                            "user_type": user.user_type,
                            "cell_phone": user.cell_phone,
                            "username": user.user.username,
                            "referral_code": user.r_code,
                            "login_type": user.login_type,
                        }
                        return Response({"status": True,
                                         "message": "Update User Type successfully!",
                                         "data": data})
                else:
                    return Response({"status": False,
                                     "message": "Invalid, only for Role User"})
            else:
                return Response({"status": False,
                                 "message": "User ID does not exist"})
        except:
            return Response(
                {"status": False,
                 "message": "Could Not update User Type!", })


# ==================User Login Request using Phone===================== #

class UserLoginPhoneRequest(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            cell_phone = request.data.get('cell_phone')
            if UserProfile.objects.filter(
                    cell_phone=cell_phone, user__is_active=False):
                return Response({"status": False,
                                 "message": "User can not login because user is inactive!"})
            if not cell_phone:
                return Response({"status": False,
                                 "message": "Phone Number required"})
            if not UserProfile.objects.filter(
                    cell_phone=cell_phone).exists():
                return Response({"status": False,
                                 "message": "Phone Number does not exist"})
            if len(cell_phone) < 9 or len(cell_phone) > 15:
                return Response({"status": False,
                                 "message": "Phone Number Length should be 9 to 15 "})
            if not cell_phone.startswith('+'):
                return Response({"status": False,
                                 "message": "Please enter phone number with Country code"})
            if cell_phone is not None:
                # generated_otp = str(random.randint(1000, 9999))
                send_otp(cell_phone, "Your Confirmation code is : ")
                # UserProfile.objects.filter(cell_phone=cell_phone).update(otp=generated_otp,
                #                                                          reset_code_time=datetime.datetime.now())
                user = UserProfile.objects.get(cell_phone=cell_phone)
                data = {
                    "user_id": user.user.id,
                    "username": user.user.username,
                    "cell_phone": user.cell_phone,
                    "email": user.user.email,
                    # "expire_otp_time": "3"

                }
                return Response({"status": True,
                                 "message": "OTP sent to cell phone for login!", "data": data})


            else:
                return Response({"status": False,
                                 "message": "some error"})
        except:
            return Response(
                {"status": False,
                 "message": "Could Not Login User!", "data": 'Could Not Login User'})


# ==================User Login using Email and Password===================== #

class UserLoginEmail(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            if not request.data.get('email'):
                return Response({"status": False,
                                 "message": "email required"})
            if not request.data.get('password'):
                return Response({"status": False,
                                 "message": "password required"})
            email = request.data.get('email').lower()
            password = request.data.get('password')
            if not User.objects.filter(
                    email=email).exists():
                return Response({"status": False,
                                 "message": "User does not exist"})

            if email is not None:
                user_email = User.objects.get(email=email)
                user = authenticate(username=user_email, password=password)
                if user is not None:
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    serializer = UserSerializer(user_email, many=False)
                    user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                    serialized_address = UserAddressSerializer(user_address, many=True)
                    data = {
                        'user': serializer.data,
                        'address': serialized_address.data,
                        # "user_id": user_email.id,
                        # "email": user_email.email,
                        # "refresh": str(refresh),
                        "access": str(refresh.access_token),

                    }
                    if not Referral.objects.filter(user=user).exists():
                        Referral.objects.create(user=user)
                    return Response({"status": True,
                                     "message": "User Signed in successfully!", "data": data})
                else:
                    return Response({"status": False,
                                     "message": "email or password does not match",
                                     "data": 'email or password does not match!'})
        except:
            return Response(
                {"status": False,
                 "message": "Could Not Login User!", "data": 'Could Not Login User'})


# ==================User Login using Facebook===================== #

class UserLoginFacebook(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        facebook_name = request.data.get('facebook_name')
        facebook_id = request.data.get('facebook_id')
        r_code = ""
        if request.data.get('r_code'):
            if len(request.data.get('r_code')) == 10:
                r_code = request.data.get('r_code')
                if not UserProfile.objects.filter(r_code=r_code).exists():
                    return Response({"status": False,
                                     "message": "Referenced code does not exist!"})
            else:
                return Response({"status": False,
                                 "message": "Referenced code length must be 10!"})
        if not facebook_name:
            return Response({"status": False,
                             "message": "Please Provide Facebook Name!"})
        if not facebook_id:
            return Response({"status": False,
                             "message": "Please Provide Facebook ID!"})
        if facebook_name and facebook_id:
            user_object = UserProfile.objects.filter(registration_id=facebook_id, login_type="Facebook").first()
            if user_object and User.objects.filter(username=facebook_id).exists():
                user = User.objects.get(username=facebook_id)
                login(request, user)
                refresh = RefreshToken.for_user(user)
                serializer = UserSerializer(user, many=False)
                user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                serialized_address = UserAddressSerializer(user_address, many=True)
                data = {
                    "user_register": True,
                    "user": serializer.data,
                    'address': serialized_address.data,
                    "access": str(refresh.access_token)
                }
                if not Referral.objects.filter(user=user).exists():
                    Referral.objects.create(user=user)
                # data = {
                #     "user_id": user_object.user.id,
                #     "user_name": user_object.user.first_name,
                #     "email": user_object.user.email,
                #     "login_type": user_object.login_type,
                #     "user_type": user_object.user_type,
                #     "referral_code": user_object.r_code,
                #     "access": str(refresh.access_token),
                # }
                return Response(
                    {"status": True, 'message': 'user logged in successfully! ',
                     'data': data})
            else:
                try:
                    role, created = Role.objects.get_or_create(role_name='user')
                    if created:
                        role = created
                    if User.objects.filter(username=facebook_id).exists():
                        return Response(
                            {"status": False,
                             "message": "Facebook ID already exist!"})
                    user = User.objects.create(username=facebook_id, first_name=facebook_name)
                    generated_rcode = str(random.randint(2345609800, 9923459000))
                    user_get = UserProfile.objects.filter(r_code=r_code).first()
                    if user_get:
                        user_profile = UserProfile.objects.create(user=user, registration_id=facebook_id,
                                                                  roles=role, login_type="Facebook",
                                                                  refer_user=user_get.user,
                                                                  r_code=generated_rcode, user_type='SS')
                    else:
                        user_profile = UserProfile.objects.create(user=user, registration_id=facebook_id,
                                                                  roles=role, login_type="Facebook",
                                                                  r_code=generated_rcode, user_type='SS')
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    serializer = UserSerializer(user, many=False)
                    user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                    serialized_address = UserAddressSerializer(user_address, many=True)
                    data = {
                        "user_register": False,
                        "user": serializer.data,
                        'address': serialized_address.data,
                        "access": str(refresh.access_token)
                    }
                    if not Referral.objects.filter(user=user).exists():
                        Referral.objects.create(user=user)
                    # data = {
                    #     "user_id": user_profile.user.id,
                    #     "user_name": user_profile.user.first_name,
                    #     "login_type": user_profile.login_type,
                    #     "user_type": user_profile.user_type,
                    #     "referral_code": user_profile.r_code,
                    #     "access": str(refresh.access_token),
                    # }
                    return Response(
                        {"status": True,
                         "message": "User Logged successfully!", "data": data})
                except:
                    return Response({"status": False,
                                     "message": "Could Not Login User!"})
        else:
            return Response(
                {"status": False,
                 "message": "You should give social id!"})


# ==================User Login using Google===================== #

class UserLoginGoogle(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        google_name = request.data.get('google_name')
        google_id = request.data.get('google_id')
        email = request.data.get('email')
        if not google_name:
            return Response({"status": False,
                             "message": "Please Provide Google Name!"})
        if not google_id:
            return Response({"status": False,
                             "message": "Please Provide Google ID!"})
        if not email:
            return Response({"status": False,
                             "message": "Please Provide Email!"})


        profile_image = ""
        if request.data.get('profile_image'):
            profile_image = request.data.get('profile_image')
        r_code = ""
        if request.data.get('r_code'):
            if len(request.data.get('r_code')) == 10:
                r_code = request.data.get('r_code')
                if not UserProfile.objects.filter(r_code=r_code).exists():
                    return Response({"status": False,
                                     "message": "Referenced code does not exist!"})
            else:
                return Response({"status": False,
                                 "message": "Referenced code length must be 10!"})
        if google_name and google_id and email:
            if User.objects.filter(username=google_id).exists():
                get_email = User.objects.get(username=google_id)
                if not get_email.email == email:
                    return Response(
                        {"status": False, 'message': 'User Register with different email'})
            user_object = UserProfile.objects.filter(registration_id=google_id, login_type="Google").first()
            if user_object and User.objects.filter(username=google_id, email=email).exists():
                user = User.objects.get(username=google_id)
                login(request, user)
                refresh = RefreshToken.for_user(user)
                serializer = UserSerializer(user, many=False)
                user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                serialized_address = UserAddressSerializer(user_address, many=True)
                data = {
                    "user_register": True,
                    "user": serializer.data,
                    'address': serialized_address.data,
                    "access": str(refresh.access_token)
                }
                if not Referral.objects.filter(user=user).exists():
                    Referral.objects.create(user=user)

                # data = {
                #     "user_id": user_object.user.id,
                #     "first_name": user_object.user.first_name,
                #     "email": user_object.user.email,
                #     "login_type": user_object.login_type,
                #     "user_type": user_object.user_type,
                #     "referral_code": user_object.r_code,
                #     "access": str(refresh.access_token)
                # }
                return Response(
                    {"status": True, 'message': 'User logged in successfully!',
                     'data': data})
            else:
                try:
                    role, created = Role.objects.get_or_create(role_name='user')
                    if created:
                        role = created
                    if User.objects.filter(username=google_id).exists():
                        return Response(
                            {"status": True,
                             "message": "Google ID already exist!"})
                    if User.objects.filter(email=email).exists():
                        return Response({"status": False,
                                         "message": "User Email already exists!"})
                    user = User.objects.create(username=google_id, first_name=google_name, email=email)
                    generated_rcode = str(random.randint(2345609800, 9923459000))
                    user_get = UserProfile.objects.filter(r_code=r_code).first()
                    if user_get:
                        user_profile = UserProfile.objects.create(user=user, registration_id=google_id,
                                                                  roles=role, login_type="Google",
                                                                  refer_user=user_get.user,
                                                                  profile_image=profile_image,
                                                                  r_code=generated_rcode, user_type='SS')
                    else:
                        user_profile = UserProfile.objects.create(user=user, registration_id=google_id,
                                                                  roles=role, login_type="Google",
                                                                  profile_image=profile_image,
                                                                  r_code=generated_rcode, user_type='SS')
                    login(request, user)
                    refresh = RefreshToken.for_user(user)
                    serializer = UserSerializer(user, many=False)
                    user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                    serialized_address = UserAddressSerializer(user_address, many=True)
                    data = {
                        "user_register": False,
                        "user": serializer.data,
                        'address': serialized_address.data,
                        "access": str(refresh.access_token)
                    }
                    data1 = {'username': request.user.first_name}
                    send_email_template(template_name='email_templates/singup.html',
                                        subject_msg="congratulations on successfully signup",
                                        email=user.email,
                                        data=data1)
                    if not Referral.objects.filter(user=user).exists():
                        Referral.objects.create(user=user)
                    # data = {
                    #     "user_id": user_profile.user.id,
                    #     "user_name": user_profile.user.first_name,
                    #     "login_type": user_profile.login_type,
                    #     "user_type": user_profile.user_type,
                    #     "referral_code": user_profile.r_code,
                    #     "access": str(refresh.access_token)
                    # }
                    return Response(
                        {"status": True,
                         "message": "User Logged in successfully!", "data": data})
                except:
                    return Response({"status": False,
                                     "message": "There's some error!"})
        else:
            return Response(
                {"status": False,
                 "message": "You should give Google id!"})


# ==================User Login using Phone OTP===================== #

class UserLoginPhone(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            otp = request.data.get('otp')
            if not user_id:
                return Response({"status": False,
                                 "message": "user id required"})
            if not otp:
                return Response({"status": False,
                                 "message": "otp required"})
            # if not UserProfile.objects.filter(
            #         otp=otp).exists():
            #     return Response({"status": False,
            #                      "message": "otp does not exist"})

            if not User.objects.filter(id=user_id).exists():
                return Response({"status": False,
                                 "message": "user id does not exist"})
            # otp_time = get_otp_time(user_id)
            # if not otp_time:
            #     return Response({"status": False,
            #                      "message": "otp time expire please generate new one"})
            # if User.objects.filter(id=user_id).exists() and UserProfile.objects.filter(otp=otp):

            if User.objects.filter(id=user_id).exists():
                user = User.objects.get(id=user_id)
                obj = UserProfile.objects.get(user=user)
                opt_status = verify_otp(obj.cell_phone, otp)
                if opt_status == 'approved':

                    if user is not None:
                        login(request, user)
                        refresh = RefreshToken.for_user(user)
                        serializer = UserSerializer(user, many=False)
                        user_address = UserAddresses.objects.filter(user_id=serializer.data['id']).order_by('-id')
                        serialized_address = UserAddressSerializer(user_address, many=True)
                        data = {
                            'user': serializer.data,
                            'address': serialized_address.data,
                            # "user_id": user.id,
                            # "first_name": user.first_name,
                            # "last_name": user.last_name,
                            # "email": user.email,
                            # "refresh": str(refresh),
                            "access": str(refresh.access_token),

                        }
                        if not Referral.objects.filter(user=user).exists():
                            Referral.objects.create(user=user)
                        return Response({"status": True,
                                         "message": "User Signed in successfully!", "data": data})

                else:
                    return Response({"status": False,
                                     "message": "Wrong Otp!",
                                     "data": "none"})

            else:
                return Response({"status": False,
                                 "message": "user id does not exist",
                                 "data": "none"})
        except:
            return Response(
                {"status": False,
                 "message": "Could Not Login User!", "data": "none"})


# ================  Soft Delete User =============== #

class SoftDeleteUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            softdel_user = User.objects.filter(id=user_id).update(is_active=False)
            if softdel_user:
                return Response({"status": True, "message": "User Deleted Successfully!"})
            else:
                return Response({"status": False, "message": "User ID does not exist"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})

# ================  Resotre User from Soft Delete =============== #


class RestoreUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            softdel_user = User.objects.filter(id=user_id).update(is_active=True)
            if softdel_user:
                return Response({"status": True, "message": "User Restore Successfully!"})
            else:
                return Response({"status": False, "message": "User ID does not exist"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})

# ==================User Logout===================== #

class UserLogoutAPI(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        refresh_token = request.data.get('refresh_token')
        token = RefreshToken(refresh_token)
        token.blacklist()
        logout(request)
        return Response({"status": True, "message": "User Log out!", "data": 'User Log out'})


# ==================User Forgot Password===================== #
class USERForgotPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            email = request.data.get('email')
            cell_phone = request.data.get('cell_phone')

            if (email and cell_phone) or email:
                if not '@' in email:
                    return Response({"status": False,
                                     "message": "incorrect email"})
                if User.objects.filter(email=email).exists():
                    with transaction.atomic():
                        user = User.objects.get(email=email)
                        generated_otp = str(random.randint(1000, 9999))
                        hyperlink_format = '<a href="{link}">{text}</a>'
                        link_text = functools.partial(hyperlink_format.format)
                        url = link_text(link='http://18.216.236.249/account/user_reset_password/ ', text='here')
                        email_from = 'noreply@gmail.com'
                        message_body = "Please click {} to update your password".format(url)
                        email = EmailMessage("Password Change Request",
                                             message_body, email_from, [email])
                        email.content_subtype = 'html'
                        email.send()
                        UserProfile.objects.filter(user=user).update(reset_pass=True, reset_code=generated_otp,
                                                                     otp=generated_otp,
                                                                     reset_code_time=datetime.datetime.now())
                        return Response({"status": True,
                                         "message": "Email sent successfully!", "data": "Email sent successfully"})
                else:
                    return Response({"status": False,
                                     "message": "Email Does not Exist!"})
            elif cell_phone:
                if len(cell_phone) < 9 or len(cell_phone) > 15:
                    return Response({"status": False,
                                     "message": "Phone Number Length should be 9 to 15 "})
                if not cell_phone.startswith('+'):
                    return Response({"status": False,
                                     "message": "Please enter phone number with Country code"})
                if UserProfile.objects.filter(cell_phone=cell_phone).exists():
                    with transaction.atomic():
                        # generated_otp = str(random.randint(1000, 9999))
                        send_otp(cell_phone, "Your Confirmation code is : ")
                        # UserProfile.objects.filter(cell_phone=cell_phone).update(reset_pass=True,
                        #                                                          reset_code=generated_otp,
                        #                                                          otp=generated_otp)
                        user = UserProfile.objects.get(cell_phone=cell_phone)
                        data = {
                            "user_id": user.user.id,
                            "username": user.user.username,
                            "cell_phone": user.cell_phone,
                            "email": user.user.email,
                            "expire_otp_time": "3"

                        }
                        return Response({"status": True,
                                         "message": "OTP Code sent successfully!",
                                         "data": data})
                else:
                    return Response({"status": False,
                                     "message": "Cell Phone Does not Exist!"})
        except:
            return Response({"status": False, "message": "Something Went Wrong!"})


# ==================User Reset Password===================== #

class USERResetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        try:
            user_id = request.data.get('user_id')
            new_password = request.data.get('new_password')
            if new_password and UserProfile.objects.filter(user=user_id).exists():
                with transaction.atomic():
                    user = UserProfile.objects.get(user=user_id)
                    if user.user.check_password(request.data.get('new_password')):
                        return Response({"status": False, "message": "You cannot use an old password"})
                    pwd = make_password(new_password)
                    User.objects.filter(email=user.user.email).update(password=pwd)
                    user.reset_pass = False
                    user.reset_code = " "
                    user.save()
                    return Response({"status": True,
                                     "message": "Password Changed Successfully!"})
            else:
                return Response({"status": False,
                                 "message": "Please enter new password and reset code!"})
        except:
            return Response({"status": False,
                             "message": "Could not change password!"})


# ==================All User===================== #

class AllUser(APIView):
    permission_classes = (IsAuthenticated,)

    def get(self, request):
        try:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            all_records = UserProfile.objects.all()
            result_page = paginator.paginate_queryset(all_records, request)
            serializer = UserProfileSerializer(result_page, many=True)
            return paginator.get_paginated_response(serializer.data)
        except:
            return Response({"status": False,
                             "message": "Please Login, First!"})


class UserTypes(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            user_type = request.data.get('user_type')
            if user_type == 'SP':
                all_records = UserProfile.objects.all().filter(user_type=user_type)
                paginator = PageNumberPagination()
                paginator.page_size = 5
                result_page = paginator.paginate_queryset(all_records, request)
                serializer = UserProfileSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)
            elif user_type == 'SS':
                all_records = UserProfile.objects.all().filter(user_type=user_type)
                paginator = PageNumberPagination()
                paginator.page_size = 5
                result_page = paginator.paginate_queryset(all_records, request)
                serializer = UserProfileSerializer(result_page, many=True)
                return paginator.get_paginated_response(serializer.data)
            else:
                return Response({"status": False,
                                 "message": "Invalid, User Type should be SP or SS"})

        except:
            return Response({"status": False,
                             "message": "Please Login First!"})


class adminLogin(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.data.get('email'):
            if not email_validator(request.data.get('email')):
                return Response({"status": False, "Response": "Invalid email"})
            if request.data.get('password'):
                email = request.data.get('email')
                password = request.data.get('password')
                user_check = User.objects.filter(email=email).exists()
                if user_check:
                    user_email = User.objects.get(email=email)
                    user = authenticate(username=user_email, password=password)
                    if user:
                        if UserProfile.objects.get(user=user).roles.role_name != "User" and user.is_superuser:
                            if user.is_active:
                                login(request, user)
                                refresh = RefreshToken.for_user(user)
                                user_list = User.objects.get(id=user.id)
                                serializer = UserSerializer(user_list, many=False)
                                role = Role.objects.get(id=serializer.data['profile']['roles'])
                                data = {
                                    "access": str(refresh.access_token),
                                    "role": role.role_name,
                                    "user": serializer.data,
                                    # "refresh": str(refresh),
                                    # "access": str(refresh.access_token),
                                    # "permissions": user_email.user_permissions.all().values_list('name', flat=True)
                                }
                                data["user"]["permissions"] = user_email.user_permissions.all().values_list('name',
                                                                                                            flat=True)
                                return Response(
                                    {"status": True, "Response": "Logged In Successfully", "data": data})
                            else:
                                return Response(
                                    {"status": False, "Response": "Your account is not active"})
                        else:
                            return Response(
                                {"status": False, "Response": "Only admin can login."})
                    else:
                        return Response(
                            {"status": False, "Response": "Password is Incorrect"})
                else:
                    return Response({"status": False, "Response": "Email Doesn't Exists"})

            else:
                return Response({"status": False, "Response": "Please enter password"})
        else:
            return Response({"status": False, "Response": "Please enter email"})


class AdminUserLogout(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        logout(request)
        return Response({"status": True, "Response": "Logged out Successfully"})


class AdminForgetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        cell_phone = request.data.get('cell_phone')
        request_for = request.data.get('request_for')

        if request.data.get('email'):
            email_validation = email_validator(request.data.get('email'))
            if email_validation:
                email = User.objects.filter(email=request.data.get('email')).exists()
                users = User.objects.filter(email=request.data.get('email')).first()
                if email:
                    # refresh = RefreshToken.for_user(users)
                    hyperlink_format = '<a href="{link}">{text}</a>'
                    link_text = functools.partial(hyperlink_format.format)
                    if request_for:
                        if request_for == 'staging':
                            reset_link = 'https://staging.dyi5w05ftgp4q.amplifyapp.com/auth/reset/' + urlsafe_base64_encode(
                                force_bytes(users.pk)) + '/' + PasswordResetTokenGenerator().make_token(
                                users) + '/'
                            url = link_text(link=reset_link, text='here')
                            admin_send_email(url, users)
                        elif request_for == 'master':
                            reset_link = 'https://master.dwezdsatdorjo.amplifyapp.com/auth/reset/' + urlsafe_base64_encode(
                                force_bytes(users.pk)) + '/' + PasswordResetTokenGenerator().make_token(
                                users) + '/'
                            url = link_text(link=reset_link, text='here')
                            admin_send_email(url, users)
                    else:
                        return Response({"status": False, "Response": "request_for is required",
                                         "message": "request_for is required"})

                    return Response({"status": True, "Response": "Password reset URL has been sent to your Email",
                                     "message": "Password reset URL has been sent to your Email"})

                else:
                    return Response(
                        {"status": False, "Response": "Email Does not exists", "message": "Email Does not exists"})
            else:
                return Response(
                    {"status": False, "Response": "Please enter valid email", "message": "Please enter valid email"})
        elif cell_phone:
            if len(cell_phone) < 9 or len(cell_phone) > 15:
                return Response({"status": False,
                                 "message": "Phone Number Length should be 9 to 15 "})
            if not cell_phone.startswith('+'):
                return Response({"status": False,
                                 "message": "Please enter phone number with Country code"})
            if UserProfile.objects.filter(cell_phone=cell_phone).exists():
                with transaction.atomic():
                    # generated_otp = str(random.randint(1000, 9999))
                    send_otp(cell_phone, "Your Confirmation code is : ")
                    # UserProfile.objects.filter(cell_phone=cell_phone).update(reset_pass=True,
                    #                                                          reset_code=generated_otp,
                    #                                                          otp=generated_otp)
                    user = UserProfile.objects.get(cell_phone=cell_phone)
                    data = {
                        "user_id": user.user.id,
                        "username": user.user.username,
                        "cell_phone": user.cell_phone,
                        "email": user.user.email,
                        "expire_otp_time": "3"

                    }
                    return Response({"status": True,
                                     "message": "OTP Code sent successfully!",
                                     "data": data})
            else:
                return Response({"status": False,
                                 "message": "Cell Phone Does not Exist!"})
        else:
            return Response({"status": False, "Response": "Please enter your email or phone",
                             "message": "Please enter your email or phone"})


class AdminResetPassword(APIView):
    permission_classes = (AllowAny,)

    def post(self, request, uidb64, token):

        try:
            uid = force_text(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid)
        except():
            user = None

        if user is not None and PasswordResetTokenGenerator().check_token(user, token):

            if request.data.get('new_password'):
                password = request.data.get('new_password')

                if not user:
                    return Response({"status": False, "Response": "Email does not exist"})
                # elif not PasswordResetTokenGenerator().check_token(user, token):
                #     return Response({"status": False, "Response": "Invalid Token"})
                elif user.check_password(request.data.get('new_password')):
                    return Response({"status": False, "Response": "You cannot use an old password"})
                elif request.data.get('confirm_password') != request.data.get('new_password'):
                    return Response({"status": False, "Response": "Passwords are not same"})

                else:
                    pass_res = password_check(password)
                    if pass_res == "Password updated successfully!":
                        user.set_password(str(request.data.get('confirm_password')))
                        user.save()
                        return Response(
                            {"status": True, "Response": pass_res})
                    else:
                        return Response(
                            {"status": True, "Response": pass_res})
            else:
                return Response({"status": False, "Response": "Please enter new_Password"})
        else:
            return Response({"status": False, "Response": "Link has been expired"})
    ############# Current Admin Profile #####################


class AdminProfile(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request):
        user = request.user
        serializer = UserSerializer(user)
        return Response({"status": True, "user": serializer.data})

    # Create your views here.


class GETAllUser(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            all_records = UserProfile.objects.filter(roles__role_name="User")
            result_page = paginator.paginate_queryset(all_records, request)
            serializer = UserProfileSerializer(result_page, many=True)
            return Response({"userdata": request.user.email})
        except:
            return Response({"status": False,
                             "message": "Please Login First!"})


# class ResendOtp(APIView):
#     permission_classes = (IsAuthenticated,)
#
#     def post(self, request):
#         try:
#             paginator = PageNumberPagination()
#             paginator.page_size = 10
#             all_records = UserProfile.objects.filter(roles__role_name="User")
#             result_page = paginator.paginate_queryset(all_records, request)
#             serializer = UserProfileSerializer(result_page, many=True)
#             return Response({"userdata": request.user.email})
#         except:
#             return Response({"status": False,
#                              "message": "Please Login First!"})

class Adress(APIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id')
        longitude = request.data.get('longitude')
        latitude = request.data.get('latitude')
        address_ = request.data.get('address')
        geolocator = Nominatim(user_agent="user")
        if not user_id:
            return Response({"status": False,
                             "message": "Please Provide User ID!"})
        if not longitude:
            return Response({"status": False,
                             "message": "Please Provide longitude!"})
        if not latitude:
            return Response({"status": False,
                             "message": "Please Provide latitude!"})
        if longitude and latitude:
            address_ln = longitude + "," + latitude

            location = geolocator.reverse(address_ln)
            print(location.address)
            return Response({"status": False,
                             "message": "return address", "data": location.address})
        if address_:
            address = geolocator.geocode(address_)
            print(address.latitude, address.longitude)
            return Response({"status": False,
                             "message": "return address",
                             "data": {"latitude": address.latitude, "longitutde": address.longitude}})
        return Response({"status": False,
                         "message": "enter correct data!"})


# User Profile Update

class SeekerProfile(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id')
        user_profile = User.objects.filter(id=user_id).annotate(rating=Avg('rated_to_in_rating__star')).values(
            'email', 'rating', active_status=F('is_active'), profile_image=F('profile__profile_image'),
            level=F('profile__level'), name=F('first_name'), cell_phone=F('profile__cell_phone'),
            country=F('profile__country'), state=F('profile__state'), postal_code=F('profile__postal_code'))
        return Response({"status": True, "data": user_profile})


class EditSeekerProfile(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SeekerSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def put(self, request, *args, **kwargs):
        try:
            with transaction.atomic():
                email = request.data.get('email')
                first_name = request.data.get('username')
                country = request.data.get('country')
                state = request.data.get('state')
                postal_code = request.data.get('postal_code')
                profile_image = ''
                # cell_phone = ''
                if request.data.get('profile_image'):
                    profile_image = request.data.get('profile_image')
                user = self.get_object()
                # if request.data.get('cell_phone'):
                #     cell_phone = request.data.get('cell_phone')
                #     if UserProfile.objects.exclude(user=user).filter(cell_phone=cell_phone):
                #         return Response({"status": False, "message": "User with that cell_phone already exists."})
                #     if not cell_phone.startswith("+"):
                #         return Response({"status": False, "message": "Phone Number must starts with +."})
                #     elif len(cell_phone) < 9 or len(cell_phone) > 15:
                #         return Response({"status": False,
                #                          "message": "Length of Phone number should not be less than 9 or greater than 15."})
                if User.objects.exclude(pk=user.id).filter(email=email.lower()).exists():
                    return Response({"status": False, "message": "User with that email already exists."})
                email_validation = email_validator(request.data.get('email'))
                if not email_validation:
                    return Response({"status": False, "message": "Please Enter a valid email."})
                if User.objects.exclude(pk=user.id).filter(username=first_name.lower()).exists():
                    return Response({"status": False, "message": "Username already taken."})
                user.email = email.lower()
                user.first_name = first_name
                user.username = first_name
                user.save()
                profile = UserProfile.objects.get(user=user)
                profile.country = country
                profile.state = state
                profile.postal_code = postal_code
                # if cell_phone:
                #     profile.cell_phone = cell_phone
                if profile_image:
                    profile.profile_image = profile_image
                profile.save()
                serializer = UserSerializer(user)
                return Response({"status": True, "message": "Profile has been updated successfully.",
                                 "data": serializer.data})
        except Exception as e:
            error = {"status": False, "message": "Please enter required data"}
            return Response(error)

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        data = []
        user_data = User.objects.filter(id=user.id).\
            values('email', 'password', user_name=F('first_name'),
                   cell_phone=F('profile__cell_phone'),
                   profile_image=F('profile__profile_image'),
                   country=F('profile__country'),
                   postal_code=F('profile__postal_code'),
                   state=F('profile__state')).first()
        user_rating = User.objects.filter(id=user.id). \
            annotate(rating=Avg('rated_to_in_rating__star')).values('rating').first()
        if user_rating['rating']:
            rating = round(user_rating['rating'], 1)
            user_data.update({"rating": rating})
        else:
            user_data.update({"rating": 0})
        data.append(user_data)
        return Response({"status": True, "data": data})

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        password = user.password
        current_password = request.data.get('current_password')
        new_password = request.data.get('new_password')
        confirm_password = request.data.get('confirm_password')
        if password == current_password or user.check_password(current_password):
            if user.check_password(new_password):
                return Response({"status": False, "Response": "You cannot use old password."})
            if confirm_password != new_password:
                return Response({"status": False, "Response": "Passwords are not same."})
            else:
                pass_res = password_check(new_password)
                if pass_res == "Password updated successfully!":
                    user.set_password(str(new_password))
                    user.save()
                    return Response({"status": True, "message": pass_res})
                else:
                    return Response({"status": False, "message": pass_res})
        else:
            return Response({"status": False, "message": "Current password is not correct."})


class SearchUser(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):

        try:
            string_value = self.request.query_params.get('search')
            user_id = Spservices.objects.all().values_list('s_user__id').distinct()
            user = User.objects.filter(Q(is_superuser=False), Q(first_name__icontains=string_value) |
                                       Q(email__icontains=string_value) | Q(last_name__icontains=string_value) |
                                       Q(profile__reference_id__icontains=string_value)).\
                order_by('-id'). \
                annotate(
                type=Case(
                    When(id__in=user_id, then=Value('SS/ SP', output_field=CharField())),
                    default=Value('SS', output_field=CharField()),
                ),
            ). \
                    annotate(bookings=Count('booking_ss_id__order_status',
                                                        filter=Q(booking_ss_id__order_status='Active') |
                                                        Q(booking_ss_id__order_status='Completed'))). \
                annotate(as_float=Cast('recevier_in_mlnTokensEarn__token', FloatField())). \
                annotate(earning=Sum('as_float')). \
                values('id', 'first_name', 'last_name', 'email', 'type', 'earning', 'bookings', status=F('is_active'),
                       reference_id=F('profile__reference_id'), level=F('profile__level'))
            sp = pagination(user, request)
            return Response({"status": True, "data": sp.data})
        except:
            return Response(
                {"status": False, "Response": "Please enter the search value."})


class Addresses(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = UserAddresses.objects.all()
    serializer_class = UserAddressSerializer

    def post(self, request, *args, **kwargs):
        serializer = UserAddressSerializer(data=request.data, context={'user': request.user})
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({'status': True, 'message': 'successfully created', 'data': serializer.data})
        except Exception as e:
            if 'error' in e.args[-1]:
                return Response({'status': False, 'message': e.args[-1].get('error')[0]})
            else:
                return Response({'status': False, 'message': 'please enter correct post data'})

    def list(self, request, *args, **kwargs):
        user_address = UserAddresses.objects.filter(user=request.user).order_by('-id')
        serializer = UserAddressSerializer(user_address, many=True)
        return Response({'status': True, 'message': "list of addresses", 'data': serializer.data})


class UpdateAddresses(generics.RetrieveUpdateDestroyAPIView):

    permission_classes = (IsAuthenticated,)
    queryset = UserAddresses.objects.all()
    serializer_class = UserAddressSerializer

    def put(self, request, *args, **kwargs):
        try:
            serializer = self.partial_update(request)
            return Response({'status': True, 'message': 'Updated successfully', 'data': serializer.data})
        except Exception as e:
            if 'error' in e.args[-1]:
                return Response({'status': False, 'message': e.args[-1].get('error')[0]})
            else:
                return Response({'status': False, 'message': 'false request sent'})

    def retrieve(self, request, *args, **kwargs):
        data = self.get_object()
        serializer = UserAddressSerializer(data)
        return Response({'status': True, "message": "object get successfully", 'data': serializer.data})

    def delete(self, request, *args, **kwargs):
        self.destroy(request)
        return Response({'status': True, "message": "object deleted successfully"})


class UpdateUserPhoneNo(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SeekerSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def put(self, request, *args, **kwargs):
        user = self.get_object()
        cell_phone = request.data.get('cell_phone')
        otp = request.data.get('otp')
        if cell_phone:
            if UserProfile.objects.exclude(user=user).filter(cell_phone=cell_phone):
                return Response({"status": False, "message": "User with that cell_phone already exists."})
            if not cell_phone.startswith("+"):
                return Response({"status": False, "message": "Phone Number must starts with +."})
            elif len(cell_phone) < 9 or len(cell_phone) > 15:
                return Response({"status": False,
                                 "message": "Length of Phone number should not be less than 9 or greater than 15."})
        else:
            return Response({"status": False, "message": "Please enter the phone number."})
        if otp:
            with transaction.atomic():
                try:
                    opt_status = verify_otp(cell_phone, otp)
                    if opt_status == 'approved':
                        profile = UserProfile.objects.get(user=user)
                        profile.cell_phone = cell_phone
                        profile.save()
                        serializer = UserSerializer(user)
                        return Response({"status": True, "message": "Your Phone number has been updated.",
                                         "data": serializer.data})
                    else:
                        return Response({"status": False,
                                         "message": "Wrong Otp!",
                                         "data": "none"})
                except:
                    return Response({"status": False, "message": "Phone number is not updated."})
        else:
            send_otp(cell_phone, "Your Confirmation code is : ")
            return Response({"status": True,
                             "message": "Enter the sent OTP to update your phone number!"})






