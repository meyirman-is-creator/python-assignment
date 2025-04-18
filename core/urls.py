from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, LocationViewSet, ItemViewSet,
    ClaimViewSet, CommentViewSet, NotificationViewSet,
    UserViewSet
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'items', ItemViewSet)
router.register(r'claims', ClaimViewSet)
router.register(r'comments', CommentViewSet)
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    path('', include(router.urls)),
]