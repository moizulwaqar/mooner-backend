from django.contrib.auth.models import Permission
from rest_framework.response import Response
from django.db.models import Q, F, Value, Count, When, Case, CharField, Sum
from django.db.models.functions import Concat, Coalesce
from rest_framework.decorators import api_view, permission_classes
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from booking.models import Booking
from booking.serializers import *
from mooner_backend.utils import email_validator, pagination
from payments.crypto_integrations import call_wallet_api
from payments.models import CreateWallet
from user.serializers import *
from geopy.geocoders import Nominatim
from django.db.models import FloatField
from django.db.models.functions import Cast

# Create your views here.


class AdminRegisterUser(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):
        if not request.data.get('email') or not request.data.get('username') or not request.data.get(
                'password') or not request.data.get('cell_phone'):
            return Response(
                {"status": False, "Response": "Email, Username, Phone Number and Password are Required."})
        else:
            email = User.objects.filter(email=request.data.get('email')).exists()
            username = User.objects.filter(username=request.data.get('username')).exists()
            cell_phone = UserProfile.objects.filter(cell_phone=request.data.get('cell_phone')).exists()
            email_validation = email_validator(request.data.get('email'))
            if not email_validation:
                return Response({"status": False, "Response": "Please Enter a valid email."})
            elif email:
                return Response({"status": False, "Response": "This email is already registered."})
            elif username:
                return Response({"status": False, "Response": "Username Already exists."})
            elif len(request.data.get('password')) < 8:
                return Response({"status": False, "Response": "Password must have atleast 8 characters."})
            elif not request.data.get('cell_phone').startswith("+"):
                return Response({"status": False, "Response": "Phone must starts with '+'."})
            elif len(request.data.get('cell_phone')) < 9 or len(request.data.get('cell_phone')) > 15:
                return Response({"status": False,
                                 "Response": "Length of Phone number should not be less than 9 or greater than 15."})
            elif cell_phone:
                return Response({"status": False, "Response": "Phone number Already exists."})
            else:
                first_name = ""
                last_name = ""
                profile_image = ""
                if request.data.get('first_name'):
                    first_name = request.data.get('first_name')
                if request.data.get('last_name'):
                    last_name = request.data.get('last_name')
                if request.data.get('roles'):
                    roles = Role.objects.create(role_name=request.data.get('roles'))
                else:
                    roles = Role.objects.create(role_name='User')
                if request.data.get('profile_image'):
                    profile_image = request.data.get('profile_image')
                if request.data.get('permissions'):
                    permissions = request.data.getlist('permissions')
                    permissions_obj = Permission.objects.filter(name__in=permissions).values_list('id', flat=True)
                else:
                    permissions_obj = None
                user = User.objects.create(username=request.data.get('username'),
                                           email=request.data.get('email'),
                                           first_name=first_name,
                                           last_name=last_name)
                user.set_password(str(request.data.get('password')))
                if roles.role_name == "Super_Admin":
                    user.is_superuser = True
                    user.is_staff = True
                    user.save()
                elif roles.role_name == "User":
                    user.is_staff = False
                    user.is_superuser = False
                    user.save()
                else:
                    user.is_staff = True
                    user.save()
                profile = UserProfile.objects.create(
                    user=user,
                    roles=roles,
                    profile_image=profile_image,
                    cell_phone=request.data.get('cell_phone'),
                    country=request.data.get('country'),
                    state=request.data.get('state'),
                    postal_code=request.data.get('postal_code'),
                    registration_id=request.data.get('registration_id'),
                    user_type=request.data.get('user_type'),

                )
                if permissions_obj:
                    user.user_permissions.set(permissions_obj)
                user.save()
                return Response({"status": True, "Response": "User has been registered."})


