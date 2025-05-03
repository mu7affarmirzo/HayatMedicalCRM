from datetime import date
from django.db import models
from django.utils import timezone

from core.models import BaseAuditModel


class CompanyModel(BaseAuditModel):
    name = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.name}"


class MedicationModel(BaseAuditModel):
    # Common unit choices for medications
    UNIT_CHOICES = [
        ('tablet', 'Таблетки'),
        ('capsule', 'Капсулы'),
        ('ml', 'Миллилитры'),
        ('mg', 'Миллиграммы'),
        ('g', 'Граммы'),
        ('piece', 'Штуки'),
        ('ampule', 'Ампулы'),
        ('vial', 'Флаконы'),
        ('patch', 'Пластыри'),
        ('supp', 'Суппозитории'),
    ]

    name = models.CharField(max_length=100)
    company = models.ForeignKey(CompanyModel, on_delete=models.CASCADE, related_name='medications')
    in_pack = models.PositiveIntegerField(default=10, help_text="Number of units in a standard package")
    unit = models.CharField(max_length=20, choices=UNIT_CHOICES, default='tablet')

    # Batch information
    batch_number = models.CharField(max_length=50, blank=True, help_text="Batch or serial number")
    manufacture_date = models.DateField(null=True, blank=True)
    expiry_date = models.DateField(null=True, blank=True)

    # Additional fields
    description = models.TextField(blank=True)
    dosage_form = models.CharField(max_length=50, blank=True, help_text="E.g., tablet, liquid, cream")
    active_ingredients = models.TextField(blank=True)
    contraindications = models.TextField(blank=True)

    # Inventory tracking
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['expiry_date']),
        ]

    def __str__(self):
        return f"{self.name} ({self.get_unit_display()}, {self.in_pack}/pack)"

    @property
    def is_expired(self):
        """Check if medication is expired based on expiry date"""
        if not self.expiry_date:
            return False
        return self.expiry_date < timezone.now().date()

    @property
    def validity_status(self):
        """
        Return medication validity status:
        - 'valid': Not expired
        - 'expiring_soon': Expires within 90 days
        - 'expired': Already expired
        """
        if not self.expiry_date:
            return 'unknown'

        today = timezone.now().date()
        days_until_expiry = (self.expiry_date - today).days

        if days_until_expiry < 0:
            return 'expired'
        elif days_until_expiry <= 90:
            return 'expiring_soon'
        else:
            return 'valid'


class MedicationsInStockModel(BaseAuditModel):
    income_seria = models.CharField(max_length=255, null=True, blank=True)
    item = models.ForeignKey(MedicationModel, on_delete=models.CASCADE, related_name="in_stock", null=True, blank=True)

    quantity = models.IntegerField()
    unit_quantity = models.IntegerField(default=0)

    price = models.IntegerField(default=0)
    unit_price = models.IntegerField(default=0)

    expire_date = models.DateField(null=True)
    warehouse = models.ForeignKey('Warehouse', on_delete=models.CASCADE)

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

