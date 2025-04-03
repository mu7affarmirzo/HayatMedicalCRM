from django.db import models


class RoomType(models.Model):
    name = models.CharField(max_length=50)
    description = models.TextField(blank=True, null=True)

    def __str__(self):
        return self.name


class Room(models.Model):
    name = models.CharField(max_length=50)
    room_type = models.ForeignKey(RoomType, on_delete=models.CASCADE, related_name='rooms')
    price = models.PositiveBigIntegerField(default=0, blank=True, null=True)
    capacity = models.PositiveSmallIntegerField(default=1)
    is_active = models.BooleanField(default=True)

    def __str__(self):
        return f"{self.name} ({self.room_type.name})"

    def is_available(self, start_date, end_date):
        """Check if room is available for the given date range"""
        # Check if there are any bookings for this room that overlap with the date range
        overlapping_bookings = self.bookings.filter(
            booking__start_date__lt=end_date,
            booking__end_date__gt=start_date,
            booking__status__in=['pending', 'confirmed', 'checked_in']
        ).exists()

        return not overlapping_bookings
    