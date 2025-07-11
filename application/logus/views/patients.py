from django.views.decorators.csrf import csrf_exempt
from django.views.generic import CreateView, UpdateView, ListView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from django.urls import reverse_lazy
from django.shortcuts import redirect, get_object_or_404, render
from django.contrib import messages
from django.http import JsonResponse
from django.utils.translation import gettext as _

from django.db import models

from application.logus.forms.patient_form import PatientRegistrationForm, SimplePatientForm
from core.models import PatientModel, Region, District


class PatientListView(LoginRequiredMixin, ListView):
    """View for listing patients"""
    model = PatientModel
    template_name = 'logus/patients/patients_list.html'
    context_object_name = 'patients'
    paginate_by = 15

    def get_queryset(self):
        """Customize query to include search functionality"""
        queryset = super().get_queryset()

        # Search functionality
        search_query = self.request.GET.get('search', '')
        if search_query:
            queryset = queryset.filter(
                models.Q(f_name__icontains=search_query) |
                models.Q(l_name__icontains=search_query) |
                models.Q(mid_name__icontains=search_query) |
                models.Q(mobile_phone_number__icontains=search_query) |
                models.Q(email__icontains=search_query)
            )

        return queryset


@csrf_exempt
def add_new_patient(request):
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
        post_data = request.POST.copy()

        # Convert date before form initialization
        date_of_birth = post_data.get('date_of_birth')
        print(f"Original date: {date_of_birth}")

        # If it's in DD.MM.YYYY format, convert it
        if date_of_birth and '.' in date_of_birth:
            try:
                day, month, year = date_of_birth.split('.')
                # Convert to YYYY-MM-DD format for Django
                converted_date = f"{year}-{month}-{day}"
                # Update the POST data
                post_data['date_of_birth'] = converted_date
                print(f"Converted date: {converted_date}")
            except (ValueError, TypeError) as e:
                print(f"Date conversion error: {e}")

        # Create form with modified data
        form = SimplePatientForm(post_data)
        if form.is_valid():
            patient = form.save(commit=False)
            patient.save()

            if next_url:
                redirect_url = f"{next_url}?patient_id={patient.id}"
                return redirect(redirect_url)
            return redirect('logus:booking_start')

        print(form.errors)

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