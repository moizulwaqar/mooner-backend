import os
from ast import literal_eval

from django.db.models import F, Value, Q, Count, FloatField, Sum
from django.db.models.functions import Concat, Cast, Coalesce
from rest_framework.views import APIView

from payments.crypto_integrations import call_wallet_api
from payments.models import CreateWallet
from .serializers import *
from rest_framework import generics, status
from rest_framework.permissions import AllowAny
from rest_framework.decorators import permission_classes
from rest_framework.authentication import SessionAuthentication
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.core.exceptions import ObjectDoesNotExist
from rest_framework.pagination import PageNumberPagination
from mooner_backend.utils import soft_delete, restore_from_softdelete, pagination, permanent_delete
from booking.models import Spservices
from service_provider.models import SpItems


# Create your views here.


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


# @permission_classes([IsAuthenticated])
class Categories(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    # authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    # permission_classes = (IsAuthenticated,)
    queryset = Category.objects.filter(tn_parent=None, is_deleted=False).order_by('-id')
    # queryset = Category.objects.all()
    serializer_class = CategoriesSerializer

    def list(self, request):

        queryset = self.get_queryset()
        serializer = CategoriesSerializer(queryset, many=True)
        return Response({"status": True, "data": serializer.data})

    def post(self, request, *args, **kwargs):
        if request.data.get('tn_parent'):
            check_category = Category.objects.filter(name=request.data.get('name'),
                                                     tn_parent=request.data.get('tn_parent'))

            try:
                parent_category = Category.objects.get(id=request.data.get('tn_parent'))
                if parent_category.tn_level == 3:
                    return Response({"status": False, "message": "Cannot create category greater than level 3"})
                if request.data.get('name').lower() == parent_category.name.lower():
                    return Response({"status": False, "message": "Child name should be different from parent name"})
            except:
                return Response({"status": False, "message": "tn_parent does not exists"})
            if check_category.exists():
                return Response({"status": False, "message": "Category is already registered"})
        else:
            check_category = Category.objects.filter(name=request.data.get('name'), tn_parent=None, is_deleted=False)
            if check_category.exists():
                return Response({"status": False, "message": "Category is already registered"})
        cat_obj = self.create(request, *args, **kwargs)
        obj = Category.objects.get(pk=cat_obj.data['id'])
        if request.FILES:
            if request.FILES['cat_icon']:
                obj.cat_icon = request.FILES['cat_icon']
                try:
                    obj.save()
                except:
                    pass
            if request.FILES['category_image']:
                obj.category_image = request.FILES['category_image']
                try:
                    obj.save()
                except:
                    pass
            object_ = Category.objects.filter(pk=obj.id)
            data = CategoriesSerializer(object_, many=True)
            return Response({"status": True, "data": data.data})
        if request.POST:
            object_ = Category.objects.filter(pk=obj.id)
            data = CategoriesSerializer(object_, many=True)
            return Response({"status": True, "data": data.data})

        return Response({"status": False, "message": "please enter data", "data": ""})


# @permission_classes([IsAuthenticated])
class UpdateCategories(generics.RetrieveUpdateAPIView):
    # authentication_classes = (CsrfExemptSessionAuthentication, BasicAuthentication, TokenAuthentication)
    permission_classes = (AllowAny,)
    queryset = Category.objects.filter(is_deleted=False).order_by('id')
    serializer_class = CategoriesSerializer

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        # category = Category.objects.filter(id=obj.id, is_deleted=False).annotate(icon_url=Concat(Value("/media/"), F("cat_icon")))\
        #     .annotate(image_url=Concat(Value("/media/"), F("category_image")))\
        #     .values('id', 'name', 'category_heading_text', 'category_heading_text2', 'tn_parent',
        #             'behaviour', category_icon=F('icon_url'), cat_image=F('image_url'))

        category = Category.objects.filter(id=obj.id, is_deleted=False).annotate(
            icon_url=Concat(Value(os.getenv('MOONER_MEDIA_BUCKET_URL')), F("cat_icon"))) \
            .annotate(image_url=F("category_image")) \
            .values('id', 'name', 'category_heading_text', 'category_heading_text2', 'tn_parent',
                    'behaviour', category_icon=F('icon_url'), cat_image=
                                       Concat(Value(os.getenv('MOONER_MEDIA_BUCKET_URL')),
                                                    F('image_url')))
        return Response({"status": True, "data": category})

    def put(self, request, pk, *args, **kwargs):
        self.update(request, *args, **kwargs)
        if request.POST:
            try:
                obj = Category.objects.get(pk=pk)
                if request.POST.get('name'):
                    obj.name = request.POST['name']
                if request.FILES.get('cat_icon'):
                    obj.cat_icon = request.FILES['cat_icon']
                    try:
                        obj.save()
                    except:
                        pass
                if request.FILES.get('category_image'):
                    obj.category_image = request.FILES['category_image']
                    try:
                        obj.save()
                    except:
                        pass
                try:
                    obj.save()
                except:
                    pass
                obj_data = Category.objects.filter(pk=obj.id)
                data = CategoriesSerializer(obj_data, many=True)

                return Response({"status": True, "data": data.data})
            except ObjectDoesNotExist as e:
                return Response({"status": False, "message": "object does not exists"})
        elif request.FILES:
            try:
                obj = Category.objects.get(pk=pk)
                if request.FILES.get('cat_icon'):
                    obj.cat_icon = request.FILES['cat_icon']
                    try:
                        obj.save()
                    except:
                        pass
                elif request.FILES.get('category_image'):
                    obj.category_image = request.FILES['category_image']
                    try:
                        obj.save()
                    except:
                        pass
                obj_data = Category.objects.filter(pk=obj.id)
                data = CategoriesSerializer(obj_data, many=True)

                return Response({"status": True, "data": data.data})
            except ObjectDoesNotExist as e:
                return Response({"status": False, "message": "object does not exists"})

# get child category  for mobile backend
# @permission_classes([IsAuthenticated])

class get_childs(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.POST:
            if request.POST['tn_parent']:
                try:
                    parent_obj = Category.objects.filter(pk=request.POST['tn_parent'], is_deleted=False)
                    if parent_obj:
                        cat_children = Category.objects.filter(tn_parent=request.POST.get('tn_parent'), is_deleted=False)
                        # child_data = [i for i in cat_children if i]
                        if cat_children:
                            data = CategoriesSerializer(cat_children, many=True)
                            return Response({"status": True, "data": data.data})
                        else:
                            return Response({"status": True, "data": []})
                    else:
                        return Response({"status": True, "data": []})
                except ObjectDoesNotExist:
                    return Response({"status": False, "message": "object does not exists"})
        return Response({"status": True, "message": "enter parent id "})


# search category on side
class SearchCategoryView(APIView):
    # permission_classes = (IsAuthenticated,)
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.POST:
            if request.POST['name']:

                try:
                    search_category = Category.objects.filter(name__icontains=request.POST['name'], is_deleted=False).order_by('id')
                    serializer = CategoriesSerializer(search_category, many=True)

                    return Response({"status": True,
                                     "data": serializer.data
                                     })
                except:
                    print("there is some error")

            else:
                return Response({"status": status.HTTP_404_NOT_FOUND,
                                 })


# category questions for admin side
@permission_classes([IsAuthenticated])
class AddListQuestion(generics.ListCreateAPIView):
    # permission_classes = (AllowAny,)
    queryset = CategoryQuestions.objects.all().order_by('-id')
    serializer_class = QuestionsSerializer

    def post(self, request, *args, **kwargs):
        # data = request.data
        serializer = QuestionsSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"status": True, "message": "Questions created successfully"})
        else:
            return Response({"status": False, "message": "Questions are not created!"})


    def list(self, request, *args, **kwargs):
        paginator = PageNumberPagination()
        paginator.page_size = 10
        # CategoryQuestions.objects.filter(Q(parent_category__is_deleted=False,
        #                                    sub_category__is_deleted=False
        #                                    ) | Q(parent_category__is_deleted=False,
        #                                          sub_category__is_deleted=False,
        #                                          sub_category_child__is_deleted=False)
        #                                  ).exclude(Q(parent_category__is_deleted=True,
        #                                              )).exclude(parent_category__is_deleted=False,
        #                                                         sub_category__is_deleted=True).order_by('-id')
        all_records = CategoryQuestions.objects.all().exclude(
            Q(parent_category__is_deleted=True) | Q(sub_category__is_deleted=True) |
            Q(sub_category_child__is_deleted=True)).order_by('-id')
        result_page = paginator.paginate_queryset(all_records, request)
        serializer = QuestionsSerializer(result_page, many=True)
        return paginator.get_paginated_response(serializer.data)


