from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, LocationViewSet, ItemViewSet,
    ClaimViewSet, CommentViewSet, NotificationViewSet,
    UserViewSet, ItemListView, ItemDetailView,
    LostItemsListView, FoundItemsListView, MyItemsListView
)

router = DefaultRouter()
router.register(r'categories', CategoryViewSet)
router.register(r'locations', LocationViewSet)
router.register(r'items', ItemViewSet, basename='item')
router.register(r'claims', ClaimViewSet, basename='claim')
router.register(r'comments', CommentViewSet, basename='comment')
router.register(r'notifications', NotificationViewSet, basename='notification')
router.register(r'users', UserViewSet, basename='user')

urlpatterns = [
    # Router URLs
    path('', include(router.urls)),
    
    # Generic views для GET запросов
    path('items-list/', ItemListView.as_view(), name='items-list'),
    path('items-detail/<int:pk>/', ItemDetailView.as_view(), name='items-detail'),
    path('items-lost/', LostItemsListView.as_view(), name='items-lost'),
    path('items-found/', FoundItemsListView.as_view(), name='items-found'),
    path('my-items-list/', MyItemsListView.as_view(), name='my-items-list'),
]