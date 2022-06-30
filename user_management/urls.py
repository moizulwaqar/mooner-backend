from django.urls import path
from .views import *
from .admin_change_password_views import *


urlpatterns = [
    path('admin_register_user/', AdminRegisterUser.as_view(), name="admin_register_user"),
    path('admin_user_list/', AdminUserList.as_view(), name="admin_user_list"),
    path('admin_user_list/<int:id>/', AdminUserDetail.as_view(), name="admin_user_list_id"),
    path('admin_sp_list/', AdminSPlist.as_view(), name='admin_sp_list'),
    path('admin_sp_list/<int:id>/', AdminSPDetails.as_view(), name='admin_sp_list_id'),
    path('admin_user_enable/', AdminUserEnable.as_view(), name='admin_user_enable'),
    path('admin_user_filter_bycolumn/', AdminFilterUser.as_view(), name='admin_user_firstname'),
    path('total_user_count/', AdminTotalUserCount.as_view(), name="total_user_count"),
    path('delete_user/<int:id>', delete_user, name="delete_user"),
    path('admin_user_list_nopagination/', AdminUserListNoPagination.as_view(), name='admin_user_list_nopagination'),
    path('address/', Adress.as_view(), name="address"),


    # change_password_admin_module urls
    path('change_password_sub_admin_list/', SubAdmin.as_view()),
    path('edit_change_password_user/<int:pk>/', ChangePasswordUser.as_view())

]
