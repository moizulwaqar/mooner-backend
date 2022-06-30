from django.contrib import admin
from django.urls import path, include
from .views import *
from .admin_users import AdminLogin
from django.conf.urls import url
from .admin_views import OverallStates

urlpatterns = [
    # ==================User Account===================== #
    path('signup/', UserRegisterAPIView.as_view(), name="signup"),
    path('profile/', UserProfileAPIView.as_view(), name="profile"),
    path('update/', UserUpdateAPIView.as_view(), name="update"),
    path('activate/<uidb64>/<token>/', activate, name='activate'),
    path('login_cellphone_request/', UserLoginPhoneRequest.as_view(), name="login_cellphone_request"),
    path('login_cellphone/', UserLoginPhone.as_view(), name="login_cellphone"),
    path('login_google/', UserLoginGoogle.as_view(), name="user_login_google"),
    path('login_facebook/', UserLoginFacebook.as_view(), name="user_login_facebook"),
    path('login_email/', UserLoginEmail.as_view(), name="user_login_email"),
    path('soft_del_user/', SoftDeleteUser.as_view(), name='soft_del_user'),
    path('restore_user/', RestoreUser.as_view(), name='restore_user'),


    # tesing urls below, can be remove in future
    path('user_forgot_password/', USERForgotPassword.as_view(), name='user_forgot_password'),
    path('user_reset_password/', USERResetPassword.as_view(), name='user_reset_password'),


    path('toggle/', UserToggleAPIView.as_view(), name="user_toggle"),
    path('roles/', UserAdminRoleAPIView.as_view(), name="admin_role"),
    path('profile_view/', UserProfiles.as_view(), name="profile_view"),
    path('profile_otp/', UserProfileOTP.as_view(), name="profile_otp"),
    path('update_user_phone/', UserUpdatePhoneAPIView.as_view(), name="update_user_phone"),
    path('logout/', UserLogoutAPI.as_view(), name="user_logout"),
    path('all/', AllUser.as_view(), name="user_all"),
    path('user-type/', UserTypes.as_view(), name="user_type"),
    path('GETAllUser/', GETAllUser.as_view(), name="GETAllUser"),

    # path('user_record_update/', UserRecordUpdate.as_view(), name="user_record_update"),

    # ==================Admin===================== #
    path('admin_login/', adminLogin.as_view(), name="admin_login"),
    path('admin_logout/', AdminUserLogout.as_view(), name='admin_logout'),
    path('admin_forgot_password/', AdminForgetPassword.as_view(), name='admin_forgot_password'),
    path('admin_reset_password/<uidb64>/<token>/', AdminResetPassword.as_view(), name='admin_reset_password'),
    path('overall_states/', OverallStates.as_view(), name='admin_team_data'),

    # ================ get current admin profile ================== #
    path('admin_profile/', AdminProfile.as_view(), name="admin_profile"),

    # ================ get current user profile ================== #
    path('user_profile/', SeekerProfile.as_view(), name="user_profile"),
    path('edit_user_profile/<int:pk>/', EditSeekerProfile.as_view()),
    path('update_user_phone_number/<int:pk>/', UpdateUserPhoneNo.as_view()),
    # path('user_profile_change_password/<int:pk>/', UserProfileChangePassword.as_view())

    # ================ search in table ========================== #
    path('usersearch/', SearchUser.as_view()),

    #  =============== Add Addresses  ============================ #
    path('user_address/', Addresses.as_view()),
    path('user_address/<int:pk>', UpdateAddresses.as_view())

]
