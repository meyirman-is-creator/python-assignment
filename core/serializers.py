from rest_framework import serializers
from django.contrib.auth.models import User
from django.utils import timezone
from django.utils.timesince import timesince
from .models import Category, Location, Item, Claim, Comment, Notification, ItemStatusEnum


class UserSerializer(serializers.ModelSerializer):
    full_name = serializers.SerializerMethodField()
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'full_name']
        read_only_fields = ['id', 'full_name']
        
    def get_full_name(self, obj):
        if obj.first_name or obj.last_name:
            return f"{obj.first_name} {obj.last_name}".strip()
        return obj.username


class CategorySerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Category
        fields = '__all__'
        
    def get_items_count(self, obj):
        return obj.items.count()
        
    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Название категории должно содержать хотя бы 2 символа")
        return value


class LocationSerializer(serializers.ModelSerializer):
    items_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Location
        fields = '__all__'
        
    def get_items_count(self, obj):
        return obj.items.count()
        
    def validate_name(self, value):
        if len(value) < 2:
            raise serializers.ValidationError("Название местоположения должно содержать хотя бы 2 символа")
        return value
        
    def validate(self, data):
        # Если указаны координаты, проверяем их валидность
        if 'latitude' in data and 'longitude' in data:
            if data['latitude'] and (data['latitude'] < -90 or data['latitude'] > 90):
                raise serializers.ValidationError({"latitude": "Широта должна быть в диапазоне от -90 до 90"})
            if data['longitude'] and (data['longitude'] < -180 or data['longitude'] > 180):
                raise serializers.ValidationError({"longitude": "Долгота должна быть в диапазоне от -180 до 180"})
        return data


class CommentSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    time_since = serializers.SerializerMethodField()
    
    class Meta:
        model = Comment
        fields = ['id', 'item', 'user', 'user_username', 'text', 'created_at', 'updated_at', 'time_since']
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'time_since']
        
    def get_time_since(self, obj):
        return timesince(obj.created_at, timezone.now())
        
    def validate_text(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Комментарий должен содержать хотя бы 3 символа")
        return value


class ClaimSerializer(serializers.ModelSerializer):
    user_username = serializers.ReadOnlyField(source='user.username')
    item_title = serializers.ReadOnlyField(source='item.title')
    time_since = serializers.SerializerMethodField()
    days_since_created = serializers.ReadOnlyField()
    
    class Meta:
        model = Claim
        fields = [
            'id', 'item', 'item_title', 'user', 'user_username', 'description', 
            'contact_info', 'is_approved', 'created_at', 'updated_at',
            'time_since', 'days_since_created'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'user', 'is_approved',
                           'time_since', 'days_since_created']
        
    def get_time_since(self, obj):
        return timesince(obj.created_at, timezone.now())
        
    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Описание должно содержать хотя бы 10 символов")
        return value
        
    def validate_contact_info(self, value):
        if len(value) < 5:
            raise serializers.ValidationError("Контактная информация должна содержать хотя бы 5 символов")
        return value


class ItemSerializer(serializers.ModelSerializer):
    category_name = serializers.ReadOnlyField(source='category.name')
    location_name = serializers.ReadOnlyField(source='location.name')
    user_username = serializers.ReadOnlyField(source='user.username')
    time_since_creation = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    claims_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    days_since_lost_found = serializers.ReadOnlyField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'title', 'description', 'category', 'category_name', 
            'location', 'location_name', 'status', 'status_display', 'date_lost_found', 
            'image', 'user', 'user_username', 'contact_info', 'created_at', 'updated_at',
            'time_since_creation', 'claims_count', 'comments_count', 'days_since_lost_found'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'user', 'time_since_creation', 
            'status_display', 'claims_count', 'comments_count', 'days_since_lost_found'
        ]
        
    def get_time_since_creation(self, obj):
        return timesince(obj.created_at, timezone.now())
        
    def get_status_display(self, obj):
        return ItemStatusEnum.get_display_name(obj.status)
        
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Название должно содержать хотя бы 3 символа")
        return value
        
    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Описание должно содержать хотя бы 10 символов")
        return value
        
    def validate_date_lost_found(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в будущем")
        return value


class ItemDetailSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    location = LocationSerializer(read_only=True)
    user = UserSerializer(read_only=True)
    comments = CommentSerializer(many=True, read_only=True)
    claims = serializers.SerializerMethodField()
    time_since_creation = serializers.SerializerMethodField()
    status_display = serializers.SerializerMethodField()
    claims_count = serializers.ReadOnlyField()
    comments_count = serializers.ReadOnlyField()
    days_since_lost_found = serializers.ReadOnlyField()
    
    class Meta:
        model = Item
        fields = [
            'id', 'title', 'description', 'category', 'location', 
            'status', 'status_display', 'date_lost_found', 'image', 'user', 
            'contact_info', 'created_at', 'updated_at', 'comments', 'claims',
            'time_since_creation', 'claims_count', 'comments_count', 'days_since_lost_found'
        ]
        read_only_fields = [
            'id', 'created_at', 'updated_at', 'time_since_creation', 
            'status_display', 'claims_count', 'comments_count', 'days_since_lost_found'
        ]
        
    def get_time_since_creation(self, obj):
        return timesince(obj.created_at, timezone.now())
        
    def get_status_display(self, obj):
        return ItemStatusEnum.get_display_name(obj.status)
        
    def get_claims(self, obj):
        # Только владелец объявления может видеть заявки
        request = self.context.get('request')
        if request and request.user and request.user == obj.user:
            return ClaimSerializer(obj.claims.all(), many=True).data
        return []


class NotificationSerializer(serializers.ModelSerializer):
    related_item_title = serializers.ReadOnlyField(source='related_item.title', allow_null=True)
    time_since = serializers.SerializerMethodField()
    short_message = serializers.ReadOnlyField()
    
    class Meta:
        model = Notification
        fields = [
            'id', 'user', 'title', 'message', 'short_message', 'is_read', 'related_item', 
            'related_item_title', 'created_at', 'time_since'
        ]
        read_only_fields = ['id', 'created_at', 'time_since', 'short_message']
        
    def get_time_since(self, obj):
        return timesince(obj.created_at, timezone.now())


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
            raise serializers.ValidationError({"password": "Пароли должны совпадать."})
        return data
        
    def validate_username(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Имя пользователя должно содержать хотя бы 3 символа")
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем уже существует")
        return value
        
    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует")
        return value
    
    def create(self, validated_data):
        validated_data.pop('password2')
        user = User.objects.create_user(**validated_data)
        return user


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    password = serializers.CharField(style={'input_type': 'password'})
    
    def validate_username(self, value):
        if not User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким именем не найден")
        return value


# Создаем Generic сериализатор, не расширяющий ModelSerializer
class GenericItemSerializer(serializers.Serializer):
    id = serializers.IntegerField(read_only=True)
    title = serializers.CharField(max_length=200)
    description = serializers.CharField()
    status = serializers.ChoiceField(choices=[(status.value, status.name) for status in ItemStatusEnum])
    category_id = serializers.IntegerField()
    location_id = serializers.IntegerField()
    date_lost_found = serializers.DateField()
    image = serializers.ImageField(required=False, allow_null=True)
    contact_info = serializers.CharField(max_length=200, required=False, allow_null=True, allow_blank=True)
    user_id = serializers.IntegerField(read_only=True)
    created_at = serializers.DateTimeField(read_only=True)
    updated_at = serializers.DateTimeField(read_only=True)
    
    def validate_title(self, value):
        if len(value) < 3:
            raise serializers.ValidationError("Название должно содержать хотя бы 3 символа")
        return value
        
    def validate_description(self, value):
        if len(value) < 10:
            raise serializers.ValidationError("Описание должно содержать хотя бы 10 символов")
        return value
        
    def validate_date_lost_found(self, value):
        if value > timezone.now().date():
            raise serializers.ValidationError("Дата не может быть в будущем")
        return value
        
    def validate(self, data):
        # Проверяем существование категории и местоположения
        try:
            Category.objects.get(pk=data['category_id'])
        except Category.DoesNotExist:
            raise serializers.ValidationError({"category_id": "Указанная категория не существует"})
            
        try:
            Location.objects.get(pk=data['location_id'])
        except Location.DoesNotExist:
            raise serializers.ValidationError({"location_id": "Указанное местоположение не существует"})
            
        return data
    
    def create(self, validated_data):
        # Получаем пользователя из контекста
        user = self.context['request'].user
        return Item.objects.create(user=user, **validated_data)
    
    def update(self, instance, validated_data):
        instance.title = validated_data.get('title', instance.title)
        instance.description = validated_data.get('description', instance.description)
        instance.status = validated_data.get('status', instance.status)
        instance.category_id = validated_data.get('category_id', instance.category_id)
        instance.location_id = validated_data.get('location_id', instance.location_id)
        instance.date_lost_found = validated_data.get('date_lost_found', instance.date_lost_found)
        instance.contact_info = validated_data.get('contact_info', instance.contact_info)
        
        if 'image' in validated_data and validated_data['image']:
            instance.image = validated_data['image']
        
        instance.save()
        return instance