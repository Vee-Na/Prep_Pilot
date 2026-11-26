from django.contrib.auth import authenticate, get_user_model
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny,IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializer import ProfileSerializer

Profile = get_user_model()


class LoginView(APIView):
    permission_classes = [AllowAny]

    def post(self, request, *args, **kwargs):
        identifier = (request.data.get('email')or request.data.get('username')
)
        password = request.data.get('password')

        if not identifier or not password:
            return Response({'msg': 'identifier and password are required'}, status=400)

        # find the account by email or username
        profile = (
            Profile.objects.filter(email__iexact=identifier).first()
            or Profile.objects.filter(username__iexact=identifier).first()
        )

        user = None
        if profile:
            user = authenticate(username=profile.username, password=password)

        if user:
            refresh_token = RefreshToken.for_user(user)
            data = {
                'refresh_token': str(refresh_token),
                'access_token': str(refresh_token.access_token),
                'role': user.role,
            }
            return Response(data, status=200)

        return Response({'msg': 'invalid credentials'}, status=400)


class UserRegisterView(APIView):
    permission_classes = [AllowAny]
    serializer_class = ProfileSerializer

    def post(self, request, *args, **kwargs):
        serializer = self.serializer_class(data=request.data)

        if serializer.is_valid():
            serializer.save()
            return Response({'msg': 'account successfully created'}, status=201)


        return Response(serializer.errors, status=400)


class WhoAmIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response({'email': request.user.email, 'role': request.user.role})

