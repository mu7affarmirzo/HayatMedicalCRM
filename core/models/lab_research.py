from django.db import models
from django.core.exceptions import ValidationError
from core.models import BaseAuditModel


class SpecimenType(BaseAuditModel):
    """Sample types that can be collected for lab tests"""
    name = models.CharField(max_length=100)  # Blood, Urine, Stool, etc.
    code = models.CharField(max_length=20, unique=True)
    container_type = models.CharField(max_length=100, blank=True)  # EDTA tube, Serum tube
    collection_instructions = models.TextField(blank=True)
    processing_instructions = models.TextField(blank=True)
    storage_temperature = models.CharField(max_length=50, blank=True)  # Room temp, 2-8°C
    stability_period = models.CharField(max_length=100, blank=True)  # 24 hours at room temp

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['code']),
        ]

    def __str__(self):
        return self.name


class LabTestGroupModel(BaseAuditModel):
    """Groups of related lab tests"""
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
        ]

    def __str__(self):
        return f"{self.name}"


class LabTestMethodModel(BaseAuditModel):
    """Methods used to perform lab tests"""
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        return f"{self.name}"


class LabMeasurementUnitModel(BaseAuditModel):
    """Units of measurement for lab test results"""
    name = models.CharField(max_length=255, blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    conversion_factor = models.DecimalField(max_digits=20, decimal_places=6, null=True, blank=True)
    si_unit = models.CharField(max_length=50, blank=True, null=True)

    class Meta:
        indexes = [
            models.Index(fields=['unit']),
        ]

    def __str__(self):
        return f"{self.name} {self.unit}"


class LabResearchCategoryModel(BaseAuditModel):
    """Main categories for lab research"""
    name = models.CharField(max_length=255, blank=True, null=True)
    code = models.CharField(max_length=20, blank=True, null=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['display_order']),
        ]
        verbose_name = "Lab Research Category"
        verbose_name_plural = "Lab Research Categories"

    def __str__(self):
        return f"{self.name}"


class LabResearchSubCategoryModel(BaseAuditModel):
    """Sub-categories for lab research"""
    name = models.CharField(max_length=255, blank=True, null=True)
    category = models.ForeignKey(
        LabResearchCategoryModel, on_delete=models.SET_NULL, null=True,
        related_name='sub_categories'
    )
    code = models.CharField(max_length=20, blank=True, null=True)
    display_order = models.IntegerField(default=0)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['category']),
            models.Index(fields=['display_order']),
        ]
        verbose_name = "Lab Research Sub-Category"
        verbose_name_plural = "Lab Research Sub-Categories"

    def __str__(self):
        return f"{self.name}"


class LabResearchModel(BaseAuditModel):
    """Lab test orders that can be requested"""
    name = models.CharField(max_length=255, blank=True, null=True)
    price = models.DecimalField(max_digits=10, decimal_places=2, default=100)
    category = models.ForeignKey(LabResearchCategoryModel, on_delete=models.SET_NULL,
                                 related_name='lab_research', null=True, blank=True)

    number = models.CharField(max_length=255, blank=True, null=True)
    alternative_code = models.CharField(max_length=255, blank=True, null=True)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    attribute = models.CharField(max_length=255, blank=True, null=True)
    sub_category = models.ForeignKey(LabResearchSubCategoryModel, on_delete=models.SET_NULL,
                                     related_name='lab_research', null=True, blank=True)

    deadline = models.IntegerField(null=True, blank=True)  # Hours
    deadline_cito = models.IntegerField(null=True, blank=True)  # Hours for urgent tests
    cito = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)

    # New fields for specimen management
    specimen_types = models.ManyToManyField(SpecimenType, related_name='lab_tests')
    minimum_volume = models.CharField(max_length=50, blank=True)

    # Workflow improvements
    requires_approval = models.BooleanField(default=True)
    approval_roles = models.CharField(max_length=255, blank=True)  # JSON list of role IDs

    # Clinical information
    preparation_instructions = models.TextField(blank=True)
    clinical_information = models.TextField(blank=True)

    # Integration
    loinc_code = models.CharField(max_length=20, blank=True)  # Standard medical code
    interface_code = models.CharField(max_length=50, blank=True)  # Lab machine integration code

    # Operational details
    turnaround_time_hours = models.IntegerField(default=24)
    days_performed = models.CharField(max_length=100, blank=True)  # e.g., "Mon,Wed,Fri"

    # Business rules
    restrictions = models.TextField(blank=True)  # Age/gender/condition restrictions
    requires_consent = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['is_active']),
            models.Index(fields=['category']),
            models.Index(fields=['sub_category']),
            models.Index(fields=['loinc_code']),
        ]
        verbose_name = "Lab Research"
        verbose_name_plural = "Lab Research"

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        if self.deadline_cito and not self.cito:
            raise ValidationError({'deadline_cito': 'CITO deadline can only be set when CITO is enabled'})


