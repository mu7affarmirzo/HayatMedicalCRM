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

    booking = models.ForeignKey(Booking, on_delete=models.CASCADE, related_name='transactions')
    patient = models.ForeignKey(PatientModel, on_delete=models.CASCADE, related_name='transactions')
    amount = models.DecimalField(decimal_places=2, max_digits=20)
    transaction_type = models.CharField(
        max_length=20,
        choices=TransactionType.choices,
        default=TransactionType.CASH
    )

    def __str__(self):
        return f'{self.booking} - {self.amount} - {self.transaction_type} - {self.patient}'