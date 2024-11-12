from cryptography import fernet
from cryptography.fernet import InvalidToken
from django.db.models import Count
from django.utils import timezone
from datetime import *
from django.contrib.auth.models import User
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.http import HttpResponseNotFound
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib.auth import update_session_auth_hash
from django.contrib.auth import login
from django.contrib.auth.forms import AuthenticationForm
from django.contrib.auth.views import LoginView
from .forms import CustomUserCreationForm
from .models import Section, Subsection, Topic, Post, UserProfile, Warn, Ban
from django.contrib import messages
from .forms import *
from django.http import HttpResponse

def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)  # Автоматический вход после регистрации
            return redirect('home')  # Перенаправление на домашнюю страницу
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/register.html', {'form': form})

# Логин будет использовать стандартную форму Django
class CustomLoginView(LoginView):
    template_name = 'registration/login.html'

# Проверка на админа
def admin_check(user):
    return user.is_superuser


def is_moderator(user):
    return user.groups.filter(name__in=['Admin', 'Moderator']).exists()


# Главная страница, отображающая список разделов
def section_list(request):
    sections = Section.objects.all()
    return render(request, 'forum/section_list.html', {'sections': sections})


def subsection_list(request, section_id):
    section = get_object_or_404(Section, id=section_id)

    # Получаем все подразделы текущего раздела
    subsections = section.subsections.all()

    # Для каждой секции аннотируем количество тем
    for subsection in subsections:
        subsection.num_topics = subsection.topics.count()  # Прямо вычисляем количество тем

    context = {
        'section': section,
        'subsections': subsections,
    }

    return render(request, 'forum/subsection_list.html', context)
# Страница с топиками в конкретном подразделе
def topic_list(request, subsection_id):
    subsection = get_object_or_404(Subsection, id=subsection_id)
    topics = subsection.topics.all()
    return render(request, 'forum/topic_list.html', {'subsection': subsection, 'topics': topics})


# Страница для просмотра конкретного топика
@login_required
def topic_detail(request, topic_id, parent_post_id=None):
    topic = get_object_or_404(Topic, id=topic_id)
    posts = topic.posts.all()

    parent_post = None
    if parent_post_id:
        parent_post = get_object_or_404(Post, id=parent_post_id)

    if request.method == 'POST':
        post_form = PostForm(request.POST)
        if post_form.is_valid():
            post = post_form.save(commit=False)
            post.topic = topic
            post.author = request.user
            post.parent_post = parent_post  # Устанавливаем, что это ответ на родительский пост, если он есть
            post.save()
            return redirect('topic_detail', topic_id=topic.id)
    else:
        post_form = PostForm()

    return render(request, 'forum/topic_detail.html', {
        'topic': topic,
        'posts': posts,
        'post_form': post_form,
        'parent_post': parent_post  # Передаем родительский пост в шаблон (если есть)
    })


@login_required
def create_topic(request, subsection_id):
    subsection = get_object_or_404(Subsection, id=subsection_id)  # Получаем субсекцию по ID

    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.subsection = subsection  # Привязываем топик к выбранной субсекции
            topic.author = request.user  # Устанавливаем автора как текущего пользователя
            topic.save()
            return redirect('topic_list', subsection_id=subsection.id)  # Перенаправляем на страницу субсекции
    else:
        form = TopicForm()

    return render(request, 'forum/create_topic.html', {'form': form, 'subsection': subsection})

@login_required
def edit_topic(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)

    if not topic.can_edit(request.user):
        return redirect('topic_detail', topic_id=topic.id)

    if request.method == 'POST':
        form = TopicEditForm(request.POST, instance=topic)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.edited_at = timezone.now()
            topic.save()
            return redirect('topic_detail', topic_id=topic.id)
    else:
        form = TopicEditForm(instance=topic)

    return render(request, 'forum/edit_topic.html', {'form': form, 'topic': topic})


