from django.shortcuts import get_object_or_404
from rest_framework import status, viewsets
from rest_framework.response import Response

from survey.serializers import OperatingSystemSerializer, SurveyResultSerializer
from survey.models import OperatingSystem, SurveyResult


class SurveyResultViewSet(viewsets.GenericViewSet):
    queryset = SurveyResult.objects.all()
    serializer_class = SurveyResultSerializer

    # GET /api/v1/survey/ -> 설문조사 결과 list
    def list(self, request):
        surveys = self.get_queryset().select_related('os')
        return Response(self.get_serializer(surveys, many=True).data)

    # GET /api/v1/survey/pk/ -> 특정 설문조사 결과
    def retrieve(self, request, pk=None):
        survey = get_object_or_404(SurveyResult, pk=pk)
        return Response(self.get_serializer(survey).data)

    # POST /api/v1/survey/ -> 새로운 설문조사 결과 추가
    def create(self, request):
        # get body data
        python = request.data.get('python')
        rdb = request.data.get('rdb')
        programming = request.data.get('programming')
        os = request.data.get('os')

        # validity check
        if not (python and rdb and programming and os):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        try:
            python = int(python)
            rdb = int(rdb)
            programming = int(programming)
        except ValueError:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        isvalid = lambda x : (1 <= x and x <= 5)
        if not (isvalid(python) and isvalid(rdb) and isvalid(programming)):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        
        # user authenticatedness check
        if not request.user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        # get or create an OperatingSystem object
        try:
            os_object = OperatingSystem.objects.get(name = os)
        except OperatingSystem.DoesNotExist:
            os_object = OperatingSystem.objects.create(name=os, description="", price=None)
        
        # create a new SurveyResult object
        survey = SurveyResult.objects.create(
            user = request.user,
            os = os_object,
            python = python, rdb=rdb, programming=programming,
            major="", grade="", backend_reason="", waffle_reason="", say_something=""
        )

        return Response(self.get_serializer(survey).data, status=status.HTTP_201_CREATED)


class OperatingSystemViewSet(viewsets.GenericViewSet):
    queryset = OperatingSystem.objects.all()
    serializer_class = OperatingSystemSerializer

    def list(self, request):
        return Response(self.get_serializer(self.get_queryset(), many=True).data)

    def retrieve(self, request, pk=None):
        try:
            os = OperatingSystem.objects.get(id=pk)
        except OperatingSystem.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return Response(self.get_serializer(os).data)
