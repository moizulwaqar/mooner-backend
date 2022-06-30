import uuid

from django.db.models.functions import Cast
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from ast import literal_eval
from django.contrib.auth.models import User
from mln.models import Referral, LevelsPercentage, TokenHistory
from django.db.models import F, Sum, FloatField
from mooner_backend.utils import pagination
from payments.crypto_integrations import call_wallet_api
from payments.models import CreateWallet
from user.models import UserProfile
from user.serializers import UserSerializer
from .serializers import LevelsPercentageSerializer, TokenHistorySerializer
from .utils import sp_user_levels, referral_soft_delete, restore_referral_from_softdelete, referral_permanent_delete
from django.core.exceptions import ObjectDoesNotExist


class ListMLNUsers(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        # if CreateWallet.objects.filter(user=request.user).exists():
        #     user_wallet = CreateWallet.objects.get(user=request.user)
        #     earning = call_wallet_api(key='get_balance', public_key=user_wallet.wallet_public_key)
        result = User.objects.all().order_by('-id'). \
            annotate(as_float=Cast('recevier_in_mlnTokensEarn__token', FloatField())). \
            annotate(profit=Sum('as_float')) \
            .values('id', 'email', 'profit', referrals=F('user_in_referral__tn_children_count'),
                    name=F('first_name'))

        users = pagination(result, request)
        return Response({"status": True, "data": users.data})


class ListReferralUsers(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = UserSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def get(self, request, *args, **kwargs):

        try:
            user = self.get_object()
            user_details = User.objects.filter(id=user.id).order_by('-id').annotate(
                as_float=Cast('recevier_in_mlnTokensEarn__token', FloatField())). \
            annotate(profit=Sum('as_float')) \
                .values('id', 'first_name', 'email', 'profit', referrals=F('user_in_referral__tn_children_count'
                                                                                  ))
            user_obj = Referral.objects.filter(user_id=user.id)
            if user_obj.exists():
                user_obj = Referral.objects.get(user_id=user.id)
                children = user_obj.tn_children_pks
                if not children:
                    return Response({"status": True, "user_details": user_details, "referral_users":
                                    "No referrals available"})
                children_in_int = literal_eval(children)
                if type(children_in_int) == int:
                    referral_users = Referral.objects.filter(id=children).annotate(
                        as_float=Cast('user_id__recevier_in_mlnTokensEarn__token', FloatField())). \
                         annotate(profit=Sum('as_float')) \
                         .values(
                        'profit', uid=F('user__id'), first_name=F('user__first_name'), email=F('user__email')
                    ).order_by('-id')[:5]
                    return Response({"status": True, "user_details": user_details, "referral_users": referral_users})

                referral_users = Referral.objects.filter(id__in=children_in_int).annotate(
                    as_float=Cast('user_id__recevier_in_mlnTokensEarn__token', FloatField())). \
                    annotate(profit=Sum('as_float')) \
                    .values(
                    'profit', uid=F('user__id'), first_name=F('user__first_name'),
                    email=F('user__email')).order_by('-id')[:5]

                return Response({"status": True, "user_details": user_details, "referral_users": referral_users})
            else:
                return Response({"status": True, "user_details": user_details, "referral_users":
                                "No referrals available"})

        except:
            return Response({"status": False, "message": "User does not exists"})


class ListReferralUsersPagination(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = UserSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            user_obj = Referral.objects.get(user_id=user.id)
            children = user_obj.tn_children_pks
            children_in_int = literal_eval(children)

            if type(children_in_int) == int:
                referral_users = Referral.objects.filter(id=children_in_int).order_by('-user__id') \
                    .annotate(
                    as_float=Cast('user_id__recevier_in_mlnTokensEarn__token', FloatField())). \
                    annotate(profit=Sum('as_float')) \
                    .values(
                    'profit', uid=F('user__id'), first_name=F('user__first_name'),
                    email=F('user__email')).order_by('-id')

                users = pagination(referral_users, request)
                return Response({"status": True, "referral_users": users.data})

            referral_users = Referral.objects.filter(id__in=children_in_int).order_by('-user__id') \
                .annotate(
                as_float=Cast('user_id__recevier_in_mlnTokensEarn__token', FloatField())). \
                annotate(profit=Sum('as_float')) \
                .values(
                'profit', uid=F('user__id'), first_name=F('user__first_name'),
                email=F('user__email')).order_by('-id')

            users = pagination(referral_users, request)
            return Response({"status": True, "referral_users": users.data})
        except:
            return Response({"status": False, "message": "User does not exists"})


class LevelMarginProfit(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = LevelsPercentageSerializer

    def get_queryset(self):
        level = LevelsPercentage.objects.filter(id=self.kwargs['pk']).all()
        return level

    def put(self, request, *args, **kwargs):
        try:
            self.update(request)
            return Response({"status": True, "message": "Profit margin has been updated"})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class EditUserDetails(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = UserSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            data = User.objects.filter(id=user.id)\
                .annotate(
                as_float=Cast('recevier_in_mlnTokensEarn__token', FloatField())). \
                annotate(profit=Sum('as_float')) \
                .values('id', 'email', 'profit', name=F('first_name'),
                        referrals_count=F('user_in_referral__tn_children_count'))

            return Response({"status": True, "data": data})
        except:
            return Response({"status": False, "message": "User does not exists"})


class EditReferralUserDetails(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = UserSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def get(self, request, *args, **kwargs):
        try:
            user = self.get_object()
            data = User.objects.filter(id=user.id) \
                .annotate(
                as_float=Cast('recevier_in_mlnTokensEarn__token', FloatField())). \
                annotate(profit=Sum('as_float'))
            data_values = data.values('id', 'email', 'profit', name=F('first_name'))
            referral = Referral.objects.get(user=user)
            parent = Referral.objects.get(id=referral.tn_parent_id)
            data_list = []
            for x in data_values:
                x.update({"parent_id": parent.user_id})
                data_list.append(x)

            return Response({"status": True, "data": data_list})
        except:
            return Response({"status": False, "message": "User does not exists"})


class GetReferenceId(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = UserSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        reference_id = user.profile.reference_id
        if not reference_id:
            user.profile.reference_id = uuid.uuid4()
            user.profile.save()
            reference_id = user.profile.reference_id
            return Response({"status": True, "data": reference_id})
        return Response({"status": True, "data": reference_id})


class ReferUsers(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        amount = int(request.data.get('amount'))
        sp_amount = int(request.data.get('sp_amount'))
        company = int(request.data.get('company'))
        convenience_fee = int(request.data.get('convenience_fee'))
        sp_id = request.data.get('sp_id')
        ss_id = request.data.get('ss_id')
        admin_id = request.data.get('admin_id')
        value = LevelsPercentage.objects.get(id=1)
        level_0 = float(value.level_0)
        level_1 = float(value.level_1)
        level_2 = float(value.level_2)
        level_3 = float(value.level_3)
        level_4 = float(value.level_4)
        data = sp_user_levels(sp_id=sp_id, ss_id=ss_id, admin_id=admin_id, amount=amount, sp_amount=sp_amount,
                              company=company, convenience_fee=convenience_fee, level_0=level_0, level_1=level_1,
                              level_2=level_2, level_3=level_3, level_4=level_4)
        if not data:
            return Response({"status": False, "message": "User id does not exists"})

        return Response({"status": True,  "admin_users": data[2], "ss_users": data[1], "sp_users": data[0]})


class UserTokenHistory(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = TokenHistorySerializer

    def post(self, request, *args, **kwargs):

        serializer = TokenHistorySerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"status": True, "message": "Token history created successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)

    def get(self, request, *args, **kwargs):

        total_tokens = TokenHistory.objects.filter(earned_by=request.user).\
                        aggregate(total_earned_tokens=Sum('earn_tokens'))
        data = TokenHistory.objects.filter(earned_by=request.user).values('earn_tokens',
                                                                          username=F('earned_from__first_name'),
                                                                          profile_image=F
                                                                          ('earned_from__profile__profile_image'))
        return Response({"status": True, "user_tokens": total_tokens, "users": data})


class SoftDeleteReferrals(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            user_id = request.data.get('user_id')
            obj = Referral.objects.get(user_id=user_id)
            referral = referral_soft_delete(id=obj.id, msg='Referral')
            return referral
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class RestoreReferrals(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            user_id = request.data.get('user_id')
            obj = Referral.all_objects.get(user_id=user_id)
            referral_restore = restore_referral_from_softdelete(id=obj.id, msg='Referral')
            return referral_restore
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class HardDeleteReferrals(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        try:
            user_id = request.data.get('user_id')
            if user_id:
                obj = Referral.all_objects.get(user_id=user_id)
                referral_restore = referral_permanent_delete(id=obj.id, msg='Referral')
                return referral_restore
            else:
                return Response({"status": False, "message": "Please Enter Category ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})
