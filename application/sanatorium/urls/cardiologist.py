from django.urls import path

from application.sanatorium.views.cardiologist_app import (
    CardiologistConsultingListView,
    CardiologistConsultingDetailView,
    CardiologistConsultingCreateView,
    CardiologistConsultingUpdateView
)

urlpatterns = [
    path('illness/<int:history_id>/',
         CardiologistConsultingListView.as_view(),
         name='cardiologist_consulting_list'),

    path('illness/<int:history_id>/create/',
         CardiologistConsultingCreateView.as_view(),
         name='cardiologist_consulting_create'),

    path('illness/<int:history_id>/detail/<int:pk>/',
         CardiologistConsultingDetailView.as_view(),
         name='cardiologist_consulting_detail'),

    path('illness/<int:history_id>/update/<int:pk>/',
         CardiologistConsultingUpdateView.as_view(),
         name='cardiologist_consulting_update'),
]
