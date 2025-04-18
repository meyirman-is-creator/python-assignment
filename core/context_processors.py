from .models import Notification


def notifications_processor(request):
    """
    Контекстный процессор для добавления уведомлений на все страницы сайта.
    Добавляет в контекст:
    - notifications: Список последних 5 уведомлений пользователя
    - unread_notifications_count: Количество непрочитанных уведомлений
    """
    context = {
        'notifications': None,
        'unread_notifications_count': 0
    }
    
    # Проверяем, авторизован ли пользователь
    if request.user.is_authenticated:
        # Получаем последние 5 уведомлений для пользователя
        notifications = Notification.objects.filter(
            user=request.user
        ).order_by('-created_at')[:5]
        
        # Считаем количество непрочитанных уведомлений
        unread_count = Notification.objects.filter(
            user=request.user, 
            is_read=False
        ).count()
        
        context['notifications'] = notifications
        context['unread_notifications_count'] = unread_count
    
    return context