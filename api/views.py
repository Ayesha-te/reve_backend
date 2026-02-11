import uuid
import os
import stripe
import requests
from urllib.parse import urljoin

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify
from django.db.models import Prefetch
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework.exceptions import ValidationError

from supabase import create_client

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
    ProductDimensionTemplate,
)
from .serializers import (
    RegisterSerializer,
    CategorySerializer,
    SubCategorySerializer,
    ProductSerializer,
    ProductWriteSerializer,
    OrderSerializer,
    ReviewSerializer,
    CollectionSerializer,
    FilterTypeSerializer,
    CategoryFilterSerializer,
    ProductFilterValueSerializer,
)


class HealthCheckView(APIView):
    permission_classes = [AllowAny]

    def get(self, request):
        return Response({"status": "ok"})


class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (AllowAny,)
    serializer_class = RegisterSerializer


class IsAdminOrReadOnly(IsAdminUser):
    def has_permission(self, request, view):
        if request.method in ("GET", "HEAD", "OPTIONS"):
            return True
        return super().has_permission(request, view)


class CategoryViewSet(viewsets.ModelViewSet):
    queryset = Category.objects.all().order_by("sort_order", "name")
    serializer_class = CategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        slug = self.request.query_params.get("slug")
        if slug:
            queryset = queryset.filter(slug=slug)
        return queryset

    def perform_create(self, serializer):
        slug = serializer.validated_data.get("slug") or slugify(serializer.validated_data.get("name", ""))
        serializer.save(slug=slug)


class SubCategoryViewSet(viewsets.ModelViewSet):
    queryset = SubCategory.objects.all().order_by("sort_order", "name")
    serializer_class = SubCategorySerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        category_id = self.request.query_params.get("category")
        if category_id:
            queryset = queryset.filter(category_id=category_id)
        return queryset

    def perform_create(self, serializer):
        slug = serializer.validated_data.get("slug") or slugify(serializer.validated_data.get("name", ""))
        serializer.save(slug=slug)


class CollectionViewSet(viewsets.ModelViewSet):
    queryset = Collection.objects.all().prefetch_related("products").order_by("sort_order", "name")
    serializer_class = CollectionSerializer
    permission_classes = [IsAdminOrReadOnly]

    def get_queryset(self):
        queryset = super().get_queryset()
        slug = self.request.query_params.get("slug")
        if slug:
            queryset = queryset.filter(slug=slug)
        return queryset

    def perform_create(self, serializer):
        slug = serializer.validated_data.get("slug") or slugify(serializer.validated_data.get("name", ""))
        serializer.save(slug=slug)


