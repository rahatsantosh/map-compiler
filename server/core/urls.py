from django.urls import path

from . import views

app_name = "core"

urlpatterns = [
    path("wms/", views.maprequest, name="map"),
    path("std/", views.nonmaprequest, name="non-map"),
    path("api/datasets/", views.list_datasets, name="datasets"),
]
