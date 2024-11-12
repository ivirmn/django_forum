from django import forms
from django.contrib.auth.forms import UserCreationForm
from .models import *


class CustomUserCreationForm(UserCreationForm):
    telegram_nickname = forms.CharField(max_length=50, required=False, label="Telegram Nickname")
    personal_site = forms.URLField(required=False, label="Personal Site")

    class Meta:
        model = User
        fields = ('username', 'password1', 'password2', 'email')

    def save(self, commit=True):
        user = super().save(commit=False)
        if commit:
            user.save()

        # Создание или обновление профиля пользователя
        user_profile = UserProfile.objects.create(user=user)
        user_profile.telegram_nickname = self.cleaned_data['telegram_nickname']
        user_profile.personal_site = self.cleaned_data['personal_site']
        user_profile.save()

        return user

class SectionForm(forms.ModelForm):
    class Meta:
        model = Section
        fields = ['name', 'description']  # поля для заполнения

class SubsectionForm(forms.ModelForm):
    class Meta:
        model = Subsection
        fields = ['name', 'description', 'section']  # поле для выбора раздела

class BanForm(forms.ModelForm):
    duration = forms.IntegerField(min_value=1, required=True)  # Количество дней для бана

    class Meta:
        model = Ban
        fields = ['reason', 'duration']

    def clean_duration(self):
        # Дополнительная валидация для продолжительности бана (если необходимо)
        duration = self.cleaned_data.get('duration')
        if duration <= 0:
            raise forms.ValidationError("Duration must be at least 1 day.")
        return duration

class TopicForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content']  # Поля для создания топика


class TopicEditForm(forms.ModelForm):
    class Meta:
        model = Topic
        fields = ['title', 'content']

class PostForm(forms.ModelForm):
    class Meta:
        model = Post
        fields = ['content']  # Только содержание поста


class UserProfileForm(forms.ModelForm):
    class Meta:
        model = UserProfile
        fields = ['telegram_nickname', 'personal_site']
        labels = {
            'telegram_nickname': 'Telegram Nickname',
            'personal_site': 'Personal Website'
        }


class UserEmailForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ['email']
        labels = {
            'email': 'Email Address'
        }


class PasswordChangeForm(forms.Form):
    current_password = forms.CharField(widget=forms.PasswordInput, label="Current Password")
    new_password = forms.CharField(widget=forms.PasswordInput, label="New Password")
    confirm_new_password = forms.CharField(widget=forms.PasswordInput, label="Confirm New Password")

    def clean(self):
        cleaned_data = super().clean()
        new_password = cleaned_data.get("new_password")
        confirm_new_password = cleaned_data.get("confirm_new_password")

        if new_password and new_password != confirm_new_password:
            raise forms.ValidationError("Passwords do not match.")
        return cleaned_data

class MessageForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea, label='Write your message:')

    class Meta:
        model = Message
        fields = ['content']