class LabResearchTestModel(BaseAuditModel):
    """Individual components/analytes within a lab research"""
    RESULT_CHOICES = (
        ('строковый', 'строковый'),
        ('числовой', 'числовой'),
    )
    name = models.CharField(max_length=255, blank=True, null=True)
    number = models.CharField(max_length=255, blank=True, null=True)
    short_name = models.CharField(max_length=255, blank=True, null=True)
    research = models.ForeignKey(LabResearchModel, on_delete=models.SET_NULL,
                                 related_name='lab_research_tests', null=True, blank=True)
    group = models.ForeignKey(LabTestGroupModel, blank=True, null=True, on_delete=models.SET_NULL)
    result_type = models.CharField(max_length=255, choices=RESULT_CHOICES, blank=True, null=True)
    is_active = models.BooleanField(default=True, null=True)
    ignore_status = models.BooleanField(default=False)
    is_required_print_result = models.BooleanField(default=True)
    method = models.ForeignKey(LabTestMethodModel, blank=True, null=True, on_delete=models.SET_NULL)
    instruments = models.CharField(max_length=255, blank=True, null=True)
    keyboard = models.CharField(max_length=255, blank=True, null=True)
    standard_result = models.CharField(max_length=255, null=True, blank=True)
    measurement_unit = models.ForeignKey(LabMeasurementUnitModel, on_delete=models.SET_NULL, null=True, blank=True)
    default_result = models.CharField(max_length=255, blank=True, null=True)
    additional_code = models.CharField(max_length=255, blank=True, null=True)
    additional_code_for_repeat = models.CharField(max_length=255, blank=True, null=True)
    is_micro_organism = models.BooleanField(default=False)

    id_test_system = models.CharField(max_length=255, blank=True, null=True)
    name_test_system = models.CharField(max_length=255, blank=True, null=True)

    # New metadata fields
    critical_low = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    critical_high = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    result_options = models.TextField(blank=True)  # For dropdown options in string values

    # Display
    result_prefix = models.CharField(max_length=10, blank=True)  # e.g., ">" for "Greater than"
    result_suffix = models.CharField(max_length=10, blank=True)  # e.g., "+" for positive
    display_order = models.IntegerField(default=0)

    # Calculated fields
    calculation_formula = models.TextField(blank=True)
    dependent_tests = models.ManyToManyField('self', blank=True, symmetrical=False, related_name='prerequisite_for')

    class Meta:
        indexes = [
            models.Index(fields=['name']),
            models.Index(fields=['research']),
            models.Index(fields=['is_active']),
            models.Index(fields=['result_type']),
            models.Index(fields=['display_order']),
        ]
        verbose_name = "Lab Research Test"
        verbose_name_plural = "Lab Research Tests"

    def __str__(self):
        return f"{self.name}"

    def clean(self):
        if self.result_type == 'числовой' and not self.measurement_unit:
            raise ValidationError({'measurement_unit': 'Measurement unit is required for numeric results'})

        if self.critical_low is not None and self.critical_high is not None:
            if self.critical_low >= self.critical_high:
                raise ValidationError({'critical_high': 'Critical high value must be greater than critical low value'})


class ReferenceRange(BaseAuditModel):
    """Reference ranges for lab test results"""
    test = models.ForeignKey(LabResearchTestModel, on_delete=models.CASCADE, related_name='reference_ranges')
    gender = models.CharField(max_length=10, choices=[('M', 'Male'), ('F', 'Female'), ('A', 'All')], default='A')
    min_age = models.IntegerField(null=True, blank=True)  # Age in months
    max_age = models.IntegerField(null=True, blank=True)  # Age in months
    lower_limit = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    upper_limit = models.DecimalField(max_digits=10, decimal_places=4, null=True, blank=True)
    text_normal = models.CharField(max_length=255, null=True, blank=True)  # For qualitative results
    is_active = models.BooleanField(default=True)

    class Meta:
        unique_together = ['test', 'gender', 'min_age', 'max_age']
        indexes = [
            models.Index(fields=['test', 'gender']),
            models.Index(fields=['is_active']),
        ]

    def __str__(self):
        gender_str = {'M': 'Male', 'F': 'Female', 'A': 'All'}[self.gender]
        age_str = ""
        if self.min_age is not None or self.max_age is not None:
            if self.min_age is not None and self.max_age is not None:
                age_str = f" ({self.min_age}-{self.max_age} months)"
            elif self.min_age is not None:
                age_str = f" (≥{self.min_age} months)"
            else:
                age_str = f" (≤{self.max_age} months)"

        if self.lower_limit is not None and self.upper_limit is not None:
            return f"{self.test.name} - {gender_str}{age_str}: {self.lower_limit}-{self.upper_limit}"
        elif self.text_normal:
            return f"{self.test.name} - {gender_str}{age_str}: {self.text_normal}"
        else:
            return f"{self.test.name} - {gender_str}{age_str}"

    def clean(self):
        if self.min_age is not None and self.max_age is not None and self.min_age > self.max_age:
            raise ValidationError({'max_age': 'Maximum age must be greater than minimum age'})

        if self.lower_limit is not None and self.upper_limit is not None and self.lower_limit > self.upper_limit:
            raise ValidationError({'upper_limit': 'Upper limit must be greater than lower limit'})

        if (self.lower_limit is None and self.upper_limit is None) and not self.text_normal:
            raise ValidationError('Either numeric limits or text normal value must be provided')


