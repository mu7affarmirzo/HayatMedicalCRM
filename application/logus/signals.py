"""
TASK-022: Django signals for auto-logging booking changes
Automatically creates BookingHistory records when bookings are modified
"""

from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.utils import timezone

from core.models.booking import Booking, BookingDetail, ServiceUsage, BookingHistory


# Store previous state of booking before save
_booking_pre_save_state = {}


@receiver(pre_save, sender=Booking)
def capture_booking_pre_save_state(sender, instance, **kwargs):
    """
    Capture the state of the booking before it's saved.
    This allows us to compare old vs new values in post_save.
    """
    if instance.pk:
        try:
            old_instance = Booking.objects.get(pk=instance.pk)
            _booking_pre_save_state[instance.pk] = {
                'status': old_instance.status,
                'start_date': old_instance.start_date,
                'end_date': old_instance.end_date,
                'notes': old_instance.notes,
            }
        except Booking.DoesNotExist:
            pass


@receiver(post_save, sender=Booking)
def log_booking_changes(sender, instance, created, **kwargs):
    """
    Automatically log booking creation and modifications to BookingHistory.
    """
    # Get the user who made the change (if available from request context)
    # Note: In production, you'd typically get this from middleware or thread-local storage
    changed_by = instance.modified_by if hasattr(instance, 'modified_by') else None

    if created:
        # Log booking creation
        BookingHistory.log_change(
            booking=instance,
            action=BookingHistory.ActionType.CREATED,
            changed_by=changed_by,
            description=f"Бронирование создано: {instance.booking_number}"
        )
    else:
        # Check if any tracked fields changed
        old_state = _booking_pre_save_state.get(instance.pk, {})

        # Check status change
        if old_state.get('status') and old_state['status'] != instance.status:
            BookingHistory.log_change(
                booking=instance,
                action=BookingHistory.ActionType.STATUS_CHANGED,
                changed_by=changed_by,
                field_name='status',
                old_value=Booking.BookingStatus(old_state['status']).label,
                new_value=instance.get_status_display(),
                description=f"Статус изменен с '{Booking.BookingStatus(old_state['status']).label}' на '{instance.get_status_display()}'"
            )

        # Check dates change
        dates_changed = False
        if old_state.get('start_date') and old_state['start_date'] != instance.start_date:
            dates_changed = True
        if old_state.get('end_date') and old_state['end_date'] != instance.end_date:
            dates_changed = True

        if dates_changed:
            old_dates = f"{old_state.get('start_date', 'N/A')} - {old_state.get('end_date', 'N/A')}"
            new_dates = f"{instance.start_date} - {instance.end_date}"
            BookingHistory.log_change(
                booking=instance,
                action=BookingHistory.ActionType.DATES_CHANGED,
                changed_by=changed_by,
                field_name='dates',
                old_value=old_dates,
                new_value=new_dates,
                description=f"Даты бронирования изменены"
            )

        # Check notes change
        if old_state.get('notes') != instance.notes:
            BookingHistory.log_change(
                booking=instance,
                action=BookingHistory.ActionType.NOTES_UPDATED,
                changed_by=changed_by,
                field_name='notes',
                old_value=old_state.get('notes', ''),
                new_value=instance.notes or '',
                description="Примечания обновлены"
            )

        # Clean up the stored state
        if instance.pk in _booking_pre_save_state:
            del _booking_pre_save_state[instance.pk]


# Store previous state of booking detail before save
_booking_detail_pre_save_state = {}


@receiver(pre_save, sender=BookingDetail)
def capture_booking_detail_pre_save_state(sender, instance, **kwargs):
    """
    Capture the state of the booking detail before it's saved.
    """
    if instance.pk:
        try:
            old_instance = BookingDetail.objects.get(pk=instance.pk)
            _booking_detail_pre_save_state[instance.pk] = {
                'tariff': old_instance.tariff,
                'room': old_instance.room,
                'price': old_instance.price,
            }
        except BookingDetail.DoesNotExist:
            pass


