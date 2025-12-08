from django.contrib.auth.decorators import login_required
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _
from django.db import models
from django.views.decorators.http import require_http_methods
import logging

from application.logus.forms.patient_form import (
    PatientRegistrationForm, SimplePatientForm, PatientForm, AdvancedPatientSearchForm
)
from core.models import PatientModel, Region, District
import datetime

logger = logging.getLogger(__name__)


class PatientListView(LoginRequiredMixin, ListView):
    """
    TASK-019: View for listing patients with advanced search capabilities
    Supports: basic search, advanced filters (age, region, gender, date ranges)
    """
    model = PatientModel
    template_name = 'logus/patients/patients_list.html'
    context_object_name = 'patients'
    paginate_by = 15

    def get_queryset(self):
        """
        Customize query to include search and advanced filtering functionality
        """
        queryset = super().get_queryset()

        # TASK-053: Fix N+1 query - select related region and district
        queryset = queryset.select_related('region', 'district', 'created_by', 'modified_by')

        # Basic search functionality (kept for backwards compatibility)
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                models.Q(f_name__icontains=search_query) |
                models.Q(l_name__icontains=search_query) |
                models.Q(mid_name__icontains=search_query) |
                models.Q(mobile_phone_number__icontains=search_query) |
                models.Q(email__icontains=search_query)
            )

        # Advanced search filters
        # Name search
        search_name = self.request.GET.get('search_name', '')
        if search_name:
            queryset = queryset.filter(
                models.Q(f_name__icontains=search_name) |
                models.Q(l_name__icontains=search_name) |
                models.Q(mid_name__icontains=search_name)
            )

        # Phone number filter
        phone_number = self.request.GET.get('phone_number', '')
        if phone_number:
            # Remove formatting characters for comparison
            cleaned_phone = phone_number.replace(' ', '').replace('-', '').replace('+', '')
            queryset = queryset.filter(
                models.Q(mobile_phone_number__icontains=cleaned_phone) |
                models.Q(home_phone_number__icontains=cleaned_phone)
            )

        # Email filter
        email = self.request.GET.get('email', '')
        if email:
            queryset = queryset.filter(email__icontains=email)

        # Document number filter
        doc_number = self.request.GET.get('doc_number', '')
        if doc_number:
            queryset = queryset.filter(doc_number__icontains=doc_number)

        # Age range filter
        age_from = self.request.GET.get('age_from')
        age_to = self.request.GET.get('age_to')

        if age_from or age_to:
            today = datetime.date.today()

            if age_to:
                try:
                    age_to_int = int(age_to)
                    # Calculate date of birth for minimum age (age_to)
                    dob_from = today - datetime.timedelta(days=age_to_int * 365.25 + 365.25)
                    queryset = queryset.filter(date_of_birth__gte=dob_from)
                except (ValueError, TypeError):
                    pass

            if age_from:
                try:
                    age_from_int = int(age_from)
                    # Calculate date of birth for maximum age (age_from)
                    dob_to = today - datetime.timedelta(days=age_from_int * 365.25)
                    queryset = queryset.filter(date_of_birth__lte=dob_to)
                except (ValueError, TypeError):
                    pass

        # Date of birth range filter
        dob_from = self.request.GET.get('date_of_birth_from')
        if dob_from:
            try:
                dob_from_date = datetime.datetime.strptime(dob_from, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_birth__gte=dob_from_date)
            except (ValueError, TypeError):
                pass

        dob_to = self.request.GET.get('date_of_birth_to')
        if dob_to:
            try:
                dob_to_date = datetime.datetime.strptime(dob_to, '%Y-%m-%d').date()
                queryset = queryset.filter(date_of_birth__lte=dob_to_date)
            except (ValueError, TypeError):
                pass

        # Registration date range filter
        reg_from = self.request.GET.get('registered_from')
        if reg_from:
            try:
                reg_from_date = datetime.datetime.strptime(reg_from, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__gte=reg_from_date)
            except (ValueError, TypeError):
                pass

        reg_to = self.request.GET.get('registered_to')
        if reg_to:
            try:
                reg_to_date = datetime.datetime.strptime(reg_to, '%Y-%m-%d').date()
                queryset = queryset.filter(created_at__date__lte=reg_to_date)
            except (ValueError, TypeError):
                pass

        # Region filter
        region = self.request.GET.get('region')
        if region:
            try:
                region_id = int(region)
                queryset = queryset.filter(region_id=region_id)
            except (ValueError, TypeError):
                pass

        # District filter
        district = self.request.GET.get('district')
        if district:
            try:
                district_id = int(district)
                queryset = queryset.filter(district_id=district_id)
            except (ValueError, TypeError):
                pass

        # Gender filter
        gender = self.request.GET.get('gender')
        if gender in ['True', 'False']:
            queryset = queryset.filter(gender=(gender == 'True'))

        # Active status filter
        is_active = self.request.GET.get('is_active')
        if is_active in ['True', 'False']:
            queryset = queryset.filter(is_active=(is_active == 'True'))

        # Sorting
        sort_by = self.request.GET.get('sort_by', '-created_at')
        # Validate sort_by to prevent SQL injection
        allowed_sorts = [
            '-created_at', 'created_at',
            'l_name', '-l_name',
            'date_of_birth', '-date_of_birth'
        ]
        if sort_by in allowed_sorts:
            queryset = queryset.order_by(sort_by)

        return queryset

    def get_context_data(self, **kwargs):
        """Add search form to context"""
        context = super().get_context_data(**kwargs)

        # Initialize the advanced search form with GET parameters
        context['search_form'] = AdvancedPatientSearchForm(self.request.GET or None)

        # Add flag to indicate if advanced search is active
        context['has_filters'] = any([
            self.request.GET.get('search_name'),
            self.request.GET.get('phone_number'),
            self.request.GET.get('email'),
            self.request.GET.get('doc_number'),
            self.request.GET.get('age_from'),
            self.request.GET.get('age_to'),
            self.request.GET.get('date_of_birth_from'),
            self.request.GET.get('date_of_birth_to'),
            self.request.GET.get('registered_from'),
            self.request.GET.get('registered_to'),
            self.request.GET.get('region'),
            self.request.GET.get('district'),
            self.request.GET.get('gender'),
            self.request.GET.get('is_active'),
        ])

        return context


