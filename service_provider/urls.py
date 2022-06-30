from django.urls import path, include
from .views import *
from .sp_views import *
from .sp_admin import *

urlpatterns = [
    path('get_sp_services/', get_sp_services.as_view(), name='get_sp_services'),
    path('sp_category_questions/', sp_category_questions.as_view(), name='sp_category_questions'),
    path('sp_dashboard/', sp_dashboard.as_view(), name='sp_dashboard'),
    path('get_sp_service_register/', SpRegisterService.as_view()),
    path('edit_sp_service_register/<int:pk>/', SpEditService.as_view()),
    path('create_sp_items/', CreateSpItem.as_view()),
    path('get_sp_items/', GetSpItem.as_view()),
    path('edit_sp_items/<int:pk>/', EditSpItem.as_view()),
    path('get_sp_categories/', SPCategories.as_view()),
    path('get_sp_service_bybudget/', ListSpByBudget.as_view()),
    path('delete_sp_items_images/<int:pk>/', DeleteSpItemsImages.as_view()),
    path('list_item_by_category/', ListItemsByCategory.as_view()),

    # sp_admin urls
    path('admin_sp_list/', SPlist.as_view()),
    path('admin_edit_sp/<int:pk>/', EditSP.as_view()),
    path('admin_edit_sp_profile/<int:pk>/', EditSPProfile.as_view()),
    path('admin_sp_management_view/<int:pk>/', SpManagementView.as_view()),
    path('admin_sp_active_bookings/<int:pk>/', SpActiveBookings.as_view()),
    path('admin_sp_completed_bookings/<int:pk>/', SpCompletedBookings.as_view()),
    path('admin_sp_ratings/<int:pk>/', SpRatings.as_view()),
    path('admin_sp_kyc/<int:pk>/', SPKYCUploads.as_view()),


    # sp search
    path('admin_sp_search/', SpSearch.as_view()),
    path('spjobsfilter/', SpJobsFilter.as_view())

]
