from django.urls import path
from . import web_views

urlpatterns = [
    # Домашняя страница и информационные страницы
    path('', web_views.home_view, name='home'),
    path('about/', web_views.about_view, name='about'),
    path('faq/', web_views.faq_view, name='faq'),
    
    # Страницы для работы с объявлениями
    path('items/', web_views.item_list_view, name='item_list'),
    path('items/<int:pk>/', web_views.item_detail_view, name='item_detail'),
    path('items/create/', web_views.item_create_view, name='item_create'),
    path('items/<int:pk>/edit/', web_views.item_edit_view, name='item_edit'),
    path('items/<int:pk>/delete/', web_views.item_delete_view, name='item_delete'),
    path('my-items/', web_views.my_items_view, name='my_items'),
    
    # Страницы для работы с заявками
    path('items/<int:item_id>/claim/', web_views.claim_create_view, name='claim_create'),
    path('claims/<int:pk>/approve/', web_views.claim_approve_view, name='claim_approve'),
    path('my-claims/', web_views.my_claims_view, name='my_claims'),
    
    # Комментарии
    path('items/<int:item_id>/comment/', web_views.comment_create_view, name='comment_create'),
    
    # Страницы аутентификации
    path('accounts/login/', web_views.login_view, name='login'),
    path('accounts/register/', web_views.register_view, name='register'),
    path('accounts/logout/', web_views.logout_view, name='logout'),
    path('accounts/profile/', web_views.profile_view, name='profile'),
    
    # Уведомления
    path('notifications/', web_views.notifications_view, name='notifications'),
    path('notifications/<int:pk>/read/', web_views.mark_notification_read_view, name='mark_notification_read'),
    path('notifications/read-all/', web_views.mark_all_notifications_read_view, name='mark_all_read'),
]