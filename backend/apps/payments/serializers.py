from rest_framework import serializers
from .models import Payment, Transaction, Refund


class TransactionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Transaction
        fields = [
            "id",
            "type",
            "amount_cents",
            "source",
            "stripe_object_id",
            "notes",
            "created_at",
        ]


class PaymentSerializer(serializers.ModelSerializer):
    transactions = TransactionSerializer(many=True, read_only=True)

    class Meta:
        model = Payment
        fields = [
            "id",
            "order",
            "stripe_payment_intent_id",
            "stripe_charge_id",
            "amount_cents",
            "currency",
            "method",
            "status",
            "failure_code",
            "failure_message",
            "transactions",
            "created_at",
            "updated_at",
        ]
        read_only_fields = fields


class CreatePaymentIntentSerializer(serializers.Serializer):
    session_token = serializers.CharField(max_length=64)


class CreateRefundSerializer(serializers.Serializer):
    amount_cents = serializers.IntegerField(min_value=1)
    reason = serializers.CharField(max_length=50)
    staff_notes = serializers.CharField(required=False, allow_blank=True, default="")
