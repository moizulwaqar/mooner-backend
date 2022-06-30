from django.db.models.functions import Cast, Coalesce
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser

from document_management.models import KycAnswer
from payments.crypto_integrations import call_wallet_api
from payments.models import CreateWallet
from .serializers import *
from rest_framework.response import Response
from django.db.models import F, Count, Q, Sum, FloatField
from mooner_backend.utils import pagination


class SPlist(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):
        # user_id = Spservices.objects.all().values_list('s_user__id').distinct()
        users = Spservices.objects.values('s_user').distinct().order_by('-s_user')
        data_list = []
        for user in users:
            sp_list = User.objects.filter(id=user['s_user']) \
                .annotate(
                bookings=Count('booking_sp_id__order_status', filter=Q(booking_sp_id__order_status='Active') | Q
                (booking_sp_id__order_status='Completed'))) \
                .values('id', 'email', 'bookings', 'first_name',
                        status=F('is_active'), reference_id=F('profile__reference_id'),
                        level=F('profile__level')).first()
            if CreateWallet.objects.filter(user_id=sp_list['id']).exists():
                user_wallet = CreateWallet.objects.get(user_id=sp_list['id'])
                earning = call_wallet_api('get_balance', public_key=user_wallet.wallet_public_key)
                sp_list.update({"earning": float(earning['MNR']['balance'])})
                data_list.append(sp_list)
            else:
                sp_list_data = User.objects.filter(id=user['s_user'])\
                    .annotate(as_float=Cast('sender_in_mlnTokenPandingHistory__token', FloatField())). \
                    annotate(earning=Coalesce(Sum('as_float'), 0)) \
                    .values('id', 'earning',).first()
                sp_list.update({"earning": float(sp_list_data['earning'])})
                data_list.append(sp_list)
        users_list = pagination(data_list, request)
        return Response({"status": True, "data": users_list.data})


