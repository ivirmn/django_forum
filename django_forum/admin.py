from django.contrib import admin
from .models import Section, Subsection, Topic, Post, UserProfile, User, Conversation, Message, Ban

admin.site.register(Section)
admin.site.register(Subsection)
admin.site.register(Topic)
admin.site.register(Post)
admin.site.register(UserProfile)
admin.site.register(Conversation)
admin.site.register(Ban)