import base64

from django.core.files.base import ContentFile
from django.db import transaction
from geopy import Nominatim
from rest_framework.response import Response
from rest_framework import generics
from rest_framework.permissions import IsAuthenticated, AllowAny
from booking.models import Spservices, Answer, SpServiceImages, Rating, Jobs, Bids
from booking.serializers import SpServiceSerializer
from category_kyc.serializers import CategoryKycAnswerSerializer
from category_management.models import Category, CategoryQuestions
from .models import SpItems, SpItemImages
from .serializers import SpItemsSerializer, SpImagesSerializer, SpFilterJobsSerializer
from django.db.models import F, Avg, Count, Q
# from django.contrib.gis.geos import Point
# from django.contrib.gis.measure import Distance


class SpRegisterService(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Spservices.objects.filter(s_cat_parent__is_deleted=False)
    serializer_class = SpServiceSerializer

    @transaction.atomic()
    def post(self, request, *args, **kwargs):
        if request.data:
            category_kyc_answers = request.data.get('category_kyc_answers')
            category_ques_ans_data = request.data.get('s_answers')
            cat_parent_obj = request.data.get('s_cat_parent')
            child_cat_obj = Category.objects.get(id=request.data.get('category_id'))
            # longitude = float(request.data.get('longitude'))
            # latitude = float(request.data.get('latitude'))
            budget = request.data.get('budget')
            files = request.data.get('files')
            image_urls = request.data.get('image_urls')
            description = request.data.get('description')
            # point = Point(latitude, longitude)
            answer = ''
            question = ''
            reg_service = Spservices.objects.filter(s_user=request.user, s_cat_parent=child_cat_obj)
            if reg_service.exists():
                return Response({"status": False, "message": "You are already registered in this service."})
            if category_kyc_answers:
                serializer = CategoryKycAnswerSerializer(data=category_kyc_answers, many=True)
                try:
                    serializer.is_valid(raise_exception=True)
                except Exception as e:
                    error = {"status": False, "message": e.args[0]}
                    return Response(error)
                serializer.save(user=request.user)
            if category_ques_ans_data:
                sp_service = Spservices.objects.create(s_cat_parent=child_cat_obj,
                                                       s_user=request.user,
                                                       budget=budget,
                                                       # location=point,
                                                       longitude=103.8198,
                                                       latitude=1.3521,
                                                       image_urls=image_urls,
                                                       portfolio=description)

                if files:
                    for file in files:
                        sp_images_obj = SpServiceImages()
                        format, imgstr = file.split(';base64,')
                        ext = format.split('/')[-1]
                        image_file = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                        sp_images_obj.file = image_file
                        sp_images_obj.sp_service = sp_service
                        sp_images_obj.save()
                for question_id, answer_ in category_ques_ans_data.items():
                    if CategoryQuestions.objects.filter(id=question_id).exists():
                        question = CategoryQuestions.objects.get(id=question_id)
                        if question.question_type == "Text" or question.question_type == "text":
                            answer = Answer.objects.create(question_id=question,
                                                           cat_parent_id_id=cat_parent_obj,
                                                           child_category=child_cat_obj,
                                                           answer=answer_,
                                                           sp_services=sp_service)

                        if question.question_type == "File" or question.question_type == "file":
                            # format, imgstr = answer_.split(';base64,')
                            # ext = format.split('/')[-1]
                            # file = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                            ans_obj = Answer()
                            ans_obj.question_id = question
                            ans_obj.cat_parent_id_id = cat_parent_obj
                            ans_obj.child_category = child_cat_obj
                            ans_obj.answer = answer_
                            ans_obj.sp_services = sp_service
                            ans_obj.save()
                        if question.question_type == "Image" or question.question_type == "image":
                            # format, imgstr = answer_.split(';base64,')
                            # ext = format.split('/')[-1]
                            # file = ContentFile(base64.b64decode(imgstr), name='temp.' + ext)
                            ans_obj = Answer()
                            ans_obj.question_id = question
                            ans_obj.cat_parent_id_id = cat_parent_obj
                            ans_obj.child_category = child_cat_obj
                            ans_obj.answer = answer_
                            ans_obj.sp_services = sp_service
                            ans_obj.save()
                        if question.question_type == "Radio" or question.question_type == "radio":
                            answer = Answer.objects.create(question_id=question,
                                                           cat_parent_id_id=cat_parent_obj,
                                                           child_category=child_cat_obj,
                                                           answer=answer_,
                                                           sp_services=sp_service)
                        if question.question_type == "Checkbox" or question.question_type == "checkbox":
                            answer = Answer.objects.create(question_id=question,
                                                           cat_parent_id_id=cat_parent_obj,
                                                           child_category=child_cat_obj,
                                                           answer=answer_)
                    else:
                        transaction.set_rollback(True)
                        return Response({"status": False, "message": "Question with id={} does not exist".
                                        format(question_id)})
                return Response({"status": True, "message": "SP Service Successfully Registered."})
            return Response({"status": False, "message": "Answer is not given!"})
        else:
            return Response({"status": False, "message": "please enter request data"})


class SpEditService(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Spservices.objects.all()
    serializer_class = SpServiceSerializer

    def put(self, request, pk, format=None):
        if request.data:
            spservice = Spservices.objects.get(id=pk)
            budget = request.data.get('budget')
            description = request.data.get('description')
            lat = request.data.get('latitude')
            long = request.data.get('longitude')
            if lat and long:
                latitude = float(request.data.get('latitude'))
                longitude = float(request.data.get('longitude'))
                # location = Point(latitude, longitude)
                spservice.budget = budget
                spservice.latitude = latitude
                spservice.longitude = longitude
                # spservice.location = location
            if description:
                spservice.portfolio = description
            spservice.save()

            ans_objects = Answer.objects.filter(sp_services=spservice.id)
            ans_obj = request.data.get('s_answers')
            for ques, answer in ans_obj.items():
                for ans_id in ans_objects:
                    try:
                        ans = Answer.objects.get(question_id=int(ques), sp_services=spservice)
                        if ans.question_id.id == int(ques):
                            ans.answer = answer
                            ans.sp_services = spservice
                            ans.save()
                    except:
                        ans_object = Answer()
                        question = CategoryQuestions.objects.get(id=int(ques))
                        ans_object.question_id = question
                        ans_object.answer = answer
                        ans_object.sp_services = spservice
                        ans_object.save()

            return Response({"status": True, "message": "Successfully updated the sp service"})
        else:
            return Response({"status": False, "message": "please enter requested data"})

    def get(self, request, pk, format=None):
        data = []
        item = {}
        if Spservices.objects.filter(id=pk).exists():

            sp = list(Spservices.objects.filter(id=pk).values(ser_reg_id=F("id"), description=F('portfolio')
                                                              ,urls=F('image_urls')))
            item["sp_service"] = sp[0]
            sp_answers = list(Answer.objects.filter(sp_services=pk).values("question_id", "answer",
                                                                           question_text=F("question_id__question_text")
                                                                           ,
                                                                           question_for=F("question_id__question_for"),
                                                                           question_type=
                                                                           F("question_id__question_type"),
                                                                           answerfile=F("answer_file"),
                                                                           r_text_one=F("question_id__r_text_one"),
                                                                           r_text_two=F("question_id__r_text_two"),
                                                                           r_text_three=F("question_id__r_text_three"),
                                                                           r_text_four=F("question_id__r_text_four")
                                                                           ))

            item['service_answers'] = sp_answers
            sp_service = Spservices.objects.filter(id=pk, s_user=request.user).values(sp_service_image=F('sp_service_files__file'))
            item['files'] = sp_service
            sp_data = Spservices.objects.filter(id=pk). \
                values(
                's_user', user_name=F('s_user__first_name'),
                sp_image=F('s_user__profile__profile_image')).first()
            item['sp_data'] = sp_data
            sp_service = self.get_object()
            sp_total_rating = Spservices.objects.filter(id=pk, s_user=sp_service.s_user,
                                                  s_user__booking_sp_id__booking__rated_to=sp_service.s_user).\
                annotate(average_ratings=Avg('s_user__booking_sp_id__booking__star'),
                         feedback_counts=Count('s_user__booking_sp_id__booking__id')).values(
                'average_ratings', 'feedback_counts').first()

            item['sp_total_rating'] = sp_total_rating
            feedback_list = Rating.objects.filter(booking__sp__s_user_in_spservices__id=pk,
                                                  booking__sp__s_user_in_spservices__s_user=sp_service.s_user,
                                                  rated_to=sp_service.s_user).values(
                'feedback', 'star', 'created_at',
                seeker_name=F('rated_by__first_name'), seeker_image=F('rated_by__profile__profile_image'),

            )
            item['feedback_list'] = feedback_list
            data.append(sp)
            return Response({"status": True, "message": "Sp Service all data", "data": item})
        else:
            return Response({"status": True, "message": "Sp does not exists"})

    def delete(self, request, *args, **kwargs):
        self.destroy(self, request, *args, **kwargs)
        return Response({"status": True, "message": "Service successfully deleted"})


class CreateSpItem(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SpItems.objects.all()
    serializer_class = SpItemsSerializer

    def post(self, request, *args, **kwargs):
        if request.data:
            serializer = self.create(request, *args, **kwargs)
            # sp_image = ''
            sp_items_list = []
            if serializer:
                sp_item = SpItems.objects.get(id=serializer.data['id'])
                for image in request.FILES.getlist("image"):
                    sp_image = SpItemImages()
                    sp_image.item = sp_item
                    sp_image.image = image
                    sp_image.save()
            category = SpItems.objects.filter(category=serializer.data['category'], user=request.user).values()
            for item in category:
                images = SpItemImages.objects.filter(item=item['id']).values('image').values()
                item["images"] = images
                sp_items_list.append(item)
            check_service = Spservices.objects.filter(s_cat_parent=serializer.data['category'], s_user=request.user)
            if not check_service:
                sp_service = Spservices()
                sp_service.s_cat_parent_id = serializer.data['category']
                sp_service.s_user = request.user
                sp_service.save()
            return Response({"status": True, "message": "SP Item Successfully Registered", "data": sp_items_list})

    def get(self, request, *args, **kwargs):
        serializer = SpItems.objects.filter(user=request.user).values()
        sp_items_list = []
        for item in serializer:
            images = SpItemImages.objects.filter(item=item['id']).values('image').values()
            item["images"] = images
            sp_items_list.append(item)
        return Response({"status": True, "message": "SP Item Successfully Registered", "data": sp_items_list})


class GetSpItem(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    # queryset = SpItems.objects.all()
    serializer_class = SpItemsSerializer

    def list(self, request, *args, **kwargs):
        category = request.data.get('sub_category_id')
        data = SpItems.objects.filter(category=category, user=request.user).values(
            'name', 'quantity', 'weight', 'method', 'description', 'opening', 'closing', 'price', 'monday', 'tuesday',
            'wednesday', 'thursday', 'friday', 'saturday', 'sunday', category_name=F('category__name'),
            user_name=F('user__username')
        )
        return Response({"status": True, "message": "Items in category", "data": data})


class EditSpItem(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SpItems.objects.all()
    serializer_class = SpItemsSerializer

    def put(self, request, *args, **kwargs):

        if request.data:

            serializer = self.update(request, *args, **kwargs)
            # images = request.FILES.getlist("image")

            if serializer:
                sp_item = SpItems.objects.get(id=serializer.data['id'])
                sp_item_images = SpItemImages.objects.filter(item=sp_item)
                for image in request.FILES.getlist("image"):
                    sp_image = SpItemImages()
                    sp_image.item = sp_item
                    sp_image.image = image
                    sp_image.save()
                # category = SpItems.objects.get(=serializer.data['category'], user=request.user).values()
                # for item in category:
                images = SpItemImages.objects.filter(item=sp_item).values('image').values()
                sp_item = [serializer.data, images]

            return Response({"status": True, "message": "SP Item Successfully Registered", "data": sp_item})


        else:
            return Response({"status": False, "message": "please enter requested data"})


class DeleteSpItemsImages(generics.RetrieveDestroyAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SpItemImages.objects.all()
    serializer_class = SpImagesSerializer


class ListSpByBudget(generics.ListCreateAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SpItems.objects.all()
    serializer_class = SpItemsSerializer

    def post(self, request, *args, **kwargs):
        if request.data:
            min_budget = request.data.get('min_budget')
            max_budget = request.data.get('max_budget')
            order_by = request.data.get('order_by')
            latitude = request.data.get('latitude')
            longitude = request.data.get('longitude')
            address = request.data.get('address')
            geo_locator = Nominatim(user_agent="user_management")
            if longitude and latitude:
                lat = float(latitude)
                lng = float(longitude)
                # point = Point(lat, lng)
                radius = 10
                if order_by == "ASC":
                    location = Spservices.objects.filter(
                                                         budget__range=[min_budget, max_budget], ).order_by('budget',
                                                                                                            'location') \
                        .values('portfolio', 'about', 'budget')
                    return Response(
                        {"status": True, "message": "Sp Services by descending order", "services": location})
                if order_by == "DSC":
                    location = Spservices.objects.filter(
                                                         budget__range=[min_budget, max_budget], ). \
                        order_by('-budget', '-location').values('portfolio', 'about', 'budget')
                    return Response(
                        {"status": True, "message": "Sp Services by descending order", "services": location})
            if address:
                address_ = geo_locator.geocode(address)
                lat = address_.latitude
                lng = address_.longitude
                if lat and lng:
                    # point = Point(lat, lng)
                    radius = 10
                    if order_by == "ASC":
                        location = Spservices.objects.filter(
                                                             budget__range=[min_budget, max_budget], ).order_by(
                            'budget', 'location') \
                            .values('portfolio', 'about', 'budget')
                        return Response(
                            {"status": True, "message": "Sp Services by descending order", "services": location})
                    if order_by == "DSC":
                        location = Spservices.objects.filter(
                                                             budget__range=[min_budget, max_budget], ). \
                            order_by('-budget', '-location').values('portfolio', 'about', 'budget')
                        return Response(
                            {"status": True, "message": "Sp Services by descending order", "services": location})
                else:
                    return Response({"status": False, "message": "There is no latitude and longitude"})
        else:
            return Response({"status": False, "message": "please enter requested data"})


class ListItemsByCategory(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = SpItems.objects.all()
    serializer_class = SpItemsSerializer

    def get(self, request, *args, **kwargs):
        if request.data:
            category = request.data.get('category_id')
            items = SpItems.objects.filter(category=category, user=request.user).values()
            return Response({"status": True, "data": items})
        else:
            return Response({"status": False, "message": "please enter requested data"})


class SpJobsFilter(generics.ListAPIView):
    permission_classes = (IsAuthenticated,)
    queryset = Spservices.objects.all()
    serializer_class = SpFilterJobsSerializer

    @staticmethod
    def post(request, *args, **kwargs):
        category_list = request.data.get('categories_list')
        serializer = SpFilterJobsSerializer(data=request.data, context={"user": request.user})
        try:
            serializer.is_valid(raise_exception=True)
        except Exception as e:
            if 'error' in e.args[-1]:
                return Response({"status": False, "message": e.args[-1].get('error')[-1]})
            elif 'categories_list' in e.args[-1]:
                return Response({"status": False, "message":  e.args[-1].get('categories_list')[-1] + ' ' +
                                                              'category_list'})
            else:
                return Response({"status": False, "message": "False request sent Please send list of ids"})
        registered_categories = Spservices.objects.filter(s_user=request.user, s_cat_parent__in=category_list,
                                                          s_cat_parent__is_deleted=False).\
            values_list('s_cat_parent__id')
        if registered_categories:
            get_bid = Bids.objects.filter(sp=request.user, job__job_cat_child__is_deleted=False).values_list('job__id')
            posted_jobs = Jobs.objects.filter(job_cat_child__in=registered_categories, job_status='Active') \
                .exclude(Q(ssid=request.user) | Q(id__in=get_bid)).order_by('-id').values(
                'id', 'budget', 'schedule', category_name=F('job_cat_child__name'),
                category_image=F('job_cat_child__category_image'))
            return Response({"status": True, "message": "Get jobs data successfully", "data": posted_jobs})


