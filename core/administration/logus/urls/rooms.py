# urls.py
from django.urls import path

from core.administration.logus.views.rooms import (
    RoomTypeListView, RoomTypeCreateView, RoomTypeUpdateView,
    RoomTypeDeleteView,
    RoomListView, RoomCreateView, RoomUpdateView, RoomDeleteView
)


urlpatterns = [
    # RoomType URLs
    path('roomtypes/', RoomTypeListView.as_view(), name='roomtype_list'),
    path('roomtypes/create/', RoomTypeCreateView.as_view(), name='roomtype_create'),
    path('roomtypes/update/<int:pk>/', RoomTypeUpdateView.as_view(), name='roomtype_update'),
    path('roomtypes/delete/<int:pk>/', RoomTypeDeleteView.as_view(), name='roomtype_delete'),

    # Room URLs
    path('rooms/', RoomListView.as_view(), name='room_list'),
    path('rooms/create/', RoomCreateView.as_view(), name='room_create'),
    path('rooms/update/<int:pk>/', RoomUpdateView.as_view(), name='room_update'),
    path('rooms/delete/<int:pk>/', RoomDeleteView.as_view(), name='room_delete'),
]