@login_required
def patient_create_view(request):
    """
    Function-based view for creating a new patient
    """
    next_url = request.GET.get('next', 'logus:patient_list')

    if request.method == 'POST':
        form = PatientForm(request.POST)
        if form.is_valid():
            # Set the created_by and modified_by fields to the current user
            patient = form.save(commit=False)
            patient.created_by = request.user
            patient.modified_by = request.user
            patient.save()

            messages.success(request, f'Пациент "{patient.full_name}" успешно создан!')

            # Redirect to the next URL if it's provided and is a safe URL
            next_param = request.POST.get('next', next_url)
            # You might want to validate the URL is safe here
            return redirect(next_param)
    else:
        form = PatientForm()

    context = {
        'form': form,
        'title': 'Новый пациент',
        'action': 'Создать',
        'next': next_url,  # Pass the next URL to the template
    }

    return render(request, 'logus/patients/patient_form.html', context)


@login_required
@require_http_methods(["GET", "POST"])
def add_new_patient(request):
    """
    DEPRECATED: Use patient_create_view instead.
    This view is kept for backward compatibility.

    View for creating a new patient with SimplePatientForm.
    Includes date format conversion (DD.MM.YYYY -> YYYY-MM-DD).
    """
    context = {}
    next_url = request.GET.get('next')

    context['regions'] = Region.objects.filter(is_active=True)

    # Add selected district's related objects if there's form data
    if request.method == 'POST' and 'region' in request.POST and request.POST['region']:
        region_id = request.POST['region']
        context['districts'] = District.objects.filter(region_id=region_id, is_active=True)

    # Action for the template to know whether we're creating or updating
    context['action'] = _('Регистрация нового пациента')

    if request.method == 'POST':
        try:
            post_data = request.POST.copy()

            # Convert date before form initialization
            date_of_birth = post_data.get('date_of_birth')
            logger.debug(f"Original date: {date_of_birth}")

            # If it's in DD.MM.YYYY format, convert it
            if date_of_birth and '.' in date_of_birth:
                try:
                    day, month, year = date_of_birth.split('.')
                    # Convert to YYYY-MM-DD format for Django
                    converted_date = f"{year}-{month}-{day}"
                    # Update the POST data
                    post_data['date_of_birth'] = converted_date
                    logger.debug(f"Converted date: {converted_date}")
                except (ValueError, TypeError) as e:
                    logger.warning(f"Date conversion error: {e}")
                    messages.error(request, _('Неверный формат даты. Используйте ДД.ММ.ГГГГ'))

            # Create form with modified data
            form = SimplePatientForm(post_data)
            if form.is_valid():
                patient = form.save(commit=False)
                patient.created_by = request.user
                patient.modified_by = request.user
                patient.save()

                messages.success(request, f'Пациент "{patient.full_name}" успешно создан!')

                if next_url:
                    redirect_url = f"{next_url}?patient_id={patient.id}"
                    return redirect(redirect_url)
                return redirect('logus:booking_start')
            else:
                logger.warning(f"Form validation errors: {form.errors}")
                messages.error(request, _('Пожалуйста, исправьте ошибки в форме'))
                context['form'] = form

        except Exception as e:
            logger.error(f"Error creating patient: {e}", exc_info=True)
            messages.error(request, _('Произошла ошибка при создании пациента'))

    return render(request, 'logus/patients/patient_registration.html', context)


