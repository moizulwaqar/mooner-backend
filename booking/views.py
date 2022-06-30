# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import Distance
from django.core.files.base import ContentFile
from django.db import transaction
from django.db.models import Q, F, Sum
import base64
import os
from django.db.models.functions import Concat, Coalesce
from rest_framework import generics, exceptions, viewsets
from rest_framework.authentication import SessionAuthentication
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated, IsAdminUser, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView

from mooner_backend.settings import STRIPE_API_KEY
from payments.models import StripeBooking, StripeCustomer, CreateWallet, MLNTokensEarn, MLNTokenPandingHistory
from payments.utils import convert_dollars, create_charge, attach_card, get_card, load_mnr_token, send_token
from service_provider.serializers import SPSerializer
from mooner_backend.utils import pagination, send_email_template
from .serializers import *
from notification.utils import *
from django.db.models import Count
from django.db.models import Value, BooleanField
from payments.payments_decoraters import *
from user.models import UserProfile

# Create your views here.
from .utils import send_referrals_earnings


class CsrfExemptSessionAuthentication(SessionAuthentication):

    def enforce_csrf(self, request):
        return


class BookingList(generics.ListCreateAPIView):
    # permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Booking.objects.filter(category__is_deleted=False)
    serializer_class = BookingSerializer

    def list(self, request):
        queryset = self.get_queryset()
        serializer = BookingSerializer(queryset, many=True)
        return Response(serializer.data)

    def post(self, request, *args, **kwargs):
        data = ""
        if request.data:
            serializer = JobsSerializer(data=request.data)
            if serializer.is_valid():
                # Rating.objects.annotate(rating=Avg())
                serializer.save()
                # location = request.data.get('distance')
                order = request.data.get('order')  # location, -location, budget, -budget,
                # rating = request.data.get('rating')
                min_budget = request.data.get('min_budget')
                max_budget = request.data.get('max_budget')
                latitude = float(request.data.get('latitude'))
                longitude = float(request.data.get('longitude'))
                # location = request.data.get('location_order')

                # return Response(serializer.data, status=status.HTTP_201_CREATED)
                answers_data = request.data.get('answers')
                files = request.data.get('files')
                # booking model change into jobs
                job_obj = Jobs.objects.get(id=serializer.data['id'])
                # booking_obj = Jobs.objects.get(booking_job_id__job=job_obj)
                cat_parent_obj = Category.objects.get(id=request.data.get('category'), is_deleted=False)
                child_cat_obj = Category.objects.get(id=request.data.get('cat_child_id'), is_deleted=False)

                if files:
                    for file in files:
                        job_obj = JobFiles()
                        format, imgstr = file.split(';base64,')
                        ext = format.split('/')[-1]
                        job_file = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                        job_obj.file = job_file
                        job_obj.job_id = serializer.data['id']
                        job_obj.save()

                if answers_data:
                    for questionid, answer_ in answers_data.items():

                        question = CategoryQuestions.objects.get(id=questionid, parent_category__is_deleted=False,
                                                                 sub_category__is_deleted=False,
                                                                 sub_category_child__is_deleted=False,)
                        if question.question_type.lower() == "text":
                            Answer.objects.create(question_id=question, jobs_id_id=serializer.data['id'],
                                                  cat_parent_id=cat_parent_obj,
                                                  child_category=child_cat_obj,
                                                  answer=answer_)
                        if question.question_type.lower() == "file":
                            data = answer_
                            format, imgstr = data.split(';base64,')
                            ext = format.split('/')[-1]

                            file = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                            ans_obj = Answer()

                            ans_obj.question_id = question
                            # ans_obj.booking_id = booking_obj.booking_job_id
                            ans_obj.cat_parent_id = cat_parent_obj
                            ans_obj.child_category = child_cat_obj
                            ans_obj.answer = file
                            ans_obj.save()
                        if question.question_type.lower() == "radio":
                            Answer.objects.create(question_id=question, jobs_id_id=serializer.data['id'],
                                                  cat_parent_id=cat_parent_obj,
                                                  child_category=child_cat_obj,
                                                  answer=answer_)
                        if question.question_type.lower() == "checkbox":
                            Answer.objects.create(question_id=question, jobs_id_id=serializer.data['id'],
                                                  cat_parent_id=cat_parent_obj,
                                                  child_category=child_cat_obj,
                                                  answer=answer_)

                    # point = Point(latitude, longitude)
                    radius = 10

                    data = Spservices.objects.filter(s_cat_parent__is_deleted=False, s_cat_parent=request.data.get('cat_child_id'),
                                                     budget__range=[min_budget, max_budget]).\
                        annotate(rating=Avg('s_cat_parent__booking_category_id__booking__star')).\
                        annotate(cnt=Count('s_user'),
                                 filter=Q(s_cat_parent__booking_category_id__order_status='Complete')). \
                        values(
                        'budget',
                        'rating',
                        username=F('s_user__username'),
                        user_id=F('s_user_id'),
                        cat_name=F('s_cat_parent__name'),
                        completed_jobs=F('cnt'),
                        profile_pic=F('s_user__profile__profile_image'),
                    ). \
                        order_by(order)

                return Response({"status": True, "message": "sp  return", "data": data})
            else:
                return Response({"status": True, "message": "enter valid data", "error": serializer.errors})
        else:
            return Response({"status": True, "message": "please enter request data"})


