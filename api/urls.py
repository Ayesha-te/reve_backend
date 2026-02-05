from django.urls import path, include
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .views import (
    RegisterView,
    CategoryViewSet,
    SubCategoryViewSet,
    CollectionViewSet,
    ProductViewSet,
    OrderViewSet,
    ReviewViewSet,
    UploadViewSet,
    PaymentViewSet,
)

router = DefaultRouter()
router.register(r"categories", CategoryViewSet)
router.register(r"subcategories", SubCategoryViewSet)
router.register(r"collections", CollectionViewSet)
router.register(r"products", ProductViewSet)
router.register(r"orders", OrderViewSet)
router.register(r"reviews", ReviewViewSet)
router.register(r"uploads", UploadViewSet, basename="uploads")
router.register(r"payments", PaymentViewSet, basename="payments")

urlpatterns = [
    path("", include(router.urls)),
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]
