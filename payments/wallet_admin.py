from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from mooner_backend.utils import pagination
from django.db.models import F, Q, Sum
from document_management.models import Document
from .models import WalletHistory
from mln.serializers import TokenHistorySerializer
from mln.models import TokenHistory


class GetKYCApprovedDocument(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):

        result = Document.objects.filter(status='Approved', doc_type='KYC').order_by('-id').\
            values('id', 'status', label=F('doc_label'), ss_name=F('ss__first_name'),
                   sp_name=F('sp__first_name'))
        document = pagination(result, request)
        return Response({"status": True, "data": document.data})


class GetKYCPendingDocument(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):

        result = Document.objects.filter(status='Pending', doc_type='KYC').order_by('-id').\
            values('id', 'status', label=F('doc_label'), ss_name=F('ss__first_name'),
                   sp_name=F('sp__first_name'))
        document = pagination(result, request)
        return Response({"status": True, "data": document.data})


class GetKYCRequest(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):

        result = Document.objects.filter(doc_type='KYC').order_by('-id').\
            values('id', 'status', 'expiration_date', ss_name=F('ss__first_name'), type=F('doc_for'),
                   sp_name=F('sp__first_name'))
        document = pagination(result, request)
        return Response({"status": True, "data": document.data})


class SendTokens(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):
        result = WalletHistory.objects.all().order_by('-id').values('id', from_public_address=F('frompublic_address'),
                                                                    topup_public_address=F('to_public_address'),
                                                                    tokens=F('earn_tokens'))
        result = pagination(result, request)
        return Response({"status": True, "data": result.data})


class AdminTokenHistory(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = TokenHistorySerializer

    def get(self, request, *args, **kwargs):
        # total_tokens = TokenHistory.objects.filter(earned_by=request.user). \
        #     aggregate(total_earned_tokens=Sum('earn_tokens'))
        data = TokenHistory.objects.filter(earned_by=request.user).values('earn_tokens',
                                                                          name=F('earned_from__first_name'),
                                                                          time=F('updated_at'),
                                                                          type=F('earned_user_type'))
        return Response({"status": True, "data": data})


class AdminWalletDashboard(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    # serializer_class = TokenHistorySerializer

    def get(self, request, *args, **kwargs):
        total_tokens = TokenHistory.objects.filter(earned_by=request.user). \
            aggregate(total_earned_tokens=Sum('earn_tokens'))

        return Response({"status": True, "data": total_tokens})
