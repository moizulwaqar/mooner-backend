# Create your views here.
import json

import requests
from django.core.exceptions import ObjectDoesNotExist
from django.db.models.functions import Cast
from rest_framework import generics
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from django.db.models import Count, Q, Sum, BooleanField, Value, When, Case, F, FloatField
from django.shortcuts import render

# Create your views here.
from rest_framework import generics
from rest_framework.decorators import permission_classes
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.views import APIView

from category_kyc.models import CategorySpecificKyc
from category_kyc.serializers import CategorySpecificSerializer
from mooner_backend.settings import BLOCK_CHAIN_BASE_URL
from payments.crypto_integrations import call_wallet_api
from payments.models import CreateWallet, MLNTokenPandingHistory
from payments.utils import load_usd
from .models import SpItems
from booking.serializers import BidsSerializer, SpServiceSerializer
from category_management.serializers import CategoriesSerializer, QuestionsSerializer
from .serializers import *


class get_sp_services(APIView):
    # permission_classes = (AllowAny,)

    def post(self, request):
        if request.POST:
            if request.POST['tn_parent']:
                try:
                    parent_obj = Category.objects.get(pk=request.POST['tn_parent'])
                    cat_children = parent_obj.get_children()

                    data = CategoriesSerializer(cat_children, many=True)
                    return Response({"status": True, "data": data.data})
                except ObjectDoesNotExist as e:
                    return Response({"status": False, "message": "object does not exists"})
            else:
                cat_parent = Category.objects.filter(tn_parent=None).order_by('id')
                data = CategoriesSerializer(cat_parent, many=True)
                return Response({"status": True, "data": data.data})

        return Response({"status": True, "message": "enter parent id "})


