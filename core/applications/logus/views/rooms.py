# views.py
from django.shortcuts import render
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from datetime import datetime
from core.applications.logus.services.rooms import get_availability_matrix


@login_required
def check_availability(request):
    """View to check room availability for a date range"""
    if request.method == 'GET':
        return render(request, 'logus/check_availability.html')

    elif request.method == 'POST':
        try:
            start_date = request.POST.get('start_date')
            end_date = request.POST.get('end_date')

            # Convert to datetime objects
            start_date = datetime.strptime(start_date, '%Y-%m-%d')
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

            # Get the availability matrix
            availability_data = get_availability_matrix(start_date, end_date)

            # For AJAX requests
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse(availability_data)

            # For regular form submissions
            return render(request, 'logus/availability_matrix.html', {
                'start_date': start_date,
                'end_date': end_date,
                'tariffs': availability_data['tariffs'],
                'matrix': availability_data['matrix']
            })

        except Exception as e:
            if request.headers.get('x-requested-with') == 'XMLHttpRequest':
                return JsonResponse({'error': str(e)}, status=400)
            else:
                return render(request, 'logus/check_availability.html', {
                    'error': str(e)
                })
