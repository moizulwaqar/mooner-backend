from django.urls import path
from .views import *

urlpatterns = [
    path('get_document/', GetDocument.as_view()),
    path('edit_document/<int:pk>/', EditDocument.as_view()),
    path('get_pending_answers/', KYCPendingAnswerAdmin.as_view()),
    path('search_document/', SearchDocument.as_view()),
    path('spkyc/', SPKycDocument.as_view()),
    path('spkyc_documents/', SpKycDocumentList.as_view()),
    path('spkycstatus/', SpKycStatus.as_view()),
    path('create_kyc/', CreateKycAnswer.as_view()),
    path('update_kyc/<int:pk>/', EditKycAnswer.as_view()),
    path('get_approved_answers/', KYCApproveAnswerAdmin.as_view()),
    path('update_kyc_admin/<int:pk>/', EditKycAnswerAdmin.as_view()),
    path('deletekycfile/', DeleteKycFile.as_view())
]