class sp_category_questions(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        # if request.POST:
        #     if request.POST.get('sub_category', False):
        #         try:
        #             business_questions = CategoryQuestions.objects.filter(
        #                 sub_category=request.POST['sub_category'], question_for="business").order_by('id')
        #             serializer = QuestionsSerializer(business_questions, many=True)
        #             category_questions = CategoryQuestions.objects.filter(
        #                 sub_category=request.POST['sub_category'], question_for="provider").order_by('id')
        #             quest_serializer = QuestionsSerializer(category_questions, many=True)
        #             return Response({"status": True, "data": {"business_questions": serializer.data,
        #                                                       "sp_questions": quest_serializer.data}})
        #         except ObjectDoesNotExist as e:
        #             return Response({"status": False, "message": "Questions does not exists related to this category "})
        #     elif request.POST['sub_category_child']:
        #         business_questions = CategoryQuestions.objects.filter(
        #             sub_category_child=request.POST['sub_category_child'], question_for="business").order_by('id')
        #         serializer = QuestionsSerializer(business_questions, many=True)
        #         category_questions = CategoryQuestions.objects.filter(
        #             sub_category_child=request.POST['sub_category_child'], question_for="provider").order_by('id')
        #         quest_serializer = QuestionsSerializer(category_questions, many=True)
        #         return Response({"status": True, "data": {"business_questions": serializer.data,
        #                                                   "sp_questions": quest_serializer.data}})
        #
        #     else:
        #         cat_questions = CategoryQuestions.objects.filter(sub_category=None).order_by('id')
        #         data = QuestionsSerializer(cat_questions, many=True)
        #         return Response({"status": True, "data": data.data})
        #
        # return Response({"status": True, "message": "enter category id"})
        if request.POST:
            parent_category = request.data.get('parent_category')
            sub_category = request.data.get('sub_category')
            sub_category_child = request.data.get('sub_category_child')
            try:
                if parent_category and not sub_category and not sub_category_child:
                    try:
                        kyc_serializer = CategorySpecificSerializer(CategorySpecificKyc.objects.filter(
                            category=parent_category, sub_category=None, sub_category_child=None), many=True)
                        business_questions = CategoryQuestions.objects.filter(
                            parent_category=parent_category, sub_category=None, sub_category_child=None,
                            question_for="business").order_by(
                            'id')
                        serializer = QuestionsSerializer(business_questions, many=True)
                        category_questions = CategoryQuestions.objects.filter(
                            parent_category=parent_category, sub_category=None, sub_category_child=None,
                            question_for="provider").order_by(
                            'id')
                        quest_serializer = QuestionsSerializer(category_questions, many=True)
                        return Response({"status": True, "data": {"business_questions": serializer.data,
                                                                  "sp_questions": quest_serializer.data,
                                                                  "category_kyc_questions": kyc_serializer.data}})
                    except:
                        return Response(
                            {"status": False, "message": "category does not exist.".format(parent_category)})
                if parent_category and sub_category and not sub_category_child:
                    try:
                        kyc_serializer = CategorySpecificSerializer(CategorySpecificKyc.objects.filter(
                            category=parent_category, sub_category=sub_category, sub_category_child=None),
                            many=True)
                        business_questions = CategoryQuestions.objects.filter(
                            parent_category=parent_category, sub_category=sub_category, sub_category_child=None,
                            question_for="business").order_by(
                            'id')
                        serializer = QuestionsSerializer(business_questions, many=True)
                        category_questions = CategoryQuestions.objects.filter(
                            parent_category=parent_category, sub_category=sub_category, sub_category_child=None,
                            question_for="provider")\
                            .order_by(
                            'id')
                        quest_serializer = QuestionsSerializer(category_questions, many=True)
                        return Response({"status": True, "data": {"business_questions": serializer.data,
                                                                  "sp_questions": quest_serializer.data,
                                                                  "category_kyc_questions": kyc_serializer.data}})
                    except:
                        return Response(
                            {"status": False, "message": "category does not exist.".format(parent_category)})
                if parent_category and sub_category and sub_category_child:
                    try:
                        kyc_serializer = CategorySpecificSerializer(CategorySpecificKyc.objects.filter(
                            category=parent_category, sub_category=sub_category, sub_category_child=sub_category_child),
                            many=True)
                        business_questions = CategoryQuestions.objects.filter(
                            parent_category=parent_category, sub_category=sub_category,
                            sub_category_child=sub_category_child,
                            question_for="business").order_by(
                            'id')
                        serializer = QuestionsSerializer(business_questions, many=True)
                        category_questions = CategoryQuestions.objects.filter(
                            parent_category=parent_category, sub_category=sub_category,
                            sub_category_child=sub_category_child,
                            question_for="provider").order_by(
                            'id')
                        quest_serializer = QuestionsSerializer(category_questions, many=True)
                        return Response({"status": True, "data": {"business_questions": serializer.data,
                                                                  "sp_questions": quest_serializer.data,
                                                                  "category_kyc_questions": kyc_serializer.data}})
                    except:
                        return Response(
                            {"status": False, "message": "category does not exist.".format(parent_category)})
            except ObjectDoesNotExist as e:
                return Response({"status": False, "message": "Questions does not exists related to this category"})

        return Response({"status": True, "message": "enter category id"})


class sp_dashboard(APIView):
    # permission_classes = (AllowAny,)
    def post(self, request):
        try:
            # data = Bids.objects.annotate(active_bids=Count('sp')).filter(sp=request.user)
            total_earnings = ''
            user_data = Booking.objects.filter(sp=request.user, order_status='Active')
            active_jobs = user_data.count()
            bids = Bids.objects.filter(sp=request.user, job__job_cat_child__is_deleted=False, status='Active')
            # bids = Bids.objects.filter(sp=request.user, status='Active')
            wallet = CreateWallet.objects.filter(user=request.user)

            if wallet.exists():
                earning = call_wallet_api('get_balance', public_key=wallet.first().wallet_public_key)
                mnr_bal = earning['MNR']['balance']
                if float(mnr_bal) > 0:
                    usd_bal = usd_to_mnr(mnr_bal)
                    if usd_bal:
                        total_earnings = str(round(usd_bal, 2))
                    else:
                        total_earnings = 0
                else:
                    total_earnings = 0
            else:
                user_token = MLNTokenPandingHistory.objects.filter(user=request.user
                                                                   ).annotate(as_float=Cast('token', FloatField())
                                                                              ).aggregate(Sum('as_float'))
                if user_token.get('as_float__sum'):
                    if user_token.get('as_float__sum') > 0:
                        bal = user_token.get('as_float__sum')
                        total_earnings = str(round(bal, 2))
                    else:
                        total_earnings = 0
                else:
                    total_earnings = 0
            active_bids = BidsSerializer(bids, many=True)

            # active_services = Spservices.objects.filter(s_user=request.user)
            active_services = Category.objects.filter(scat_parent__s_user=request.user).annotate(
                registered=Case(When(scat_parent__s_user=request.user, then=Value(True)), default=Value(False),
                                output_field=BooleanField())).distinct().\
                values('id', 'registered', 'name', 'cat_icon', 'category_image', 'behaviour',
                       is_active=F('scat_parent__is_active'), in_active_by=F('scat_parent__in_active_by'),
                       service_id=F('scat_parent__id'))

            # registered_categories = Spservices.objects.filter(s_user=request.user).values_list('s_cat_parent__id')
            registered_categories = Spservices.objects.filter(s_user=request.user, s_cat_parent__is_deleted=False)\
                .values_list('s_cat_parent__id')
            get_bid = Bids.objects.filter(sp=request.user).values_list('job__id')
            posted_jobs = Jobs.objects.filter(job_cat_child__in=registered_categories, job_status='Active')\
                                      .exclude(Q(ssid=request.user) | Q(id__in=get_bid)).order_by('-id').values(
                          'id', 'budget', 'schedule', category_name=F('job_cat_child__name'),
                          category_image=F('job_cat_child__category_image'))

            # total_earnings = user_data.annotate(total_earning=Sum("job__booking_job_id__price"))

            return Response({"status": True, "message": "SP Dashboard Data", "data": {"active_jobs": active_jobs,
                                                                                      "total_earnings": total_earnings,
                                                                                      "active_bids": active_bids.data,
                                                                                      "posted_jobs": posted_jobs,
                                                                                      "active_services": active_services}})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "object does not exists"})
        except Exception as e:
            return Response({"status": False, "message": e.args[-1]})


