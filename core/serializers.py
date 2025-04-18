from rest_framework import serializers
from django.contrib.auth.models import User
from .models import Category, Location, Item, Claim, Comment, Notification


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id']


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = '__all__'


class LocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = Location
        fields = '__all__'


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    location_name = serializers.ReadOnlyField(source='location.name')
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Item
        fields = ['id', 'title', 'description', 'category', 'category_name', 
                  'location', 'location_name', 'status', 'date_lost_found', 
                  'image', 'user', 'user_username', 'contact_info', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class ItemDetailSerializer(ItemSerializer):
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    
    class Meta:
        model = Item
        fields = ['id', 'title', 'description', 'category', 'location', 
                  'status', 'date_lost_found', 'image', 'user', 
                  'contact_info', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at']


class ClaimSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    item_title = serializers.ReadOnlyField(source='item.title')
    
    class Meta:
        model = Claim
        fields = ['id', 'item', 'item_title', 'user', 'user_username', 'description', 
                  'contact_info', 'is_approved', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'is_approved']


class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    
    class Meta:
        model = Comment
        fields = ['id', 'item', 'user', 'user_username', 'text', 'created_at', 'updated_at']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user']


class NotificationSerializer(serializers.ModelSerializer):
    related_item_title = serializers.ReadOnlyField(source='related_item.title', allow_null=True)
    
    class Meta:
        model = Notification
        fields = ['id', 'user', 'title', 'message', 'is_read', 'related_item', 
                  'related_item_title', 'created_at']
        read_only_fields = ['id', 'created_at']


class UserRegistrationSerializer(serializers.ModelSerializer):
    password2 = serializers.CharField(style={'input_type': 'password'}, write_only=True)
    
    class Meta:
        model = User
        fields = ['username', 'email', 'password', 'password2', 'first_name', 'last_name']
        extra_kwargs = {
            'password': {'write_only': True}
        }
    
    def validate(self, data):
        if data['password'] != data['password2']:
            raise serializers.ValidationError({"password": "Passwords must match."})
        return data
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={'input_type': 'password'})