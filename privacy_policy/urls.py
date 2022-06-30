from rest_framework.routers import SimpleRouter
from .views import *
from django.urls import path, include


router = SimpleRouter()
router.register("privacy_policy", PrivacyViewSet, basename="privacy")
router.register("about_content", AboutContentViewSet, basename="about_content")
router.register("terms_and_condition", TermsAndConditionViewSet, basename="terms_and_condition")

urlpatterns = [
    path("", include(router.urls)),

]
