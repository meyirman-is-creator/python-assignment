from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import HttpResponseForbidden
from django.urls import reverse

from .models import Category, Location, Item, Claim, Comment, Notification, ItemStatus
from .forms import ItemForm, LoginForm, RegistrationForm, ClaimForm, CommentForm


def home_view(request):
    """Главная страница сайта"""
    recent_items = Item.objects.all().order_by('-created_at')[:6]
    
    # Статистика для отображения на главной странице
    stats = {
        'total_items': Item.objects.count(),
        'lost_items': Item.objects.filter(status=ItemStatus.LOST).count(),
        'found_items': Item.objects.filter(status=ItemStatus.FOUND).count(),
    }
    
    return render(request, 'pages/home.html', {
        'recent_items': recent_items,
        'stats': stats,
    })


def about_view(request):
    """Страница о сервисе"""
    return render(request, 'pages/about.html')


def faq_view(request):
    """Страница с FAQ"""
    return render(request, 'pages/faq.html')


def item_list_view(request):
    """Список всех объявлений с фильтрацией"""
    items = Item.objects.all().order_by('-created_at')
    
    # Фильтр по статусу
    status = request.GET.get('status')
    if status:
        items = items.filter(status=status)
    
    # Поиск
    query = request.GET.get('q')
    if query:
        items = items.filter(
            Q(title__icontains=query) |
            Q(description__icontains=query) |
            Q(category__name__icontains=query) |
            Q(location__name__icontains=query)
        )
    
    # Сортировка
    sort = request.GET.get('sort', '-created_at')
    items = items.order_by(sort)
    
    # Пагинация
    paginator = Paginator(items, 9)  # 9 объявлений на страницу
    page_number = request.GET.get('page')
    items_page = paginator.get_page(page_number)
    
    # Список категорий для фильтрации
    categories = Category.objects.all()
    
    return render(request, 'items/list.html', {
        'items': items_page,
        'categories': categories,
        'status': status,
        'query': query,
        'sort': sort,
    })


def item_detail_view(request, pk):
    """Детальная страница объявления"""
    item = get_object_or_404(Item, pk=pk)
    comments = item.comments.all().order_by('-created_at')
    
    # Если пользователь - владелец объявления, показываем ему заявки
    claims = []
    if request.user.is_authenticated and request.user == item.user:
        claims = item.claims.all().order_by('-created_at')
    
    return render(request, 'items/detail.html', {
        'item': item,
        'comments': comments,
        'claims': claims,
    })


@login_required
def item_create_view(request):
    """Создание нового объявления"""
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            item = form.save(commit=False)
            item.user = request.user
            item.save()
            messages.success(request, 'Объявление успешно создано!')
            return redirect('item_detail', pk=item.pk)
    else:
        form = ItemForm()
    
    categories = Category.objects.all()
    locations = Location.objects.all()
    
    return render(request, 'items/create.html', {
        'form': form,
        'categories': categories,
        'locations': locations,
    })


@login_required
def item_edit_view(request, pk):
    """Редактирование объявления"""
    item = get_object_or_404(Item, pk=pk)
    
    # Проверка прав доступа
    if request.user != item.user:
        return HttpResponseForbidden("У вас нет прав для редактирования этого объявления")
    
    if request.method == 'POST':
        form = ItemForm(request.POST, request.FILES, instance=item)
        if form.is_valid():
            form.save()
            messages.success(request, 'Объявление успешно обновлено!')
            return redirect('item_detail', pk=item.pk)
    else:
        form = ItemForm(instance=item)
    
    categories = Category.objects.all()
    locations = Location.objects.all()
    
    return render(request, 'items/edit.html', {
        'form': form,
        'item': item,
        'categories': categories,
        'locations': locations,
    })


@login_required
def item_delete_view(request, pk):
    """Удаление объявления"""
    item = get_object_or_404(Item, pk=pk)
    
    # Проверка прав доступа
    if request.user != item.user and not request.user.is_staff:
        return HttpResponseForbidden("У вас нет прав для удаления этого объявления")
    
    if request.method == 'POST':
        item.delete()
        messages.success(request, 'Объявление успешно удалено!')
        return redirect('my_items')
    
    return render(request, 'items/delete.html', {'item': item})


@login_required
def my_items_view(request):
    """Список объявлений текущего пользователя"""
    items = Item.objects.filter(user=request.user).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(items, 9)
    page_number = request.GET.get('page')
    items_page = paginator.get_page(page_number)
    
    return render(request, 'items/my_items.html', {'items': items_page})


@login_required
def claim_create_view(request, item_id):
    """Создание заявки на возврат"""
    item = get_object_or_404(Item, pk=item_id)
    
    # Пользователь не может создать заявку на свое же объявление
    if request.user == item.user:
        messages.error(request, 'Вы не можете создать заявку на свое собственное объявление')
        return redirect('item_detail', pk=item_id)
    
    # Проверка, что пользователь еще не создавал заявку на это объявление
    existing_claim = Claim.objects.filter(item=item, user=request.user).exists()
    if existing_claim:
        messages.error(request, 'Вы уже создали заявку на это объявление')
        return redirect('item_detail', pk=item_id)
    
    if request.method == 'POST':
        form = ClaimForm(request.POST)
        if form.is_valid():
            claim = form.save(commit=False)
            claim.item = item
            claim.user = request.user
            claim.save()
            
            # Создаем уведомление для владельца объявления
            Notification.objects.create(
                user=item.user,
                title=f"Новая заявка на ваше объявление",
                message=f"Пользователь {request.user.username} оставил заявку на ваше объявление '{item.title}'",
                related_item=item
            )
            
            messages.success(request, 'Ваша заявка успешно отправлена!')
            return redirect('item_detail', pk=item_id)
    else:
        form = ClaimForm()
    
    return render(request, 'claims/create.html', {
        'form': form,
        'item': item,
    })


