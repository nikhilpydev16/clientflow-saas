
from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import WorkspaceViewSet


router = DefaultRouter()

router.register(
    r"workspaces",
    WorkspaceViewSet,
    basename="workspace",
)

urlpatterns = [
    path("", include(router.urls)),
]
