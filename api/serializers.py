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
    ProductFabric,
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
        fields = ("id", "name", "hex_code")


class ProductSizeSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductSize
        fields = ("id", "name", "description")


class ProductStyleSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductStyle
        fields = ("id", "name", "options")


class ProductFabricSerializer(serializers.ModelSerializer):
    class Meta:
        model = ProductFabric
        fields = ("id", "name", "image_url")


class DimensionRowSerializer(serializers.ModelSerializer):
    class Meta:
        model = DimensionRow
        fields = ("id", "measurement", "values", "display_order")


class DimensionTemplateSerializer(serializers.ModelSerializer):
    rows = DimensionRowSerializer(many=True, read_only=True)

    class Meta:
        model = DimensionTemplate
        fields = ("id", "name", "slug", "notes", "is_default", "rows")


class ProductSerializer(serializers.ModelSerializer):
    images = ProductImageSerializer(many=True, read_only=True)
    videos = ProductVideoSerializer(many=True, read_only=True)
    colors = ProductColorSerializer(many=True, read_only=True)
    sizes = ProductSizeSerializer(many=True, read_only=True)
    styles = ProductStyleSerializer(many=True, read_only=True)
    fabrics = ProductFabricSerializer(many=True, read_only=True)
    filters = serializers.SerializerMethodField()
    computed_dimensions = serializers.SerializerMethodField()
    wingback_width_delta_cm = serializers.SerializerMethodField()
    dimension_template = serializers.SerializerMethodField()
    dimension_template_name = serializers.SerializerMethodField()
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
            "dimensions",
            "faqs",
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
            "fabrics",
            "filters",
            "computed_dimensions",
            "dimension_template",
            "dimension_template_name",
            "wingback_width_delta_cm",
            "category_name",
            "subcategory_name",
            "category_slug",
            "subcategory_slug",
        )


