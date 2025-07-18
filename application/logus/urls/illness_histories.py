from django.urls import path
from application.logus.views.illness_history import (
    IllnessHistoryListView,
    IllnessHistoryCreateView,
    IllnessHistoryUpdateView,
    IllnessHistoryDeleteView,
    IllnessHistoryCloseView, illness_history_detail, IllnessHistoryEditView, illness_history_edit_function_view,
)

urlpatterns = [
    path('', IllnessHistoryListView.as_view(), name='illness_history_list'),
    path('create/', IllnessHistoryCreateView.as_view(), name='illness_history_create'),
    path('<int:pk>/', illness_history_detail, name='illness_history_detail'),
    path('<int:pk>/update/', IllnessHistoryUpdateView.as_view(), name='illness_history_update'),
    path('<int:pk>/edit/', IllnessHistoryEditView.as_view(), name='illness_history_edit'),
    path('<int:pk>/edit/func', illness_history_edit_function_view, name='illness_history_edit_func'),
    path('<int:pk>/delete/', IllnessHistoryDeleteView.as_view(), name='illness_history_delete'),
    path('<int:pk>/close/', IllnessHistoryCloseView.as_view(), name='illness_history_close'),
    path('<int:pk>/close/', IllnessHistoryCloseView.as_view(), name='illness_history_close'),
]