class ProductViewSet(viewsets.ModelViewSet):
    queryset = Product.objects.all().select_related("category", "subcategory").prefetch_related(
        "images",
        "videos",
        "colors",
        "sizes",
        "styles",
        "fabrics",
        Prefetch(
            "filter_values",
            queryset=ProductFilterValue.objects.select_related("filter_option__filter_type"),
            to_attr="filter_values_all",
        ),
        "dimension_template_link__template__rows",
    ).order_by("-created_at")
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        if self.action == "list":
            from .serializers import ProductListSerializer
            return ProductListSerializer
        if self.request.method in ("POST", "PUT", "PATCH"):
            return ProductWriteSerializer
        return ProductSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        category = self.request.query_params.get("category")
        subcategory = self.request.query_params.get("subcategory")
        bestseller = self.request.query_params.get("bestseller")
        is_new = self.request.query_params.get("is_new")
        slug = self.request.query_params.get("slug")
        
        if category:
            queryset = queryset.filter(category__slug=category)
        if subcategory:
            queryset = queryset.filter(subcategory__slug=subcategory)
        if bestseller:
            queryset = queryset.filter(is_bestseller=True)
        if is_new:
            queryset = queryset.filter(is_new=True)
        if slug:
            queryset = queryset.filter(slug=slug)
        
        # Apply dynamic filters from filter system
        filter_types = FilterType.objects.filter(is_active=True)
        for ft in filter_types:
            filter_values = self.request.query_params.get(ft.slug)
            if filter_values:
                option_slugs = filter_values.split(',')
                queryset = queryset.filter(
                    filter_values__filter_option__slug__in=option_slugs,
                    filter_values__filter_option__filter_type=ft
                ).distinct()
        
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        images = data.pop("images", [])
        videos = data.pop("videos", [])
        colors = data.pop("colors", [])
        sizes = data.pop("sizes", [])
        styles = data.pop("styles", [])
        fabrics = data.pop("fabrics", [])
        filter_values = data.pop("filter_values", [])

        images, videos, colors, sizes, styles, fabrics = self._validate_related_data(
            images, videos, colors, sizes, styles, fabrics
        )

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        self._handle_related_data(product, images, videos, colors, sizes, styles, fabrics)
        self._handle_filter_values(product, filter_values)
        self._handle_dimension_template(product, serializer.validated_data.get("_dimension_template_obj"))

        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        images = data.pop("images", None)
        videos = data.pop("videos", None)
        colors = data.pop("colors", None)
        sizes = data.pop("sizes", None)
        styles = data.pop("styles", None)
        fabrics = data.pop("fabrics", None)
        filter_values = data.pop("filter_values", None)

        images, videos, colors, sizes, styles, fabrics = self._validate_related_data(
            images or [], videos or [], colors or [], sizes or [], styles or [], fabrics or []
        )

        instance = self.get_object()
        serializer = self.get_serializer(instance, data=data, partial=True)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        if images is not None:
            product.images.all().delete()
        if videos is not None:
            product.videos.all().delete()
        if colors is not None:
            product.colors.all().delete()
        if sizes is not None:
            product.sizes.all().delete()
        if styles is not None:
            product.styles.all().delete()
        if fabrics is not None:
            product.fabrics.all().delete()

        self._handle_related_data(
            product,
            images or [],
            videos or [],
            colors or [],
            sizes or [],
            styles or [],
            fabrics or [],
        )
        if filter_values is not None:
            self._handle_filter_values(product, filter_values)

        self._handle_dimension_template(product, serializer.validated_data.get("_dimension_template_obj"))

        return Response(ProductSerializer(product).data)

    def _handle_related_data(self, product, images, videos, colors, sizes, styles, fabrics):
        for img in images:
            ProductImage.objects.create(product=product, url=img.get("url"))
        for vid in videos:
            ProductVideo.objects.create(product=product, url=vid.get("url"))
        for col in colors:
            ProductColor.objects.create(product=product, name=col.get("name", ""), hex_code=col.get("hex_code", "#000000"))
        for size in sizes:
            ProductSize.objects.create(
                product=product,
                name=size.get("name", ""),
                description=size.get("description", ""),
            )
        for style in styles:
            ProductStyle.objects.create(product=product, name=style.get("name"), options=style.get("options", []))
        for fabric in fabrics:
            ProductFabric.objects.create(
                product=product,
                name=fabric.get("name", ""),
                image_url=fabric.get("image_url", ""),
            )

    def _validate_related_data(self, images, videos, colors, sizes, styles, fabrics):
        image_url_max = ProductImage._meta.get_field("url").max_length
        video_url_max = ProductVideo._meta.get_field("url").max_length
        color_name_max = ProductColor._meta.get_field("name").max_length
        size_name_max = ProductSize._meta.get_field("name").max_length
        size_desc_max = ProductSize._meta.get_field("description").max_length
        style_name_max = ProductStyle._meta.get_field("name").max_length
        fabric_name_max = ProductFabric._meta.get_field("name").max_length
        fabric_url_max = ProductFabric._meta.get_field("image_url").max_length

        cleaned_images = []
        for img in images:
            url = str((img or {}).get("url", "")).strip()
            if not url:
                continue
            if len(url) > image_url_max:
                raise ValidationError({"images": [f"Image URL too long (max {image_url_max} chars)."]})
            cleaned_images.append({"url": url})

        cleaned_videos = []
        for vid in videos:
            url = str((vid or {}).get("url", "")).strip()
            if not url:
                continue
            if len(url) > video_url_max:
                raise ValidationError({"videos": [f"Video URL too long (max {video_url_max} chars)."]})
            cleaned_videos.append({"url": url})

        cleaned_colors = []
        for col in colors:
            name = str((col or {}).get("name", "")).strip()
            if not name:
                continue
            if len(name) > color_name_max:
                raise ValidationError({"colors": [f"Color name too long (max {color_name_max} chars)."]})
            hex_code = str((col or {}).get("hex_code", "#000000")).strip() or "#000000"
            cleaned_colors.append({"name": name, "hex_code": hex_code})

        cleaned_sizes = []
        for size in sizes:
            if isinstance(size, dict):
                value = str(size.get("name", "")).strip()
                description = str(size.get("description", "")).strip()
            else:
                value = str(size).strip()
                description = ""

            if not value:
                continue
            if len(value) > size_name_max:
                raise ValidationError({"sizes": [f"Size value too long (max {size_name_max} chars)."]})
            if len(description) > size_desc_max:
                raise ValidationError({"sizes": [f"Size description too long (max {size_desc_max} chars)."]})
            cleaned_sizes.append({"name": value, "description": description})

        cleaned_styles = []
        for style in styles:
            name = str((style or {}).get("name", "")).strip()
            if not name:
                continue
            if len(name) > style_name_max:
                raise ValidationError({"styles": [f"Style name too long (max {style_name_max} chars)."]})
            options = (style or {}).get("options", [])
            cleaned_styles.append({"name": name, "options": options if isinstance(options, list) else []})

        cleaned_fabrics = []
        for fabric in fabrics:
            name = str((fabric or {}).get("name", "")).strip()
            image_url = str((fabric or {}).get("image_url", "")).strip()
            if not name and not image_url:
                continue
            if len(name) > fabric_name_max:
                raise ValidationError({"fabrics": [f"Fabric name too long (max {fabric_name_max} chars)."]})
            if len(image_url) > fabric_url_max:
                raise ValidationError({"fabrics": [f"Fabric image URL too long (max {fabric_url_max} chars)."]})
            cleaned_fabrics.append({"name": name, "image_url": image_url})

        return cleaned_images, cleaned_videos, cleaned_colors, cleaned_sizes, cleaned_styles, cleaned_fabrics

    def _handle_filter_values(self, product, filter_values):
        product.filter_values.all().delete()
        cleaned = []
        for fv in filter_values or []:
            opt_id = fv.get("filter_option") if isinstance(fv, dict) else fv
            if not opt_id:
                continue
            try:
                option = FilterOption.objects.get(id=opt_id)
            except FilterOption.DoesNotExist:
                continue
            cleaned.append(option)
        for option in cleaned:
            ProductFilterValue.objects.create(product=product, filter_option=option)

    def _handle_dimension_template(self, product, dimension_template_obj):
        # Remove existing link if cleared
        if dimension_template_obj is None:
            ProductDimensionTemplate.objects.filter(product=product).delete()
            return
        link, _ = ProductDimensionTemplate.objects.get_or_create(product=product)
        link.template = dimension_template_obj
        link.save()