class ProductWriteSerializer(serializers.ModelSerializer):
    slug = serializers.CharField(required=False, allow_blank=True, max_length=50)
    images = ProductImageSerializer(many=True, required=False)
    videos = ProductVideoSerializer(many=True, required=False)
    colors = ProductColorSerializer(many=True, required=False)
    sizes = ProductSizeSerializer(many=True, required=False)
    styles = ProductStyleSerializer(many=True, required=False)
    fabrics = ProductFabricSerializer(many=True, required=False)
    dimension_template = serializers.IntegerField(required=False, allow_null=True, write_only=True)

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
            "dimensions",
            "faqs",
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
            "fabrics",
            "dimension_template",
        )

    def _generate_unique_slug(self, raw_value: str) -> str:
        max_length = Product._meta.get_field("slug").max_length or 50
        base_slug = (slugify(raw_value) or "product")[:max_length]
        slug = base_slug
        counter = 1

        queryset = Product.objects.all()
        if self.instance:
            queryset = queryset.exclude(pk=self.instance.pk)

        while queryset.filter(slug=slug).exists():
            suffix = f"-{counter}"
            truncated_base = base_slug[: max_length - len(suffix)]
            slug = f"{truncated_base}{suffix}"
            counter += 1

        return slug

    def validate(self, attrs):
        description = attrs.get("description", getattr(self.instance, "description", ""))
        short_description = attrs.get("short_description", getattr(self.instance, "short_description", ""))

        if isinstance(description, str):
            description = description.strip()
            attrs["description"] = description

        if isinstance(short_description, str):
            short_description = short_description.strip()

        if not short_description and isinstance(description, str) and description:
            first_sentence = description.split(".")[0].strip()
            short_description = first_sentence or description
            if len(short_description) > 220:
                short_description = f"{short_description[:217].rstrip()}..."

        attrs["short_description"] = short_description or ""

        raw_dimensions = attrs.get("dimensions", getattr(self.instance, "dimensions", []))
        cleaned_dimensions = []
        if isinstance(raw_dimensions, list):
            for row in raw_dimensions:
                if not isinstance(row, dict):
                    continue
                measurement = str(row.get("measurement", "")).strip()
                values = row.get("values", {})
                if not measurement or not isinstance(values, dict):
                    continue
                cleaned_values = {}
                for key, value in values.items():
                    size_key = str(key).strip()
                    if not size_key:
                        continue
                    cleaned_values[size_key] = str(value).strip()
                if cleaned_values:
                    cleaned_dimensions.append({"measurement": measurement, "values": cleaned_values})
        attrs["dimensions"] = cleaned_dimensions

        raw_slug_or_name = attrs.get("slug") or attrs.get("name")
        if raw_slug_or_name:
            attrs["slug"] = self._generate_unique_slug(raw_slug_or_name)
        elif self.instance and self.instance.slug:
            attrs["slug"] = self._generate_unique_slug(self.instance.slug)

        dt_id = attrs.pop("dimension_template", None)
        if dt_id:
            try:
                attrs["_dimension_template_obj"] = DimensionTemplate.objects.get(id=dt_id)
            except DimensionTemplate.DoesNotExist:
                raise serializers.ValidationError({"dimension_template": "Dimension template not found"})
        elif dt_id is None:
            attrs["_dimension_template_obj"] = None
        return attrs

    def get_filters(self, obj):
        values = ProductFilterValue.objects.filter(product=obj).select_related("filter_option__filter_type")
        by_type = {}
        for val in values:
            ft = val.filter_option.filter_type
            if ft.id not in by_type:
                by_type[ft.id] = {
                    "id": ft.id,
                    "name": ft.name,
                    "slug": ft.slug,
                    "display_type": ft.display_type,
                    "icon_url": ft.icon_url,
                    "display_hint": ft.display_hint,
                    "is_default": ft.is_default,
                    "is_expanded_by_default": ft.is_expanded_by_default,
                    "options": [],
                }
            opt = val.filter_option
            by_type[ft.id]["options"].append({
                "id": opt.id,
                "name": opt.name,
                "slug": opt.slug,
                "color_code": opt.color_code,
                "icon_url": opt.icon_url,
                "price_delta": opt.price_delta,
                "is_wingback": opt.is_wingback,
                "metadata": opt.metadata,
            })
        # preserve display order
        ordered = sorted(by_type.values(), key=lambda item: (0 if item["is_default"] else 1, item["name"]))
        return ordered

    def get_dimension_template(self, obj):
        if hasattr(obj, "dimension_template_link"):
            return obj.dimension_template_link.template.id
        return None

    def get_dimension_template_name(self, obj):
        if hasattr(obj, "dimension_template_link"):
            return obj.dimension_template_link.template.name
        return ""

    def _merge_dimensions(self, obj):
        template_rows = []
        if hasattr(obj, "dimension_template_link"):
            template_rows = list(obj.dimension_template_link.template.rows.all().order_by("display_order"))
        override_rows = obj.dimensions or []
        merged = []
        # map for quick override lookup
        override_map = {row.get("measurement"): row.get("values", {}) for row in override_rows if isinstance(row, dict)}
        for row in template_rows:
            values = dict(row.values or {})
            if row.measurement in override_map:
                values.update({k: v for k, v in override_map[row.measurement].items() if v})
            merged.append({"measurement": row.measurement, "values": values})
        # Add overrides that weren't in template
        for measurement, values in override_map.items():
            if not any(r["measurement"] == measurement for r in merged):
                merged.append({"measurement": measurement, "values": values})
        return merged

    def get_computed_dimensions(self, obj):
        return self._merge_dimensions(obj)

    def get_wingback_width_delta_cm(self, obj):
        return 4  # requirement: wingback headboard adds approx 4 cm width


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
        fields = ['id', 'name', 'slug', 'color_code', 'icon_url', 'price_delta', 'is_wingback', 'metadata', 'product_count']
    
    def get_product_count(self, obj):
        # This will be computed based on current category context
        return getattr(obj, 'product_count', 0)


class FilterTypeSerializer(serializers.ModelSerializer):
    options = FilterOptionSerializer(many=True, read_only=True)
    
    class Meta:
        model = FilterType
        fields = ['id', 'name', 'slug', 'display_type', 'icon_url', 'display_hint', 'is_default', 'is_expanded_by_default', 'options']


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
