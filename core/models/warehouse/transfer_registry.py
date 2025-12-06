import uuid
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from core.models import BaseAuditModel


class TransferModel(BaseAuditModel):
    STATE_CHOICES = (
        ('в ожидании', 'в ожидании'),
        ('принято', 'принято'),
        ('отказано', 'отказано'),
    )
    serial = models.CharField(default=uuid.uuid4, max_length=255, unique=True)
    sender = models.ForeignKey('Warehouse', on_delete=models.CASCADE, related_name='sent_transfers')
    receiver = models.ForeignKey('Warehouse', on_delete=models.CASCADE, related_name='received_transfers')
    state = models.CharField(choices=STATE_CHOICES, max_length=50, default='в ожидании')
    notes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Transfer {self.serial}: {self.sender} → {self.receiver}"

    @property
    def overall_sum(self):
        return sum(item.overall_price for item in self.transfer_items.all())

    class Meta:
        verbose_name_plural = "Warehouses | Transfers"
        verbose_name = "Warehouses | Transfer"


class TransferItemsModel(BaseAuditModel):
    transfer = models.ForeignKey(TransferModel, on_delete=models.CASCADE, related_name="transfer_items")
    item = models.ForeignKey('MedicationsInStockModel', on_delete=models.CASCADE)
    price = models.BigIntegerField(default=0, null=True, blank=True)
    unit_price = models.BigIntegerField(default=0, null=True, blank=True)
    overall_price = models.BigIntegerField(default=0, null=True, blank=True)
    quantity = models.IntegerField()
    unit_quantity = models.IntegerField(default=0, null=True, blank=True)
    expire_date = models.DateField(null=True, blank=True)
    income_seria = models.CharField(max_length=255, null=True, blank=True)

    def __str__(self):
        return f"{self.transfer.serial} - {self.item.item.name} - {self.quantity}"

    class Meta:
        verbose_name_plural = "Warehouses | Transfer Items"
        verbose_name = "Warehouses | Transfer Item"


@receiver(pre_save, sender=TransferItemsModel)
def transfer_item_overall_price(sender, instance, **kwargs):
    # Calculate the overall price based on quantity and unit price
    total_units = (instance.quantity * instance.item.item.in_pack) + instance.unit_quantity
    instance.overall_price = total_units * instance.unit_price


@receiver(post_save, sender=TransferItemsModel)
def update_stock_on_transfer(sender, instance: TransferItemsModel, created, **kwargs):
    """
    NOTE: Stock is deducted from sender warehouse when item is added to transfer.
    This signal only handles adding stock to receiver warehouse when transfer is accepted.
    """
    from core.models import MedicationsInStockModel

    if instance.transfer.state != 'принято':
        return  # Only add to receiver warehouse when transfer is accepted

    # Add stock to receiver warehouse
    total_units_transfer = (instance.quantity * instance.item.item.in_pack) + instance.unit_quantity

    receiver_stock = MedicationsInStockModel.objects.filter(
        item=instance.item.item,
        warehouse=instance.transfer.receiver,
        expire_date=instance.expire_date,
        income_seria=instance.income_seria
    ).first()

    if receiver_stock:
        # Update existing stock in receiver warehouse
        total_units_receiver = (receiver_stock.quantity * receiver_stock.item.in_pack) + receiver_stock.unit_quantity
        new_total_units = total_units_receiver + total_units_transfer

        receiver_stock.quantity = new_total_units // receiver_stock.item.in_pack
        receiver_stock.unit_quantity = new_total_units % receiver_stock.item.in_pack
        receiver_stock.save()
    else:
        # Create new stock entry in receiver warehouse
        MedicationsInStockModel.objects.create(
            item=instance.item.item,
            income_seria=instance.income_seria,
            quantity=instance.quantity,
            unit_quantity=instance.unit_quantity,
            expire_date=instance.expire_date,
            warehouse=instance.transfer.receiver,
            price=instance.price,
            unit_price=instance.unit_price,
        )


@receiver(post_save, sender=TransferModel)
def create_transfer_serial_number(sender, instance=None, created=False, **kwargs):
    if created:
        number_str = str(instance.id).zfill(5)
        instance.serial = f"TRF-{instance.serial}|{number_str}"
        instance.save()


@receiver(post_save, sender=TransferModel)
def process_transfer_items_on_state_change(sender, instance, created, **kwargs):
    """
    Handle transfer state changes:
    - 'принято' (accepted): Add stock to receiver warehouse
    - 'отказано' (rejected): Restore stock to sender warehouse
    """
    from core.models import MedicationsInStockModel

    if created:
        return  # Skip for newly created transfers

    # Get the previous state from database
    if instance.state == 'принято':
        # Re-save all transfer items to trigger their post_save signal
        # This will add stock to receiver warehouse
        for item in instance.transfer_items.all():
            item.save()

    elif instance.state == 'отказано':
        # Restore stock to sender warehouse for all transfer items
        for transfer_item in instance.transfer_items.all():
            total_units_transfer = (transfer_item.quantity * transfer_item.item.item.in_pack) + transfer_item.unit_quantity

            # Try to find existing stock in sender warehouse
            sender_stock = MedicationsInStockModel.objects.filter(
                item=transfer_item.item.item,
                warehouse=instance.sender,
                expire_date=transfer_item.expire_date,
                income_seria=transfer_item.income_seria
            ).first()

            if sender_stock:
                # Add back to existing stock
                total_units_sender = (sender_stock.quantity * sender_stock.item.in_pack) + sender_stock.unit_quantity
                new_total_units = total_units_sender + total_units_transfer

                sender_stock.quantity = new_total_units // sender_stock.item.in_pack
                sender_stock.unit_quantity = new_total_units % sender_stock.item.in_pack
                sender_stock.save()
            else:
                # Recreate stock entry in sender warehouse
                MedicationsInStockModel.objects.create(
                    item=transfer_item.item.item,
                    income_seria=transfer_item.income_seria,
                    quantity=transfer_item.quantity,
                    unit_quantity=transfer_item.unit_quantity,
                    expire_date=transfer_item.expire_date,
                    warehouse=instance.sender,
                    price=transfer_item.price,
                    unit_price=transfer_item.unit_price,
                )
