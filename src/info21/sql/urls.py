from django.urls import path

from . import views

app_name = "sql"

urlpatterns = [
    path("", views.index, name="index"),
    path("data/", views.data, name="data"),
    path("data/<str:table>/read", views.data_read, name="data_read"),
    path("data/<str:table>/create", views.data_create, name="data_create"),
    path("data/<str:table>/<pk>/update", views.data_update, name="data_update"),
    path("data/<str:table>/<pk>/delete", views.data_delete, name="data_delete"),
    path("data/<str:table>/export", views.data_export, name="data_export"),
    path("data/<str:table>/import", views.data_import, name="data_import"),
    path("data/<str:table>/table_delete", views.table_delete, name="table_delete"),
    path("operation/", views.operation, name="operation"),
    path("operation/execute_sql/", views.execute_sql, name="execute_sql"),
    path(
        "operation/execute_form/<str:type_sql>/<str:name>",
        views.execute_form,
        name="execute_form",
    ),
    path(
        "operation/execute/<str:type_sql>/<str:name>/<str:params>",
        views.execute,
        name="execute",
    ),
    path("export_csv/", views.export_csv, name="export_csv"),
]