class AdminUserList(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request):
        paginator = PageNumberPagination()
        paginator.page_size = 10

        users = User.objects.filter(is_superuser=False).order_by('-id')
        data_list = []
        sp_id = Spservices.objects.all().values_list('s_user__id').distinct()
        for user in users:
            end_user = User.objects.filter(is_superuser=False, id=user.id) \
                .annotate(
                type=Case(
                    When(id__in=sp_id, then=Value('SS/ SP', output_field=CharField())),
                    default=Value('SS', output_field=CharField()),
                ),
            ) \
                .annotate(
                bookings=Count(
                    'booking_ss_id__order_status',
                    filter=Q(booking_ss_id__order_status='Active') | Q(booking_ss_id__order_status='Completed')
                )
            ). \
                values('id', 'first_name', 'last_name', 'email', 'type', 'bookings', status=F('is_active'),
                       reference_id=F('profile__reference_id'), level=F('profile__level')).first()
            if CreateWallet.objects.filter(user=end_user['id']).exists():
                user_wallet = CreateWallet.objects.get(user=end_user['id'])
                earning = call_wallet_api('get_balance', public_key=user_wallet.wallet_public_key)
                end_user.update({"earning": float(earning['MNR']['balance'])})
                data_list.append(end_user)
            else:
                ss_user = User.objects.filter(id=end_user['id']). \
                    annotate(as_float=Cast('sender_in_mlnTokenPandingHistory__token', FloatField())). \
                    annotate(earning=Coalesce(Sum('as_float'), 0)). \
                    values('id', 'earning').first()
                end_user.update({"earning": float(ss_user['earning'])})
                data_list.append(end_user)
        users_list = pagination(data_list, request)
        return Response({"status": True, "data": users_list.data})


class AdminUserListNoPagination(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request):
        user = User.objects.filter(is_superuser=False).order_by('-id')
        data = []
        for user_id in user:
            booking_count = Booking.objects.filter(Q(ss=user_id.id) | Q(sp=user_id.id)).count()
            serializer = UserSerializer(user_id)
            booking_data = {'Total_number_of_bookings': booking_count, 'user': serializer.data}
            data.append(booking_data)
        return Response({"status": True, "data": data})


class AdminUserDetail(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, id):
        try:
            user_list = User.objects.get(id=id,is_active=True)
            serializer = UserSerializer(user_list, many=False)
            role = Role.objects.get(id=serializer.data['profile']['roles'])
            data = {
                "user": serializer.data,
                "user-role": role.role_name
            }
            return Response({"status": True, "data": data})
        except:
            return Response({"status": False, "message": "User does not Exist"})

    def put(self, request, id):
        try:
            instance = UserProfile.objects.get(user=id)
            instance_user = User.objects.get(id=id)

            first_name = ""
            last_name = ""
            profile_image = ""

            if request.data.get('first_name'):
                first_name = request.data.get('first_name')
            if request.data.get('last_name'):
                last_name = request.data.get('last_name')
            if request.data.get('email'):
                email_validation = email_validator(request.data.get('email'))
                if email_validation:
                    email = User.objects.filter(email=request.data.get('email')).exists()
                    if email:
                        return Response({"status": False, "Response": "This email is already registered."})
                    else:
                        instance_user.email = request.data.get('email')
                else:
                    return Response({"status": False, "Response": "Please Enter a valid email."})
            if request.data.get('username'):
                username = User.objects.filter(username=request.data.get('username')).exists()
                if username:
                    return Response({"status": False, "Response": "Username Already exists."})
                else:
                    instance_user.username = request.data.get('username')
            if request.data.get('cell_phone'):
                cell_phone = UserProfile.objects.filter(cell_phone=request.data.get('cell_phone')).exists()
                if not request.data.get('cell_phone').startswith("+"):
                    return Response({"status": False, "Response": "Phone Number must starts with '+'."})
                elif len(request.data.get('cell_phone')) < 9 or len(request.data.get('cell_phone')) > 15:
                    return Response({"status": False,
                                     "Response": "Length of Phone number should not be less than 9 or greater than 15."})
                elif cell_phone:
                    return Response({"status": False, "Response": "Phone number Already exists."})

                else:
                    instance.cell_phone = request.data.get('cell_phone')

            if request.data.get('role'):
                instance_role = Role.objects.get(id=instance.roles.id)
                if instance_role:
                    Role.objects.filter(id=instance.roles.id).update(role_name=request.data.get('roles'))

            if request.data.get('profile_image'):
                profile_image = request.data.get('profile_image')
            if instance:
                instance.profile_image = profile_image
                instance.profile_image = request.data.get('profile_image')
                instance.cell_phone = request.data.get('cell_phone')
                instance.country = request.data.get('country')
                instance.state = request.data.get('state')
                instance.postal_code = request.data.get('postal_code')
                instance.user_type = request.data.get('user_type')
                instance.registration_id = request.data.get('registration_id')
                instance.save()
                if instance_user:
                    if request.data.get('first_name'):
                        instance_user.first_name = first_name
                    if request.data.get('last_name'):
                        instance_user.last_name = last_name
                    instance_user.save()
                return Response(
                    {"status": True, "message": "User Profile Updated Successfully"})
            else:
                return Response(
                    {"status": False, "message": "User Profile is not Updated."})
        except:
            return Response(
                {"status": False, "message": "User Profile is not Updated."})

    def delete(self, request, id):
        user = User.objects.get(id=id)
        user.delete()
        return Response({"status": True, "Response": "User has been deleted."})


