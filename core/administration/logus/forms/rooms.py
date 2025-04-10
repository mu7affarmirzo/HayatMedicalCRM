# forms.py
from django import forms
from core.models import Room, RoomType


class RoomTypeForm(forms.ModelForm):
    class Meta:
        model = RoomType
        fields = ['name', 'description']

class RoomForm(forms.ModelForm):
    class Meta:
        model = Room
        fields = ['name', 'room_type', 'price', 'capacity', 'is_active']
