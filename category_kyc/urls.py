from rest_framework.routers import SimpleRouter
from .views import *
from django.urls import path, include


router = SimpleRouter()
router.register("category_kyc", CategoryKycViews, basename="category_kyc")
router.register("category_kyc_answer", CategoryKycAnswerViews, basename="category_kyc_answer")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "kyc_common_list/",
        CategoryKycViews.as_view({"get": "kyc_common_list"}),
        name="kyc_common_list",
    ),
    path(
        "common_questions_for_catogory_kyc/",
        CategoryKycViews.as_view({"get": "common_kyc_for_category"}),
        name="common_kyc_for_category",
    ),
    path(
        "kyc_specific_list/",
        CategoryKycViews.as_view({"post": "kyc_specific_list"}),
        name="kyc_specific_list",
    ),
    path(
        "get_category_kyc_questions/",
        CategoryKycViews.as_view({"post": "get_questions_of_categories"}),
        name="get_questions_of_categories",
    ),
    path(
        "get_expire_document_time/",
        CategoryKycViews.as_view({"get": "get_expire_document_time"}),
        name="get_questions_of_categories",
    ),
]