# Добавление нового поста в топик (только для авторизованных пользователей)
@login_required
def add_post(request, topic_id):
    topic = get_object_or_404(Topic, id=topic_id)
    if request.method == 'POST':
        content = request.POST.get('content')
        Post.objects.create(topic=topic, content=content, author=request.user)
        return redirect('topic_detail', topic_id=topic.id)
    return render(request, 'forum/add_post.html', {'topic': topic})


@login_required
def user_profile(request, user_id):
    user_profile = get_object_or_404(UserProfile, user__id=user_id)
    warnings = Warn.objects.filter(user=user_profile.user)

    # Проверяем, является ли текущий пользователь администратором или модератором
    is_moderator_or_admin = request.user.groups.filter(name__in=['Admin', 'Moderator']).exists()

    # Логика изменения кармы
    if request.method == 'POST':
        action = request.POST.get('action')
        if action == 'increase':
            user_profile.karma += 1
        elif action == 'decrease':
            user_profile.karma -= 1
        user_profile.save()
        return redirect('user_profile', user_id=user_profile.user.id)

    return render(request, 'forum/user_profile.html', {
        # Проверяем, является ли текущий пользователь администратором или модератором
        'user_profile': user_profile,
        'warnings': warnings,
        'is_moderator_or_admin': is_moderator_or_admin,  # Добавляем переменную в контекст
    })



# Сигналы для создания профиля при создании пользователя
@receiver(post_save, sender=User)
def create_user_profile(sender, instance, created, **kwargs):
    if created:
        UserProfile.objects.create(user=instance)


@receiver(post_save, sender=User)
def save_user_profile(sender, instance, **kwargs):
    instance.userprofile.save()


# Создание раздела
@user_passes_test(admin_check)
def create_section(request):
    if request.method == 'POST':
        form = SectionForm(request.POST)  # Используем SectionForm напрямую
        if form.is_valid():
            form.save()
            return redirect('section_list')
    else:
        form = SectionForm()  # Используем SectionForm напрямую
    return render(request, 'forum/create_section.html', {'form': form})


# Создание подраздела
@user_passes_test(admin_check)
def create_subsection(request):
    if request.method == 'POST':
        form = SubsectionForm(request.POST)  # Используем SubsectionForm напрямую
        if form.is_valid():
            form.save()
            return redirect('section_list')
    else:
        form = SubsectionForm()  # Используем SubsectionForm напрямую
    return render(request, 'forum/create_subsection.html', {'form': form})


def subsection_list(request, section_id):
    section = Section.objects.get(id=section_id)
    is_moderator_or_admin = request.user.groups.filter(name__in=['Admin', 'Moderator']).exists()
    subsections = Subsection.objects.filter(section=section)
    return render(request, 'forum/subsection_list.html', {'section': section, 'subsections': subsections,
    'is_moderator_or_admin': is_moderator_or_admin,  # Добавляем переменную в контекст
    })


def topic_list(request, subsection_id):
    subsection = Subsection.objects.get(id=subsection_id)
    is_moderator_or_admin = request.user.groups.filter(name__in=['Admin', 'Moderator']).exists()
    topics = Topic.objects.filter(subsection=subsection)
    return render(request, 'forum/topic_list.html', {'subsection': subsection, 'topics': topics,
    'is_moderator_or_admin': is_moderator_or_admin})


@login_required
@user_passes_test(is_moderator)
def warn_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        reason = request.POST.get('reason')
        Warn.objects.create(user=user, moderator=request.user, reason=reason)
        return redirect('user_profile', user_id=user.id)

    return render(request, 'forum/warn_user.html', {'user': user})


# Модерация: бан пользователей
@login_required
@user_passes_test(is_moderator)
def ban_user(request, user_id):
    user = get_object_or_404(User, id=user_id)

    if request.method == 'POST':
        form = BanForm(request.POST)
        if form.is_valid():
            reason = form.cleaned_data['reason']
            duration = form.cleaned_data['duration']  # Время бана в днях
            end_date = timezone.now() + timedelta(days=duration)

            # Создаем запись о бане
            Ban.objects.create(user=user, moderator=request.user, reason=reason, end_date=end_date)
            return redirect('user_profile', user_id=user.id)
    else:
        form = BanForm()

    return render(request, 'forum/ban_user.html', {'user': user, 'form': form})