@login_required
def claim_approve_view(request, pk):
    """Одобрение заявки на возврат"""
    claim = get_object_or_404(Claim, pk=pk)
    
    # Проверка прав доступа
    if request.user != claim.item.user:
        return HttpResponseForbidden("Только владелец объявления может одобрить заявку")
    
    if request.method == 'POST':
        claim.is_approved = True
        claim.save()
        
        # Обновляем статус объявления
        item = claim.item
        item.status = ItemStatus.CLAIMED if item.status == ItemStatus.LOST else ItemStatus.RETURNED
        item.save()
        
        # Создаем уведомление для пользователя, создавшего заявку
        Notification.objects.create(
            user=claim.user,
            title=f"Ваша заявка одобрена",
            message=f"Ваша заявка на объявление '{item.title}' была одобрена владельцем",
            related_item=item
        )
        
        messages.success(request, 'Заявка успешно одобрена!')
        return redirect('item_detail', pk=claim.item.pk)
    
    return redirect('item_detail', pk=claim.item.pk)


@login_required
def my_claims_view(request):
    """Список заявок текущего пользователя"""
    claims = Claim.objects.filter(user=request.user).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(claims, 10)
    page_number = request.GET.get('page')
    claims_page = paginator.get_page(page_number)
    
    return render(request, 'claims/my_claims.html', {'claims': claims_page})


@login_required
def comment_create_view(request, item_id):
    """Создание комментария к объявлению"""
    item = get_object_or_404(Item, pk=item_id)
    
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.item = item
            comment.user = request.user
            comment.save()
            
            # Создаем уведомление для владельца объявления (если комментарий не от него самого)
            if request.user != item.user:
                Notification.objects.create(
                    user=item.user,
                    title=f"Новый комментарий к вашему объявлению",
                    message=f"Пользователь {request.user.username} оставил комментарий к вашему объявлению '{item.title}'",
                    related_item=item
                )
            
            messages.success(request, 'Комментарий успешно добавлен!')
        else:
            messages.error(request, 'Ошибка при добавлении комментария')
    
    return redirect('item_detail', pk=item_id)


@login_required
def profile_view(request):
    """Профиль пользователя"""
    # Получаем последние 3 объявления пользователя
    user_items = Item.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    # Получаем последние 3 заявки пользователя
    user_claims = Claim.objects.filter(user=request.user).order_by('-created_at')[:3]
    
    return render(request, 'account/profile.html', {
        'user_items': user_items,
        'user_claims': user_claims,
    })


def login_view(request):
    """Страница входа пользователя"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)
            
            if user is not None:
                login(request, user)
                
                # Перенаправляем пользователя на страницу, с которой он пришел
                next_url = request.POST.get('next', 'home')
                return redirect(next_url)
            else:
                messages.error(request, 'Неверное имя пользователя или пароль')
    else:
        form = LoginForm()
    
    return render(request, 'account/login.html', {
        'form': form,
        'next': request.GET.get('next', ''),
    })


def register_view(request):
    """Страница регистрации пользователя"""
    if request.user.is_authenticated:
        return redirect('home')
    
    if request.method == 'POST':
        form = RegistrationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            messages.success(request, 'Регистрация успешно завершена!')
            return redirect('home')
    else:
        form = RegistrationForm()
    
    return render(request, 'account/register.html', {'form': form})


@login_required
def logout_view(request):
    """Выход пользователя"""
    logout(request)
    messages.success(request, 'Вы успешно вышли из системы')
    return redirect('home')


@login_required
def notifications_view(request):
    """Страница со всеми уведомлениями пользователя"""
    notifications = Notification.objects.filter(user=request.user).order_by('-created_at')
    
    # Пагинация
    paginator = Paginator(notifications, 10)
    page_number = request.GET.get('page')
    notifications_page = paginator.get_page(page_number)
    
    return render(request, 'account/notifications.html', {'notifications': notifications_page})


@login_required
def mark_notification_read_view(request, pk):
    """Отметка уведомления как прочитанного"""
    notification = get_object_or_404(Notification, pk=pk, user=request.user)
    notification.is_read = True
    notification.save()
    
    # Если есть related_item, перенаправляем на его страницу
    if notification.related_item:
        return redirect('item_detail', pk=notification.related_item.pk)
    
    return redirect('notifications')


@login_required
def mark_all_notifications_read_view(request):
    """Отметка всех уведомлений как прочитанных"""
    if request.method == 'POST':
        Notification.objects.filter(user=request.user, is_read=False).update(is_read=True)
        messages.success(request, 'Все уведомления отмечены как прочитанные')
    
    return redirect('notifications')