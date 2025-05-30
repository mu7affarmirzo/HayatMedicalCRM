from django.urls import path
from application.sanatorium.views.doctors_viewset.illness_history import (
    IllnessHistoryListView,
    IllnessHistoryCreateView,
    IllnessHistoryUpdateView,
    IllnessHistoryDeleteView,
    IllnessHistoryCloseView, illness_history_detail,
)

urlpatterns = [
    path('', IllnessHistoryListView.as_view(), name='illness_history_list'),
    path('create/', IllnessHistoryCreateView.as_view(), name='illness_history_create'),
    path('<int:pk>/', illness_history_detail, name='illness_history_detail'),
    path('<int:pk>/edit/', IllnessHistoryUpdateView.as_view(), name='illness_history_update'),
    path('<int:pk>/delete/', IllnessHistoryDeleteView.as_view(), name='illness_history_delete'),
    path('<int:pk>/close/', IllnessHistoryCloseView.as_view(), name='illness_history_close'),
    path('<int:pk>/close/', IllnessHistoryCloseView.as_view(), name='illness_history_close'),
]