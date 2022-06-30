from botocore.exceptions import ClientError
import logging
from django.contrib.auth.models import User
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response

from .models import KycAnswer
from .serializers import *
from mooner_backend.utils import pagination, email_function
from django.db.models import F, Q
from rest_framework.views import APIView
import boto3
from mooner_backend.settings import AWS_ACCESS_KEY, AWS_SECRET_ACCESS_KEY, AWS_BUCKET_NAME


# Create your views here.

class GetDocument(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = DocumentSerializer

    def list(self, request, *args, **kwargs):

        result = Document.objects.all().order_by('-id').values('id', 'expiration_date', 'doc_for', 'doc_label',
                                                               'doc_question_type', 'parent_category')

        document = pagination(result, request)
        return Response({"status": True, "data": document.data})

    def post(self, request, *args, **kwargs):

        serializer = DocumentSerializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response({"status": True, "message": "Document has been created successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class EditDocument(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = DocumentSerializer

    def get_queryset(self):
        ticket = Document.objects.filter(id=self.kwargs['pk']).all()
        return ticket

    def put(self, request, *args, **kwargs):
        try:
            serializer = self.update(request)
            if serializer.data['status'] == 'Approved':
                body = '<strong>Your document has been Approved:</strong>' \
                       '<strong>Document status:</strong> ' + serializer.data['status'] + \
                       '<br><strong>Document type:</strong> ' + serializer.data['doc_type'] + \
                       '<br><strong>Document label:</strong> ' + serializer.data['doc_label']
                user = User.objects.get(Q(id=serializer.data['sp']) | Q(id=serializer.data['ss']))
                email_function(body=body, subject="Document response", email=user.email)
                return Response({"status": True, "message": "Document has been updated successfully."})
            if serializer.data['status'] == 'Disapproved' and not serializer.data['disapproval_reason']:
                body = '<strong>Your document has been disapproved:</strong>' \
                       '<br><strong>Document status:</strong> ' + serializer.data['status'] + \
                       '<br><strong>Document type:</strong> ' + serializer.data['doc_type'] + \
                       '<br><strong>Document Label:</strong> ' + serializer.data['doc_label']
                user = User.objects.get(Q(id=serializer.data['sp']) | Q(id=serializer.data['ss']))
                email_function(body=body, subject="Document response", email=user.email)
                data = {
                    "doc_id": serializer.data['id'],
                    "doc_name": serializer.data['doc_label'],
                    "category_id": serializer.data['parent_category']
                }
                return Response({"status": True, "message": "Document has been updated successfully.",
                                 "data": data})
            else:
                body = '<strong>Your document has been disapproved:</strong>' \
                       '<br><strong>Document status:</strong> ' + serializer.data['status'] + \
                       '<br><strong>Document type:</strong> ' + serializer.data['doc_type'] + \
                       '<br><strong>Document label:</strong> ' + serializer.data['doc_label'] + \
                       '<br><strong>Disapproval Reason:</strong> ' + serializer.data['disapproval_reason']
                user = User.objects.get(Q(id=serializer.data['sp']) | Q(id=serializer.data['ss']))
                email_function(body=body, subject="Document response", email=user.email)
                return Response({"status": True, "message": "Document has been updated successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)

    def get(self, request, *args, **kwargs):
        document = self.get_object()
        images_1 = Document.objects.filter(id=document.id).values('image_urls')
        images = images_1[0]['image_urls']
        data = Document.objects.filter(id=document.id).values('id', 'expiration_date', 'status', 'experience',
                                                              'disapproval_reason', 'occupation',
                                                              label=F('doc_label'),
                                                              type=F('doc_type'), ss_name=F('ss__first_name'),
                                                              sp_name=F('sp__first_name'),
                                                              category_name=F('parent_category__name'),
                                                              category_id=F('parent_category__id'),
                                                              sub_category_name=F('sub_category__name'),
                                                              )
        return Response({"status": True, "data": data, "images": images})


class KYCPendingAnswerAdmin(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = DocumentSerializer

    def list(self, request, *args, **kwargs):
        result = KycAnswer.objects.filter(status='Pending').order_by('-id').values('id', 'answer', 'status',
                                                                                   label=F('document__doc_label'),
                                                                                   category_name=F(
                                                                                       'document__parent_category__name'),
                                                                                   user_name=F('user__first_name'),
                                                                                   documentid=F('document__id'),
                                                                                   document_for=F('document__doc_for'),
                                                                                   doc_question_type=F(
                                                                                       'document__doc_question_type'),
                                                                                   expiration_date=F(
                                                                                       'document__expiration_date'))

        document = pagination(result, request)
        return Response({"status": True, "data": document.data})


class SearchDocument(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        if self.request.query_params.get('search'):
            string_value = self.request.query_params.get('search')
            result = Document.objects.filter(Q(sp__first_name__icontains=string_value) |
                                             Q(ss__first_name__icontains=string_value)
                                             ).order_by('-id').values('id', 'expiration_date', 'status',
                                                                      label=F('doc_label'), type=F('doc_type'),
                                                                      ss_name=F('ss__first_name'),
                                                                      sp_name=F('sp__first_name'))
            document = pagination(result, request)
            return Response({"status": True, "data": document.data})
        else:
            return Response(
                {"status": False, "Response": "Please enter the search value."})


class SPKycDocument(generics.ListAPIView):
    permission_classes = (AllowAny,)

    def list(self, request, *args, **kwargs):
        if KycAnswer.objects.filter(user=request.user).exists():
            user_kyc = KycAnswer.objects.filter(user=request.user).values('id', 'status',
                                                                          document_label=F('document__doc_label')
                                                                          , document_urls=F('answer'),
                                                                          document_type=F(
                                                                              'document__doc_question_type'),

                                                                          )
            return Response({"status": True, "call_type": "update", "data": user_kyc})
        else:
            document = Document.objects.filter(doc_for='SP').values('id', 'doc_for',  'status', document_label=F('doc_label'),
                                                                    document_type=F('doc_question_type'))
            return Response({"status": True, "call_type": "post", "data": document})


class SpKycDocumentList(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):
        user_kyc = KycAnswer.objects.filter(user=request.user).values('id', document_label=F('document__doc_label'),
                                                                      document_urls=
                                                                      F('answer'), )
        return Response({"status": True, "data": user_kyc})


class SpKycStatus(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    def list(self, request, *args, **kwargs):

        user_kycstatus = KycAnswer.objects.filter(user=request.user).exists()
        if not user_kycstatus:
            return Response({"status": True, "kyc_status": False})

        document_status = KycAnswer.objects.filter(user=request.user).count()
        document_status_approves = KycAnswer.objects.filter(Q(status='Approve'), user=request.user).count()

        if document_status == document_status_approves:
            return Response({"status": True, "kyc_status": True})
        else:
            return Response({"status": True, "kyc_status": False})


class CreateKycAnswer(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        serializer = KycAnswerSerializer(data=request.data, many=True)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            return Response({"status": True, "message": "Kyc created successfully"})
        else:
            return Response({"status": False, "message": "Kyc are not created!"})


class EditKycAnswer(generics.UpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = KycAnswer.objects.all()
    serializer_class = KycAnswerSerializer

    def put(self, request, *args, **kwargs):
        try:
            serializer = self.partial_update(request, *args, **kwargs)
            return Response({"status": True, "message": "Document has been updated successfully.",
                             "data": serializer.data})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)


class KYCApproveAnswerAdmin(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = DocumentSerializer

    def list(self, request, *args, **kwargs):
        result = KycAnswer.objects.filter(status='Approve').order_by('-id').values('id', 'answer', 'status',
                                                                                   label=F('document__doc_label'),
                                                                                   category_name=F(
                                                                                       'document__parent_category__name'),
                                                                                   user_name=F('user__first_name'),
                                                                                   documentid=F('document__id'),
                                                                                   document_for=F('document__doc_for'),
                                                                                   doc_question_type=F(
                                                                                       'document__doc_question_type'),
                                                                                   expiration_date=F(
                                                                                       'document__expiration_date'))

        document = pagination(result, request)
        return Response({"status": True, "data": document.data})


class EditKycAnswerAdmin(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = KycAnswer.objects.all()
    serializer_class = KycAnswerSerializer

    def put(self, request, *args, **kwargs):
        try:
            serializer = self.partial_update(request, *args, **kwargs)
            if serializer.data['status'] == 'Approve':
                document = Document.objects.filter(id=serializer.data['document']).values('expiration_date', 'doc_for',
                                                                                          'doc_label',
                                                                                          'doc_question_type').first()
                body = '<strong>Your document has been Approved</strong>' \
                       '<br><strong>Document label:</strong> ' + document['doc_label']
                user = User.objects.get(id=serializer.data['user'])
                email_function(body=body, subject="Document response", email=user.email)
                return Response({"status": True, "message": "Document has been updated successfully.",
                                 "data": serializer.data, "document_data": document})
            if serializer.data['status'] == 'Disapprove' and not serializer.data['disapproval_reason']:
                document = Document.objects.filter(id=serializer.data['document']).values('expiration_date', 'doc_for',
                                                                                          'doc_label',
                                                                                          'doc_question_type').first()
                body = '<strong>Your document has been disapproved</strong>' \
                       '<br><strong>Document label:</strong> ' + document['doc_label']
                user = User.objects.get(id=serializer.data['user'])
                email_function(body=body, subject="Document response", email=user.email)
                return Response({"status": True, "message": "Document has been updated successfully.",
                                 "data": serializer.data, "document_data": document})
            else:
                document = Document.objects.filter(id=serializer.data['document']).values('expiration_date', 'doc_for',
                                                                                          'doc_label',
                                                                                          'doc_question_type').first()
                body = '<strong>Your document has been disapproved</strong>' \
                       '<br><strong>Document label:</strong> ' + document['doc_label'] + \
                       '<br><strong>Disapproval Reason:</strong> ' + serializer.data['disapproval_reason']
                user = User.objects.get(id=serializer.data['user'])
                email_function(body=body, subject="Document response", email=user.email)
                document = Document.objects.filter(id=serializer.data['document']).values('expiration_date', 'doc_for',
                                                                                          'doc_label',
                                                                                          'doc_question_type').first()
                return Response({"status": True, "message": "Document has been updated successfully.",
                                 "data": serializer.data, "document_data": document})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        result = KycAnswer.objects.filter(id=obj.id).values('id', 'answer', 'status', 'disapproval_reason', 'user_id',
                                                            label=F('document__doc_label'),
                                                            category_name=F('document__parent_category__name'),
                                                            category_id=F('document__parent_category__id'),
                                                            user_name=F('user__first_name'),
                                                            documentid=F('document__id'),
                                                            document_for=F('document__doc_for'),
                                                            doc_question_type=F('document__doc_question_type'),
                                                            expiration_date=F('document__expiration_date'))

        return Response({"status": True, "data": result})


class DeleteKycFile(APIView):
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        answer_id = request.data.get('kycanswer_id')
        delete_file = request.data['del_file']
        client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY,
                              aws_secret_access_key=AWS_SECRET_ACCESS_KEY)
        bucket = AWS_BUCKET_NAME
        key = delete_file
        if delete_file:
            try:
                client.delete_object(Bucket=bucket, Key=key)
                kyc_answer = KycAnswer.objects.get(id=int(answer_id)).answer
                index_ = kyc_answer.index(delete_file)
                kyc_answer.pop(index_)
                if delete_file not in kyc_answer:
                    KycAnswer.objects.filter(id=int(answer_id)).update(answer=kyc_answer)
                    return Response({"status": True, "message": "File deleted"})
                else:
                    return Response({"status": False, "messgae": "File not deleted."})
            except ClientError as e:
                logging.error(e)
                return Response({"status": False, "message": "File not deleted"})
