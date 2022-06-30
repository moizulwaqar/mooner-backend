from itertools import chain

from django.db import transaction
from django.db.models.functions import Coalesce
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated
from payments.models import StripeCustomer
from .serializers import *
from rest_framework.response import Response
from django.db.models import F, Avg, Count, Q, IntegerField, Subquery, FloatField, Case, When, Value, BooleanField, Sum
from rest_framework.views import APIView
from mooner_backend.utils import soft_delete, restore_from_softdelete, permanent_delete, pagination,  send_email_template
from booking.utils import ss_booking_cancel, sp_booked_or_not, sp_booking_cancel, send_referrals_earnings
from django.core.exceptions import ObjectDoesNotExist
from notification.utils import *
import stripe
from mooner_backend.settings import STRIPE_API_KEY
from payments.utils import create_booking, attach_card, get_card
from payments.payments_decoraters import *


class JobPostedBySeeker(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Jobs.objects.filter(job_category__is_deleted=False).order_by('-id')
    serializer_class = JobsSerializer

    def post(self, request, *args, **kwargs):

        job_ques_ans_data = request.data.get('job_answers')
        serializer = JobsSerializer(data=request.data)
        sp = request.data.get('sp_id')
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            error = {"status": False, "message": e.args[0], "data": ""}
            return Response(error)

        if job_ques_ans_data:
            job = serializer.save()
            for question_id, answer in job_ques_ans_data.items():
                question = CategoryQuestions.objects.get(id=question_id)
                if question.question_type.lower() == "text":
                    Answer.objects.create(question_id=question,
                                          cat_parent_id=job.job_category,
                                          child_category=job.job_cat_child,
                                          answer=answer,
                                          jobs_id=job)
                elif question.question_type.lower() == "radio":
                    Answer.objects.create(question_id=question,
                                          cat_parent_id=job.job_category,
                                          child_category=job.job_cat_child,
                                          answer=answer,
                                          jobs_id=job)
                elif question.question_type.lower() == "file":
                    Answer.objects.create(question_id=question,
                                          cat_parent_id=job.job_category,
                                          child_category=job.job_cat_child,
                                          answer=answer,
                                          jobs_id=job)
                elif question.question_type.lower() == "image":
                    Answer.objects.create(question_id=question,
                                          cat_parent_id=job.job_category,
                                          child_category=job.job_cat_child,
                                          answer=answer,
                                          jobs_id=job)
                else:
                    return Response({"status": False, "message": "Question must be of type text or radio or file or image"})
        else:
            return Response({"status": False, "message": "Answers are not given."})
        if sp:
            job.job_status = "Pending"
            job.sp_id = sp
            job.save()
            device_list = list(DeviceRegistration.objects.filter(user=job.sp_id)
                               .values_list('device_id', flat=True).distinct())
            if len(device_list) != 0:
                payload = {}
                payload['type'] = 'Job'
                payload['type_id'] = job.id
                send_notification(sender=Jobs, message_title='Mooner',
                                  message_body='You have received offer',
                                  extra_notification_kwargs=payload, user=job.sp_id, list_of_devices=device_list,
                                  user_type='SP')
        else:
            users_list = Spservices.objects.filter(s_cat_parent=job.job_cat_child).values_list('s_user', flat=True)
            devices = list(DeviceRegistration.objects.filter(user__in=users_list).values_list('device_id',
                                                                                         flat=True).distinct())
            payload = {}
            payload['type'] = 'No Action'
            payload['type_id'] = job.id
            send_notification(sender=Jobs, message_title='Mooner',
                              message_body='Job has been created in your registered category' + ' ' +
                                           job.job_cat_child.name,
                              extra_notification_kwargs=payload, user=None, list_of_devices=devices,
                              user_type='SP')

        posted_answers = Answer.objects.filter(jobs_id=job).values(job_question=
                                                                   F('question_id__question_text'),
                                                          job_answer=F('answer'))



        data = {
            "job": serializer.data,
            "job_answers": posted_answers
        }

        return Response({"status": True, "message": "Job posted successfully.", "data": data})


class EditJobPostedBySeeker(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Jobs.objects.all().order_by('-id')
    serializer_class = JobsSerializer

    def put(self, request, *args, **kwargs):

        job = self.get_object()
        job_ques_ans_data = request.data.get('job_answers')
        serializer = JobsSerializer(job, data=request.data)
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            error = {"status": False, "message": e.args[0], "data": ""}
            return Response(error)

        if job_ques_ans_data:
            serializer.save()
            for question_id, answer in job_ques_ans_data.items():
                question = CategoryQuestions.objects.get(id=question_id)
                if question.question_type.lower() == "text":

                    try:
                        job_answer = Answer.objects.get(question_id=question.id, jobs_id=job)
                        job_answer.answer = answer
                        job_answer.save()

                    except:
                        Answer.objects.create(question_id=question,
                                              cat_parent_id=job.job_category,
                                              child_category=job.job_cat_child,
                                              answer=answer,
                                              jobs_id=job)

                elif question.question_type.lower() == "radio":
                    try:
                        job_answer = Answer.objects.get(question_id=question.id, jobs_id=job, cat_parent_id__is_deleted=False)
                        job_answer.answer = answer
                        job_answer.save()

                    except:
                        Answer.objects.create(question_id=question,
                                              cat_parent_id=job.job_category,
                                              child_category=job.job_cat_child,
                                              answer=answer,
                                              jobs_id=job)

                elif question.question_type.lower() == "image":
                    try:
                        job_answer = Answer.objects.get(question_id=question.id, jobs_id=job, cat_parent_id__is_deleted=False)
                        job_answer.answer = answer
                        job_answer.save()

                    except:
                        Answer.objects.create(question_id=question,
                                              cat_parent_id=job.job_category,
                                              child_category=job.job_cat_child,
                                              answer=answer,
                                              jobs_id=job)

                elif question.question_type.lower() == "file":
                    try:
                        job_answer = Answer.objects.get(question_id=question.id, jobs_id=job, cat_parent_id__is_deleted=False)
                        job_answer.answer = answer
                        job_answer.save()

                    except:
                        Answer.objects.create(question_id=question,
                                              cat_parent_id=job.job_category,
                                              child_category=job.job_cat_child,
                                              answer=answer,
                                              jobs_id=job)
                else:
                    return Response({"status": False, "message": "Question must be of type text, radio, image or file"})
        else:
            return Response({"status": False, "message": "Answers are not given."})

        posted_answers = Answer.objects.filter(jobs_id=job, cat_parent_id__is_deleted=False).values(job_question=
                                                                   F('question_id__question_text'),
                                                                   job_answer=F('answer'))
        data = {
            "job": serializer.data,
            "job_answers": posted_answers
        }
        return Response({"status": True, "message": "Job updated successfully.", "data": data})

    def get(self, request, *args, **kwargs):

        job = self.get_object()

        bid_data = Bids.objects.filter(job=job, sp=job.sp).values('id', 'sp', 'job', 'price', 'time', 'status',
                                                                        job_description=F('job__job_description'),
                                                                        job_budget=F('job__budget'), ssid=F('job__ssid')
                                                                        , schedule=F('job__schedule'),
                                                                        image_urls=F('job__image_urls'),
                                                                        category_name=F('job__job_cat_child__name'))

        job_data = Jobs.objects.filter(id=job.id, job_category__is_deleted=False,
                                       booking_job_id__booking__rated_by=request.user). \
            annotate(
            is_rated=Case(When(booking_job_id__booking__isnull=False, then=Value(True)), default=Value(False),
                          output_field=BooleanField())).distinct(). \
            annotate(
            is_tip_given=Case(When(booking_job_id__booking_in_tips__booking__isnull=False, then=Value(True)),
                              default=Value(False),
                              output_field=BooleanField())).distinct(). \
            values('id', 'job_description', 'budget', 'is_rated', 'is_tip_given',
                   'job_status', 'ssid', 'sp', 'schedule', 'image_urls', 'address', 'floor_no', 'unit_no', 'longitude',
                   'latitude', 'job_category', 'job_cat_child',
                   category_name=F('job_cat_child__name'),
                   booking_schedule=F('booking_job_id__end_date'),
                   booking_id=F('booking_job_id__id'),
                   booking_status=F('booking_job_id__order_status'),
                   is_payment=F('booking_job_id__is_payment'),
                   is_tip_request=F('booking_job_id__is_tip_request'),
                   again_tip_request=F('booking_job_id__again_tip_request'),
                   )
        if not job_data:
            job_data = Jobs.objects.filter(id=job.id, job_category__is_deleted=False). \
                annotate(is_rated=Value(False, output_field=BooleanField())). \
                annotate(
                is_tip_given=Case(When(booking_job_id__booking_in_tips__booking__isnull=False, then=Value(True)),
                                  default=Value(False),
                                  output_field=BooleanField())). \
                values('id', 'job_description', 'budget', 'is_rated', 'is_tip_given',
                       'job_status', 'ssid', 'sp', 'schedule', 'image_urls', 'address', 'floor_no', 'unit_no',
                       'longitude', 'latitude', 'job_category', 'job_cat_child',
                       category_name=F('job_cat_child__name'),
                       booking_schedule=F('booking_job_id__end_date'),
                       booking_id=F('booking_job_id__id'),
                       booking_status=F('booking_job_id__order_status'),
                       is_payment=F('booking_job_id__is_payment'),
                       is_tip_request=F('booking_job_id__is_tip_request'),
                       again_tip_request=F('booking_job_id__again_tip_request'),
                       )
        posted_answers = Answer.objects.filter(jobs_id=job, cat_parent_id__is_deleted=False).values('answer',
                                                                                                    question_type=
                                                                                                    F('question_id__question_type'),
                                                                                                    question_text=
                                                                   F('question_id__question_text'),

                                                                   questionid=F('question_id__id'),
                                                                   r_text_one=F('question_id__r_text_one'),
                                                                   r_text_two=F('question_id__r_text_two'),
                                                                   r_text_three=F('question_id__r_text_three'),
                                                                   r_text_four=F('question_id__r_text_four'),
                                                                   r_text_five=F('question_id__r_text_five'),
                                                                   r_text_six=F('question_id__r_text_six'))
        booking_count1 = Jobs.objects.filter(ssid=job.ssid, id=job.id, job_category__is_deleted=False).annotate(booking_count=Count
        ('ssid__booking_ss_id',
         filter=Q
         (ssid__booking_ss_id__order_status
          ='Completed')))
        # rating1 = Jobs.objects.filter(ssid=job.ssid, id=job.id, job_category__is_deleted=False).annotate(rating=
        #                                                                  Avg('ssid__rated_to_in_rating__star'))
        rating1 = Booking.objects.filter(job_id=job.id, is_deleted=False).annotate(rating=Coalesce(Sum(
            Case(
                When(booking__rated_to=job.ssid, then='booking__star'),
                output_field=FloatField()
            )
        ), 0))
        ss_user = Jobs.objects.filter(ssid=job.ssid, id=job.id, job_category__is_deleted=False).annotate(booking_count=Subquery(
            booking_count1.values('booking_count'),
            output_field=IntegerField()),
            rating=Subquery(rating1.values('rating'),
                            output_field=FloatField())) \
            .values(
            'ssid_id', 'booking_count', 'rating', 'budget',
            seeker_name=F('ssid__first_name'),
            seeker_image=
            F('ssid__profile__profile_image'))

        booking_count2 = Jobs.objects.filter(sp=job.sp, id=job.id, job_category__is_deleted=False).annotate(
            booking_count=Count
            ('sp__booking_sp_id',
             filter=Q
             (sp__booking_sp_id__order_status
              ='Completed')))
        # rating2 = Jobs.objects.filter(ssid=job.sp, id=job.id, job_category__is_deleted=False).annotate(rating=
        #                                                                                                  F('ssid__rated_to_in_rating__star'))
        rating2 = Booking.objects.filter(job_id=job.id, is_deleted=False).annotate(rating=Coalesce(Sum(
            Case(
                When(booking__rated_to=job.sp, then='booking__star'),
                output_field=FloatField()
            )
        ), 0))
        sp_user = Jobs.objects.filter(sp=job.sp, id=job.id, job_category__is_deleted=False).annotate(booking_count=Subquery(
                booking_count2.values('booking_count'),
                output_field=IntegerField()),
                rating=Subquery(rating2.values('rating'),
                                output_field=FloatField())) \
                .values(
                'booking_count', 'rating', 'budget',
                p_id=F('sp__id'),
                provider_name=F('sp__first_name'),
                provider_image=
                F('sp__profile__profile_image'))
        booking_obj = Booking.objects.filter(job_id=job.id)
        get_extra_price = list()
        if booking_obj.exists():
            book_obj = booking_obj.first()
            get_extra_price = SPAddPrice.objects.filter(booking=book_obj.id).values(
                'id', 'description', 'add_amount', 'booking_id', 'ss', 'sp', 'payment_status')
        update_price_status = False
        if booking_obj.exists():
            book_obj = booking_obj.first()
            pending_obj = SPAddPrice.objects.filter(booking=book_obj.id, payment_status='Pending').values(
                'id', 'description', 'add_amount', 'booking_id', 'ss', 'sp', 'payment_status')
            if pending_obj.exists():
                update_price_status = True


        data = {
            "user": ss_user,
            "sp_user": sp_user,
            "job": job_data,
            "job_answers": posted_answers,
            "bid_data": bid_data,
            "add_extra": get_extra_price,
            "update_price_status": update_price_status
        }
        return Response({"status": True, "data": data})

    def delete(self, request, *args, **kwargs):
        print("urls -----------")
        if 'pk' in kwargs:
            job_id = Jobs.objects.filter(id=kwargs.get('pk'))
            booking_obj = Booking.objects.filter(job_id=kwargs.get('pk'))
            if booking_obj.exists():
                return Response({"status": False, "message": "job is in the booking so you cannot delete this"})
            if job_id.exists():
                Jobs.all_objects.filter(id=kwargs.get('pk')).hard_delete()
                return Response({"status": True, "message": "Job deleted successfully"})
            else:
                return Response({"status": True, "message": "Job id does not exist"})
        # else:
        #     return Response({"status": False, "message": "Please give the id in query params"})


class ProviderActionOnPostedJob(generics.RetrieveAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Jobs.objects.filter(job_category__is_deleted=False).order_by('-id')
    serializer_class = JobsSerializer

    @exception_handler
    def post(self, request, *args, **kwargs):

        if request.data:
            with transaction.atomic():
                job = self.get_object()
                sp_action = request.data.get('sp_action')
                sp_id = request.data.get('sp_id')
                bid_id = request.data.get('bid_id')

                if sp_action.lower() == "accept":
                    if Booking.objects.filter(job=job, sp=job.sp).exists():
                        return Response({"status": True, "message": "This job is already booked."})
                    if sp_id:
                        bids = Bids.objects.get(id=bid_id, job__job_category__is_deleted=False)
                        created_booking = Booking.objects.create(order_status='Active', job=job, ss=job.ssid,
                                                                 sp_id=sp_id,
                                                                 budget=bids.price,
                                                                 category=job.job_category,
                                                                 cat_child_id=job.job_cat_child)
                        job.job_status = 'Hired'
                        job.sp_id = sp_id
                        job.budget = bids.price
                        job.save()
                        bids.status = 'Hired'
                        bids.save()
                        data = {'category': created_booking.category.name,
                                'budget': created_booking.budget,
                                'booking_id': created_booking.id,
                                'time': created_booking.start_date
                                }
                        # send_email_template(template_name='email_templates/invoice_temp.html',
                        #                     subject_msg="Invoice has been sent",
                        #                     email=request.user.email,
                        #                     data=data)

                        device_list = list(DeviceRegistration.objects.filter(user=created_booking.sp_id)
                                           .values_list('device_id', flat=True).distinct())
                        if len(device_list) != 0:
                            payload = {}
                            # 'you have received order from {}'.format(request.user.first_name),
                            payload['type'] = 'Booking'
                            payload['type_id'] = created_booking.job_id
                            send_notification(sender=Booking, message_title='Mooner',
                                              message_body='you Offer has been accepted',
                                              extra_notification_kwargs=payload, user=created_booking.sp_id,
                                              user_type='SP',
                                              list_of_devices=device_list)
                        stripe.api_key = STRIPE_API_KEY
                        if Jobs.objects.filter(id=job.id, ss_stripe_token=job.ss_stripe_token).exists():
                            card_token = stripe.Token.retrieve(job.ss_stripe_token)
                            if not card_token.used:
                                attach_card(token=job.ss_stripe_token, user=created_booking.ss_id,
                                            email=job.ss_stripe_email)
                                card = get_card(token=job.ss_stripe_token)
                                if StripeCustomer.objects.filter(user_id=created_booking.ss_id).exists():
                                    customer = StripeCustomer.objects.get(user_id=created_booking.ss_id)
                                    create_booking(ss=created_booking.ss_id, sp=created_booking.sp_id,
                                                   amount=bids.price,
                                                   booking_id=created_booking.id, payment_method_id=card,
                                                   customer_id=customer.stripe_customer)
                                else:
                                    return Response({"status": False, "message": "Stripe Customer does not exist!"})
                            else:
                                return Response(
                                    {"status": False, "message": "You cannot use a Stripe token more than once!"})
                        else:
                            return Response({"status": False, "message": "Stripe Source Token does not exist!"})
                        return Response({"status": True, "message": "Job has been accepted"})
                    else:
                        created_booking = Booking.objects.create(order_status='Active', job=job, ss=job.ssid, sp=job.sp,
                                                                 budget=job.budget,
                                                                 category=job.job_category,
                                                                 cat_child_id=job.job_cat_child)
                        job.job_status = 'Hired'
                        job.save()
                        data = {'category': created_booking.category.name,
                                'budget': created_booking.budget,
                                'booking_id': created_booking.id,
                                'time': created_booking.start_date
                                }
                        # send_email_template(template_name='email_templates/invoice_temp.html',
                        #                     subject_msg="Offer has been accepted",
                        #                     email=created_booking.ss.email,
                        #                     data=data)
                        device_list = list(DeviceRegistration.objects.filter(user=created_booking.ss_id).
                                           values_list('device_id', flat=True).distinct())
                        if len(device_list) != 0:
                            payload = {}
                            payload['type'] = 'Booking'
                            payload['type_id'] = created_booking.job_id
                            send_notification(sender=Booking, message_title='Mooner',
                                              message_body='your order has been accepted',
                                              extra_notification_kwargs=payload, user=created_booking.ss_id,
                                              user_type='SS',
                                              list_of_devices=device_list)
                        stripe.api_key = STRIPE_API_KEY
                        if Jobs.objects.filter(id=job.id, ss_stripe_token=job.ss_stripe_token).exists():
                            card_token = stripe.Token.retrieve(job.ss_stripe_token)
                            if not card_token.used:
                                attach_card(token=job.ss_stripe_token, user=created_booking.ss_id,
                                            email=job.ss_stripe_email)
                                card = get_card(token=job.ss_stripe_token)
                                if StripeCustomer.objects.filter(user_id=created_booking.ss_id).exists():
                                    customer = StripeCustomer.objects.get(user_id=created_booking.ss_id)
                                    create_booking(ss=created_booking.ss_id, sp=created_booking.sp_id,
                                                   amount=job.budget,
                                                   booking_id=created_booking.id, payment_method_id=card,
                                                   customer_id=customer.stripe_customer)
                                else:
                                    return Response({"status": False, "message": "Stripe Customer does not exist!"})
                            else:
                                return Response(
                                    {"status": False, "message": "You cannot use a Stripe token more than once!"})
                        else:
                            return Response({"status": False, "message": "Stripe Source Token does not exist!"})
                        return Response({"status": True, "message": "Job has been accepted"})

                if sp_action.lower() == "decline":
                    if bid_id:
                        bid = Bids.objects.get(id=bid_id, job__job_category__is_deleted=False)
                        bid.status = 'InActive'
                        bid.save()
                        device_list = list(
                            DeviceRegistration.objects.filter(user=sp_id).values_list('device_id', flat=True)
                            .distinct())
                        if len(device_list) != 0:
                            payload = {}
                            payload['type'] = 'Bid'
                            payload['type_id'] = bid.job_id
                            send_notification(sender=Bids, message_title='Mooner',
                                              message_body='Your bid has been declined',
                                              extra_notification_kwargs=payload, user=sp_id, user_type='SP',
                                              list_of_devices=device_list)
                        return Response({"status": True, "message": "Job has been declined"})
                    else:
                        job.job_status = 'InActive'
                        job.save()
                        return Response({"status": True, "message": "Job has been declined"})
        else:
            return Response({"status": False, "message": "Please enter requested data"})



class SeekerBookings(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Jobs.objects.filter(job_category__is_deleted=False).order_by('-id')
    serializer_class = JobsSerializer

    def post(self, request, *args, **kwargs):

        status = request.data.get('status')
        column_name = request.data.get('for')

        if status.lower() == "active_bids":
            if column_name == "ss":
                column_name = 'ssid'
                filters = {
                    column_name: request.user
                }
                active_jobs = Jobs.objects.filter(Q(job_status='Active') | Q(job_status='Pending'), **filters) \
                    .annotate(Total_bids=Count('bd_job_id', filter=Q(bd_job_id__status='Active'))). \
                    values('id', 'Total_bids', 'budget', 'job_status',
                           category_name=F('job_cat_child__name'), category_image=F('job_cat_child__category_image'),
                           category_icon=F('job_cat_child__cat_icon'),
                           provider_id=F('sp__id'), seeker_id=F('ssid__id')).order_by('-id')

                return Response({"status": True, "data": active_jobs})

            if column_name == "sp":
                filters = {
                    column_name: request.user
                }
                jobs = Jobs.objects.filter(Q(job_status='Active') | Q(job_status='Pending'), **filters) \
                    .annotate(Total_bids=Count('bd_job_id', filter=Q(bd_job_id__status='Active'))). \
                    values('Total_bids', 'budget', 'job_status', jobs_id=F('id'),
                           category_name=F('job_cat_child__name'), category_image=F('job_cat_child__category_image'),
                           category_icon=F('job_cat_child__cat_icon'),
                           provider_id=F('sp__id'), seeker_id=F('ssid__id')
                           )
                bids = Bids.objects.filter(status='Active', job__job_category__is_deleted=False, **filters).values('id', job_status=F('status'),
                                                                              budget=F('price'), category_name=F(
                                                                              'job__job_cat_child__name'),category_image
                                                                              =F('job__job_cat_child__category_image'),
                                                                               category_icon=F(
                                                                                   'job__job_cat_child__cat_icon'),
                                                                              provider_id=F('sp__id'), seeker_id=
                                                                              F('job__ssid__id'), jobs_id=F('job__id')).order_by('-id')
                active_jobs = chain(jobs, bids)
                return Response({"status": True, "data": active_jobs})

        if status.lower() == "ongoing":
            filters = {
                column_name: request.user
            }
            ongoing_jobs = Booking.objects.filter(Q(order_status='Active') | Q(order_status='Anytime Now') |
                                                  Q(order_status='At Your Doorstep'), **filters,
                                                  category__is_deleted=False). \
                values('id', 'budget', 'end_date', 'order_status',
                       category_name=F('category__name'), category_image=F('cat_child_id__category_image'),
                       category_icon=F('cat_child_id__cat_icon'),
                       provider_name=F('sp__first_name'), provider_image=F('sp__profile__profile_image'),
                       provider_id=F('sp__id'), seeker_id=F('ss__id'), seeker_name=F('ss__first_name'),
                       seeker_image=F('ss__profile__profile_image'), jobid=F('job__id')
                       ).order_by('-id')
            return Response({"status": True, "data": ongoing_jobs})

        if status.lower() == "completed":
            filters = {
                column_name: request.user
            }
            completed_jobs = []
            data = Booking.objects.filter(Q(order_status='Completed'),
                                          **filters). \
                values('id', 'budget', 'end_date', 'order_status',
                       category_name=F('category__name'), category_image=F('cat_child_id__category_image'),
                       category_icon=F('cat_child_id__cat_icon'),
                       provider_name=F('sp__first_name'), provider_image=F('sp__profile__profile_image'),
                       provider_id=F('sp__id'), seeker_id=F('ss__id'), seeker_name=F('ss__first_name'),
                       seeker_image=F('ss__profile__profile_image'), jobid=F('job__id')
                       ).order_by('-id').distinct('id')
            for job in data:
                if Rating.objects.filter(rated_by=request.user, booking=job['id']).exists():
                    job.update({"is_rated": True})
                    completed_jobs.append(job)
                else:
                    job.update({"is_rated": False})
                    completed_jobs.append(job)
            return Response({"status": True, "data": completed_jobs})

        if status.lower() == "cancelled":
            filters = {
                column_name: request.user
            }
            data = Booking.objects.filter(Q(order_status='Cancelled'),
                                          **filters). \
                values('id', 'budget', 'end_date', 'order_status', 'cancelled_by',
                       category_name=F('category__name'), category_image=F('cat_child_id__category_image'),
                       category_icon=F('cat_child_id__cat_icon'),
                       provider_name=F('sp__first_name'), provider_image=F('sp__profile__profile_image'),
                       provider_id=F('sp__id'), seeker_id=F('ss__id'), seeker_name=F('ss__first_name'),
                       seeker_image=F('ss__profile__profile_image'), jobid=F('job__id')
                       ).order_by('-id')
            return Response({"status": True, "data": data})
        else:
            return Response({"status": True, "message": "Please enter the correct status."})


class   OrderCompletion(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Booking.objects.filter(category__is_deleted=False).order_by('-id')
    serializer_class = BookingSerializer

    @exception_handler
    def put(self, request, *args, **kwargs):
        data = ""
        # stripe.api_key = STRIPE_API_KEY
        booking = self.get_object()
        if Booking.objects.filter(id=booking.id).exists():
            with transaction.atomic():
                # if StripeBooking.objects.filter(booking_id=booking.id).exists():
                #     stripe_booking = StripeBooking.objects.get(booking_id=booking.id)
                #     charge = stripe.Charge.capture(stripe_booking.charge_id)
                #     transaction_id = charge.balance_transaction
                #     if charge.status == 'succeeded':
                #         transaction_details = stripe.BalanceTransaction.retrieve(
                #             transaction_id,
                #         )
                #         send_referrals_earnings(transaction_details.net, booking.id)
                serializer = BookingSerializer(booking, data=request.data)
                try:
                    serializer.is_valid(raise_exception=True)
                except Exception as e:
                    error = {"status": False, "message": e.args[0], "data": ""}
                    return Response(error)
                serializer.save(again_tip_request=True)
                if serializer.data['order_status'] == 'Completed':
                    data = {'category': booking.category.name,
                            'budget': booking.budget,
                            'booking_id': booking.id,
                            'time': booking.end_date
                            }
                    # send_email_template(template_name='email_templates/complete_order_temp.html',
                    #                     subject_msg="Job has been completed",
                    #                     email=booking.sp.email,
                    #                     data=data)
                    # send_email_template(template_name='email_templates/complete_order_temp.html',
                    #                     subject_msg="Job has been completed",
                    #                     email=booking.ss.email,
                    #                     data=data)
                    seeker_data = Booking.objects.filter(id=booking.id, category__is_deleted=False).annotate(
                        reviews=Count('ss__rated_to_in_rating__feedback'),
                        rating=Avg('ss__rated_to_in_rating__star')).values(
                        'reviews', 'rating', 'budget', 'order_status', 'is_payment',
                        category_name=F('cat_child_id__name'),
                        seeker_name=F('ss__first_name'),
                        seeker_image=F('ss__profile__profile_image')),
                    service_id = Spservices.objects.filter(s_cat_parent__is_deleted=False,
                                                           s_cat_parent=booking.cat_child_id,
                                                           s_user=booking.sp).values('id')
                    data = {
                        "seeker_data": seeker_data[0],
                        "service_id": service_id
                    }
                    device_list = list(DeviceRegistration.objects.filter(user=booking.ss).
                                       values_list('device_id', flat=True).distinct())
                    if len(device_list) != 0:
                        payload = dict()
                        payload['type'] = 'Booking'
                        payload['type_id'] = booking.job_id
                        send_notification(sender=Booking, message_title='Mooner',
                                          message_body='your order has been completed',
                                          extra_notification_kwargs=payload, user=booking.ss.id, user_type='SS',
                                          list_of_devices=device_list)
                    return Response({"status": True, "data": data})

        return Response({"status": True, "data": data})

    def get(self, request, *args, **kwargs):

        booking = self.get_object()
        provider_data = Booking.objects.filter(id=booking.id, category__is_deleted=False).annotate(reviews=Count('sp__rated_to_in_rating__feedback'),
                                                              rating=Avg('sp__rated_to_in_rating__star')).values(
            'reviews', 'rating', 'budget', 'order_status',
            category_name=F('cat_child_id__name'),
            provider_name=F('sp__first_name'),
            provider_image=F('sp__profile__profile_image')),
        service_id = Spservices.objects.filter(s_cat_parent__is_deleted=False, s_cat_parent=booking.cat_child_id, s_user=booking.sp).values('id')
        data = {
            "provider_data": provider_data[0],
            "service_id": service_id
        }
        return Response({"status": True, "data": data})


class SoftDeleteQuestionCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            question_id = request.data.get('question_id')
            if question_id:
                category_question = soft_delete(user_modal=CategoryQuestions, id=question_id, msg='Category Question')
                return category_question
            else:
                return Response({"status": False, "message": "Please Enter Category Question ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class RestoreQuestionCategory(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            question_id = request.data.get('question_id')
            if question_id:
                category_question = restore_from_softdelete(user_modal=CategoryQuestions, id=question_id, msg='Category Question')
                return category_question
            else:
                return Response({"status": False, "message": "Please Enter Category Question ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class SoftDeleteJob(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            job_id = request.data.get('job_id')
            if job_id:
                softdel_job = soft_delete(user_modal=Jobs, id=job_id, msg='Job')
                return softdel_job
            else:
                return Response({"status": False, "message": "Please Enter Job ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class RestoreJob(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            job_id = request.data.get('job_id')
            if job_id:
                softdel_job = restore_from_softdelete(user_modal=Jobs, id=job_id, msg='Job')
                return softdel_job
            else:
                return Response({"status": False, "message": "Please Enter Job ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class SSBookingCancel(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SSBookingSerializer

    @staticmethod
    def post(request):
        try:
            serializer = SSBookingSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                ss_cancel = ss_booking_cancel(user_modal=Booking, booking_id=serializer.data.get('booking_id'),
                                                         ss_id=serializer.data.get('ss_id'))
                return ss_cancel
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class SPBookingCancel(APIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = SPBookingSerializer

    @staticmethod
    def post(request):
        try:
            serializer = SPBookingSerializer(data=request.data)
            if serializer.is_valid(raise_exception=True):
                sp_cancel = sp_booking_cancel(user_modal=Booking, booking_id=serializer.data.get('booking_id'),
                                              sp_id=serializer.data.get('sp_id'))
                return sp_cancel
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class SPBooked(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            booking_id = request.data.get('booking_id')
            sp_id = request.data.get('sp_id')
            is_sp_booked = sp_booked_or_not(user_modal=Booking, booking_id=booking_id, sp_id=sp_id)
            return is_sp_booked
        except ObjectDoesNotExist:
            return Response({"status": False, "message": "There are some error!"})


class SoftDeleteBooking(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            booking_id = request.data.get('booking_id')
            if booking_id:
                booking = soft_delete(user_modal=Booking, id=booking_id, msg='Booking')
                return booking
            else:
                return Response({"status": False, "message": "Please Enter Booking ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class HardDeleteBooking(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            booking_id = request.data.get('booking_id')
            if booking_id:
                booking = permanent_delete(user_modal=Booking, id=booking_id, msg='Booking')
                return booking
            else:
                return Response({"status": False, "message": "Please Enter Booking ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class RestoreBooking(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            booking_id = request.data.get('booking_id')
            if booking_id:
                booking = restore_from_softdelete(user_modal=Booking, id=booking_id, msg='Booking')
                return booking
            else:
                return Response({"status": False, "message": "Please Enter Booking ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class HardDeleteQuestion(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            question_id = request.data.get('question_id')
            if question_id:
                question = permanent_delete(user_modal=CategoryQuestions, id=question_id, msg='Category Question')
                return question
            else:
                return Response({"status": False, "message": "Please Enter Question ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class HardDeleteJob(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            job_id = request.data.get('job_id')
            if job_id:
                job = permanent_delete(user_modal=Jobs, id=job_id, msg='Job')
                return job
            else:
                return Response({"status": False, "message": "Please Enter Job ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class SoftDeleteAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            answer_id = request.data.get('answer_id')
            if answer_id:
                softdel_answer = soft_delete(user_modal=Answer, id=answer_id, msg='Answer')
                return softdel_answer
            else:
                return Response({"status": False, "message": "Please Enter Answer ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class RestoreAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            answer_id = request.data.get('answer_id')
            if answer_id:
                softdel_answer = restore_from_softdelete(user_modal=Answer, id=answer_id, msg='Answer')
                return softdel_answer
            else:
                return Response({"status": False, "message": "Please Enter Answer ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class HardDeleteAnswer(APIView):
    permission_classes = (IsAuthenticated,)

    def post(self, request):
        try:
            answer_id = request.data.get('answer_id')
            if answer_id:
                softdel_answer = permanent_delete(user_modal=Answer, id=answer_id, msg='Answer')
                return softdel_answer
            else:
                return Response({"status": False, "message": "Please Enter Answer ID!"})
        except ObjectDoesNotExist as e:
            return Response({"status": False, "message": "There are some error!"})


class CancelledBookingList(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    serializer_class = BookingSerializer

    def list(self, request, *args, **kwargs):
        data = Booking.objects.filter(order_status='Cancelled').values('id', 'start_date', 'price', 'order_status',
                                                                        seeker=F('ss__first_name'),
                                                                        provider=F('sp__first_name'),
                                                                        category_name=F('category__name'))
        result = pagination(data, request)
        return Response({"status": True, "data": result.data})
