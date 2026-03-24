from django.urls import path
from . import views

urlpatterns = [
    path("", views.CartView.as_view()),
    path("items/", views.AddItemView.as_view()),
    path("items/<int:pk>/", views.CartItemView.as_view()),
    path("merge/", views.MergeCartView.as_view()),
]
