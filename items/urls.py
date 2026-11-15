from django.urls import path

from . import views

app_name = "items"

urlpatterns = [
    path("", views.home_view, name="home"),
    path("items/", views.item_list_view, name="item_list"),
    path("items/report/", views.create_item_view, name="create_item"),
    path("items/<int:item_id>/", views.item_detail_view, name="item_detail"),
    path("items/<int:item_id>/resolve/", views.mark_resolved_view, name="mark_resolved"),
    path("my-items/", views.my_items_view, name="my_items"),
]
