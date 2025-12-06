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
    """
    NOTE: Stock is deducted from sender warehouse when item is added to transfer (in view).
    This signal is kept empty for consistency but doesn't perform stock deduction.
    Stock will be returned to warehouse when transfer state changes to 'отказано' or 'возвращено'.
    """
    # Stock deduction happens in the view when adding items
    # No action needed here for 'принято' state
    pass


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
    Handle account transfer state changes:
    - 'отказано' (rejected): Restore stock to sender warehouse
    Note: 'принято' doesn't need action as stock was already deducted when items were added
    """
    from core.models import MedicationsInStockModel

    if created:
        return  # Skip for newly created transfers

    if instance.state == 'отказано':
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