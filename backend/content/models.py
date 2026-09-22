from django.db import models


class Article(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    excerpt = models.CharField(max_length=280)
    body = models.TextField()
    category_label = models.CharField(max_length=80, default="Wellness")
    cover = models.URLField(blank=True)
    published = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]


class NewsletterSubscriber(models.Model):
    email = models.EmailField(unique=True)
    created_at = models.DateTimeField(auto_now_add=True)


class ContactMessage(models.Model):
    KIND = [("contact", "Contact"), ("wholesale", "Wholesale")]
    kind = models.CharField(max_length=20, choices=KIND, default="contact")
    name = models.CharField(max_length=140)
    email = models.EmailField()
    phone = models.CharField(max_length=40, blank=True)
    subject = models.CharField(max_length=200, blank=True)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
