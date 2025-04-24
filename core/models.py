from django.db import models
from django.contrib.auth.models import User
from enum import Enum as PyEnum

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name
    
    class Meta:
        verbose_name_plural = "Categories"


class Location(models.Model):
    name = models.CharField(max_length=200)
    address = models.TextField(blank=True, null=True)
    latitude = models.FloatField(blank=True, null=True)
    longitude = models.FloatField(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.name


class ItemStatusEnum(PyEnum):
    LOST = 'LOST'
    FOUND = 'FOUND'
    CLAIMED = 'CLAIMED'
    RETURNED = 'RETURNED'
    
    @classmethod
    def choices(cls):
        return [(item.value, item.name) for item in cls]

    @classmethod
    def get_display_name(cls, value):
        for item in cls:
            if item.value == value:
                return item.name
        return None


class Item(models.Model):
    title = models.CharField(max_length=200)
    description = models.TextField()
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True, related_name='items')
    location = models.ForeignKey(Location, on_delete=models.SET_NULL, null=True, related_name='items')
    status = models.CharField(
        max_length=20, 
        choices=[(status.value, status.name) for status in ItemStatusEnum],
        default=ItemStatusEnum.LOST.value
    )
    date_lost_found = models.DateField()
    image = models.ImageField(upload_to='items/', blank=True, null=True)
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='items')
    contact_info = models.CharField(max_length=200, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return self.title
        
    @property
    def claims_count(self):
        return self.claims.count()
        
    @property
    def comments_count(self):
        return self.comments.count()
        
    @property
    def status_display(self):
        return ItemStatusEnum.get_display_name(self.status)
        
    @property
    def days_since_lost_found(self):
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        return (today - self.date_lost_found).days


class Claim(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='claims')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='claims')
    description = models.TextField(help_text="Please describe why you believe this item belongs to you")
    contact_info = models.CharField(max_length=200)
    is_approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Claim for {self.item.title} by {self.user.username}"
        
    @property
    def days_since_created(self):
        from django.utils import timezone
        import datetime
        today = timezone.now().date()
        return (today - self.created_at.date()).days


class Comment(models.Model):
    item = models.ForeignKey(Item, on_delete=models.CASCADE, related_name='comments')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='comments')
    text = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Comment by {self.user.username} on {self.item.title}"


class Notification(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='notifications')
    title = models.CharField(max_length=200)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    related_item = models.ForeignKey(Item, on_delete=models.SET_NULL, null=True, blank=True, related_name='notifications')
    created_at = models.DateTimeField(auto_now_add=True)
    
    def __str__(self):
        return self.title
        
    @property
    def short_message(self):
        if len(self.message) > 100:
            return f"{self.message[:100]}..."
        return self.message