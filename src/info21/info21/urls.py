from django.contrib import admin
from django.urls import include, path

urlpatterns = [
    path("", include("sql.urls", namespace="sql")),
    path("admin/", admin.site.urls),
]
