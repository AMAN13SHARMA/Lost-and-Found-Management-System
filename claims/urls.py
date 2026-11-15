from django.urls import path

from . import views

app_name = "claims"

urlpatterns = [
    path("item/<int:item_id>/submit/", views.submit_claim_view, name="submit_claim"),
    path("<int:claim_id>/<str:action>/", views.decide_claim_view, name="decide_claim"),
]
