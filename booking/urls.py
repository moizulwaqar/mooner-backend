from django.urls import path, include
from rest_framework.routers import SimpleRouter
from .views import *
from .admin_views import *
from .seeker_bookings import *

router = SimpleRouter()
router.register("dispute", DisputeViews, basename="dispute")
router.register("tip", TipViews, basename="tip")
router.register("AdminConvenienceFee", AdminConvenienceFeeViews, basename="AdminConvenienceFee")
router.register("AdminTransactionList", AdminTransactionListViews, basename="AdminTransactionList")
router.register("change_status", change_sp_status, basename="change_sp_status")
urlpatterns = [
    path('booking_details/', BookingList.as_view()),
    path('booking_change_order_status/<int:pk>/', ChangeBookingStatus.as_view()),
    path('delete_booking/<int:pk>/', DeleteBooking.as_view()),
    path('get_booking_list/', GetBookingList.as_view()),
    path('create_rating/', Ratings.as_view()),
    path('edit_rating/<int:pk>/', EditRatings.as_view()),
    path('rating_list/<int:pk>/', ListRatings.as_view()),
    path('user_management_view/<int:pk>/', UserManagementView.as_view()),

    ################### seeker_bookings urls ################################
    path('jobs_posted_by_seeker/', JobPostedBySeeker.as_view()),
    path('sp_bid/', SPBids.as_view()),
    path('edit_jobs_posted_by_seeker/<int:pk>/', EditJobPostedBySeeker.as_view()),
    path('filter_sp/', FilterSp.as_view()),
    path('provider_action_on_job/<int:pk>/', ProviderActionOnPostedJob.as_view()),
    path('seeker_bookings/', SeekerBookings.as_view()),
    path('order_completion/<int:pk>/', OrderCompletion.as_view()),
    path('soft_del_question/', SoftDeleteQuestionCategory.as_view(), name='soft_del_question'),
    path('soft_del_booking/', SoftDeleteBooking.as_view(), name='soft_del_booking'),
    path('hard_del_booking/', HardDeleteBooking.as_view(), name='hard_del_booking'),
    path('resotre_booking/', RestoreBooking.as_view(), name='resotre_booking'),
    path('hard_del_question/', HardDeleteQuestion.as_view(), name='hard_del_question'),
    path('restore_question_category/', RestoreQuestionCategory.as_view(), name='restore_question_category'),
    path('soft_del_job/', SoftDeleteJob.as_view(), name='soft_del_job'),
    path('hard_del_job/', HardDeleteJob.as_view(), name='hard_del_job'),
    path('restore_job/', RestoreJob.as_view(), name='restore_job'),
    path('soft_del_answer/', SoftDeleteAnswer.as_view(), name='soft_del_answer'),
    path('hard_del_answer/', HardDeleteAnswer.as_view(), name='hard_del_answer'),
    path('restore_answer/', RestoreAnswer.as_view(), name='restore_answer'),
    path('ss_booking_cancel/', SSBookingCancel.as_view(), name='ss_booking_cancel'),
    path('sp_booking_cancel/', SPBookingCancel.as_view(), name='sp_booking_cancel'),
    path('sp_booked/', SPBooked.as_view(), name='sp_booked'),
    path('cancelled_bookings/', CancelledBookingList.as_view(), name='cancelled_bookings'),
    path('update_booking/', UpdateBooking.as_view(), name='update_booking'),
    path('ss_payment_acknowledge/', SSAcknowledge.as_view(), name='ss_payment_acknowledge'),
    path('add_extra_budget/', AddExtraBudget.as_view(), name='add_extra_budget'),
    path('update_extra_budget/<int:pk>', UpdateExtraBudget.as_view(), name='update_extra_budget'),
    path('list_booking_add_extra/', BookingExtraPayment.as_view(), name='list_booking_add_extra'),
    path('ssaction_price_update/', SSActionExtraPayment.as_view(), name='ssaction_price_update'),
    path('request_tip/<int:pk>/', RequestTipBySp.as_view(), name='request_tip'),
    path('update_booking_date_in_chat/<int:pk>/', UpdateBookingDateInChat.as_view(), name='update_booking_date'),

    path("", include(router.urls)),
    path(
        "approved_dispute/",
        DisputeViews.as_view({"get": "approved_dispute"}),
        name="approved_dispute",
    ),
    path(
        "dispute_history/",
        DisputeViews.as_view({"post": "dispute_history"}),
        name="dispute_history",
    ),
    path(
        "rejected_dispute/",
        DisputeViews.as_view({"get": "rejected_dispute"}),
        name="rejected_dispute",
    ),
]
