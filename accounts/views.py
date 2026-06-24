from drf_spectacular.utils import extend_schema
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from accounts.serializers import RegisterSerializer, UserSerializer, MeSerializer
from accounts.schema_serializers import RegisterResponseSerializer, MeResponseSerializer

@extend_schema(
    request=RegisterSerializer,
    responses={201: RegisterResponseSerializer},
)
class RegisterView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response(
            {"ok": True, "user": UserSerializer(user).data},
            status=status.HTTP_201_CREATED,
        )

@extend_schema(
    responses={200: MeResponseSerializer},
)
class MeView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        return Response(MeSerializer(request.user).data)
