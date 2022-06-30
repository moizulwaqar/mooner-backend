from rest_framework.permissions import IsAuthenticated, IsAdminUser
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework import generics
from django.db.models import F, Count, Q
from mooner_backend.utils import pagination, password_check
from .serializers import UserChangePasswordSerializer


class SubAdmin(generics.ListAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)

    def list(self, request, *args, **kwargs):

        sub_admin = User.objects.filter(profile__roles__role_name='Sub_Admin')\
            .values('id', 'username', 'email', 'first_name', 'last_name', status=F('is_active'),
                    cell_phone=F('profile__cell_phone'),
                    level=F('profile__level'))
        sa = pagination(sub_admin, request)
        return Response({"status": True, "data": sa.data})


class ChangePasswordUser(generics.RetrieveUpdateAPIView):
    permission_classes = (IsAuthenticated, IsAdminUser)
    queryset = User.objects.all()
    serializer_class = UserChangePasswordSerializer

    def put(self, request, *args, **kwargs):
        password = request.data.get('password')
        confirm_password = request.data.get('confirm_password')
        user = self.get_object()

        if password != confirm_password:
            return Response({"status": False, "Response": "Passwords mismatch."})
        else:
            pass_res = password_check(confirm_password)
            if pass_res == "Password updated successfully!":
                user.set_password(str(confirm_password))
                user.save()
                return Response({"status": True, "Response": pass_res})
            else:
                return Response({"status": False, "Response": pass_res})