from rest_framework import generics
from rest_framework.permissions import AllowAny
from mooner_backend.utils import pagination
from .models import Faqs
from .serializers import FaqsSerializer
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAdminUser
# Create your views here.


class Faq(generics.ListCreateAPIView):
    permission_classes = (AllowAny,)
    queryset = Faqs.objects.all().order_by('-id')
    serializer_class = FaqsSerializer

    def list(self, request, *args, **kwargs):

        queryset = self.get_queryset()
        serializer = FaqsSerializer(queryset, many=True)
        faqs = pagination(serializer.data, request)
        return Response({"status": True, "data": faqs.data})

    def post(self, request, *args, **kwargs):
            create_faqs = self.create(request, *args, **kwargs)
            return Response({"status": True, "message": "Faq successfully registered"})


class GetFaq(generics.RetrieveUpdateDestroyAPIView):
    queryset = Faqs.objects.all().order_by('-id')
    serializer_class = FaqsSerializer

    def get(self, request, *args, **kwargs):
        obj = self.retrieve(request, *args, **kwargs)
        return Response({"status": True, "data": obj.data})

    def put(self, request, *args, **kwargs):
        self.update(request, *args, **kwargs)
        return Response({"status": True, "data": "Updated Successfully"})

    def delete(self, request, *args, **kwargs):
        self.destroy(request, *args, **kwargs)
        return Response({"status": True, "data": "Deleted Successfully"})


class SearchFaqs(generics.CreateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def get(self, request, *args, **kwargs):
        if self.request.query_params.get('search'):
            string_value = self.request.query_params.get('search')
            result = Faqs.objects.filter(question__icontains=string_value).order_by('-id').values()
            faqs = pagination(result, request)
            return Response({"status": True, "data": faqs.data})
        else:
            return Response(
                {"status": False, "Response": "Please enter the search value."})

