
from django.contrib import admin
from django.urls import path

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('', views.section_list, name='section_list'),
    path('admin/', admin.site.urls),  # Это подключает админку
    path('section/<int:section_id>/', views.subsection_list, name='subsection_list'),
    path('subsection/<int:subsection_id>/', views.topic_list, name='topic_list'),
    path('topic/<int:topic_id>/', views.topic_detail, name='topic_detail'),
    path('topic/<int:topic_id>/edit/', views.edit_topic, name='edit_topic'),
    path('topic/<int:topic_id>/reply/<int:parent_post_id>/', views.topic_detail, name='reply_to_post'),
    path('subsection/<int:subsection_id>/create_topic/', views.create_topic, name='create_topic'),
    path('topic/<int:topic_id>/add_post/', views.add_post, name='add_post'),
    path('section/create/', views.create_section, name='create_section'),
    path('subsection/create/', views.create_subsection, name='create_subsection'),
    path('login/', auth_views.LoginView.as_view(), name='login'),  # маршрут для входа
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),  # маршрут для выхода
    path('user/<int:user_id>/', views.user_profile, name='user_profile'),
    path('user/<int:user_id>/warn/', views.warn_user, name='warn_user'),
    path('user/<int:user_id>/ban/', views.ban_user, name='ban_user'),
    path('stats/', views.forum_stats, name='forum_stats'),
    path('qms/', views.conversation_list, name='conversation_list'),
    path('qms/conversation/<int:conversation_id>/', views.conversation_detail, name='conversation_detail'),
    path('qms/start/<int:user_id>/', views.start_conversation, name='start_conversation'),
    path('user/<int:user_id>/ban/', views.ban_user, name='ban_user'),
]