class ReferenceRangeVersion(BaseAuditModel):
    """Version history for reference ranges"""
    range = models.ForeignKey(ReferenceRange, on_delete=models.CASCADE, related_name='versions')
    effective_from = models.DateField()
    effective_to = models.DateField(null=True, blank=True)
    reason_for_change = models.TextField(blank=True)
    version_number = models.IntegerField()
    is_current = models.BooleanField(default=True)

    class Meta:
        unique_together = ['range', 'version_number']
        indexes = [
            models.Index(fields=['range', 'is_current']),
            models.Index(fields=['effective_from', 'effective_to']),
        ]

    def __str__(self):
        return f"{self.range} - v{self.version_number}"

    def clean(self):
        if self.effective_to and self.effective_from > self.effective_to:
            raise ValidationError({'effective_to': 'Effective to date must be after effective from date'})


class LabResult(BaseAuditModel):
    """Lab test order results"""
    STATUS_CHOICES = (
        ('pending', 'Pending'),
        ('collected', 'Sample Collected'),
        ('processing', 'Processing'),
        ('preliminary', 'Preliminary'),
        ('final', 'Final'),
        ('amended', 'Amended'),
        ('cancelled', 'Cancelled'),
    )

    patient = models.ForeignKey('PatientModel', on_delete=models.CASCADE)
    illness_history = models.ForeignKey('IllnessHistory', on_delete=models.CASCADE, null=True,
                                        related_name='lab_results')
    research = models.ForeignKey(LabResearchModel, on_delete=models.CASCADE)
    specimen_type = models.ForeignKey(SpecimenType, on_delete=models.SET_NULL, null=True)
    ordered_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, related_name='ordered_labs')
    ordered_at = models.DateTimeField(auto_now_add=True)
    priority = models.CharField(max_length=20, choices=[('routine', 'Routine'), ('urgent', 'Urgent')],
                                default='routine')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='pending')
    collected_at = models.DateTimeField(null=True, blank=True)
    collected_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, related_name='collected_labs')
    processed_at = models.DateTimeField(null=True, blank=True)
    reported_at = models.DateTimeField(null=True, blank=True)
    validated_by = models.ForeignKey('Account', on_delete=models.SET_NULL, null=True, related_name='validated_labs')
    clinical_notes = models.TextField(blank=True)
    accession_number = models.CharField(max_length=50, blank=True, unique=True)
    external_lab_reference = models.CharField(max_length=100, blank=True)
    report_pdf = models.FileField(upload_to='lab_reports/', null=True, blank=True)
    is_abnormal = models.BooleanField(default=False)

    class Meta:
        indexes = [
            models.Index(fields=['patient']),
            models.Index(fields=['illness_history']),
            models.Index(fields=['research']),
            models.Index(fields=['status']),
            models.Index(fields=['ordered_at']),
            models.Index(fields=['accession_number']),
        ]

    def __str__(self):
        return f"{self.patient} - {self.research} - {self.status}"


class LabTestResult(BaseAuditModel):
    """Individual test component results"""
    FLAG_CHOICES = (
        ('N', 'Normal'),
        ('L', 'Low'),
        ('H', 'High'),
        ('LL', 'Critically Low'),
        ('HH', 'Critically High'),
        ('A', 'Abnormal'),
    )

    lab_result = models.ForeignKey(LabResult, on_delete=models.CASCADE, related_name='test_results')
    test = models.ForeignKey(LabResearchTestModel, on_delete=models.CASCADE)
    numeric_result = models.DecimalField(max_digits=20, decimal_places=4, null=True, blank=True)
    text_result = models.TextField(blank=True)
    flag = models.CharField(max_length=2, choices=FLAG_CHOICES, blank=True)
    comments = models.TextField(blank=True)
    is_abnormal = models.BooleanField(default=False)
    delta_check = models.CharField(max_length=50, blank=True)  # Percentage change from previous result
    reference_range_used = models.ForeignKey(ReferenceRange, on_delete=models.SET_NULL, null=True, blank=True)

    class Meta:
        indexes = [
            models.Index(fields=['lab_result']),
            models.Index(fields=['test']),
            models.Index(fields=['is_abnormal']),
        ]

    def __str__(self):
        return f"{self.test.name} - {self.numeric_result or self.text_result or 'No result'}"

    def clean(self):
        if self.test.result_type == 'числовой' and self.numeric_result is None and not self.text_result:
            raise ValidationError('Numeric result required for numeric test type')
        elif self.test.result_type == 'строковый' and not self.text_result and self.numeric_result is None:
            raise ValidationError('Text result required for string test type')