from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes
from rest_framework.renderers import JSONRenderer
from .serializers import RegistrationSerializer, LoginSerializer
from rest_framework.parsers import JSONParser
from rest_framework import status
from rest_framework.permissions import AllowAny


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([AllowAny])
def register(request):
    data = JSONParser().parse(request)
    serializer = RegistrationSerializer(data=data)
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@renderer_classes([JSONRenderer])
@permission_classes([AllowAny])
def login(request):
    data = JSONParser().parse(request)
    serializer = LoginSerializer(data=data)
    serializer.is_valid(raise_exception=True)

    return Response(serializer.data, status=status.HTTP_200_OK)