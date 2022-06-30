from django.urls import path
from .views import *

urlpatterns = [
    path('list_mln_users/', ListMLNUsers.as_view()),
    path('list_referal_users/<int:pk>/', ListReferralUsers.as_view()),
    path('list_referal_users_pagination/<int:pk>/', ListReferralUsersPagination.as_view()),
    path('get_user_details/<int:pk>/', EditUserDetails.as_view()),
    path('get_referral_user_details/<int:pk>/', EditReferralUserDetails.as_view()),
    path('set_level_profit/<int:pk>/', LevelMarginProfit.as_view()),
    path('get_reference_id/<int:pk>/', GetReferenceId.as_view()),
    path('refer_user/', ReferUsers.as_view()),
    path('token_history/', UserTokenHistory.as_view()),


    # soft and hard delete
    path('soft_del_referrals/', SoftDeleteReferrals.as_view(), name='soft_del_referrals'),
    path('restore_soft_del_referrals/', RestoreReferrals.as_view(), name='restore_soft_del_referrals'),
    path('hard_del_referrals/', HardDeleteReferrals.as_view(), name='hard_del_referrals')
]
