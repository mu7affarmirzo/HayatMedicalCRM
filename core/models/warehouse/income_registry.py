import uuid
from django.db import models
from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver

from core.models import BaseAuditModel


class IncomeModel(BaseAuditModel):
    STATE_CHOICES = (
        ('в ожидании', 'в ожидании'),
        ('принято', 'принято'),
        ('отказано', 'отказано'),
    )
    serial = models.CharField(default=uuid.uuid4, max_length=255, unique=True)
    delivery_company = models.ForeignKey('DeliveryCompanyModel', on_delete=models.SET_NULL, null=True, blank=True)
    receiver = models.ForeignKey('Warehouse', on_delete=models.CASCADE)
    bill_amount = models.BigIntegerField(default=0, null=True, blank=True)
    state = models.CharField(choices=STATE_CHOICES, max_length=50, default='в ожидании')

    def __str__(self):
        return f"{self.receiver} - {self.serial}"

    @property
    def overall_sum(self):
        return sum(item.overall_price for item in self.income_items.all())

    class Meta:
        verbose_name_plural = "Warehouses | Income"
        verbose_name = "Warehouses | Income"


class IncomeItemsModel(BaseAuditModel):
    income = models.ForeignKey(IncomeModel, on_delete=models.CASCADE, related_name="income_items")
    item = models.ForeignKey('MedicationModel', on_delete=models.CASCADE)
    price = models.BigIntegerField(default=0, null=True, blank=True)
    unit_price = models.BigIntegerField(default=0, null=True, blank=True)
    nds = models.PositiveIntegerField(default=0, null=True, blank=True)
    overall_price = models.BigIntegerField(default=0, null=True, blank=True)
    quantity = models.IntegerField()
    unit_quantity = models.IntegerField(default=0, null=True, blank=True)
    expire_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.income.serial} - {self.item.name} - {self.quantity}"

    class Meta:
        verbose_name_plural = "Warehouses | Income Registry Item"
        verbose_name = "Warehouses | Income Registry Item"


@receiver(pre_save, sender=IncomeItemsModel)
def income_item_overall_price(sender, instance, **kwargs):
    if instance.nds:
        instance.unit_price = int(instance.unit_price * (100 + instance.nds) / 100)
        instance.price = instance.unit_price * instance.item.in_pack

    total_units = (instance.quantity * instance.item.in_pack) + instance.unit_quantity
    instance.overall_price = total_units * instance.unit_price


@receiver(post_save, sender=IncomeItemsModel)
def items_to_stock(sender, instance: IncomeItemsModel, created, **kwargs):
    """
    NOTE: Stock is only added when income state is 'принято' (accepted).
    Items in 'в ожидании' (pending) state are NOT added to stock.
    This allows editing items before acceptance.
    """
    from core.models import MedicationsInStockModel

    # Only add to stock if income is accepted
    if instance.income.state != 'принято':
        return

    stock_data = {
        'item': instance.item,
        'income_seria': instance.income.serial,
        'quantity': instance.quantity,
        'unit_quantity': instance.unit_quantity,
        'expire_date': instance.expire_date,
        'warehouse': instance.income.receiver,
        'price': instance.price,
        'unit_price': instance.unit_price,
    }

    if created:
        MedicationsInStockModel.objects.create(**stock_data)
    else:
        MedicationsInStockModel.objects.filter(
            income_seria=instance.income.serial,
            item=instance.item,
            warehouse=instance.income.receiver
        ).update(**stock_data)


@receiver(post_save, sender=IncomeModel)
def create_income_serial_number(sender, instance=None, created=False, **kwargs):
    if created:
        number_str = str(instance.id).zfill(5)
        instance.serial = f"{instance.serial}|{number_str}"
        instance.save()


@receiver(post_save, sender=IncomeModel)
def process_income_items_on_state_change(sender, instance, created, **kwargs):
    """
    Handle income state changes:
    - 'принято' (accepted): Add all income items to stock
    """
    if created:
        return  # Skip for newly created income

    if instance.state == 'принято':
        # Re-save all income items to trigger their post_save signal
        # This will add stock to warehouse
        for item in instance.income_items.all():
            item.save()
