# views.py
from django.urls import reverse_lazy
from django.views.generic import ListView, CreateView, UpdateView, DeleteView

from core.models import Room, RoomType

from administration.logus.forms.rooms import RoomForm, RoomTypeForm


class RoomTypeListView(ListView):
    model = RoomType
    template_name = 'administration/logus/room_types/roomtype_list.html'
    context_object_name = 'roomtypes'

class RoomTypeCreateView(CreateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'administration/logus/room_types/roomtype_form.html'
    success_url = reverse_lazy('roomtype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context

class RoomTypeUpdateView(UpdateView):
    model = RoomType
    form_class = RoomTypeForm
    template_name = 'administration/logus/room_types/roomtype_form.html'
    success_url = reverse_lazy('roomtype_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context

class RoomTypeDeleteView(DeleteView):
    model = RoomType
    template_name = 'administration/logus/room_types/roomtype_confirm_delete.html'
    success_url = reverse_lazy('roomtype_list')


# ----- Room Views -----

class RoomListView(ListView):
    model = Room
    template_name = 'administration/logus/rooms/room_list.html'
    context_object_name = 'rooms'

class RoomCreateView(CreateView):
    model = Room
    form_class = RoomForm
    template_name = 'administration/logus/rooms/room_form.html'
    success_url = reverse_lazy('room_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Create'
        return context

class RoomUpdateView(UpdateView):
    model = Room
    form_class = RoomForm
    template_name = 'administration/logus/rooms/room_form.html'
    success_url = reverse_lazy('room_list')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['action'] = 'Update'
        return context

class RoomDeleteView(DeleteView):
    model = Room
    template_name = 'administration/logus/rooms/room_confirm_delete.html'
    success_url = reverse_lazy('room_list')