class Ratings(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Rating.objects.filter(booking__category__is_deleted=False).order_by('-id')
    serializer_class = RatingSerializer

    def post(self, request, *args, **kwargs):
        serializer = RatingSerializer(data=request.data)
        if serializer.is_valid(raise_exception=True):
            serializer.save()
            booking = Booking.objects.filter(id=request.data.get('booking')).first()
            booking.is_tip_request = False
            booking.save()
            return Response({"status": True, "message": "Rating created successfully!"})
        else:
            return Response({"status": False, "message": "Rating not created"})

    def list(self, request, *args, **kwargs):
        user_id = request.data.get('user_id')
        rating = Rating.objects.filter(rated_to=user_id).values('id', 'booking_id', 'feedback', 'star', 'rated_by', 'rated_to',
                                             ratedby=F('rated_by__first_name'),
                                             ratedto=F('rated_to__first_name'),
                                             seeker_id=F('booking__ss_id'),
                                             provider_id=F('booking__sp_id'),
                                             category_name=F('booking__category__name'),
                                             category_id=F('booking__category__id'),
                                             )
        result = pagination(rating, request)
        return Response({"status": True, "data": result.data})


class ListRatings(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    serializer_class = SPSerializer

    def get_queryset(self):
        user = User.objects.filter(id=self.kwargs['pk']).all()
        return user

    def get(self, request, *args, **kwargs):
        sp = self.get_object()
        rating = Rating.objects.filter(rated_to=sp.id).values('id', 'booking_id', 'feedback', 'star', 'rated_by',
                                                              'rated_to', ratedby=F('rated_by__first_name'),
                                                              ratedto=F('rated_to__first_name'),
                                                              seeker_id=F('booking__ss_id'),
                                                              provider_id=F('booking__sp_id'),
                                                              category_name=F('booking__category__name'),
                                                              category_id=F('booking__category__id'))
        result = pagination(rating, request)
        return Response({"status": True, "data": result.data})


class EditRatings(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = Rating.objects.filter(booking__category__is_deleted=False).order_by('-id')
    serializer_class = RatingSerializer

    def get_queryset(self):
        rating = Rating.objects.filter(id=self.kwargs['pk']).all()
        return rating

    def put(self, request, *args, **kwargs):
        try:
            self.update(request)
            return Response({"status": True, "message": "Rating has been updated successfully."})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        rating = Rating.objects.filter(id=obj.id).values('id', 'booking_id', 'feedback', 'star', 'rated_by', 'rated_to',
                                                         ratedby=F('rated_by__first_name'),
                                                         ratedto=F('rated_to__first_name'),
                                                         seeker_id=F('booking__ss_id'),
                                                         provider_id=F('booking__sp_id'),
                                                         category_name=F('booking__category__name'),
                                                         category_id=F('booking__category__id'),
                                                         )
        return Response({"status": True, "data": rating})


class SPBids(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BidsSerializer

    def get_queryset(self):
        return Bids.objects.filter(job=self.request.query_params.get('job_id'), status='Active',
                                   job__job_category__is_deleted=False)

    def get(self, request, *args, **kwargs):
        if request.query_params.get('job_id'):
            serializer = self.list(request, *args, **kwargs)
            if serializer.data:
                return Response({"status": True, "message": "bids on this job", "data": serializer.data})
            else:
                return Response({"status": False, "message": "No bids"})
        else:
            return Response({"status": False, "message": "enter job_id in query params"})

    def post(self, request, *args, **kwargs):
        job_obj = request.POST.get('job_id')
        offer_amount = request.POST.get('offer_amount')
        if Bids.objects.filter(job_id=job_obj, sp=request.user, job__job_category__is_deleted=False).exists():
            # Bids.objects.filter(job_id=job_obj, sp=request.user, job__job_category__is_deleted=False). \
            #     update(price=offer_amount)
            Bids.objects.filter(job_id=job_obj, sp=request.user, job__job_category__is_deleted=False). \
                update(price=1)
            return Response({"status": True, "message": "Your offer has been updated"})
        if not offer_amount:
            return Response({"status": False, "message": "Please Enter Offer Amount"})
        if request.POST.get('job_id'):
            # create_bid = Bids.objects.create(job_id=job_obj, sp=request.user, price=offer_amount)
            create_bid = Bids.objects.create(job_id=job_obj, sp=request.user, price=1)
            device_list = list(DeviceRegistration.objects.filter(user=create_bid.job.ssid_id)
                               .values_list('device_id', flat=True).distinct())
            if len(device_list) != 0:
                payload = {}
                payload['type'] = 'Bid'
                payload['type_id'] = create_bid.job_id
                send_notification(sender=Bids, message_title='Mooner',
                                  message_body='You have received quote',
                                  extra_notification_kwargs=payload, user=create_bid.job.ssid_id, list_of_devices=device_list,
                                  user_type='SS')
            return Response({"status": True, "message": "Bids placed successfully"})
        return Response({"status": False, "message": "Please Enter Job ID"})


class FilterSp(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = FilterSPSerializer

    def get_queryset(self):
        sp_services = Spservices.objects.filter(s_cat_parent__is_deleted=False, s_cat_parent=self.request.data.get('cat_child_id'), budget__range=[self.
                                                request.data.get('min_budget'), self.
                                             request.data.get('max_budget')
                                                            ]).\
                        annotate(rating=Avg('s_cat_parent__booking_category_id__booking__star')).exclude(s_user=self.
                                                                                                         request.user
                                                                                                         ).order_by(self
                                                                                                         .request.
                                                                                                          data.
                                                                                                          get('order'))
        return sp_services

    def post(self, request, *args, **kwargs):

        serializer = self.list(request, *args, **kwargs)
        if serializer.data:
            return Response({"status": True, "message": "list Of Service Providers", "data": serializer.data})
        else:
            return Response({"status": False, "message": "Service Providers not available of this services", "data": []}
                            )


class UpdateBooking(APIView):
    """
    booking statuses
    ('Completed', 'Completed'),
    ('Cancelled', 'Cancelled'),
    ('Anytime Now', 'Anytime Now'),
    ('At Your Doorstep', 'At Your Doorstep')
    """
    permission_classes = (IsAuthenticated,)

    @staticmethod
    def post(request):
        notification_body = ''
        if request.POST:
            if request.POST.get('order_status') and request.POST.get('booking_id'):
                if request.POST.get('order_status') == 'Anytime Now' or request.POST.get('order_status') == \
                        'At Your Doorstep':
                    booking_obj = Booking.objects.filter(id=request.POST.get('booking_id')).first()
                    if booking_obj:
                        Booking.objects.filter(id=request.POST.get('booking_id')) \
                            .update(order_status=request.POST.get('order_status'))
                        job_data = Jobs.objects.filter(id=booking_obj.job_id, job_category__is_deleted=False). \
                            annotate(is_rated=Value(False, output_field=BooleanField())). \
                            values('id', 'job_description', 'budget', 'is_rated',
                                   'job_status', 'ssid', 'sp', 'schedule', 'image_urls',
                                   category_name=F('job_cat_child__name'),
                                   booking_schedule=F('booking_job_id__end_date'),
                                   booking_id=F('booking_job_id__id'),
                                   booking_status=F('booking_job_id__order_status')
                                   )
                        device_list = list(
                            DeviceRegistration.objects.filter(user=booking_obj.ss).values_list('device_id', flat=True)
                                .distinct())
                        if request.POST.get('order_status') == 'Anytime Now':
                            # 'Provider has started your job'
                            notification_body = 'Mooner is enroute to your premises'
                        else:
                            notification_body = 'Mooner Has Reached Your Doorstep'

                        if len(device_list) != 0:
                            payload = {}
                            payload['type'] = 'Booking'
                            payload['type_id'] = booking_obj.job_id
                            send_notification(sender=Bids, message_title='Mooner',
                                              message_body=notification_body,
                                              extra_notification_kwargs=payload, user=booking_obj.ss.id, user_type='SS',
                                              list_of_devices=device_list)
                        return Response({"status": True, "message": "Booking successfully updated",
                                         "data": job_data})
                    else:
                        return Response({"status": False, "message": "Booking does not exists",
                                         })
                else:
                    return Response({"status": True, "message": "order_status should be 'Anytime Now' or"
                                                                " 'At Your Doorstep'",
                                     })

            else:
                return Response({"status": False, "message": "order_status and booking_id is required"
                                 })
        else:
            return Response({"status": False, "message": "order_status is required"})


class SSAcknowledge(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Booking.objects.filter(category__is_deleted=False).order_by('-id')
    serializer_class = PaymentAcknowledgeSerializer

    @staticmethod
    @exception_handler
    def post(request, *args, **kwargs):
        with transaction.atomic():
            stripe.api_key = STRIPE_API_KEY
            serializer = PaymentAcknowledgeSerializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                if 'error' in e.args[-1]:
                    return Response({'status': False, 'message': e.args[-1].get('error')[0]})
                else:
                    return Response({'status': False, 'message': 'id is not correct'})

            if not Booking.objects.filter(id=serializer.validated_data.get('booking_id'), ss=request.user):
                return Response({'status': False, 'message': "User does used not as SS in that booking"})
            booking = Booking.objects.get(id=serializer.validated_data.get('booking_id'))
            stripe_booking = StripeBooking.objects.get(booking_id=booking.id)
            charge = stripe.Charge.capture(stripe_booking.charge_id)
            transaction_id = charge.balance_transaction
            transaction_details = stripe.BalanceTransaction.retrieve(
                transaction_id
            )
            sp_added_price = SPAddPrice.objects.filter(booking_id=booking.id, payment_status='Accept')
            sum_of_budgets = 0
            if sp_added_price.exists():
                for i in sp_added_price:
                    charge_item = stripe.Charge.capture(i.charge_id)
                    charge_trans_id = charge_item.balance_transaction
                    item_trans_details = stripe.BalanceTransaction.retrieve(
                        charge_trans_id
                    )
                    charge_amount = item_trans_details.net
                    i.add_price_is_payment = True
                    i.save()
                    sum_of_budgets += charge_amount
            total_budget = transaction_details.net + sum_of_budgets
            amount = convert_dollars(total_budget)
            # if charge.status == 'succeeded':
                # transaction_details = stripe.BalanceTransaction.retrieve(
                #     transaction_id,
                # )
            send_referrals_earnings(amount, booking.id)
            Booking.objects.filter(id=booking.id, ss=request.user).update(is_payment=True)
            seeker_data = Booking.objects.filter(id=booking.id, category__is_deleted=False).annotate(
                reviews=Count('ss__rated_to_in_rating__feedback'),
                rating=Avg('ss__rated_to_in_rating__star')).values(
                'reviews', 'rating', 'budget', 'order_status', 'is_payment',
                category_name=F('cat_child_id__name'),
                seeker_name=F('ss__first_name'),
                seeker_image=F('ss__profile__profile_image'),
            ),
            service_id = Spservices.objects.filter(s_cat_parent__is_deleted=False,
                                                   s_cat_parent=booking.cat_child_id,
                                                   s_user=booking.sp).values('id')
            base_url = os.getenv('MOONER_MEDIA_BUCKET_URL')
            sp_data = Booking.objects.filter(id=booking.id).annotate(
                sp_star=Coalesce(Avg('sp__rated_to_in_rating__star'), 0)). \
                annotate(count_rating=Count('sp__rated_to_in_rating__star')).\
                annotate(sp_profile_image=Concat(Value(base_url), F('sp__profile__profile_image'))). \
                values('sp_star', 'sp_profile_image', 'count_rating', 'end_date__date', sp_name=F('sp__first_name'), ss_name=F('ss__first_name'),
                       job_description=F('job__job_description')).first()
            email_data = {
                'category': booking.category.name,
                'budget': booking.budget,
                'booking_id': booking.id,
                'sp_rating': sp_data.get('sp_star'),
                'count_rating': sp_data.get('count_rating'),
                'job_description': sp_data.get('job_description'),
                'sp_profile_image': sp_data.get('sp_profile_image'),
                'completion_date': sp_data.get('end_date__date'),
                'sp_name': sp_data.get('sp_name'),
                'ss_name': sp_data.get('ss_name'),
                'amount': amount,
            }
            send_email_template(template_name='email_templates/new_invoice.html',
                                subject_msg="Invoice has been sent",
                                email=request.user.email,
                                data=email_data)
            data = {
                "seeker_data": seeker_data[0],
                "service_id": service_id
            }

            device_list = list(DeviceRegistration.objects.filter(user=booking.sp).
                               values_list('device_id', flat=True).distinct())
            if len(device_list) != 0:
                payload = dict()
                payload['type'] = 'Booking'
                payload['type_id'] = booking.job_id
                send_notification(sender=Booking, message_title='Mooner',
                                  message_body='your payment has been Released',
                                  extra_notification_kwargs=payload, user=booking.sp.id, user_type='SP',
                                  list_of_devices=device_list)
            return Response({"status": True, "data": data})

        # return Response({"status": False, "message": "Payment has not captured"})


class AddExtraBudget(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SPAddPrice.objects.all()
    serializer_class = AddExtraPriceSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
            serializer.save(sp=request.user)
            device_list = list(DeviceRegistration.objects.filter(user=serializer.data.get('ss')).
                               values_list('device_id', flat=True).distinct())
            booking_obj = Booking.objects.filter(id=serializer.data.get('booking_id')).first()
            if len(device_list) != 0:
                payload = dict()
                payload['type'] = 'Booking'
                payload['type_id'] = booking_obj.job_id
                send_notification(sender=Booking, message_title='Mooner',
                                  message_body='A Price change request has been initiated by your Service Provider, would you like to accept?',
                                  extra_notification_kwargs=payload, user=serializer.data.get('ss'), user_type='SS',
                                  list_of_devices=device_list)

            return Response({"status": True, "message": "Price added successfully", "data": serializer.data})
        except Exception as e:
            if 'error' in e.args[-1]:
                return Response({"status": False, "message": e.args[-1].get('error')[-1]})
            else:
                return Response({"status": False, "message": "In correct data sent"})
# serializer = self.update(request, *args, **kwargs)


class UpdateExtraBudget(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SPAddPrice.objects.all()
    serializer_class = UpdateExtraPriceSerializer

    def put(self, request, *args, **kwargs):
        kwargs['partial'] = True
        price_obj = self.get_object()
        if not price_obj.payment_status == 'Accept':
            serializer = self.update(request, *args, **kwargs)
            return Response({"status": True, "message": "Updated successfully", "data": serializer.data})
        else:
            return Response({"status": True, "message": "Cannot changed the amount of accepted budget"})

    def get(self, request, *args, **kwargs):
        obj = self.retrieve(request, *args, **kwargs)
        return Response({"status": True, "message": "object get successfully", "data": obj.data})

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response({"status": True, "message": "object deleted successfully"})


class BookingExtraPayment(APIView):
    permission_classes = (IsAuthenticated,)
    queryset = SPAddPrice.objects.all()
    serializer_class = AddExtraPriceSerializer

    @staticmethod
    def post(request):
        if request.data.get('booking_id'):
            data_obj = SPAddPrice.objects.filter(booking_id=request.data.get('booking_id'))
            try:
                serializer = AddExtraPriceSerializer(data_obj, many=True)
                return Response({"status": True, "data": serializer.data})
            except Exception as e:
                if 'error' in e.args[-1]:
                    return Response({"status": False, "message": e.args[-1].get('error')[-1]})
                else:
                    return Response({"status": False, "message": "In correct data sent"})
        else:
            return Response({"status": False, "message": "Booking_id is required"})


class SSActionExtraPayment(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SPAddPrice.objects.all()
    serializer_class = SSActionExtraPriceSerializer

    @exception_handler
    def put(self, request, *args, **kwargs):
        with transaction.atomic():
            kwargs['partial'] = True
            action = request.data.get('action')
            serializer = self.get_serializer(data=request.data)
            if action.lower() == 'reject':
                try:
                    serializer.is_valid(raise_exception=True)
                    SPAddPrice.objects.filter(id=serializer.data.get('sp_add_price_id')).delete()
                    return Response({"status": True, "data": "Request rejected"})
                except Exception as e:
                    if 'error' in e.args[-1]:
                        return Response({"status": False, "message": e.args[-1].get('error')[-1]})
                    else:
                        return Response({"status": False, "message": "In correct data sent"})
            elif action.lower() == 'accept':
                if request.data.get('stripe_token'):
                    try:
                        serializer.is_valid(raise_exception=True)
                        price_obj = SPAddPrice.objects.filter(id=serializer.data.get('sp_add_price_id')).first()
                        customer = StripeCustomer.objects.filter(user=request.user)
                        stripe.api_key = STRIPE_API_KEY
                        dollar_amount = float(price_obj.add_amount)
                        cents = round(int(dollar_amount * 100))
                        card = stripe.Customer.create_source(
                            customer.first().stripe_customer,
                            source=request.data.get('stripe_token'),
                        )
                        charge = stripe.Charge.create(
                            amount=cents,
                            currency='sgd',
                            source=card.id,
                            customer=customer.first().stripe_customer,
                            capture=False,
                        )

                        price_obj.charge_id = charge.id
                        price_obj.payment_status = 'Accept'
                        price_obj.save()
                        added_amount = SPAddPrice.objects.filter(
                            booking_id=serializer.data.get('booking_id')).aggregate(Sum('add_amount'
                                                                                        ))
                        total_amount = added_amount.get('add_amount__sum') + price_obj.booking.budget
                        device_list = list(DeviceRegistration.objects.filter(user=price_obj.sp)
                                           .values_list('device_id', flat=True).distinct())
                        if len(device_list) != 0:
                            payload = dict()
                            payload['type'] = 'Booking'
                            payload['type_id'] = price_obj.booking.job_id
                            notification_msg = "You price change has been accepted.New Price: " + str(total_amount)
                            send_notification(sender=Booking, message_title='Mooner',
                                              message_body=notification_msg,
                                              extra_notification_kwargs=payload, user=price_obj.sp_id,
                                              user_type='SP',
                                              list_of_devices=device_list)
                        return Response({"status": True, "message": "Request Accept"})

                    except Exception as e:
                        if 'error' in e.args[-1]:
                            return Response({"status": False, "message": e.args[-1].get('error')[-1]})
                        else:
                            return Response({"status": False, "message": "In correct data sent"})
                else:
                    return Response({"status": False, "message": "stripe token is required"})
            else:
                return Response({"status": False, "message": "Incorrect action"})


class DisputeViews(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = DisputeSerializer
    queryset = Dispute.objects.all()

    def create(self, request, *args, **kwargs):
        if request.user.profile.user_type == 'SS':
            serializer = self.get_serializer(data=request.data)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            serializer.save()
            return Response({"status": True, "message": "Dispute has been created successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            data = Dispute.objects.filter(dispute_status='Pending',).\
                values('id', 'dispute_status', 'booking_id', 'ss_created_at', ss_name=F('booking__ss__username'),
                       sp_name=F('booking__sp__username'), category_name=F('booking__category__name'),
                       booking_date=F('booking__booking_date'), )
            result = paginator.paginate_queryset(data, request)
            # serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(result)
        raise exceptions.PermissionDenied()

    def retrieve(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            serializer = self.get_serializer(instance)
            return Response({"status": True, "message": "Dispute", "data": serializer.data})
        raise exceptions.PermissionDenied()

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"status": True, "message": "Dispute has been updated successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "Dispute successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()

    def approved_dispute(self, request):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            data = self.queryset.filter(dispute_status='Approved',).\
                values('id', 'dispute_status', 'booking_id', 'ss_created_at', 'admin_updated_at',
                       ss_name=F('booking__ss__username'), sp_name=F('booking__sp__username'),
                       category_name=F('booking__category__name'), booking_date=F('booking__booking_date'), )
            result = paginator.paginate_queryset(data, request)
            # serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(result)
        raise exceptions.PermissionDenied()

    def rejected_dispute(self, request):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            data = self.queryset.filter(dispute_status='Rejected', ). \
                values('id', 'dispute_status', 'booking_id', 'ss_created_at', 'admin_updated_at',
                       ss_name=F('booking__ss__username'), sp_name=F('booking__sp__username'),
                       category_name=F('booking__category__name'), booking_date=F('booking__booking_date'), )
            result = paginator.paginate_queryset(data, request)
            # serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(result)
        raise exceptions.PermissionDenied()

    def dispute_history(self, request):
        if request.user.is_superuser:
            booking_id = request.data.get('booking_id')
            if not booking_id:
                return Response({"status": False, "message": "booking id is required"})
            data = self.queryset.filter(booking=booking_id).\
                values('id', 'dispute_status', 'booking_id', 'ss_created_at', 'admin_updated_at',
                       ss_name=F('booking__ss__username'), sp_name=F('booking__sp__username'),
                       category_name=F('booking__category__name'), booking_date=F('booking__booking_date'), )
            return Response({"status": True, "message": "Dispute", "data": data})
            # serializer = self.serializer_class(result, many=True)
        raise exceptions.PermissionDenied()


class RequestTipBySp(generics.UpdateAPIView):
    permission_classes = [IsAuthenticated]
    queryset = Booking.objects.filter(category__is_deleted=False)
    serializer_class = BookingSerializer
    http_method_names = ["put"]

    def update(self, request, *args, **kwargs):
        booking = self.get_object()
        if booking.ss == request.user:
            booking.is_tip_request = False
            booking.save()
            return Response({"status": True, "message": "is_tip_request status had changed."})
        elif booking.sp == request.user:
            tip_count = booking.tip_request_count
            booking.is_tip_request = True
            booking.tip_request_count = tip_count + 1
            if booking.tip_request_count == 1:
                booking.again_tip_request = False
            booking.save()
            device_list = list(DeviceRegistration.objects.filter(user=booking.ss).values_list('device_id', flat=True))
            if len(device_list) != 0:
                payload = {}
                payload['type'] = 'Booking'
                payload['type_id'] = booking.job_id
                send_notification(sender=Booking, message_title='Mooner',
                                  message_body='You have got a tip request from Mooner',
                                  extra_notification_kwargs=payload, user=booking.ss_id, list_of_devices=device_list,
                                  user_type='SS')
            return Response({"status": True, "message": "Tip has been requested."})
        raise exceptions.PermissionDenied()


class TipViews(viewsets.ModelViewSet):

    permission_classes = [IsAuthenticated]
    serializer_class = TipSerializer
    queryset = Tip.objects.all()
    http_method_names = ['get', 'post', 'delete', 'head']

    def create(self, request, *args, **kwargs):
        if request.user.profile.user_type == 'SS':
            serializer = self.get_serializer(data=request.data)

            try:
                serializer.is_valid(raise_exception=True)
                attach_card(token=request.data.get('stripe_token'), user=request.user.id, email=request.user.email)
                card = get_card(token=request.data.get('stripe_token'))
                customer = StripeCustomer.objects.filter(user=request.user).first()
                amount = create_charge(amount=request.data.get('amount'), source=card,
                                       customer=customer.stripe_customer)
                usd_to_mnr = load_mnr_token(amount)
                booking = Booking.objects.filter(id=request.data.get('booking_id')).first()
                if CreateWallet.objects.filter(user_id=booking.sp_id).exists():
                    sp_account = CreateWallet.objects.get(user_id=booking.sp_id)
                    mnr = send_token(amount=usd_to_mnr, to_public_address=sp_account.wallet_public_key)
                    if mnr:
                        MLNTokensEarn.objects.create(sender_id=booking.ss_id, recevier_id=booking.sp_id,
                                                     )
                else:
                    MLNTokenPandingHistory.objects.create(user_id=booking.sp_id,
                                                          token=usd_to_mnr)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            serializer.save()
            booking.is_tip_request = False
            booking.save()
            device_list = list(DeviceRegistration.objects.filter(user=booking.sp).values_list('device_id', flat=True))
            if len(device_list) != 0:
                payload = {}
                payload['type'] = 'Booking'
                payload['type_id'] = booking.job_id
                send_notification(sender=Booking, message_title='Mooner',
                                  message_body='Seeker has added a tip for you',
                                  extra_notification_kwargs=payload, user=booking.sp_id, list_of_devices=device_list,
                                  user_type='SP')
            return Response({"status": True, "message": "Tip has been created successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def list(self, request, *args, **kwargs):
        paginator = PageNumberPagination()
        paginator.page_size = 10
        data = Tip.objects.all().values()
        result = paginator.paginate_queryset(data, request)
        # serializer = self.serializer_class(result, many=True)
        return paginator.get_paginated_response(result)

    def destroy(self, request, *args, **kwargs):
        if request.user.is_superuser:
            instance = self.get_object()
            self.perform_destroy(instance)
            return Response({"status": True, "message": "Tip successfully deleted!"})
        raise exceptions.PermissionDenied()

    def perform_destroy(self, instance):
        instance.delete()


class AdminConvenienceFeeViews(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminConvenienceFeeSerializer
    queryset = AdminConvenienceFee.objects.all()
    http_method_names = ['get', 'post', 'put']

    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            serializer = self.serializer_class(self.queryset.first())
            return Response({"status": True, "message": "Admin Convenience Fee", "data": serializer.data})
        raise exceptions.PermissionDenied()

    def update(self, request, *args, **kwargs):
        if request.user.is_superuser:
            partial = kwargs.pop('partial', False)
            instance = self.get_object()
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            try:
                serializer.is_valid(raise_exception=True)
            except Exception as e:
                error = {"status": False, "message": e.args[0]}
                return Response(error)
            self.perform_update(serializer)

            if getattr(instance, '_prefetched_objects_cache', None):
                # If 'prefetch_related' has been applied to a queryset, we need to
                # forcibly invalidate the prefetch cache on the instance.
                instance._prefetched_objects_cache = {}
            return Response({"status": True, "message": "Admin Convenience Fee has been updated successfully.",
                             "data": serializer.data})
        raise exceptions.PermissionDenied()

    def perform_update(self, serializer):
        serializer.save()

    def partial_update(self, request, *args, **kwargs):
        kwargs['partial'] = True
        return self.update(request, *args, **kwargs)


class AdminTransactionListViews(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    serializer_class = AdminTransactionListSerializer
    queryset = AdminTransactionList.objects.all().order_by('-id')
    http_method_names = ['get']

    def list(self, request, *args, **kwargs):
        if request.user.is_superuser:
            paginator = PageNumberPagination()
            paginator.page_size = 10
            result = paginator.paginate_queryset(self.queryset, request)
            serializer = self.serializer_class(result, many=True)
            return paginator.get_paginated_response(serializer.data)
        raise exceptions.PermissionDenied()


class change_sp_status(viewsets.ModelViewSet):
    permission_classes = [IsAuthenticated]
    queryset = Spservices.objects.all()
    serializer_class = SpServiceSerializer
    http_method_names = ["patch"]

    def update(self, request, *args, **kwargs):
        service = self.get_object()
        status = request.data.get('status')
        try:
            if service.s_user == request.user or request.user.is_superuser:
                if status:
                    if request.user.is_superuser:
                        service.in_active_by = 'Admin'
                        service.is_active = status
                        service.save()
                        return Response({"status": True, "message": "is_active status had changed."})
                    else:
                        service.in_active_by = 'SP'
                        service.is_active = status
                        service.save()
                        return Response({"status": True, "message": "is_active status had changed."})
                else:
                    return Response({"status": False, "message": "provide a status."})
            raise exceptions.PermissionDenied()

        except:
            return Response({"status": False, "message": "provide a status True or False."})


class UpdateBookingDateInChat(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Booking.objects.filter(category__is_deleted=False).order_by('-id')
    serializer_class = BookingDateSerializer

    def get_queryset(self):
        booking = Booking.objects.filter(id=self.kwargs['pk']).all()
        return booking

    def put(self, request, *args, **kwargs):
        try:
            # serializer = self.get_serializer(data=request.data)
            # serializer.is_valid(raise_exception=True)
            self.update(request, partial=True)
            obj = self.get_object()
            serializer = self.serializer_class(obj)
            return Response({"status": True, "message": "Booking date has been updated.", "data": serializer.data})
        except Exception as e:
            error = {"status": False, "message": e.args[0]}
            return Response(error)

    def get(self, request, *args, **kwargs):
        obj = self.get_object()
        serializer = self.serializer_class(obj)
        return Response({"status": True, "data": serializer.data})
