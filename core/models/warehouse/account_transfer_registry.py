import uuid
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from core.models import BaseAuditModel, Account


class AccountTransferModel(BaseAuditModel):
    """
    Model for transfers of medications from a branch (warehouse) to an account (doctor/nurse).
    This allows medical staff to have medications on hand for treatment periods.
    """
    STATE_CHOICES = (
        ('в ожидании', 'в ожидании'),
        ('принято', 'принято'),
        ('отказано', 'отказано'),
        ('возвращено', 'возвращено'),  # Added for when medications are returned to the warehouse
    )
    serial = models.CharField(default=uuid.uuid4, max_length=255, unique=True)
    sender = models.ForeignKey('Warehouse', on_delete=models.CASCADE, related_name='sent_account_transfers')
    receiver = models.ForeignKey(Account, on_delete=models.CASCADE, related_name='received_transfers')
    state = models.CharField(choices=STATE_CHOICES, max_length=50, default='в ожидании')
    notes = models.TextField(blank=True, null=True)
    treatment_period = models.CharField(max_length=255, blank=True, null=True, 
                                       help_text="Period for which medications are provided")
    expected_return_date = models.DateField(null=True, blank=True, 
                                           help_text="Expected date for unused medications to be returned")

    def __str__(self):
        return f"Account Transfer {self.serial}: {self.sender} → {self.receiver.full_name}"

    @property
    def overall_sum(self):
        return sum(item.overall_price for item in self.transfer_items.all())

    class Meta:
        verbose_name_plural = "Warehouses | Account Transfers"
        verbose_name = "Warehouses | Account Transfer"


class AccountTransferItemsModel(BaseAuditModel):
    """
    Model for items in a transfer from a branch (warehouse) to an account (doctor/nurse).
    """
    transfer = models.ForeignKey(AccountTransferModel, on_delete=models.CASCADE, related_name="transfer_items")
    item = models.ForeignKey('MedicationsInStockModel', on_delete=models.CASCADE)
    price = models.BigIntegerField(default=0, null=True, blank=True)
    unit_price = models.BigIntegerField(default=0, null=True, blank=True)
    overall_price = models.BigIntegerField(default=0, null=True, blank=True)
    quantity = models.IntegerField()
    unit_quantity = models.IntegerField(default=0, null=True, blank=True)
    expire_date = models.DateField(null=True, blank=True)
    income_seria = models.CharField(max_length=255, null=True, blank=True)
    
    # Fields for tracking usage and returns
    used_quantity = models.IntegerField(default=0, help_text="Quantity used by the account")
    used_unit_quantity = models.IntegerField(default=0, help_text="Unit quantity used by the account")
    returned_quantity = models.IntegerField(default=0, help_text="Quantity returned to the warehouse")
    returned_unit_quantity = models.IntegerField(default=0, help_text="Unit quantity returned to the warehouse")

    def __str__(self):
        return f"{self.transfer.serial} - {self.item.item.name} - {self.quantity}"

    class Meta:
        verbose_name_plural = "Warehouses | Account Transfer Items"
        verbose_name = "Warehouses | Account Transfer Item"


@receiver(pre_save, sender=AccountTransferItemsModel)
def account_transfer_item_overall_price(sender, instance, **kwargs):
    """Calculate the overall price based on quantity and unit price"""
    total_units = (instance.quantity * instance.item.item.in_pack) + instance.unit_quantity
    instance.overall_price = total_units * instance.unit_price


@receiver(post_save, sender=AccountTransferItemsModel)
def update_stock_on_account_transfer(sender, instance: AccountTransferItemsModel, created, **kwargs):
    """Update stock when a transfer is accepted"""
    from core.models import MedicationsInStockModel

    if instance.transfer.state != 'принято':
        return  # Only process accepted transfers

    # Decrement stock from sender warehouse
    sender_stock = MedicationsInStockModel.objects.filter(
        item=instance.item.item,
        warehouse=instance.transfer.sender,
        expire_date=instance.expire_date,
        income_seria=instance.income_seria
    ).first()

    if sender_stock:
        # Calculate total units
        total_units_sender = (sender_stock.quantity * sender_stock.item.in_pack) + sender_stock.unit_quantity
        total_units_transfer = (instance.quantity * instance.item.item.in_pack) + instance.unit_quantity

        # Ensure we have enough stock
        if total_units_sender >= total_units_transfer:
            # Calculate remaining units
            remaining_units = total_units_sender - total_units_transfer

            # Update or delete sender stock
            if remaining_units > 0:
                sender_stock.quantity = remaining_units // sender_stock.item.in_pack
                sender_stock.unit_quantity = remaining_units % sender_stock.item.in_pack
                sender_stock.save()
            else:
                sender_stock.delete()


@receiver(post_save, sender=AccountTransferModel)
def create_account_transfer_serial_number(sender, instance=None, created=False, **kwargs):
    """Generate a unique serial number for the transfer"""
    if created:
        number_str = str(instance.id).zfill(5)
        instance.serial = f"ATF-{instance.serial}|{number_str}"
        instance.save()


@receiver(post_save, sender=AccountTransferModel)
def process_account_transfer_items_on_state_change(sender, instance, created, **kwargs):
    """
    When a transfer's state changes to 'принято' (accepted), 
    trigger the stock update for all its items.
    """
    if not created and instance.state == 'принято':
        # Re-save all transfer items to trigger their post_save signal
        for item in instance.transfer_items.all():
            item.save()


@receiver(post_save, sender=AccountTransferModel)
def process_account_transfer_items_on_return(sender, instance, created, **kwargs):
    """
    When a transfer's state changes to 'возвращено' (returned),
    return unused medications to the warehouse.
    """
    from core.models import MedicationsInStockModel
    
    if not created and instance.state == 'возвращено':
        for item in instance.transfer_items.all():
            # Calculate returned units
            returned_units = (item.returned_quantity * item.item.item.in_pack) + item.returned_unit_quantity
            
            if returned_units > 0:
                # Check if there's existing stock for this item in the warehouse
                existing_stock = MedicationsInStockModel.objects.filter(
                    item=item.item.item,
                    warehouse=instance.sender,
                    expire_date=item.expire_date,
                    income_seria=item.income_seria
                ).first()
                
                if existing_stock:
                    # Update existing stock
                    total_units = (existing_stock.quantity * existing_stock.item.in_pack) + existing_stock.unit_quantity
                    new_total_units = total_units + returned_units
                    
                    existing_stock.quantity = new_total_units // existing_stock.item.in_pack
                    existing_stock.unit_quantity = new_total_units % existing_stock.item.in_pack
                    existing_stock.save()
                else:
                    # Create new stock entry
                    MedicationsInStockModel.objects.create(
                        item=item.item.item,
                        income_seria=item.income_seria,
                        quantity=item.returned_quantity,
                        unit_quantity=item.returned_unit_quantity,
                        expire_date=item.expire_date,
                        warehouse=instance.sender,
                        price=item.price,
                        unit_price=item.unit_price,
                    )