from django.db import models
from django.contrib.auth.models import User


class Category(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.URLField(max_length=1000, blank=True)
    sort_order = models.IntegerField(default=0)

    def __str__(self) -> str:
        return self.name


class SubCategory(models.Model):
    category = models.ForeignKey(Category, related_name="subcategories", on_delete=models.CASCADE)
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.URLField(max_length=1000, blank=True)
    sort_order = models.IntegerField(default=0)

    def __str__(self) -> str:
        return f"{self.category.name} -> {self.name}"


class Collection(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    description = models.TextField(blank=True)
    image = models.URLField(max_length=1000, blank=True)
    sort_order = models.IntegerField(default=0)
    products = models.ManyToManyField("Product", related_name="collections", blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class Product(models.Model):
    name = models.CharField(max_length=255)
    slug = models.SlugField(unique=True)
    category = models.ForeignKey(Category, related_name="products", on_delete=models.CASCADE)
    subcategory = models.ForeignKey(
        SubCategory, related_name="products", on_delete=models.SET_NULL, null=True, blank=True
    )
    price = models.DecimalField(max_digits=10, decimal_places=2)
    original_price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    discount_percentage = models.IntegerField(default=0)
    description = models.TextField()
    short_description = models.TextField(blank=True)
    features = models.JSONField(default=list, blank=True)
    delivery_info = models.TextField(blank=True)
    returns_guarantee = models.TextField(blank=True)
    delivery_charges = models.DecimalField(max_digits=10, decimal_places=2, default=0.00)
    in_stock = models.BooleanField(default=True)
    is_bestseller = models.BooleanField(default=False)
    is_new = models.BooleanField(default=False)
    rating = models.DecimalField(max_digits=3, decimal_places=1, default=0.0)
    review_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self) -> str:
        return self.name


class ProductImage(models.Model):
    product = models.ForeignKey(Product, related_name="images", on_delete=models.CASCADE)
    url = models.URLField(max_length=1000)


class ProductVideo(models.Model):
    product = models.ForeignKey(Product, related_name="videos", on_delete=models.CASCADE)
    url = models.URLField(max_length=1000)


class ProductColor(models.Model):
    product = models.ForeignKey(Product, related_name="colors", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)
    image = models.URLField(max_length=1000, blank=True)


class ProductSize(models.Model):
    product = models.ForeignKey(Product, related_name="sizes", on_delete=models.CASCADE)
    name = models.CharField(max_length=50)


class ProductStyle(models.Model):
    product = models.ForeignKey(Product, related_name="styles", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    options = models.JSONField(default=list)


class Order(models.Model):
    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("paid", "Paid"),
        ("shipped", "Shipped"),
        ("delivered", "Delivered"),
        ("cancelled", "Cancelled"),
    ]
    user = models.ForeignKey(User, related_name="orders", on_delete=models.SET_NULL, null=True, blank=True)
    first_name = models.CharField(max_length=100)
    last_name = models.CharField(max_length=100)
    email = models.EmailField()
    phone = models.CharField(max_length=20)
    address = models.TextField()
    city = models.CharField(max_length=100)
    postal_code = models.CharField(max_length=20)
    total_amount = models.DecimalField(max_digits=10, decimal_places=2)
    delivery_charges = models.DecimalField(max_digits=10, decimal_places=2)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    payment_method = models.CharField(max_length=50)
    payment_id = models.CharField(max_length=255, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)


class OrderItem(models.Model):
    order = models.ForeignKey(Order, related_name="items", on_delete=models.CASCADE)
    product = models.ForeignKey(Product, on_delete=models.SET_NULL, null=True)
    quantity = models.IntegerField()
    price = models.DecimalField(max_digits=10, decimal_places=2)
    size = models.CharField(max_length=50, blank=True)
    color = models.CharField(max_length=50, blank=True)
    style = models.CharField(max_length=100, blank=True)


class Review(models.Model):
    product = models.ForeignKey(Product, related_name="reviews", on_delete=models.CASCADE)
    name = models.CharField(max_length=100)
    rating = models.IntegerField(default=5)
    comment = models.TextField(blank=True)
    approved = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
