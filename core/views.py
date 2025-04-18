from rest_framework import viewsets, permissions, status, filters
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from django.db.models import Q
from django.utils import timezone
from .models import Category, Location, Item, Claim, Comment, Notification
from .serializers import (
    CategorySerializer, LocationSerializer, ItemSerializer, ItemDetailSerializer,
    ClaimSerializer, CommentSerializer, NotificationSerializer,
    UserSerializer, UserRegistrationSerializer, UserLoginSerializer
)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'created_at']


class LocationViewSet(viewsets.ModelViewSet):
    queryset = Location.objects.all()
    serializer_class = LocationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'address']
    ordering_fields = ['name', 'created_at']


class ItemViewSet(viewsets.ModelViewSet):
    queryset = Item.objects.all()
    serializer_class = ItemSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['title', 'description', 'category__name', 'location__name', 'status']
    ordering_fields = ['created_at', 'date_lost_found', 'title']
    
    def get_serializer_class(self):
        if self.action == 'retrieve':
            return ItemDetailSerializer
        return ItemSerializer
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
    
    @action(detail=False, methods=['get'])
    def lost(self, request):
        lost_items = Item.objects.filter(status='LOST')
        page = self.paginate_queryset(lost_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(lost_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def found(self, request):
        found_items = Item.objects.filter(status='FOUND')
        page = self.paginate_queryset(found_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(found_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        recent_items = Item.objects.all().order_by('-created_at')[:10]
        serializer = self.get_serializer(recent_items, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def my_items(self, request):
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=status.HTTP_401_UNAUTHORIZED)
        my_items = Item.objects.filter(user=request.user)
        page = self.paginate_queryset(my_items)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = self.get_serializer(my_items, many=True)
        return Response(serializer.data)


class ClaimViewSet(viewsets.ModelViewSet):
    queryset = Claim.objects.all()
    serializer_class = ClaimSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Create notification for item owner
        item = serializer.validated_data['item']
        if item.user != self.request.user:
            Notification.objects.create(
                user=item.user,
                title=f"New claim for your {item.title}",
                message=f"User {self.request.user.username} has claimed your {item.get_status_display()} item: {item.title}",
                related_item=item
            )
    
    @action(detail=True, methods=['post'])
    def approve(self, request, pk=None):
        claim = self.get_object()
        if request.user != claim.item.user:
            return Response({"error": "Only the item owner can approve claims"}, status=status.HTTP_403_FORBIDDEN)
        
        claim.is_approved = True
        claim.save()
        
        # Update item status
        item = claim.item
        item.status = 'CLAIMED' if item.status == 'LOST' else 'RETURNED'
        item.save()
        
        # Create notification for claimer
        Notification.objects.create(
            user=claim.user,
            title=f"Claim approved for {item.title}",
            message=f"Your claim for {item.title} has been approved by the owner.",
            related_item=item
        )
        
        return Response({"message": "Claim approved successfully"})


class CommentViewSet(viewsets.ModelViewSet):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
        
        # Create notification for item owner
        item = serializer.validated_data['item']
        if item.user != self.request.user:
            Notification.objects.create(
                user=item.user,
                title=f"New comment on your {item.title}",
                message=f"User {self.request.user.username} has commented on your item: {item.title}",
                related_item=item
            )


class NotificationViewSet(viewsets.ReadOnlyModelViewSet):
    serializer_class = NotificationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user).order_by('-created_at')
    
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