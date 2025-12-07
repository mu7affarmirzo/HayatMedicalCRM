from django.db import models

from core.models import BaseAuditModel, Booking
from core.models.clients import PatientModel


class TransactionsModel(BaseAuditModel):
    class TransactionType(models.TextChoices):
        CASH = 'cash', 'Наличка'
        PAYME = 'payme', 'PayMe'
        CLICK = 'click', 'Click'
        CARD = 'card', 'Банковская карта'
        TRANSFER = 'transfer', 'Банковский перевод'
        HUMO = 'humo', 'Humo'
        UZCARD = 'uzcard', 'UzCard'

    class TransactionStatus(models.TextChoices):
        PENDING = 'PENDING', 'В обработке'
        COMPLETED = 'COMPLETED', 'Завершено'
        FAILED = 'FAILED', 'Ошибка'
        REFUNDED = 'REFUNDED', 'Возвращено'

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    patient = models.ForeignKey(PatientModel, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(decimal_places=2, max_digits=20)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.CASH
    )

    # New fields for payment processing
    billing = models.ForeignKey(
        'BookingBilling',
        on_delete=models.CASCADE,
        related_name='transactions',
        null=True,
        blank=True,
        help_text="Reference to the billing record for this transaction"
    )

    reference_number = models.CharField(
        max_length=100,
        blank=True,
        null=True,
        help_text="External transaction reference (card, PayMe, etc.)"
    )

    notes = models.TextField(
        blank=True,
        null=True,
        help_text="Additional notes about the transaction"
    )

    status = models.CharField(
        max_length=20,
        choices=TransactionStatus.choices,
        default=TransactionStatus.COMPLETED,
        help_text="Status of the transaction"
    )

    class Meta:
        db_table = 'transactions'
        verbose_name = 'Transaction'
        verbose_name_plural = 'Transactions'
        indexes = [
            models.Index(fields=['booking'], name='idx_trans_booking'),
            models.Index(fields=['billing'], name='idx_trans_billing'),
            models.Index(fields=['status'], name='idx_trans_status'),
            models.Index(fields=['created_at'], name='idx_trans_created'),
        ]

    def __str__(self):
        return f'{self.booking} - {self.amount} - {self.transaction_type} - {self.patient}'