from rest_framework import viewsets
from rest_framework.pagination import PageNumberPagination

from .models import Achievement, Cat

from .serializers import AchievementSerializer, CatSerializer


class CatViewSet(viewsets.ModelViewSet):
    """
    CRUD для котиков: список, создание, просмотр, изменение, удаление.

    При создании кота его владельцем автоматически становится
    текущий аутентифицированный пользователь (perform_create).
    Список отдаётся с постраничной пагинацией.

    """

    queryset = Cat.objects.all()
    serializer_class = CatSerializer
    pagination_class = PageNumberPagination 

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user) 


class AchievementViewSet(viewsets.ModelViewSet):
    """
    CRUD для достижений: список, создание, просмотр, изменение, удаление.

    Список отдаётся целиком, без пагинации.

    """

    queryset = Achievement.objects.all()
    serializer_class = AchievementSerializer
    pagination_class = None