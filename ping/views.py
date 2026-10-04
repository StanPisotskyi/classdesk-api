from rest_framework.response import Response
from rest_framework.decorators import api_view, renderer_classes
from rest_framework.renderers import JSONRenderer


@api_view(['GET'])
@renderer_classes([JSONRenderer])
def ping(request):
    return Response({'status': True})