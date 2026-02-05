from django.contrib import admin
from .models import (
    Category,
    SubCategory,
    Product,
    ProductImage,
    ProductVideo,
    ProductColor,
    ProductSize,
    ProductStyle,
    Order,
    OrderItem,
    Review,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 0


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0


class ProductStyleInline(admin.TabularInline):
    model = ProductStyle
    extra = 0


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "in_stock", "is_bestseller", "is_new")
    list_filter = ("category", "in_stock", "is_bestseller", "is_new")
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVideoInline, ProductColorInline, ProductSizeInline, ProductStyleInline]


class OrderItemInline(admin.TabularInline):
    model = OrderItem
    extra = 0


@admin.register(Order)
class OrderAdmin(admin.ModelAdmin):
    list_display = ("id", "email", "total_amount", "status", "payment_method", "created_at")
    list_filter = ("status", "payment_method")
    inlines = [OrderItemInline]


@admin.register(Review)
class ReviewAdmin(admin.ModelAdmin):
    list_display = ("product", "name", "rating", "approved", "created_at")
    list_filter = ("approved", "rating")