class AdminSPlist(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request):
        try:
            sp_profile = User.objects.filter(profile__user_type='SP',is_active=True)
            if sp_profile:
                serializer = UserSerializer(sp_profile, many=True)
                return Response(serializer.data)
            else:
                return Response({"status": False, "Response": "There is no SP available"})
        except:
            return Response({"status": False, "message": "User does not Exist"})


class AdminSPDetails(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, id):
        try:
            user_id = User.objects.get(id=id,is_active=True)
            if user_id.profile.user_type == 'SP':
                serializer = UserSerializer(user_id, many=False)

                data = {
                    "sp-user": serializer.data,
                }
                return Response({"status": True, "data": data})
            else:
                return Response({"status": False, "message": "SP is not available."})
        except:
            return Response({"status": False, "message": "User does not Exist."})

    def put(self, request, id):
        try:
            instance = UserProfile.objects.get(user=id)
            instance_user = User.objects.get(id=id)

            first_name = ""
            last_name = ""
            if request.data.get('first_name'):
                first_name = request.data.get('first_name')
            if request.data.get('last_name'):
                last_name = request.data.get('last_name')

            if request.data.get('email'):
                email_validation = email_validator(request.data.get('email'))
                if email_validation:
                    email = User.objects.filter(email=request.data.get('email')).exists()
                    if email:
                        return Response({"status": False, "Response": "This email is already registered."})
                    else:
                        instance_user.email = request.data.get('email')
                else:
                    return Response({"status": False, "Response": "Please Enter a valid email."})
            if request.data.get('username'):
                username = User.objects.filter(username=request.data.get('username')).exists()
                if username:
                    return Response({"status": False, "Response": "Username Already exists."})
                else:
                    instance_user.username = request.data.get('username')
            if request.data.get('cell_phone'):
                cell_phone = UserProfile.objects.filter(cell_phone=request.data.get('cell_phone')).exists()
                if not request.data.get('cell_phone').startswith("+"):
                    return Response({"status": False, "Response": "Phone Number must starts with '+'."})
                elif len(request.data.get('cell_phone')) < 9 or len(request.data.get('cell_phone')) > 15:
                    return Response({"status": False,
                                     "Response": "Length of Phone number should not be less than 9 or greater than 15."})
                elif cell_phone:
                    return Response({"status": False, "Response": "Phone number Already exists."})
                else:
                    instance.cell_phone = request.data.get('cell_phone')

            if request.data.get('role'):
                instance_role = Role.objects.get(id=instance.roles.id)
                if instance_role:
                    Role.objects.filter(id=instance.roles.id).update(role_name=request.data.get('roles'))
            profile_image = ""
            if request.data.get('profile_image'):
                profile_image = request.data.get('profile_image')

            if instance:
                instance.profile_image = profile_image
                instance.cell_phone = request.data.get('cell_phone')
                instance.country = request.data.get('country')
                instance.state = request.data.get('state')
                instance.postal_code = request.data.get('postal_code')
                if request.data.get('user_type'):
                    instance.user_type = request.data.get('user_type')
                instance.registration_id = request.data.get('registration_id')
                instance.save()
                if instance_user:
                    if request.data.get('first_name'):
                        instance_user.first_name = first_name
                    if request.data.get('last_name'):
                        instance_user.last_name = last_name
                    instance_user.save()
                return Response(
                    {"status": True, "message": "User Profile Updated Successfully"})
            else:
                return Response(
                    {"status": False, "message": "User Profile is not Updated."})
        except:
            return Response(
                {"status": False, "message": "User Profile is not Updated."})

    def delete(self, request, id):
        user = User.objects.get(id=id)
        user.delete()
        return Response({"status": True, "Response": "User has been deleted."})