class EditSP(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def put(self, request, *args, **kwargs):

        status = request.data.get('status')
        user = self.get_object()
        if status == 'Active':
            user.is_active = True
            user.profile.user_status = status
            user.save()
            user.profile.save()
            return Response({"status": True, "message": "Status changed successfully"})
        elif status == 'Inactive':
            user.is_active = False
            user.profile.user_status = status
            user.save()
            user.profile.save()
            return Response({"status": True, "message": "Status changed successfully"})
        else:
            return Response({"status": True, "message": "Please enter correct status"})


class EditSPProfile(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def put(self, request, *args, **kwargs):
        try:
            self.update(request)
            return Response({"status": True, "message": "Profile Updated Successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class SpManagementView(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def get(self, request, *args, **kwargs):
        sp = self.get_object()
        sp_detail = []
        if CreateWallet.objects.filter(user=sp).exists():
            user_wallet = CreateWallet.objects.get(user=sp)
            earning = call_wallet_api('get_balance', public_key=user_wallet.wallet_public_key)
            sp_detail_data = User.objects.filter(id=sp.id). \
                values('username', 'email', 'first_name', 'last_name',
                       cell_phone=F('profile__cell_phone'), reference_id=F
                ('profile__reference_id'), level=F('profile__level'),
                       status=F('is_active')).first()
            sp_detail_data.update({"earning": float(earning['MNR']['balance'])})
            sp_detail.append(sp_detail_data)
        else:
            sp_detail_data = User.objects.filter(id=sp.id). \
                annotate(as_float=Cast('sender_in_mlnTokenPandingHistory__token', FloatField())). \
                annotate(earning=Coalesce(Sum('as_float'), 0)). \
                values('username', 'email', 'first_name', 'last_name', 'earning',
                       cell_phone=F('profile__cell_phone'), reference_id=F
                ('profile__reference_id'), level=F('profile__level'),
                       status=F('is_active')).first()
            sp_detail.append(sp_detail_data)

        sp_active_bookings = Booking.objects.filter(sp=sp, order_status='Active', sp__is_active=True).values(
            'id', 'start_date', 'budget', 'order_status', seeker_name=F('ss__first_name'), category_name=
            F('category__name')).order_by('-id')[:2]

        sp_complete_bookings = Booking.objects.filter(sp=sp, order_status='Completed', sp__is_active=True).values(
            'id', 'start_date', 'budget', 'order_status', seeker_name=F('ss__first_name'),
            category_name=F('category__name')).order_by('-id')[:2]

        sp_ratings = Rating.objects.filter(rated_to=sp, rated_to__is_active=True).values(
            'id', 'star', seeker_name=F('rated_by__first_name'), category=F('booking__cat_child_id__name'),
            seeker_id=F('rated_by__id')).order_by('-id')[:2]

        sp_documents = KycAnswer.objects.filter(user=sp, status='Approve').order_by('-id').values(
            'id', 'answer', 'status', label=F('document__doc_label'), category_name=F('document__parent_category__name')
            , user_name=F('user__first_name'), documentid=F('document__id'), document_for=F('document__doc_for'),
            doc_question_type=F('document__doc_question_type'), expiration_date=F(
                                                                                    'document__expiration_date'))[:2]

        return Response({"status": True, "sp_detail": sp_detail, "sp_active_bookings": sp_active_bookings,
                         "sp_complete_bookings": sp_complete_bookings, "sp_ratings": sp_ratings,
                         "sp_kyc": sp_documents})


class SpActiveBookings(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def get(self, request, *args, **kwargs):
        sp = self.get_object()
        sp_active_bookings_records = Booking.objects.filter(sp=sp, order_status='Active').values(
            'id', 'start_date', 'budget', 'order_status', seeker_name=F('ss__first_name'), category_name=F(
                'category__name'))
        sp_active_bookings = pagination(sp_active_bookings_records, request)
        return Response({"status": True, "sp_active_bookings": sp_active_bookings.data})


class SpCompletedBookings(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def get(self, request, *args, **kwargs):
        sp = self.get_object()
        sp_complete_bookings_records = Booking.objects.filter(sp=sp, order_status='Completed').values(
            'id', 'start_date', 'budget', 'order_status', seeker_name=F('ss__first_name'), category_name=F(
                'category__name'))

        sp_complete_bookings = pagination(sp_complete_bookings_records, request)

        return Response({"status": True, "sp_active_bookings": sp_complete_bookings.data})


class SpRatings(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def get(self, request, *args, **kwargs):
        sp = self.get_object()
        sp_ratings_records = Rating.objects.filter(rated_to=sp).values('id', 'star',
                                                                       seeker_name=F('rated_by__first_name'),
                                                                       category=F('booking__cat_child_id__name'),
                                                                       seeker_id=F('rated_by__id'))
        sp_ratings = pagination(sp_ratings_records, request)

        return Response({"status": True, "sp_active_bookings": sp_ratings.data})


class SpSearch(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        if self.request.query_params.get('search'):
            string_value = self.request.query_params.get('search')
            user_id = Spservices.objects.all().values_list('s_user__id').distinct()
            user = User.objects.filter(Q(id__in=user_id), Q(first_name__icontains=string_value) |
                                       Q(email__icontains=string_value) | Q(last_name__icontains=string_value) |
                                       Q(profile__reference_id__icontains=string_value)).order_by('-id').annotate(
                                        bookings=Count('booking_sp_id__order_status',
                                                       filter=Q(booking_sp_id__order_status='Active') |
                                                       Q(booking_sp_id__order_status='Completed'))).values(
                                                       'id', 'email', 'bookings', 'first_name', 'last_name',
                                                       status=F('is_active'), reference_id=F('profile__reference_id'),
                                                       level=F('profile__level'), earning=F('profile__earning'))
            sp = pagination(user, request)
            return Response({"status": True, "data": sp.data})
        else:
            return Response(
                {"status": False, "Response": "Please enter the search value."})


class SPKYCUploads(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = SPSerializer

    def list(self, request, *args, **kwargs):
        sp = self.get_object()
        result = KycAnswer.objects.filter(user=sp, status='Approve').order_by('-id').values('id', 'answer', 'status',
                                                                          label=F('document__doc_label'),
                                                                          category_name=
                                                                          F('document__parent_category__name'),
                                                                          user_name=F('user__first_name'),
                                                                          documentid=F('document__id'),
                                                                          document_for=F('document__doc_for'),
                                                                          doc_question_type=F(
                                                                                       'document__doc_question_type'),
                                                                          expiration_date=F(
                                                                                       'document__expiration_date'))

        document = pagination(result, request)
        return Response({"status": True, "data": document.data})