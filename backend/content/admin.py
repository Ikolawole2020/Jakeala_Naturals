from django.contrib import admin
from .models import Article, NewsletterSubscriber, ContactMessage

admin.site.register(Article)
admin.site.register(NewsletterSubscriber)
admin.site.register(ContactMessage)