class OrderViewSet(viewsets.ModelViewSet):
    queryset = Order.objects.all().order_by("-created_at")
    serializer_class = OrderSerializer

    def get_permissions(self):
        if self.action == "create":
            return [AllowAny()]
        if self.request.user.is_staff:
            return [IsAdminUser()]
        return [IsAuthenticated()]

    def get_queryset(self):
        if self.request.user.is_staff:
            return super().get_queryset()
        return super().get_queryset().filter(user=self.request.user)

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        items = data.pop("items", [])
        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        order = serializer.save(user=request.user if request.user.is_authenticated else None)

        for item in items:
            OrderItem.objects.create(
                order=order,
                product_id=item.get("product_id"),
                quantity=item.get("quantity"),
                price=item.get("price"),
                size=item.get("size", ""),
                color=item.get("color", ""),
                style=item.get("style", ""),
            )

        return Response(OrderSerializer(order).data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def mark_paid(self, request, pk=None):
        order = self.get_object()
        order.status = "paid"
        order.save()
        return Response({"status": "order marked as paid"})

    @action(detail=True, methods=["post"])
    def mark_shipped(self, request, pk=None):
        order = self.get_object()
        order.status = "shipped"
        order.save()
        return Response({"status": "order marked as shipped"})

    @action(detail=True, methods=["post"])
    def mark_delivered(self, request, pk=None):
        order = self.get_object()
        order.status = "delivered"
        order.save()
        return Response({"status": "order marked as delivered"})

    @action(detail=True, methods=["post"])
    def mark_cancelled(self, request, pk=None):
        order = self.get_object()
        order.status = "cancelled"
        order.save()
        return Response({"status": "order marked as cancelled"})


class ReviewViewSet(viewsets.ModelViewSet):
    queryset = Review.objects.all().order_by("-created_at")
    serializer_class = ReviewSerializer
    permission_classes = [IsAdminOrReadOnly]


class UploadViewSet(viewsets.ViewSet):
    permission_classes = [IsAdminUser]

    def _extract_public_url(self, value):
        if isinstance(value, str):
            return value
        if isinstance(value, dict):
            for key in ("url", "publicUrl", "publicURL", "signedUrl", "signedURL"):
                candidate = value.get(key)
                if isinstance(candidate, str):
                    return candidate
            data = value.get("data")
            if isinstance(data, dict):
                for key in ("url", "publicUrl", "publicURL", "signedUrl", "signedURL"):
                    candidate = data.get(key)
                    if isinstance(candidate, str):
                        return candidate
        if hasattr(value, "data") and isinstance(value.data, dict):
            for key in ("url", "publicUrl", "publicURL", "signedUrl", "signedURL"):
                candidate = value.data.get(key)
                if isinstance(candidate, str):
                    return candidate
        if hasattr(value, "model_dump"):
            dumped = value.model_dump()
            if isinstance(dumped, dict):
                return self._extract_public_url(dumped)
        return None

    def create(self, request):
        if "file" not in request.FILES:
            return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES["file"]
        base_name, ext = os.path.splitext(file_obj.name or "")
        safe_base = slugify(base_name) or "upload"
        safe_ext = (ext or "").lower()
        file_name = f"{uuid.uuid4().hex}-{safe_base}{safe_ext}"

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        bucket = settings.SUPABASE_BUCKET
        upload_result = supabase.storage.from_(bucket).upload(
            file_name,
            file_obj.read(),
            {"content-type": file_obj.content_type},
        )
        if hasattr(upload_result, "error") and upload_result.error:
            return Response({"error": str(upload_result.error)}, status=status.HTTP_400_BAD_REQUEST)

        public_url_raw = supabase.storage.from_(bucket).get_public_url(file_name)
        public_url = self._extract_public_url(public_url_raw)
        if not public_url:
            return Response({"error": "Unable to determine public file URL"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        if public_url.startswith("/"):
            public_url = urljoin(settings.SUPABASE_URL.rstrip("/") + "/", public_url.lstrip("/"))

        return Response({"url": public_url})


class PaymentViewSet(viewsets.ViewSet):
    @action(detail=False, methods=["post"])
    def create_stripe_session(self, request):
        stripe.api_key = settings.STRIPE_SECRET_KEY
        items = request.data.get("items", [])
        line_items = []
        for item in items:
            line_items.append(
                {
                    "price_data": {
                        "currency": request.data.get("currency", "gbp"),
                        "product_data": {"name": item["name"]},
                        "unit_amount": int(float(item["price"]) * 100),
                    },
                    "quantity": item["quantity"],
                }
            )

        delivery_charges = request.data.get("delivery_charges", 0)
        if float(delivery_charges) > 0:
            line_items.append(
                {
                    "price_data": {
                        "currency": request.data.get("currency", "gbp"),
                        "product_data": {"name": "Delivery Charges"},
                        "unit_amount": int(float(delivery_charges) * 100),
                    },
                    "quantity": 1,
                }
            )

        checkout_session = stripe.checkout.Session.create(
            payment_method_types=["card"],
            line_items=line_items,
            mode="payment",
            success_url=request.data.get("success_url"),
            cancel_url=request.data.get("cancel_url"),
        )
        return Response({"id": checkout_session.id, "url": checkout_session.url})

    @action(detail=False, methods=["post"])
    def create_paypal_order(self, request):
        access_token = self._paypal_access_token()
        if not access_token:
            return Response({"error": "PayPal auth failed"}, status=status.HTTP_400_BAD_REQUEST)

        total = request.data.get("total")
        currency = request.data.get("currency", "GBP")
        return_url = request.data.get("return_url")
        cancel_url = request.data.get("cancel_url")
        payload = {
            "intent": "CAPTURE",
            "purchase_units": [{"amount": {"currency_code": currency, "value": str(total)}}],
        }
        if return_url and cancel_url:
            payload["application_context"] = {"return_url": return_url, "cancel_url": cancel_url}

        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            json=payload,
            timeout=30,
        )
        if response.status_code >= 400:
            return Response({"error": response.text}, status=status.HTTP_400_BAD_REQUEST)
        return Response(response.json())

    @action(detail=False, methods=["post"])
    def capture_paypal_order(self, request):
        access_token = self._paypal_access_token()
        if not access_token:
            return Response({"error": "PayPal auth failed"}, status=status.HTTP_400_BAD_REQUEST)
        order_id = request.data.get("orderID")
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v2/checkout/orders/{order_id}/capture",
            headers={"Authorization": f"Bearer {access_token}", "Content-Type": "application/json"},
            timeout=30,
        )
        if response.status_code >= 400:
            return Response({"error": response.text}, status=status.HTTP_400_BAD_REQUEST)
        return Response(response.json())

    def _paypal_access_token(self):
        response = requests.post(
            f"{settings.PAYPAL_BASE_URL}/v1/oauth2/token",
            auth=(settings.PAYPAL_CLIENT_ID, settings.PAYPAL_CLIENT_SECRET),
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            data={"grant_type": "client_credentials"},
            timeout=30,
        )
        if response.status_code >= 400:
            return None
        return response.json().get("access_token")


class FilterTypeViewSet(viewsets.ModelViewSet):
    """ViewSet for managing filter types"""
    queryset = FilterType.objects.all().order_by('display_order', 'name')
    serializer_class = FilterTypeSerializer
    permission_classes = [IsAdminOrReadOnly]


class DimensionTemplateViewSet(viewsets.ModelViewSet):
    queryset = DimensionTemplate.objects.all().order_by("name")
    serializer_class = FilterTypeSerializer  # placeholder, set below
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
        from .serializers import DimensionTemplateSerializer
        return DimensionTemplateSerializer


class CategoryFiltersView(generics.GenericAPIView):
    """
    GET /api/categories/{category_slug}/filters/
    Returns all available filters for a category with product counts
    """
    permission_classes = [AllowAny]
    
    def get(self, request, category_slug):
        from django.db.models import Q, Count
        
        # Get the category
        try:
            category = Category.objects.get(slug=category_slug)
        except Category.DoesNotExist:
            return Response({"error": "Category not found"}, status=status.HTTP_404_NOT_FOUND)
        
        # Get filters linked to this category
        category_filters = CategoryFilter.objects.filter(
            Q(category=category) | Q(subcategory__category=category),
            is_active=True
        ).select_related('filter_type').prefetch_related(
            'filter_type__options'
        ).order_by('display_order')
        
        # Collect unique filter types
        filter_types = []
        seen_ids = set()
        for cf in category_filters:
            ft = cf.filter_type
            if ft.is_active and ft.id not in seen_ids:
                filter_types.append(ft)
                seen_ids.add(ft.id)
        
        # Annotate with product counts for each option
        for ft in filter_types:
            for option in ft.options.filter(is_active=True):
                option.product_count = ProductFilterValue.objects.filter(
                    filter_option=option,
                    product__category=category,
                    product__in_stock=True
                ).values('product').distinct().count()
        
        serializer = FilterTypeSerializer(filter_types, many=True)
        return Response({'filters': serializer.data})
