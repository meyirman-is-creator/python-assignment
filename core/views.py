from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from rest_framework.generics import ListAPIView, RetrieveAPIView
from django.contrib.auth import authenticate
from django.db.models import Q, Prefetch
from django.utils import timezone
from .models import Category, Location, Item, Claim, Comment, Notification
from .serializers import (
    CategorySerializer, LocationSerializer, ItemSerializer, ItemDetailSerializer,
    ClaimSerializer, CommentSerializer, NotificationSerializer,
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer,
    GenericItemSerializer
)
from .profiling import profile_endpoint


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']
    
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']
    
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class ItemViewSet(viewsets.ModelViewSet):
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'location__name', 'status']
    ordering_fields = ['created_at', 'date_lost_found', 'title']
    
    def get_queryset(self):
        # Используем prefetch_related для решения проблемы N+1
        return Item.objects.all().select_related(
            'category', 'location', 'user'
        ).prefetch_related(
            'comments', 'claims'
        )
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ItemDetailSerializer
        elif self.action == 'create' and self.request.query_params.get('generic', False):
            return GenericItemSerializer
        return ItemSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
    
    @action(detail=False, methods=['get'])
    def lost(self, request):
        lost_items = self.get_queryset().filter(status='LOST')
        page = self.paginate_queryset(lost_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(lost_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def found(self, request):
        found_items = self.get_queryset().filter(status='FOUND')
        page = self.paginate_queryset(found_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(found_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_items = self.get_queryset().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_items(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        my_items = self.get_queryset().filter(user=request.user)
        page = self.paginate_queryset(my_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(my_items, many=True)
        return Response(serializer.data)
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class ClaimViewSet(viewsets.ModelViewSet):
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Claim.objects.all().select_related('item', 'user', 'item__category', 'item__location')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Create notification for item owner
        item = serializer.validated_data['item']
        if item.user != self.request.user:
            Notification.objects.create(
                user=item.user,
                title=f"Новая заявка на ваше объявление {item.title}",
                message=f"Пользователь {self.request.user.username} подал заявку на ваше объявление: {item.title}",
                related_item=item
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        claim = self.get_object()
        if request.user != claim.item.user:
            return Response({"error": "Только владелец объявления может одобрить заявку"}, status=status.HTTP_403_FORBIDDEN)
        
        claim.is_approved = True
        claim.save()
        
        # Update item status
        item = claim.item
        item.status = 'CLAIMED' if item.status == 'LOST' else 'RETURNED'
        item.save()
        
        # Create notification for claimer
        Notification.objects.create(
            user=claim.user,
            title=f"Заявка одобрена для {item.title}",
            message=f"Ваша заявка на объявление {item.title} была одобрена владельцем.",
            related_item=item
        )
        
        return Response({"message": "Заявка успешно одобрена"})
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class CommentViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_queryset(self):
        return Comment.objects.all().select_related('item', 'user')
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Create notification for item owner
        item = serializer.validated_data['item']
        if item.user != self.request.user:
            Notification.objects.create(
                user=item.user,
                title=f"Новый комментарий к вашему объявлению {item.title}",
                message=f"Пользователь {self.request.user.username} оставил комментарий к вашему объявлению: {item.title}",
                related_item=item
            )
            
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).select_related('related_item').order_by('-created_at')
    
    @action(detail=True, methods=['post'])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"message": "Notification marked as read"})
    
    @action(detail=False, methods=['post'])
    def mark_all_read(self, request):
        notifications = self.get_queryset()
        notifications.update(is_read=True)
        return Response({"message": "All notifications marked as read"})
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class UserViewSet(viewsets.GenericViewSet):
    queryset = Token.objects.none()  # Not used but required for DRF
    
    @action(detail=False, methods=['post'])
    def register(self, request):
        serializer = UserRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            token, created = Token.objects.get_or_create(user=user)
            return Response({
                "user": UserSerializer(user).data,
                "token": token.key
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['post'])
    def login(self, request):
        serializer = UserLoginSerializer(data=request.data)
        if serializer.is_valid():
            username = serializer.validated_data['username']
            password = serializer.validated_data['password']
            user = authenticate(username=username, password=password)
            if user:
                token, created = Token.objects.get_or_create(user=user)
                return Response({
                    "user": UserSerializer(user).data,
                    "token": token.key
                })
            return Response({"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.IsAuthenticated])
    def me(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)
    
    @action(detail=False, methods=['post'], permission_classes=[permissions.IsAuthenticated])
    def logout(self, request):
        try:
            request.user.auth_token.delete()
        except:
            pass
        return Response({"message": "Successfully logged out"}, status=status.HTTP_200_OK)
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


# Generic Views для GET запросов (ListAPIView и RetrieveAPIView)
class ItemListView(ListAPIView):
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'location__name', 'status']
    ordering_fields = ['created_at', 'date_lost_found', 'title']
    
    def get_queryset(self):
        return Item.objects.all().select_related(
            'category', 'location', 'user'
        )
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class ItemDetailView(RetrieveAPIView):
    serializer_class = ItemDetailSerializer
    
    def get_queryset(self):
        return Item.objects.all().select_related(
            'category', 'location', 'user'
        ).prefetch_related(
            'comments__user', 'claims__user'
        )
        
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['request'] = self.request
        return context
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class LostItemsListView(ListAPIView):
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'location__name']
    ordering_fields = ['created_at', 'date_lost_found', 'title']
    
    def get_queryset(self):
        return Item.objects.filter(status='LOST').select_related(
            'category', 'location', 'user'
        )
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class FoundItemsListView(ListAPIView):
    serializer_class = ItemSerializer
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'location__name']
    ordering_fields = ['created_at', 'date_lost_found', 'title']
    
    def get_queryset(self):
        return Item.objects.filter(status='FOUND').select_related(
            'category', 'location', 'user'
        )
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)


class MyItemsListView(ListAPIView):
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'location__name', 'status']
    ordering_fields = ['created_at', 'date_lost_found', 'title']
    
    def get_queryset(self):
        return Item.objects.filter(user=self.request.user).select_related(
            'category', 'location'
        )
        
    def dispatch(self, request, *args, **kwargs):
        return profile_endpoint(super().dispatch)(request, *args, **kwargs)