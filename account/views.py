from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes, permission_classes, parser_classes
from rest_framework.renderers import JSONRenderer
from .serializers import UserSerializer, EditAccountSerializer
from rest_framework import status
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.parsers import MultiPartParser, FormParser, JSONParser
from django.core.signing import TimestampSigner, BadSignature, SignatureExpired
from user.models import User

signer = TimestampSigner()


@api_view(['GET'])
@renderer_classes([JSONRenderer])
@permission_classes([IsAuthenticated])
def me(request):
    serializer = UserSerializer(request.user)

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["PUT"])
@permission_classes([IsAuthenticated])
@parser_classes([MultiPartParser, FormParser, JSONParser])
def edit_account(request):
    serializer = EditAccountSerializer(
        instance=request.user,
        data=request.data,
        partial=True,
        context={"request": request},
    )
    serializer.is_valid(raise_exception=True)
    serializer.save()

    return Response(serializer.data, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([AllowAny])
def confirm_email(request):
    token = request.query_params.get("token")
    if not token:
        return Response({"detail": "Token is required"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        data = signer.unsign(token, max_age=3600)
        user_id, new_email = data.split(":", 1)
    except (BadSignature, SignatureExpired):
        return Response({"detail": "Invalid or expired token"}, status=status.HTTP_400_BAD_REQUEST)

    try:
        user = User.objects.get(pk=user_id)
    except User.DoesNotExist:
        return Response({"detail": "User not found"}, status=status.HTTP_404_NOT_FOUND)

    if User.objects.exclude(pk=user.pk).filter(email=new_email).exists():
        return Response({"detail": "This email is already taken"}, status=status.HTTP_400_BAD_REQUEST)

    user.email = new_email
    user.save(update_fields=["email"])

    return Response({"detail": "Email successfully updated"})