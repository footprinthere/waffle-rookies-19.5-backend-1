from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.db import IntegrityError
from django.views import View

from rest_framework import status, viewsets
from rest_framework.decorators import action
from rest_framework.generics import get_object_or_404
from rest_framework.response import Response

from user.serializers import UserSerializer


class UserViewSet(viewsets.GenericViewSet):
    serializer_class = UserSerializer
    queryset = User.objects.all()

    # POST /api/v1/user/ -> 신규 유저 생성
    def create(self, request, *args, **kwargs):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # body의 데이터를 체크
        if not username or not email or not password:
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if (not first_name and last_name) or (first_name and not last_name):
            return Response(status=status.HTTP_400_BAD_REQUEST)

        try:
            # Django 내부에 기본으로 정의된 User에 대해서는 create가 아닌 create_user를 사용
            # password가 자동으로 암호화되어 저장됨. database를 직접 조회해도 알 수 없는 형태로 저장됨.
            if first_name:
                if (not first_name.isalpha()) or (not last_name.isalpha()):
                    return Response(status=status.HTTP_400_BAD_REQUEST)
                user = User.objects.create_user(username, email, password, first_name=first_name, last_name=last_name)
            else:
                user = User.objects.create_user(username, email, password)
        except IntegrityError:  # 중복된 username
            return Response(status=status.HTTP_409_CONFLICT)

        # 가입했으니 바로 로그인 시켜주기
        login(request, user)
        # login을 하면 Response의 Cookies에 csrftoken이 발급됨
        # 이후 요청을 보낼 때 이 csrftoken을 Headers의 X-CSRFToken의 값으로 사용해야 POST, PUT 등의 method 사용 가능
        return Response(self.get_serializer(user).data, status=status.HTTP_201_CREATED)

    # PUT /api/v1/user/<pk> -> 유저 정보 변경
    def update(self, request, pk=None):
        user = get_object_or_404(User, pk=pk)

        # 로그인되지 않은 유저일 때
        if not user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)
        
        username = request.data.get('username')
        first_name = request.data.get('first_name')
        last_name = request.data.get('last_name')

        # username을 포함할 때
        if username:
            user.username = username
        
        # first_namer, last_name을 포함할 때
        if (not first_name and last_name) or (first_name and not last_name):
            return Response(status=status.HTTP_400_BAD_REQUEST)
        if first_name:
            if (not first_name.isalpha()) or (not last_name.isalpha()):
                return Response(status=status.HTTP_400_BAD_REQUEST)
            user.first_name = first_name
            user.last_name = last_name
        
        # 변경 사항 반영
        try:
            user.save()
        except IntegrityError:
            return Response(status=status.HTTP_409_CONFLICT)

        return Response(self.get_serializer(user).data)

    # PUT /api/v1/user/login/ -> 유저 로그인
    @action(detail=False, methods=['PUT'])
    def login(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        # authenticate라는 함수는 username, password가 올바르면 해당 user를, 그렇지 않으면 None을 return
        user = authenticate(request, username=username, password=password)
        if user:
            login(request, user)
            # login을 하면 Response의 Cookies에 csrftoken이 발급됨 (반복 로그인 시 매번 값이 달라짐)
            # 이후 요청을 보낼 때 이 csrftoken을 Headers의 X-CSRFToken의 값으로 사용해야 POST, PUT 등의 method 사용 가능
            return Response(self.get_serializer(user).data)
        # 존재하지 않는 사용자이거나 비밀번호가 틀린 경우
        return Response(status=status.HTTP_403_FORBIDDEN)

    # POST /api/v1/user/logout/ -> 유저 로그아웃
    @action(detail=False, methods=['POST'])
    def logout(self, request):
        user = request.user

        # 로그인 되지 않은 유저일 때
        if not user.is_authenticated:
            return Response(status=status.HTTP_403_FORBIDDEN)

        logout(request)
        return Response(self.get_serializer(user).data, status=status.HTTP_200_OK)
    
    