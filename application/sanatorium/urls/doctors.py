from django.urls import path
from application.sanatorium.views.illness_history import (
    IllnessHistoryListView,
    IllnessHistoryCreateView,
    IllnessHistoryDetailView,
    IllnessHistoryUpdateView,
    IllnessHistoryDeleteView,
    IllnessHistoryCloseView, assigned_patients_list,
)

urlpatterns = [
    path('main_screen/', assigned_patients_list, name='doctors_main_screen'),
    path('histories/', IllnessHistoryListView.as_view(), name='illness_history_list'),
    path('histories/create/', IllnessHistoryCreateView.as_view(), name='illness_history_create'),
    path('histories/<int:pk>/', IllnessHistoryDetailView.as_view(), name='illness_history_detail'),
    path('histories/<int:pk>/edit/', IllnessHistoryUpdateView.as_view(), name='illness_history_update'),
    path('histories/<int:pk>/delete/', IllnessHistoryDeleteView.as_view(), name='illness_history_delete'),
    path('histories/<int:pk>/close/', IllnessHistoryCloseView.as_view(), name='illness_history_close'),
    path('histories/<int:pk>/close/', IllnessHistoryCloseView.as_view(), name='illness_history_close'),
]