@permission_classes([IsAuthenticated, IsAdminUser])
class UpdateQuestions(generics.RetrieveUpdateDestroyAPIView):
    # permission_classes = (AllowAny,)

    # queryset = CategoryQuestions.objects.filter(Q(parent_category__is_deleted=False,
    #                                                      sub_category__is_deleted=False
    #                                                      ) | Q(parent_category__is_deleted=False,
    #                                                            sub_category__is_deleted=False,
    #                                                            sub_category_child__is_deleted=False)
    #                                                    ).exclude(Q(parent_category__is_deleted=True,
    #                                                                )).exclude(parent_category__is_deleted=False,
    #                                                                           sub_category__is_deleted=True).order_by('-id')
    queryset = CategoryQuestions.objects.all().exclude(
            Q(parent_category__is_deleted=True) | Q(sub_category__is_deleted=True) |
            Q(sub_category_child__is_deleted=True))
    serializer_class = QuestionsSerializer


# get category questions for mobile
# @permission_classes([IsAuthenticated])
class GetQuestions(APIView):
    permission_classes = (AllowAny,)

    def post(self, request):
        if request.POST:
            if request.POST.get('sub_category'):
                try:
                    qategory_questions = CategoryQuestions.objects.filter(
                                                                          sub_category=request.POST.get('sub_category'),
                                                                          question_for="seeker").order_by('id')
                    serializer = QuestionsSerializer(qategory_questions, many=True)
                    return Response({"status": True, "data": serializer.data})
                except ObjectDoesNotExist:
                    return Response({"status": False, "message": "Questions does not exists related to this category "})
            elif request.POST.get('sub_category_child'):
                try:
                    qategory_questions = CategoryQuestions.objects.filter(
                        sub_category_child=request.POST.get('sub_category_child'), question_for="seeker").order_by('id')
                    serializer = QuestionsSerializer(qategory_questions, many=True)
                    return Response({"status": True, "data": serializer.data})
                except ObjectDoesNotExist:
                    return Response({"status": False, "message": "Questions does not exists related to this category "})
            else:
                return Response({"status": False, "message": "enter category id"})
        return Response({"status": False, "message": "enter category id"})


