from django.db import models


class Category(models.Model):
    name = models.CharField(max_length=120)
    slug = models.SlugField(unique=True)
    tagline = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    image = models.URLField(blank=True)
    sort_order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ["sort_order", "name"]
        verbose_name_plural = "categories"

    def __str__(self):
        return self.name


class Product(models.Model):
    category = models.ForeignKey(Category, related_name="products", on_delete=models.PROTECT)
    name = models.CharField(max_length=200)
    slug = models.SlugField(unique=True)
    short_benefit = models.CharField(max_length=280)
    description = models.TextField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    compare_at = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    size = models.CharField(max_length=80, blank=True)
    sku = models.CharField(max_length=40, unique=True)
    image = models.URLField()
    gallery = models.JSONField(default=list, blank=True)
    benefits = models.JSONField(default=list, blank=True)
    ingredients = models.TextField(blank=True)
    directions = models.TextField(blank=True)
    who_it_is_for = models.TextField(blank=True)
    warnings = models.TextField(blank=True)
    disclaimer = models.TextField(blank=True)
    faqs = models.JSONField(default=list, blank=True)
    is_featured = models.BooleanField(default=False)
    is_supplement = models.BooleanField(default=False)
    in_stock = models.BooleanField(default=True)
    rating = models.DecimalField(max_digits=3, decimal_places=2, default=4.80)
    review_count = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-is_featured", "name"]

    def __str__(self):
        return self.name


class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    author = models.CharField(max_length=80)
    rating = models.PositiveSmallIntegerField(default=5)
    title = models.CharField(max_length=140)
    body = models.TextField()
    verified = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
