import logging
from rest_framework import status
from rest_framework.filters import OrderingFilter
from rest_framework.generics import ListAPIView
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from apps.core.pagination import StandardCursorPagination
from .models import Order
from .serializers import OrderSummarySerializer, OrderDetailSerializer

logger = logging.getLogger(__name__)


class OrderListView(ListAPIView):
    """
    GET /orders/
    Returns the authenticated user's orders. Supports ?status= filtering.
    """

    serializer_class = OrderSummarySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardCursorPagination
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["status"]
    ordering_fields = ["created_at", "total"]
    ordering = ["-created_at"]

    def get_queryset(self):
        return (
            Order.objects.filter(user=self.request.user)
            .prefetch_related("items")
            .order_by("-created_at")
        )


class OrderDetailView(APIView):
    """
    GET /orders/<order_number>/
    Returns full order detail. Accessible to the order owner (authenticated)
    or via guest_tracking_token query param.
    """

    permission_classes = [AllowAny]

    def get(self, request, order_number):
        try:
            order = (
                Order.objects.prefetch_related("items", "status_history__changed_by")
                .get(order_number=order_number)
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Access control: owner or guest token
        if request.user and request.user.is_authenticated:
            if order.user != request.user and not request.user.is_staff:
                return Response(
                    {"detail": "You do not have permission to view this order."},
                    status=status.HTTP_403_FORBIDDEN,
                )
        else:
            guest_token = request.query_params.get("token", "").strip()
            if not guest_token or order.guest_tracking_token != guest_token:
                return Response(
                    {"detail": "Authentication required or invalid token."},
                    status=status.HTTP_403_FORBIDDEN,
                )

        serializer = OrderDetailSerializer(order)
        return Response(serializer.data)


class OrderTrackView(APIView):
    """
    GET /orders/track/<order_number>/?token=<guest_tracking_token>
    Public endpoint for guest order tracking. Requires the tracking token.
    """

    permission_classes = [AllowAny]

    def get(self, request, order_number):
        guest_token = request.query_params.get("token", "").strip()
        if not guest_token:
            return Response(
                {"detail": "Tracking token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            order = Order.objects.prefetch_related("items").get(
                order_number=order_number,
                guest_tracking_token=guest_token,
            )
        except Order.DoesNotExist:
            return Response(
                {"detail": "Order not found or invalid tracking token."},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Return a limited view for tracking purposes
        return Response(
            {
                "order_number": order.order_number,
                "status": order.status,
                "shipping_method": order.shipping_method,
                "tracking_number": order.tracking_number,
                "tracking_url": order.tracking_url,
                "created_at": order.created_at,
                "items": [
                    {
                        "product_title": item.product_title,
                        "sku_code": item.sku_code,
                        "quantity": item.quantity,
                        "line_total": str(item.line_total),
                    }
                    for item in order.items.all()
                ],
                "total": str(order.total),
            }
        )