class AdminUserEnable(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):

        if not request.data.get('status') and not request.data.get('user_id'):
            return Response({"status": False, "Response": "Please Enter User Status and User ID"})
        if request.data.get('status'):
            if request.data.get('user_id'):
                try:
                    sta = request.data.get('status')
                    user_id = request.data.get('user_id')
                    user = User.objects.get(id=user_id)
                    if sta == 1 or sta == "1":
                        user.is_active = True
                        user.save()
                        return Response({"status": True, "message": "User Status Change"})
                    else:
                        user.is_active = False
                        user.save()
                        return Response({"status": True, "message": "User Status Change"})
                except:
                    return Response({"status": False, "Response": "User does not exists"})
            else:
                return Response({"status": False, "Response": "Please Enter the User ID"})
        else:
            return Response({"status": False, "Response": "Please Enter the User Status"})


class AdminFilterUser(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def post(self, request):

        try:
            column_name = request.data.get('column_name')
            string_value = request.data.get('string_value')
            profile = ''
            if column_name == 'cell_phone' or column_name == 'r_code':
                profile = 'profile__'
            filters = {
                profile + column_name + '__icontains': string_value
            }
            user = User.objects.filter(**filters)
            data = []
            for user_id in user:
                booking_count = Booking.objects.filter(Q(ss=user_id.id) | Q(sp=user_id.id)).count()
                serializer = UserSerializer(user_id)
                booking_data = {'Total_number_of_bookings': booking_count, 'user': serializer.data}
                data.append(booking_data)
            return Response({"status": True, "Response": "Searched by" + " " + column_name, "data": data})

        except:
            return Response(
                {"status": False, "Response": "You can search by column_name: username, email, first_name, last_name"})


class AdminTotalUserCount(APIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request):
        users = User.objects.values('profile__profile_image').exclude(is_superuser=True)
        total_users = users.count()
        users_images = users.annotate(text=Concat(Value('/media/'), F('profile__profile_image'))).exclude(
            profile__profile_image='')
        top_three_users_images = users_images.order_by('-id')[:3]
        data = {
            "total_users": total_users,
            "top_three_users_images": top_three_users_images
        }
        return Response({"status": True, "data": data})


@api_view(('GET',))
@permission_classes([AllowAny])
def delete_user(request, id):
    if User.objects.filter(id=id).exists():
        user = User.objects.get(id=id)
        user.delete()
        return Response({"status": True, "Message": "User successfully deleted"})
    else:
        return Response({"status": False, "Message": "User does not exist!"})


# =================  Adress ======================================
class Adress(APIView):
    # permission_classes = (IsAuthenticated,)

    def post(self, request):
        user_id = request.data.get('user_id')
        latitude = request.data.get('latitude')
        longitude = request.data.get('longitude')

        address_ = request.data.get('address_string')
        geolocator = Nominatim(user_agent="user_management")
        # if not user_id:
        #     return Response({"status": False,
        #                      "message": "Please Provide User ID!"})
        # if not longitude:
        #     return Response({"status": False,
        #                      "message": "Please Provide longitude!"})
        # if not latitude:
        #     return Response({"status": False,
        #                      "message": "Please Provide latitude!"})
        if longitude and latitude:
            address_ln = latitude + "," + longitude

            location = geolocator.reverse(address_ln)
            print(location.address)
            return Response({"status": True,
                             "message": "Location updated successfully",
                             "data": {"latitude": latitude, "longitude": longitude, "address": location.address}})
        if address_:
            address = geolocator.geocode(address_)
            print(address.latitude, address.longitude)
            return Response({"status": True,
                             "message": "Location updated successfully",
                             "data": {"latitude": address.latitude, "longitude": address.longitude,
                                      "address": address_}})
        return Response({"status": False,
                         "message": "Location not found!"})
