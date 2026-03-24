from django.urls import path
from . import views

urlpatterns = [
    path("", views.OrderListView.as_view()),
    path("track/<str:order_number>/", views.OrderTrackView.as_view()),
    path("<str:order_number>/", views.OrderDetailView.as_view()),
]
