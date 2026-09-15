from django.urls import include, path
from rest_framework.routers import DefaultRouter
from rest_framework_simplejwt.views import TokenRefreshView

from .views import LogoutView, UserTokenObtainPairView, UserViewSet

router = DefaultRouter()
router.register("users", UserViewSet, basename="user")

auth_patterns = [
    path("login/", UserTokenObtainPairView.as_view(), name="token_login"),
    path("refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    path("logout/", LogoutView.as_view(), name="logout"),
]

urlpatterns = [
    path("auth/", include(auth_patterns)),
    path("", include(router.urls)),
]
