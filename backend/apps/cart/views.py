import secrets
import logging
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Cart, CartItem
from .serializers import (
    CartSerializer,
    AddToCartSerializer,
    UpdateCartItemSerializer,
)

logger = logging.getLogger(__name__)

CART_TOKEN_HEADER = "HTTP_X_CART_TOKEN"
GUEST_CART_TTL_HOURS = 72


def get_cart_for_request(request):
    """
    Return the Cart for the current request.

    - Authenticated user: look up the most-recent non-expired cart owned by that user;
      create one if none exists (no expiry).
    - Guest: read the X-Cart-Token header; look up cart by token; create one if absent
      (with a TTL expiry).
    """
    if request.user and request.user.is_authenticated:
        cart = (
            Cart.objects.filter(user=request.user)
            .order_by("-created_at")
            .first()
        )
        if cart is None:
            cart = Cart.objects.create(
                token=secrets.token_urlsafe(32),
                user=request.user,
                expires_at=None,
            )
        return cart

    # Guest flow
    token = request.META.get(CART_TOKEN_HEADER, "").strip()
    if not token:
        token = secrets.token_urlsafe(32)

    cart, created = Cart.objects.get_or_create(
        token=token,
        defaults={
            "expires_at": timezone.now() + timezone.timedelta(hours=GUEST_CART_TTL_HOURS),
        },
    )

    if not created and cart.expires_at and timezone.now() > cart.expires_at:
        # Expired cart: clear items and reset expiry
        cart.items.all().delete()
        cart.expires_at = timezone.now() + timezone.timedelta(hours=GUEST_CART_TTL_HOURS)
        cart.save(update_fields=["expires_at"])

    return cart


class CartView(APIView):
    """GET /cart/ — return the current cart."""

    permission_classes = [AllowAny]

    def get(self, request):
        cart = get_cart_for_request(request)
        serializer = CartSerializer(cart, context={"request": request})
        return Response(serializer.data)


class AddItemView(APIView):
    """POST /cart/items/ — add an item or increment quantity."""

    permission_classes = [AllowAny]

    def post(self, request):
        serializer = AddToCartSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        sku = serializer.validated_data["sku"]
        quantity = serializer.validated_data["quantity"]
        cart = get_cart_for_request(request)

        try:
            item = CartItem.objects.get(cart=cart, sku=sku)
            new_qty = item.quantity + quantity
            # Re-validate combined quantity against stock
            try:
                stock = sku.stock_level
                if not stock.is_unlimited and stock.available_quantity < new_qty:
                    new_qty = stock.available_quantity
            except Exception:
                pass
            item.quantity = new_qty
            item.save(update_fields=["quantity", "updated_at"])
        except CartItem.DoesNotExist:
            item = CartItem.objects.create(
                cart=cart,
                sku=sku,
                quantity=quantity,
                unit_price=sku.effective_price,
            )

        cart_serializer = CartSerializer(cart, context={"request": request})
        return Response(cart_serializer.data, status=status.HTTP_200_OK)


class CartItemView(APIView):
    """
    PATCH /cart/items/<pk>/ — update quantity
    DELETE /cart/items/<pk>/ — remove item
    """

    permission_classes = [AllowAny]

    def _get_item(self, request, pk):
        cart = get_cart_for_request(request)
        try:
            return cart.items.get(pk=pk), cart
        except CartItem.DoesNotExist:
            return None, cart

    def patch(self, request, pk):
        item, cart = self._get_item(request, pk)
        if item is None:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        serializer = UpdateCartItemSerializer(
            data=request.data, context={"cart_item": item}
        )
        serializer.is_valid(raise_exception=True)
        item.quantity = serializer.validated_data["quantity"]
        item.save(update_fields=["quantity", "updated_at"])
        cart_serializer = CartSerializer(cart, context={"request": request})
        return Response(cart_serializer.data)

    def delete(self, request, pk):
        item, cart = self._get_item(request, pk)
        if item is None:
            return Response(
                {"detail": "Cart item not found."},
                status=status.HTTP_404_NOT_FOUND,
            )
        item.delete()
        cart_serializer = CartSerializer(cart, context={"request": request})
        return Response(cart_serializer.data)


class MergeCartView(APIView):
    """
    POST /cart/merge/ — authenticated only.
    Body: { "guest_cart_token": "<token>" }
    Merges guest cart items into the authenticated user's cart.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        guest_token = request.data.get("guest_cart_token", "").strip()
        if not guest_token:
            return Response(
                {"detail": "guest_cart_token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            guest_cart = Cart.objects.prefetch_related("items__sku").get(
                token=guest_token, user__isnull=True
            )
        except Cart.DoesNotExist:
            return Response(
                {"detail": "Guest cart not found."},
                status=status.HTTP_404_NOT_FOUND,
            )

        user_cart = get_cart_for_request(request)

        for guest_item in guest_cart.items.all():
            try:
                user_item = user_cart.items.get(sku=guest_item.sku)
                # Sum quantities, capped by stock
                new_qty = user_item.quantity + guest_item.quantity
                try:
                    stock = guest_item.sku.stock_level
                    if not stock.is_unlimited:
                        new_qty = min(new_qty, stock.available_quantity)
                except Exception:
                    pass
                user_item.quantity = new_qty
                user_item.save(update_fields=["quantity", "updated_at"])
            except CartItem.DoesNotExist:
                CartItem.objects.create(
                    cart=user_cart,
                    sku=guest_item.sku,
                    quantity=guest_item.quantity,
                    unit_price=guest_item.unit_price,
                )

        guest_cart.delete()

        cart_serializer = CartSerializer(user_cart, context={"request": request})
        return Response(cart_serializer.data)