# class GetQuestions(APIView):
#     permission_classes = (AllowAny,)
#
#     def post(self, request):
#         if self.request.POST:
#             if self.request.POST['sub_category']:
#                 try:
#                     business_questions = CategoryQuestions.objects.filter(
#                         sub_category=request.POST['sub_category'], question_for="business").order_by('id')
#                     serializer = QuestionsSerializer(business_questions, many=True)
#                     category_questions = CategoryQuestions.objects.filter(
#                         sub_category=request.POST['sub_category'], question_for="seeker").order_by('id')
#                     quest_serializer = QuestionsSerializer(category_questions, many=True)
#                     return Response({"status": True, "data": {"business_questions": serializer.data,
#                                                               "ss_questions": quest_serializer.data}})
#                 except ObjectDoesNotExist as e:
#                     return Response({"status": False, "message": "Questions does not exists related to this category "})
#             else:
#                 cat_questions = CategoryQuestions.objects.filter(sub_category=None).order_by('id')
#                 data = QuestionsSerializer(cat_questions, many=True)
#                 return Response({"status": True, "data": data.data})
#
#         return Response({"status": True, "message": "enter category id"})


class SoftDeleteCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            category_id = request.data.get('category_id')
            if category_id:
                category = soft_delete(user_modal='Category', id=category_id, msg='Category')
                return category
            else:
                return Response({"status": False, "message": "Please Enter Category ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class HardDeleteCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            category_id = request.data.get('category_id')
            if category_id:
                category = permanent_delete(user_modal='Category', id=category_id, msg='Category')
                return category
            else:
                return Response({"status": False, "message": "Please Enter Category ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class RestoreCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            category_id = request.data.get('category_id')
            if category_id:
                # restore all category
                # Category.all_objects.all().restore()
                category_restore = restore_from_softdelete(user_modal='Category', id=category_id, msg='Category')
                return category_restore
            else:
                return Response({"status": False, "message": "Please Enter Category ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class SoftDeleteRecord(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Category.all_objects.filter(is_deleted=True).order_by('id')
    serializer_class = CategoriesSerializer


class ActiveCategory(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Category.objects.all().alive()
    serializer_class = CategoriesSerializer


class SearchCategory(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        if self.request.query_params.get('search'):
            string_value = self.request.query_params.get('search')
            category = Category.objects.filter(name__icontains=string_value, is_deleted=False).order_by('-id')\
                .values('id', 'name', 'cat_icon', 'category_image', 'category_heading_text', 'category_heading_text2',
                        'tn_parent', 'behaviour')
            sp = pagination(category, request)
            return Response({"status": True, "data": sp.data})
        else:
            return Response(
                {"status": False, "Response": "Please enter the search value."})


class SearchQuestions(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        if self.request.query_params.get('search'):
            string_value = self.request.query_params.get('search')
            category = CategoryQuestions.objects.filter(Q(parent_category__name__icontains=string_value) |
                                                        Q(sub_category__name__icontains=string_value) |
                                                        Q(sub_category_child__name__icontains=string_value)).exclude(
                Q(parent_category__is_deleted=True) | Q(sub_category__is_deleted=True) |
                Q(sub_category_child__is_deleted=True)
            )\
                .values('id', 'question_text', 'question_type',
                        'question_for', 'r_question_text', 'r_text_one', 'r_text_two', 'parent_category',
                        'sub_category', 'sub_category_child', parent_category_name=F('parent_category__name'),
                        sub_category_name=F('sub_category__name'),
                        sub_category_child_name=F('sub_category_child__name'))
            sp = pagination(category, request)
            return Response({"status": True, "data": sp.data})
        else:
            return Response(
                {"status": False, "Response": "Please enter the search value."})


class CategoryListDel(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        try:
            category_ids = request.data.get('category_ids')
            if Category.all_objects.filter(id__in=category_ids).exists():
                Category.all_objects.filter(id__in=category_ids).hard_delete()
                return Response({"status": True, "message": "Categories Deleted Successfully!"})
            else:
                return Response({"status": False, "message": "Category ID's Dos not Exists!"})
        except ObjectDoesNotExist:
            return Response({"status": False,
                             "message": "There is some error!"})


class CategoryRegisteredUsers(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = CategoriesSerializer

    def get_queryset(self):
        category = Category.objects.filter(id=self.kwargs['pk']).all()
        return category

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        data_list = []
        if not obj.tn_parent_id:
            descendants = obj.tn_descendants_pks
            if not descendants:
                result = pagination(data_list, request)
                return Response({"status": True, "data": result.data})
            descendants_ids = literal_eval(descendants)
            if type(descendants_ids) == int:
                users = Spservices.objects.filter(s_cat_parent=descendants_ids).distinct().\
                    annotate(
                    bookings=Count(
                        's_user__booking_sp_id__order_status',
                        filter=Q(s_user__booking_sp_id__order_status='Active'
                                 ) | Q(s_user__booking_sp_id__order_status='Completed')
                    )
                ).values(
                    'bookings', sp_id=F('s_user__id'), name=F('s_user__first_name'), email=F('s_user__email'), status=F('s_user__is_active'),
                    reference_id=F('s_user__profile__reference_id'), level=F('s_user__profile__level')
                ).order_by('-s_user__id')
                for user in users:
                    if CreateWallet.objects.filter(user=user['sp_id']).exists():
                        user_wallet = CreateWallet.objects.get(user=user['sp_id'])
                        earning = call_wallet_api('get_balance', public_key=user_wallet.wallet_public_key)
                        user.update({"earning": float(earning['MNR']['balance'])})
                        data_list.append(user)
                    else:
                        sp = User.objects.filter(id=user['sp_id']) \
                            .annotate(as_float=Cast('sender_in_mlnTokenPandingHistory__token', FloatField())). \
                            annotate(earning=Coalesce(Sum('as_float'), 0)) \
                            .values('earning', sp_id=F('id')).first()
                        user.update({"earning": sp['earning']})
                        data_list.append(user)
                result = pagination(data_list, request)
                return Response({"status": True, "data": result.data})
            users = Spservices.objects.filter(s_cat_parent__in=descendants_ids).distinct(). \
                annotate(
                    bookings=Count(
                        's_user__booking_sp_id__order_status',
                        filter=Q(s_user__booking_sp_id__order_status='Active'
                                 ) | Q(s_user__booking_sp_id__order_status='Completed')
                    )
                ).values(
                    'bookings', sp_id=F('s_user__id'), name=F('s_user__first_name'), email=F('s_user__email'), status=F('s_user__is_active'),
                    reference_id=F('s_user__profile__reference_id'), level=F('s_user__profile__level')
                ).order_by('-s_user__id')
            for user in users:
                if CreateWallet.objects.filter(user=user['sp_id']).exists():
                    user_wallet = CreateWallet.objects.get(user=user['sp_id'])
                    earning = call_wallet_api('get_balance', public_key=user_wallet.wallet_public_key)
                    user.update({"earning": float(earning['MNR']['balance'])})
                    data_list.append(user)
                else:
                    sp = User.objects.filter(id=user['sp_id'])\
                        .annotate(as_float=Cast('sender_in_mlnTokenPandingHistory__token', FloatField())). \
                        annotate(earning=Coalesce(Sum('as_float'), 0)) \
                        .values('earning', sp_id=F('id')).first()
                    user.update({"earning": sp['earning']})
                    data_list.append(user)
            result = pagination(data_list, request)
            return Response({"status": True, "data": result.data})
        else:
            users = Spservices.objects.filter(s_cat_parent=obj.id).distinct(). \
                annotate(
                bookings=Count(
                    's_user__booking_sp_id__order_status',
                    filter=Q(s_user__booking_sp_id__order_status='Active'
                             ) | Q(s_user__booking_sp_id__order_status='Completed')
                    )
                ).values(
                    'bookings', sp_id=F('s_user__id'), name=F('s_user__first_name'), email=F('s_user__email'), status=F('s_user__is_active'),
                    reference_id=F('s_user__profile__reference_id'), level=F('s_user__profile__level')
                ).order_by('-s_user__id')
            for user in users:
                if CreateWallet.objects.filter(user=user['sp_id']).exists():
                    user_wallet = CreateWallet.objects.get(user=user['sp_id'])
                    earning = call_wallet_api('get_balance', public_key=user_wallet.wallet_public_key)
                    user.update({"earning": float(earning['MNR']['balance'])})
                    data_list.append(user)
                else:
                    sp = User.objects.filter(id=user['sp_id']) \
                        .annotate(as_float=Cast('sender_in_mlnTokenPandingHistory__token', FloatField())). \
                        annotate(earning=Coalesce(Sum('as_float'), 0)) \
                        .values('earning', sp_id=F('id')).first()
                    user.update({"earning": sp['earning']})
                    data_list.append(user)
            result = pagination(data_list, request)
            return Response({"status": True, "data": result.data})




