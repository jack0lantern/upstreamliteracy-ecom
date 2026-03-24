from django.urls import path
from . import views

urlpatterns = [
    path("events/", views.EventIngestionView.as_view()),
    path("identify/", views.IdentifyView.as_view()),
    path("dashboard/operational/", views.OperationalDashboardView.as_view()),
    path("dashboard/funnel/", views.FunnelView.as_view()),
    path("dashboard/revenue/", views.RevenueView.as_view()),
    path("dashboard/abandonment/", views.AbandonmentView.as_view()),
    path("dashboard/top-products/", views.TopProductsView.as_view()),
]