@login_required
def manage_account(request):
    user_profile = request.user.userprofile
    if request.method == 'POST':
        profile_form = UserProfileForm(request.POST, instance=user_profile)
        email_form = UserEmailForm(request.POST, instance=request.user)
        password_form = PasswordChangeForm(request.POST)

        if 'update_profile' in request.POST and profile_form.is_valid():
            profile_form.save()
            messages.success(request, "Profile updated successfully.")
            return redirect('manage_account')

        if 'update_email' in request.POST and email_form.is_valid():
            email_form.save()
            messages.success(request, "Email updated successfully.")
            return redirect('manage_account')

        if 'change_password' in request.POST and password_form.is_valid():
            current_password = password_form.cleaned_data['current_password']
            new_password = password_form.cleaned_data['new_password']

            if request.user.check_password(current_password):
                request.user.set_password(new_password)
                request.user.save()
                update_session_auth_hash(request,
                                         request.user)  # Оставляем пользователя залогиненным после смены пароля
                messages.success(request, "Password changed successfully.")
                return redirect('manage_account')
            else:
                messages.error(request, "Current password is incorrect.")

    else:
        profile_form = UserProfileForm(instance=user_profile)
        email_form = UserEmailForm(instance=request.user)
        password_form = PasswordChangeForm()

    context = {
        'profile_form': profile_form,
        'email_form': email_form,
        'password_form': password_form
    }
    return render(request, 'forum/manage_account.html', context)


def forum_stats(request):
    # Общее количество разделов и подразделов
    section_count = Section.objects.count()
    subsection_count = Subsection.objects.count()

    # Общее количество тем и сообщений
    topic_count = Topic.objects.count()
    post_count = Post.objects.count()

    # Количество тем по разделам
    topics_by_section = Section.objects.annotate(num_topics=models.Count('subsections__topics'))

    # Количество тем по подразделам
    topics_by_subsection = Subsection.objects.annotate(num_topics=models.Count('topics'))

    context = {
        'section_count': section_count,
        'subsection_count': subsection_count,
        'topic_count': topic_count,
        'post_count': post_count,
        'topics_by_section': topics_by_section,
        'topics_by_subsection': topics_by_subsection
    }
    return render(request, 'forum/forum_stats.html', context)


@login_required
def conversation_list(request):
    conversations = request.user.conversations.all()
    return render(request, 'forum/conversation_list.html', {'conversations': conversations})


@login_required
def start_conversation(request, user_id):
    other_user = get_object_or_404(User, id=user_id)

    # Найти или создать переписку с двумя участниками
    conversation = Conversation.objects.filter(
        participants=request.user
    ).filter(
        participants=other_user
    ).annotate(num_participants=Count('participants')).filter(num_participants=2).first()

    if not conversation:
        conversation = Conversation.objects.create()
        conversation.participants.add(request.user, other_user)

    return redirect('conversation_detail', conversation_id=conversation.id)

@login_required
def conversation_detail(request, conversation_id):
    conversation = get_object_or_404(Conversation, id=conversation_id)

    if request.method == 'POST':
        message_text = request.POST.get('message')
        if message_text:
            Message.objects.create(conversation=conversation, author=request.user, content=message_text)

    messages = conversation.messages.all().order_by('created_at')  # Получаем сообщения в порядке создания
    return render(request, 'forum/conversation_detail.html', {
        'conversation': conversation,
        'messages': messages,
    })

@login_required
def conversation_list(request):
    conversations = Conversation.objects.filter(participants=request.user)
    return render(request, 'forum/conversation_list.html', {'conversations': conversations})