@receiver(post_save, sender=BookingDetail)
def log_booking_detail_changes(sender, instance, created, **kwargs):
    """
    Automatically log booking detail creation and modifications.
    """
    changed_by = instance.modified_by if hasattr(instance, 'modified_by') else None

    if created:
        # Log guest addition
        BookingHistory.log_change(
            booking=instance.booking,
            action=BookingHistory.ActionType.GUEST_ADDED,
            changed_by=changed_by,
            booking_detail=instance,
            description=f"Гость добавлен: {instance.client.full_name} в комнату {instance.room.name}"
        )
    else:
        old_state = _booking_detail_pre_save_state.get(instance.pk, {})

        # Check tariff change
        if old_state.get('tariff') and old_state['tariff'] != instance.tariff:
            BookingHistory.log_change(
                booking=instance.booking,
                action=BookingHistory.ActionType.TARIFF_CHANGED,
                changed_by=changed_by,
                booking_detail=instance,
                field_name='tariff',
                old_value=old_state['tariff'].name,
                new_value=instance.tariff.name,
                description=f"Тариф изменен для {instance.client.full_name}: {old_state['tariff'].name} → {instance.tariff.name}"
            )

        # Check room change
        if old_state.get('room') and old_state['room'] != instance.room:
            BookingHistory.log_change(
                booking=instance.booking,
                action=BookingHistory.ActionType.ROOM_CHANGED,
                changed_by=changed_by,
                booking_detail=instance,
                field_name='room',
                old_value=old_state['room'].name,
                new_value=instance.room.name,
                description=f"Комната изменена для {instance.client.full_name}: {old_state['room'].name} → {instance.room.name}"
            )

        # Clean up the stored state
        if instance.pk in _booking_detail_pre_save_state:
            del _booking_detail_pre_save_state[instance.pk]


@receiver(post_delete, sender=BookingDetail)
def log_booking_detail_deletion(sender, instance, **kwargs):
    """
    Log when a guest is removed from a booking.
    """
    # Note: We can't get modified_by from a deleted instance
    # In production, you'd need to capture this before deletion
    BookingHistory.log_change(
        booking=instance.booking,
        action=BookingHistory.ActionType.GUEST_REMOVED,
        changed_by=None,
        booking_detail=None,  # Instance is already deleted
        description=f"Гость удален: {instance.client.full_name} из комнаты {instance.room.name}"
    )


@receiver(post_save, sender=ServiceUsage)
def log_service_usage(sender, instance, created, **kwargs):
    """
    Log when additional services are added to a booking.
    """
    if created:
        changed_by = instance.modified_by if hasattr(instance, 'modified_by') else None

        BookingHistory.log_change(
            booking=instance.booking,
            action=BookingHistory.ActionType.SERVICE_ADDED,
            changed_by=changed_by,
            booking_detail=instance.booking_detail,
            description=f"Добавлена услуга: {instance.service.name} (количество: {instance.quantity}, цена: {instance.price})"
        )


@receiver(post_delete, sender=ServiceUsage)
def log_service_usage_deletion(sender, instance, **kwargs):
    """
    Log when a service usage is removed from a booking.
    """
    BookingHistory.log_change(
        booking=instance.booking,
        action=BookingHistory.ActionType.SERVICE_REMOVED,
        changed_by=None,
        booking_detail=instance.booking_detail,
        description=f"Услуга удалена: {instance.service.name}"
    )


def log_service_session_recorded(booking_detail, service, sessions_count, changed_by):
    """
    Helper function to log service session recording.
    Call this function from the view that records service sessions.

    Args:
        booking_detail: BookingDetail instance
        service: Service instance
        sessions_count: Number of sessions recorded
        changed_by: User who recorded the session
    """
    BookingHistory.log_change(
        booking=booking_detail.booking,
        action=BookingHistory.ActionType.SERVICE_SESSION_RECORDED,
        changed_by=changed_by,
        booking_detail=booking_detail,
        description=f"Записаны сессии услуги: {service.name} (количество: {sessions_count}) для {booking_detail.client.full_name}"
    )
