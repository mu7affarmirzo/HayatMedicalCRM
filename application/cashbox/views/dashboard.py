from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Count, Sum
from django.utils import timezone
from datetime import timedelta

from core.models import Booking, BookingBilling


@login_required
def dashboard(request):
    """
    Cashbox dashboard with overview statistics
    """
    # Redirect to billing list for now
    return redirect('cashbox:billing_list')


@login_required
def dashboard_stats(request):
    """
    Dashboard with statistics for cashbox operations
    """
    today = timezone.now().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)
    
    # Get billing statistics
    total_billings = BookingBilling.objects.count()
    pending_billings = BookingBilling.objects.filter(billing_status='pending').count()
    calculated_billings = BookingBilling.objects.filter(billing_status='calculated').count()
    invoiced_billings = BookingBilling.objects.filter(billing_status='invoiced').count()
    
    # Recent activity
    recent_bookings = Booking.objects.filter(
        status__in=['checked_in', 'in_progress', 'completed', 'discharged'],
        created_at__gte=week_ago
    ).count()
    
    # Revenue statistics (from invoiced billings)
    total_revenue = BookingBilling.objects.filter(
        billing_status='invoiced'
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    monthly_revenue = BookingBilling.objects.filter(
        billing_status='invoiced',
        created_at__gte=month_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    weekly_revenue = BookingBilling.objects.filter(
        billing_status='invoiced',
        created_at__gte=week_ago
    ).aggregate(total=Sum('total_amount'))['total'] or 0
    
    context = {
        'total_billings': total_billings,
        'pending_billings': pending_billings,
        'calculated_billings': calculated_billings,
        'invoiced_billings': invoiced_billings,
        'recent_bookings': recent_bookings,
        'total_revenue': total_revenue,
        'monthly_revenue': monthly_revenue,
        'weekly_revenue': weekly_revenue,
    }
    
    return render(request, 'cashbox/dashboard.html', context)