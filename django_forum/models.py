from django.db import models
from django.contrib.auth.models import User
from datetime import timedelta
from django.utils import timezone
from cryptography.fernet import Fernet
from django.conf import settings


# Модель для разделов форума (Section)
class Section(models.Model):
    name = models.CharField(max_length=100)  # Название раздела
    description = models.TextField(blank=True, null=True)  # Описание раздела
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания раздела

    def __str__(self):
        return self.name


# Модель для подразделов (Subsection)
class Subsection(models.Model):
    section = models.ForeignKey(Section, on_delete=models.CASCADE, related_name='subsections')  # Связь с разделом
    name = models.CharField(max_length=100)  # Название подраздела
    description = models.TextField(blank=True, null=True)  # Описание подраздела
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания

    def __str__(self):
        return self.name


# Модель для топиков (Topic)
class Topic(models.Model):
    subsection = models.ForeignKey('Subsection', on_delete=models.CASCADE, related_name='topics')  # Связь с подразделом
    title = models.CharField(max_length=200)  # Название топика
    content = models.TextField()  # Содержание топика
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # Автор топика
    curator = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                related_name='curated_topics')  # Куратор
    edited_at = models.DateTimeField(null=True, blank=True)  # Время последнего редактирования

    def __str__(self):
        return self.title

    def can_edit(self, user):
        return user.is_superuser or user.is_staff or user == self.author or user == self.curator  # Проверка прав на редактирование


# Модель для постов (Post)
class Post(models.Model):
    topic = models.ForeignKey('Topic', on_delete=models.CASCADE, related_name='posts')  # Связь с топиком
    content = models.TextField()  # Содержание поста
    created_at = models.DateTimeField(auto_now_add=True)  # Время создания поста
    author = models.ForeignKey(User, on_delete=models.CASCADE)  # Автор поста
    parent_post = models.ForeignKey('self', null=True, blank=True, on_delete=models.SET_NULL,
                                    related_name='replies')  # Ответ на другой пост

    def __str__(self):
        return f'Post by {self.author.username} on {self.created_at}'

    def get_absolute_url(self):
        return f'/topic/{self.topic.id}/#post-{self.id}'  # Ссылка на конкретный пост


# Модель для кармы пользователя
class UserProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE)  # Связь с пользователем
    karma = models.IntegerField(default=0)  # Карма пользователя
    last_activity = models.DateTimeField(auto_now=True)  # Последняя активность пользователя
    telegram_nickname = models.CharField(max_length=50, null=True, blank=True, default=None)  # Telegram ник
    personal_site = models.URLField(null=True, blank=True, default=None)  # Персональный сайт

    def __str__(self):
        return self.user.username


# Модель для варнов (Warn)
class Warn(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='warns')  # Пользователь, которому выдан варн
    moderator = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='moderator_warns')  # Модератор, который выдал варн
    reason = models.TextField()  # Причина варна
    created_at = models.DateTimeField(auto_now_add=True)  # Время выдачи варна

    def __str__(self):
        return f'Warn for {self.user.username}'


# Модель для банов (Ban)
class Ban(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='bans')  # Забаненный пользователь
    moderator = models.ForeignKey(User, on_delete=models.CASCADE,
                                  related_name='moderator_bans')  # Модератор, который забанил
    reason = models.TextField()  # Причина бана
    start_date = models.DateTimeField(auto_now_add=True)  # Начало бана
    end_date = models.DateTimeField()  # Конец бана
    is_active = models.BooleanField(default=True)  # Активен ли бан

    def __str__(self):
        return f'Ban for {self.user.username}'


class Conversation(models.Model):
    participants = models.ManyToManyField(User)  # Участники переписки
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'Conversation {self.id}'


class Message(models.Model):
    conversation = models.ForeignKey(Conversation, on_delete=models.CASCADE, related_name='messages')
    author = models.ForeignKey(User, on_delete=models.CASCADE)
    content = models.TextField()  # Сообщение без шифрования
    created_at = models.DateTimeField(auto_now_add=True, null=True)

    def __str__(self):
        return f'Message from {self.author.username} in conversation {self.conversation.id}'
