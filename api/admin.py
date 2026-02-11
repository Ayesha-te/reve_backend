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
    Collection,
    FilterType,
    FilterOption,
    CategoryFilter,
    ProductFilterValue,
    DimensionTemplate,
    DimensionRow,
    ProductDimensionTemplate,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


@admin.register(SubCategory)
class SubCategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "slug", "sort_order")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ["name", "slug"]


class ProductImageInline(admin.TabularInline):
    model = ProductImage
    extra = 0


class ProductVideoInline(admin.TabularInline):
    model = ProductVideo
    extra = 0


class ProductColorInline(admin.TabularInline):
    model = ProductColor
    extra = 1
    fields = ['name', 'hex_code']


class ProductSizeInline(admin.TabularInline):
    model = ProductSize
    extra = 0
    fields = ["name", "description"]


class ProductStyleInline(admin.TabularInline):
    model = ProductStyle
    extra = 0


class ProductFilterValueInline(admin.TabularInline):
    model = ProductFilterValue
    extra = 1
    autocomplete_fields = ['filter_option']


@admin.register(Product)
class ProductAdmin(admin.ModelAdmin):
    list_display = ("name", "category", "price", "in_stock", "is_bestseller", "is_new")
    list_filter = ("category", "in_stock", "is_bestseller", "is_new")
    search_fields = ["name", "slug", "short_description", "description"]
    prepopulated_fields = {"slug": ("name",)}
    inlines = [ProductImageInline, ProductVideoInline, ProductColorInline, ProductSizeInline, ProductStyleInline, ProductFilterValueInline]


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


@admin.register(Collection)
class CollectionAdmin(admin.ModelAdmin):
    list_display = ("name", "slug", "sort_order", "created_at")
    prepopulated_fields = {"slug": ("name",)}
    filter_horizontal = ('products',)


# Filter System Admin


class FilterOptionInline(admin.TabularInline):
    model = FilterOption
    extra = 3
    fields = ['name', 'slug', 'color_code', 'icon_url', 'price_delta', 'is_wingback', 'display_order', 'is_active']
    prepopulated_fields = {'slug': ('name',)}


@admin.register(FilterType)
class FilterTypeAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'display_type', 'display_order', 'is_active', 'is_default', 'is_expanded_by_default']
    list_filter = ['display_type', 'is_active', 'is_default']
    search_fields = ['name', 'slug']
    prepopulated_fields = {'slug': ('name',)}
    inlines = [FilterOptionInline]
    ordering = ['display_order', 'name']


@admin.register(FilterOption)
class FilterOptionAdmin(admin.ModelAdmin):
    list_display = ['name', 'filter_type', 'slug', 'color_code', 'icon_url', 'price_delta', 'is_wingback', 'display_order', 'is_active']
    list_filter = ['filter_type', 'is_active']
    search_fields = ['name', 'slug', 'filter_type__name']
    prepopulated_fields = {'slug': ('name',)}
    autocomplete_fields = ['filter_type']


@admin.register(CategoryFilter)
class CategoryFilterAdmin(admin.ModelAdmin):
    list_display = ['filter_type', 'category', 'subcategory', 'display_order', 'is_active']
    list_filter = ['filter_type', 'category', 'is_active']
    search_fields = ['filter_type__name', 'category__name', 'subcategory__name']
    autocomplete_fields = ['category', 'subcategory', 'filter_type']


@admin.register(ProductFilterValue)
class ProductFilterValueAdmin(admin.ModelAdmin):
    list_display = ['product', 'filter_option']
    list_filter = ['filter_option__filter_type']
    search_fields = ['product__name', 'filter_option__name']
    autocomplete_fields = ['product', 'filter_option']


# Dimension templates
class DimensionRowInline(admin.TabularInline):
    model = DimensionRow
    extra = 1
    fields = ['measurement', 'values', 'display_order']


@admin.register(DimensionTemplate)
class DimensionTemplateAdmin(admin.ModelAdmin):
    list_display = ['name', 'slug', 'is_default', 'updated_at']
    list_filter = ['is_default']
    prepopulated_fields = {'slug': ('name',)}
    search_fields = ['name', 'slug']
    inlines = [DimensionRowInline]


@admin.register(ProductDimensionTemplate)
class ProductDimensionTemplateAdmin(admin.ModelAdmin):
    list_display = ['product', 'template', 'allow_overrides']
    autocomplete_fields = ['product', 'template']
    search_fields = ['product__name', 'template__name']
