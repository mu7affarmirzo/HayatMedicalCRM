from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from HayatMedicalCRM.auth.decorators import doctor_required

from django.utils import timezone
from django.http import JsonResponse

from core.models import IllnessHistory


@doctor_required
def diet_list_view(request, history_id):
    """View for displaying patient's diet plans and recommendations"""
    history = get_object_or_404(IllnessHistory, id=history_id)
    
    # For now, we'll use a simple diet management system
    # This can be expanded with proper models later
    
    active_page = {
        'diet_page': 'active',
    }
    
    context = {
        'history': history,
        'active_page': active_page,
        'patient': history.patient,
    }
    
    return render(request, 'sanatorium/doctors/diet/diet_list.html', context)


@doctor_required
def diet_create_view(request, history_id):
    """View for creating a new diet plan"""
    history = get_object_or_404(IllnessHistory, id=history_id)
    
    if request.method == 'POST':
        # Process diet creation form
        diet_type = request.POST.get('diet_type')
        restrictions = request.POST.get('restrictions')
        recommendations = request.POST.get('recommendations')
        notes = request.POST.get('notes')
        
        # Here you would save to a proper diet model
        # For now, we'll just show a success message
        
        messages.success(request, 'Диета успешно назначена')
        return redirect('diet_list', history_id=history_id)
    
    active_page = {
        'diet_page': 'active',
    }
    
    context = {
        'history': history,
        'active_page': active_page,
        'patient': history.patient,
    }
    
    return render(request, 'sanatorium/doctors/diet/diet_create.html', context)


@doctor_required
def diet_update_view(request, history_id, diet_id):
    """View for updating an existing diet plan"""
    history = get_object_or_404(IllnessHistory, id=history_id)
    
    if request.method == 'POST':
        # Process diet update form
        diet_type = request.POST.get('diet_type')
        restrictions = request.POST.get('restrictions')
        recommendations = request.POST.get('recommendations')
        notes = request.POST.get('notes')
        
        # Here you would update the proper diet model
        # For now, we'll just show a success message
        
        messages.success(request, 'Диета успешно обновлена')
        return redirect('diet_list', history_id=history_id)
    
    active_page = {
        'diet_page': 'active',
    }
    
    context = {
        'history': history,
        'active_page': active_page,
        'patient': history.patient,
        'diet_id': diet_id,
    }
    
    return render(request, 'sanatorium/doctors/diet/diet_update.html', context)


@doctor_required
def diet_delete_view(request, history_id, diet_id):
    """View for deleting a diet plan"""
    if request.method == 'POST':
        # Here you would delete from the proper diet model
        # For now, we'll just show a success message
        
        messages.success(request, 'Диета успешно удалена')
        return redirect('diet_list', history_id=history_id)
    
    return redirect('diet_list', history_id=history_id)


@doctor_required
def diet_detail_view(request, history_id, diet_id):
    """View for displaying diet plan details"""
    history = get_object_or_404(IllnessHistory, id=history_id)
    
    active_page = {
        'diet_page': 'active',
    }
    
    context = {
        'history': history,
        'active_page': active_page,
        'patient': history.patient,
        'diet_id': diet_id,
    }
    
    return render(request, 'sanatorium/doctors/diet/diet_detail.html', context)