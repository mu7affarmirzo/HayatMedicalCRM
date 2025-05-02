from datetime import date
from django.db import models

from core.models import BaseAuditModel


class Warehouse(BaseAuditModel):
    is_main = models.BooleanField(default=False)
    is_emergency = models.BooleanField(default=False)
    name = models.CharField(max_length=255)
    address = models.CharField(max_length=255)
    email = models.EmailField()

    def __str__(self):
        return f"{self.name} - {self.address} - {self.is_main}"


class CompanyModel(BaseAuditModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class ItemsModel(BaseAuditModel):
    company = models.ForeignKey(CompanyModel, on_delete=models.CASCADE)
    in_pack = models.IntegerField(null=True, blank=True, default=10)
    name = models.CharField(max_length=255)
    unit = models.CharField(max_length=255, default="shtuk")
    seria = models.CharField(max_length=255, default="")
    is_expired = models.BooleanField(default=False)

    def __str__(self):
        return f"{self.name}-({self.in_pack}) --|by: {self.company}|--"

    @property
    def validity_color(self):
        return 1


class ItemsInStockModel(BaseAuditModel):
    income_seria = models.CharField(max_length=255, null=True, blank=True)
    item = models.ForeignKey(ItemsModel, on_delete=models.CASCADE, related_name="in_stock", null=True, blank=True)

    quantity = models.IntegerField()
    unit_quantity = models.IntegerField(default=0)

    price = models.IntegerField(default=0)
    unit_price = models.IntegerField(default=0)

    expire_date = models.DateField(null=True)
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE)

    def save(self, *args, **kwargs):
        # Get the in_pack value from the related item
        in_pack = self.item.in_pack

        # Calculate the total units including the new unit_quantity
        total_units = (self.quantity * in_pack) + self.unit_quantity

        # Update quantity and unit_quantity
        self.quantity = total_units // in_pack
        self.unit_quantity = total_units % in_pack

        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.item}-{self.income_seria}"

    @property
    def for_doctors_naming(self):
        return f"{self.item}"

    @property
    def days_until_expire(self):
        if self.expire_date:
            delta = self.expire_date - date.today()
            return delta.days
        return 0

    class Meta:
        unique_together = ('item', 'warehouse', 'expire_date', 'income_seria')
        ordering = ('expire_date', )

