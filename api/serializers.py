from django.contrib.auth.models import User
from django.utils.text import slugify
from rest_framework import serializers
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
)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("id", "username", "email", "first_name", "last_name")


class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ("username", "password", "email", "first_name", "last_name")

    def create(self, validated_data):
        user = User.objects.create_user(**validated_data)
        return user


class SubCategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = SubCategory
        fields = "__all__"


class CategorySerializer(serializers.ModelSerializer):
    subcategories = SubCategorySerializer(many=True, read_only=True)

    class Meta:
        model = Category
        fields = "__all__"




class ProductImageSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductImage
        fields = ("id", "url")


class ProductVideoSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductVideo
        fields = ("id", "url")


class ProductColorSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductColor
        fields = ("id", "name", "image")


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ("id", "name")


class ProductStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStyle
        fields = ("id", "name", "options")


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    styles = ProductStyleSerializer(many=True, read_only=True)
    category_name = serializers.ReadOnlyField(source="category.name")
    subcategory_name = serializers.ReadOnlyField(source="subcategory.name")
    category_slug = serializers.ReadOnlyField(source="category.slug")
    subcategory_slug = serializers.ReadOnlyField(source="subcategory.slug")

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "subcategory",
            "price",
            "original_price",
            "discount_percentage",
            "description",
            "short_description",
            "features",
            "delivery_info",
            "returns_guarantee",
            "delivery_charges",
            "in_stock",
            "is_bestseller",
            "is_new",
            "rating",
            "review_count",
            "created_at",
            "updated_at",
            "images",
            "videos",
            "colors",
            "sizes",
            "styles",
            "category_name",
            "subcategory_name",
            "category_slug",
            "subcategory_slug",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(required=False, allow_blank=True)
    images = ProductImageSerializer(many=True, required=False)
    videos = ProductVideoSerializer(many=True, required=False)
    colors = ProductColorSerializer(many=True, required=False)
    sizes = serializers.ListField(child=serializers.CharField(), required=False)
    styles = ProductStyleSerializer(many=True, required=False)

    class Meta:
        model = Product
        fields = (
            "id",
            "name",
            "slug",
            "category",
            "subcategory",
            "price",
            "original_price",
            "discount_percentage",
            "description",
            "short_description",
            "features",
            "delivery_info",
            "returns_guarantee",
            "delivery_charges",
            "in_stock",
            "is_bestseller",
            "is_new",
            "rating",
            "review_count",
            "images",
            "videos",
            "colors",
            "sizes",
            "styles",
        )

    def validate(self, attrs):
        if not attrs.get("slug") and attrs.get("name"):
            attrs["slug"] = slugify(attrs["name"])
        return attrs


class CollectionSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(required=False, allow_blank=True)
    products = serializers.PrimaryKeyRelatedField(many=True, queryset=Product.objects.all(), required=False)
    products_data = ProductSerializer(source="products", many=True, read_only=True)

    class Meta:
        model = Collection
        fields = (
            "id",
            "name",
            "slug",
            "description",
            "image",
            "sort_order",
            "created_at",
            "updated_at",
            "products",
            "products_data",
        )


class OrderItemSerializer(serializers.ModelSerializer):
    product_name = serializers.ReadOnlyField(source="product.name")

    class Meta:
        model = OrderItem
        fields = "__all__"


class OrderSerializer(serializers.ModelSerializer):
    items = OrderItemSerializer(many=True, read_only=True)

    class Meta:
        model = Order
        fields = "__all__"


class ReviewSerializer(serializers.ModelSerializer):
    class Meta:
        model = Review
        fields = "__all__"


class FilterOptionSerializer(serializers.ModelSerializer):
    product_count = serializers.SerializerMethodField()
    
    class Meta:
        model = FilterOption
        fields = ['id', 'name', 'slug', 'color_code', 'product_count']
    
    def get_product_count(self, obj):
        # This will be computed based on current category context
        return getattr(obj, 'product_count', 0)


class FilterTypeSerializer(serializers.ModelSerializer):
    options = FilterOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FilterType
        fields = ['id', 'name', 'slug', 'display_type', 'is_expanded_by_default', 'options']


class CategoryFilterSerializer(serializers.ModelSerializer):
    filter_type_name = serializers.ReadOnlyField(source="filter_type.name")
    category_name = serializers.ReadOnlyField(source="category.name")
    subcategory_name = serializers.ReadOnlyField(source="subcategory.name")
    
    class Meta:
        model = CategoryFilter
        fields = "__all__"


class ProductFilterValueSerializer(serializers.ModelSerializer):
    filter_option_name = serializers.ReadOnlyField(source="filter_option.name")
    filter_type_name = serializers.ReadOnlyField(source="filter_option.filter_type.name")
    
    class Meta:
        model = ProductFilterValue
        fields = "__all__"
