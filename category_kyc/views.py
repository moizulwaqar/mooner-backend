from django.db.models import F, Q
from rest_framework import viewsets, exceptions
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from .serializers import *
from .models import CategoryKyc, CategorySpecificKyc, CategoryKycAnswer
import datetime

# Create your views here.


class CategoryKycViews(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategoryKycSerializer
    queryset = CategoryKyc.objects.all()

    def create(self, request, *args, **kwargs):
        if request.user.is_superuser:
            serializer = self.get_serializer(data=request.data, many=True)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            serializer.save()
            if serializer.data[0]['category_kyc_type'] == 'Common':
                return Response({"status": True, "message": "Common KYC has been created successfully.",
                                "data": serializer.data})
            else:
                return Response({"status": True, "message": "Category KYC has been created successfully.",
                                 "data": serializer.data})
        raise exceptions.PermissionDenied()

    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            result = paginator.paginate_queryset(CategoryKyc.objects.filter(category_kyc_type='Specific').
                                                 order_by('-id'), request)
            serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(serializer.data)
        raise exceptions.PermissionDenied()

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            if serializer.data.get('category_kyc_type') == 'Common':
                data = {"label": serializer.data.get('label'),
                        "category_kyc_type": serializer.data.get('category_kyc_type'),
                        "doc_file_type": serializer.data.get('doc_file_type'),
                        "doc_type": serializer.data.get('doc_type'),
                        "expiration_date_required": serializer.data.get('expiration_date_required'),
                        "question_type": serializer.data.get('question_type')}
                return Response({"status": True, "message": "Category KYC", "data": data})
            else:
                result = CategorySpecificKyc.objects.filter(specific_doc=instance).first()
                common_questions = result.specific_doc.filter(category_kyc_type='Common').values_list('id', flat=True)
                data = CategoryKyc.objects.filter(id=instance.id).values('id', 'label', 'category_kyc_type',
                                                                         'doc_file_type', 'doc_for',
                                                                         'doc_type', 'question_type',
                                                                         'expiration_date_required',
                                                                         category=
                                                                         F('specific_doc_in_category_kyc__category'),
                                                                         sub_category=
                                                                         F('specific_doc_in_category_kyc__sub_category')
                                                                         , sub_category_child=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'sub_category_child'),
                                                                         category_name=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'category__name'),
                                                                         sub_category_name=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'sub_category__name')
                                                                         , sub_category_child_name=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'sub_category_child__name')
                                                                         ).first()
                data["common_questions"] = common_questions
                return Response({"status": True, "message": "Category KYC", "data": data})
        raise exceptions.PermissionDenied()

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            if instance.category_kyc_type == 'Common':
                return Response({"status": True, "message": "Category KYC has been updated successfully.",
                                 "data": serializer.data})
            else:
                result = CategorySpecificKyc.objects.filter(specific_doc=instance).first()
                common_questions = result.specific_doc.filter(category_kyc_type='Common').values('id', 'label')
                data = CategoryKyc.objects.filter(id=instance.id).values('id', 'label', 'category_kyc_type',
                                                                         'doc_file_type', 'doc_for',
                                                                         'doc_type', 'question_type',
                                                                         'expiration_date_required',
                                                                         category=
                                                                         F('specific_doc_in_category_kyc__category'),
                                                                         sub_category=
                                                                         F('specific_doc_in_category_kyc__sub_category')
                                                                         , sub_category_child=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'sub_category_child'),
                                                                         category_name=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'category__name'),
                                                                         sub_category_name=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'sub_category__name')
                                                                         , sub_category_child_name=
                                                                         F('specific_doc_in_category_kyc__'
                                                                           'sub_category_child__name')
                                                                         ).first()
                data["common_questions"] = common_questions
                return Response({"status": True, "message": "Category KYC", "data": data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "Category KYC successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()

    def kyc_common_list(self, request):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            result = paginator.paginate_queryset(CategoryKyc.objects.filter(category_kyc_type='Common').order_by('-id')
                                                 .values('id', 'label', 'category_kyc_type', 'doc_file_type', 'doc_type'
                                                         , 'question_type', 'expiration_date_required'), request)
            serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(serializer.data)
        raise exceptions.PermissionDenied()

    def kyc_specific_list(self, request):
        if request.user.is_superuser:
            category = request.data.get('category_id')
            if category:
                try:
                    paginator = PageNumberPagination()
                    paginator.page_size = 10
                    specific_questions = CategorySpecificKyc.objects.filter(category=category).first()
                    result = paginator.paginate_queryset(
                        specific_questions.specific_doc.filter(category_kyc_type='Specific')
                        .values().order_by('-id'), request)
                    serializer = self.serializer_class(result, many=True)
                    return paginator.get_paginated_response(serializer.data)
                except:
                    return Response({"status": False, "message": "category with id={} does not exist.".format(category)})
            else:
                return Response({"status": False, "message": "category_id is required."})
        raise exceptions.PermissionDenied()

    def common_kyc_for_category(self, request):
        if request.user.is_superuser:

            data = self.queryset.filter(category_kyc_type='Common').order_by('-id').values('id', 'label')
            return Response({"status": True, "message": "Common questions for Category KYC.",
                             "data": data})
        raise exceptions.PermissionDenied()

    def get_questions_of_categories(self, request):
        category = self.request.data.get('category_id')
        sub_category = request.data.get('sub_category_id')
        sub_category_child = request.data.get('sub_category_child_id')
        if category and not sub_category and not sub_category_child:
            try:
                serializer = CategorySpecificSerializer(CategorySpecificKyc.objects.filter(category=category,
                                                        sub_category=None,
                                                        sub_category_child=None), many=True)
                return Response({"status": True, "message": "Questions for categories",
                                 "data": serializer.data})
            except:
                return Response(
                    {"status": False, "message": "category does not exist.".format(category)})
        if category and sub_category and not sub_category_child:
            try:
                serializer = CategorySpecificSerializer(CategorySpecificKyc.objects.filter(category=category,
                                                        sub_category=sub_category,
                                                        sub_category_child=None), many=True)
                return Response({"status": True, "message": "Questions for categories",
                                 "data": serializer.data})
            except:
                return Response(
                    {"status": False, "message": "category does not exist.".format(category)})
        if category and sub_category and sub_category_child:
            try:
                serializer = CategorySpecificSerializer(CategorySpecificKyc.objects.filter(category=category,
                                                        sub_category=sub_category,
                                                        sub_category_child=sub_category_child), many=True)
                return Response({"status": True, "message": "Questions for categories",
                                 "data": serializer.data})
            except:
                return Response(
                    {"status": False, "message": "category does not exist.".format(category)})
        else:
            return Response({"status": False, "message": "category_id is required."})

    def get_expire_document_time(self, request):
        # date = datetime.date
        today_date = datetime.date.today()
        # expiry_date = date +
        expiry_date = today_date + datetime.timedelta(days=6)
        print(expiry_date)


class CategoryKycAnswerViews(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = CategoryKycAnswerSerializer
    queryset = CategoryKycAnswer.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data, many=True)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)
        serializer.save(user=request.user)
        return Response({"status": True, "message": "Category KYC answer has been submitted.",
                         "data": serializer.data})

    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            result = paginator.paginate_queryset(CategoryKycAnswer.objects.filter(status='Pending').
                                                 order_by('-id'), request)
            serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(serializer.data)
        raise exceptions.PermissionDenied()

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"status": True, "message": "Category KYC answer", "data": serializer.data})
        raise exceptions.PermissionDenied()

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"status": True, "message": "Category KYC answer has been updated successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "Category KYC answer successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()