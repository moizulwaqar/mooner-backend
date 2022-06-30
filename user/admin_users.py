from mooner_backend.utils import CsrfExemptSessionAuthentication
from django.contrib.auth.models import User
from rest_framework.views import APIView
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.authentication import BasicAuthentication
from rest_framework.response import Response
from rest_framework.decorators import permission_classes
from django.contrib.auth import authenticate, login
from rest_framework.authtoken.models import Token


@permission_classes([AllowAny])
class AdminLogin(APIView):
    authentication_classes = [CsrfExemptSessionAuthentication, BasicAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):

        try:

            if not request.data.get('email') and not request.data.get('password'):
                return Response({"status": False, "Response": "please enter email and password"})

            if request.data.get('email'):
                if request.data.get('password'):
                    email = request.data.get('email')
                    password = request.data.get('password')
                    user_check = User.objects.filter(email=email).exists()
                    if user_check:
                        user_email = User.objects.get(email=email)
                        user = authenticate(username=user_email, password=password)
                        if user:
                            login(request, user)
                            token, created = Token.objects.get_or_create(user=user)
                            data = {
                                "token": token.key,
                                "user_id": user.id,
                                "username": user.username,
                                "email": user.email,
                            }
                            return Response({"status": True, "Response": "Logged In Successfully", "data": data})
                        elif not user:
                            return Response(
                                {"status": False, "Response": "Password is Incorrect"})

                        else:
                            return Response({"status": False, "Response": "Invalid email or Password"})
                    else:
                        return Response({"status": False, "Response": "Email Doesn't Exists"})
                else:
                    return Response({"status": False, "Response": "please enter password"})
            else:
                return Response({"status": "Failed", "Response": "please enter email"})


        except:
            return Response({"status": "Failed", "Response": "Invalid email or Password"})
