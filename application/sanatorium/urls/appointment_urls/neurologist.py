from django.urls import path

from application.sanatorium.views.appointment_views.neurologist_app import (
    NeurologistConsultingCreateView,
    NeurologistConsultingUpdateView,
    NeurologistConsultingDetailView,
    NeurologistConsultingListView,
)

urlpatterns = [
    path('illness/<int:history_id>/',
         NeurologistConsultingListView.as_view(),
         name='neurologist_consulting_list'),

    path('illness/<int:history_id>/create/',
         NeurologistConsultingCreateView.as_view(),
         name='neurologist_consulting_create'),

    path('detail/<int:pk>/',
         NeurologistConsultingDetailView.as_view(),
         name='neurologist_consulting_detail'),

    path('illness/<int:history_id>/update/<int:pk>/',
         NeurologistConsultingUpdateView.as_view(),
         name='neurologist_consulting_update'),
]