class PatientCreateView(LoginRequiredMixin, CreateView):
    """View for creating a new patient"""
    model = PatientModel
    template_name = 'logus/patients/patient_registration.html'
    fields = [
        'f_name', 'l_name', 'mid_name',
        'date_of_birth', 'gender', 'gestational_age',
        'mobile_phone_number', 'home_phone_number', 'email',
        'country', 'region', 'district', 'address',
        'doc_type', 'doc_number', 'INN', 'additional_info'
    ]
    success_url = reverse_lazy('patient_list')

    def get_context_data(self, **kwargs):
        """Add extra context data for the template"""
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(is_active=True)

        # Add selected district's related objects if there's form data
        if self.request.method == 'POST' and 'region' in self.request.POST and self.request.POST['region']:
            region_id = self.request.POST['region']
            context['districts'] = District.objects.filter(region_id=region_id, is_active=True)

        # Action for the template to know whether we're creating or updating
        context['action'] = _('Регистрация нового пациента')
        return context

    def form_valid(self, form):
        """Process valid form data and save the user who created the patient"""
        # Don't save the form yet (commit=False) so we can add created_by
        date_of_birth = self.request.POST.get('date_of_birth')
        print(date_of_birth)

        # If it's in DD.MM.YYYY format, convert it
        if date_of_birth and '.' in date_of_birth:
            try:
                day, month, year = date_of_birth.split('.')
                # Create a date object
                import datetime
                converted_date = datetime.date(int(year), int(month), int(day))
                # Update the form's cleaned_data
                form.instance.date_of_birth = converted_date
            except (ValueError, TypeError):
                # Handle invalid dates
                pass

        patient = form.save(commit=False)


        # Set the user who created this patient record
        patient.created_by = self.request.user
        patient.modified_by = self.request.user

        # Now save the patient to the database
        patient.save()

        # Show success message
        messages.success(self.request, _('Пациент успешно зарегистрирован'))

        # Check if we need to redirect back to a booking page
        next_url = self.request.GET.get('next')
        if next_url:
            # Add patient ID as a query parameter
            redirect_url = f"{next_url}?patient_id={patient.id}"
            return redirect(redirect_url)

        return super().form_valid(form)

    def form_invalid(self, form):
        print(form.errors)
        """Handle invalid form data"""
        messages.error(self.request, _('Пожалуйста, исправьте ошибки в форме'))
        return super().form_invalid(form)