class SPCategories(generics.ListCreateAPIView):
    queryset = Category.objects.filter(tn_parent=None).order_by('id')
    serializer_class = CategoriesSerializer

    # permission_classes = (AllowAny,)

    def list(self, request):
        query_params = self.request.query_params['sub_category_id']
        if query_params:

            queryset = Category.objects.filter(tn_parent=query_params, scat_parent__s_user=request.user).annotate(
                registered=Case(When(Q(scat_parent__s_user=request.user), then=Value(True)),
                                default=Value(False),
                                output_field=BooleanField())).values('id', 'registered', 'name', 'cat_icon',
                                                                     'category_image', 'behaviour').union\
                (Category.objects.filter(tn_parent=query_params).exclude(scat_parent__s_user=request.user).annotate(
                    registered=Case(When(Q(scat_parent__s_user=request.user), then=Value(True)),
                                    default=Value(False),
                                    output_field=BooleanField())).values('id', 'registered', 'name', 'cat_icon',
                                                                         'category_image', 'behaviour'))

        else:
            queryset = Category.objects.filter(tn_parent=None).annotate(
                registered=Case(When(scat_parent__s_user=request.user, then=Value(True)), default=Value(False),
                                output_field=BooleanField())).distinct().values('id', 'registered', 'name', 'cat_icon',
                                                                                'category_image', 'behaviour')

        return Response({"success": True, "data": queryset})


def usd_to_mnr(token):
    url = "{}MNRtoUSD".format(BLOCK_CHAIN_BASE_URL)
    token = float(token)
    payload = {'tokenAmount': token}
    json_data = json.dumps(payload)
    headers = {
        'Content-Type': 'application/json'
    }
    response = requests.request("POST", url, headers=headers, data=json_data)
    print(response.text)
    api_data = json.loads(response.text)
    if api_data:
        balance = api_data.get('data').get('USD').get('balance')
        return balance
    else:
        return False