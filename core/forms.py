from django import forms
from django.contrib.auth.models import User
from django.contrib.auth.forms import UserCreationForm
from .models import Item, Claim, Comment


class ItemForm(forms.ModelForm):
    """Форма для создания и редактирования объявлений"""
    class Meta:
        model = Item
        fields = ['title', 'description', 'category', 'location', 'status', 
                  'date_lost_found', 'image', 'contact_info']
        widgets = {
            'date_lost_found': forms.DateInput(attrs={'type': 'date'}),
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class ClaimForm(forms.ModelForm):
    """Форма для создания заявки на возврат"""
    class Meta:
        model = Claim
        fields = ['description', 'contact_info']
        widgets = {
            'description': forms.Textarea(attrs={'rows': 5}),
        }


class CommentForm(forms.ModelForm):
    """Форма для создания комментария"""
    class Meta:
        model = Comment
        fields = ['text']
        widgets = {
            'text': forms.Textarea(attrs={'rows': 3}),
        }


class LoginForm(forms.Form):
    """Форма для входа пользователя"""
    username = forms.CharField(max_length=150, label='Имя пользователя')
    password = forms.CharField(widget=forms.PasswordInput, label='Пароль')


class RegistrationForm(UserCreationForm):
    """Форма для регистрации пользователя"""
    email = forms.EmailField(required=True, label='Email')
    first_name = forms.CharField(max_length=30, required=False, label='Имя')
    last_name = forms.CharField(max_length=30, required=False, label='Фамилия')

    class Meta:
        model = User
        fields = ['username', 'email', 'first_name', 'last_name', 'password1', 'password2']
    
    def save(self, commit=True):
        user = super().save(commit=False)
        user.email = self.cleaned_data['email']
        user.first_name = self.cleaned_data['first_name']
        user.last_name = self.cleaned_data['last_name']
        if commit:
            user.save()
        return user