class PatientUpdateView(LoginRequiredMixin, UpdateView):
    """View for updating an existing patient"""
    model = PatientModel
    template_name = 'logus/patients/patient_registration.html'
    fields = [
        'f_name', 'l_name', 'mid_name',
        'date_of_birth', 'gender', 'gestational_age',
        'mobile_phone_number', 'home_phone_number', 'email',
        'country', 'region', 'district', 'address',
        'doc_type', 'doc_number', 'INN', 'additional_info',
        'is_active'
    ]
    success_url = reverse_lazy('patient_list')

    def get_context_data(self, **kwargs):
        """Add extra context data for the template"""
        context = super().get_context_data(**kwargs)
        context['regions'] = Region.objects.filter(is_active=True)

        # Add district choices for the selected region
        patient = self.get_object()
        if patient.region:
            context['districts'] = District.objects.filter(region=patient.region, is_active=True)

        # Action for the template to know whether we're creating or updating
        context['action'] = _('Редактирование данных пациента')
        return context

    def form_valid(self, form):
        """Process valid form data and save the user who updated the patient"""
        # Don't save the form yet (commit=False) so we can add modified_by
        patient = form.save(commit=False)

        # Set the user who modified this patient record
        patient.modified_by = self.request.user

        # Now save the patient to the database
        patient.save()

        # Show success message
        messages.success(self.request, _('Данные пациента успешно обновлены'))
        return super().form_valid(form)

    def form_invalid(self, form):
        """Handle invalid form data"""
        messages.error(self.request, _('Пожалуйста, исправьте ошибки в форме'))
        return super().form_invalid(form)


class PatientDetailView(LoginRequiredMixin, DetailView):
    """View for viewing patient details"""
    model = PatientModel
    template_name = 'logus/patients/patient_detail.html'
    context_object_name = 'patient'


def get_districts(request):
    """AJAX view to get districts for a selected region"""
    region_id = request.GET.get('region_id')

    if not region_id:
        return JsonResponse([], safe=False)

    districts = District.objects.filter(region_id=region_id, is_active=True).values('id', 'name')
    return JsonResponse(list(districts), safe=False)


# Additional utility view for booking integration
def patient_quick_create(request):
    """
    Simple view for quick patient creation during booking flow
    Returns JSON response with patient data on success
    """
    if request.method != 'POST':
        return JsonResponse({'error': 'Only POST method allowed'}, status=405)

    # Extract only essential fields for quick registration
    required_fields = ['f_name', 'l_name', 'date_of_birth', 'gender', 'mobile_phone_number']

    # Validate required fields
    for field in required_fields:
        if field not in request.POST or not request.POST[field]:
            return JsonResponse({'error': f'Field {field} is required'}, status=400)

    try:
        # Create new patient with minimal data
        patient = PatientModel(
            f_name=request.POST['f_name'],
            l_name=request.POST['l_name'],
            mid_name=request.POST.get('mid_name', ''),
            date_of_birth=request.POST['date_of_birth'],
            gender=request.POST['gender'] == '1',  # Convert to boolean
            mobile_phone_number=request.POST['mobile_phone_number'],
            created_by=request.user,
            modified_by=request.user
        )
        patient.save()

        # Return patient data for use in booking form
        return JsonResponse({
            'success': True,
            'patient_id': patient.id,
            'patient_name': patient.full_name,
            'message': 'Пациент успешно создан'
        })

    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)