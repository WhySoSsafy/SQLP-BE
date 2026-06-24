from drf_spectacular.utils import extend_schema
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView
from accounts.serializers import UserSerializer
from accounts.schema_serializers import LoginRequestSerializer, LoginResponseSerializer

class LoginSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        data["user"] = UserSerializer(self.user).data
        return data

@extend_schema(
    request=LoginRequestSerializer,
    responses={200: LoginResponseSerializer},
)
class LoginView(TokenObtainPairView):
    serializer_class = LoginSerializer
