import uuid
import stripe
import requests

from django.conf import settings
from django.contrib.auth.models import User
from django.utils.text import slugify
from rest_framework import viewsets, status, generics
from rest_framework.decorators import action
from rest_framework.permissions import AllowAny, IsAdminUser, IsAuthenticated
from rest_framework.response import Response

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
    Order,
    OrderItem,
    Review,
    Collection,
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
)


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
    queryset = Product.objects.all().order_by("-created_at")
    permission_classes = [IsAdminOrReadOnly]

    def get_serializer_class(self):
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
        return queryset

    def create(self, request, *args, **kwargs):
        data = request.data.copy()
        images = data.pop("images", [])
        videos = data.pop("videos", [])
        colors = data.pop("colors", [])
        sizes = data.pop("sizes", [])
        styles = data.pop("styles", [])

        serializer = self.get_serializer(data=data)
        serializer.is_valid(raise_exception=True)
        product = serializer.save()

        self._handle_related_data(product, images, videos, colors, sizes, styles)

        return Response(ProductSerializer(product).data, status=status.HTTP_201_CREATED)

    def update(self, request, *args, **kwargs):
        data = request.data.copy()
        images = data.pop("images", None)
        videos = data.pop("videos", None)
        colors = data.pop("colors", None)
        sizes = data.pop("sizes", None)
        styles = data.pop("styles", None)

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

        self._handle_related_data(product, images or [], videos or [], colors or [], sizes or [], styles or [])

        return Response(ProductSerializer(product).data)

    def _handle_related_data(self, product, images, videos, colors, sizes, styles):
        for img in images:
            ProductImage.objects.create(product=product, url=img.get("url"))
        for vid in videos:
            ProductVideo.objects.create(product=product, url=vid.get("url"))
        for col in colors:
            ProductColor.objects.create(product=product, name=col.get("name"), image=col.get("image", ""))
        for size in sizes:
            ProductSize.objects.create(product=product, name=size)
        for style in styles:
            ProductStyle.objects.create(product=product, name=style.get("name"), options=style.get("options", []))


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

    def create(self, request):
        if "file" not in request.FILES:
            return Response({"error": "file is required"}, status=status.HTTP_400_BAD_REQUEST)

        file_obj = request.FILES["file"]
        file_name = f"{uuid.uuid4().hex}-{file_obj.name}"

        supabase = create_client(settings.SUPABASE_URL, settings.SUPABASE_SERVICE_KEY)
        bucket = settings.SUPABASE_BUCKET
        upload_result = supabase.storage.from_(bucket).upload(
            file_name,
            file_obj.read(),
            {"content-type": file_obj.content_type},
        )
        if hasattr(upload_result, "error") and upload_result.error:
            return Response({"error": str(upload_result.error)}, status=status.HTTP_400_BAD_REQUEST)

        public_url = supabase.storage.from_(bucket).get_public_url(file_name)
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
