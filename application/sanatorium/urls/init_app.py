from django.urls import path


from application.sanatorium.views.init_app import (
    AppointmentListView,
    AppointmentDetailView,
    AppointmentCreateView,
    AppointmentUpdateView,
    AppointmentDeleteView,
)

urlpatterns = [
    path('', AppointmentListView.as_view(), name='appointment-list'),
    path('<int:pk>/', AppointmentDetailView.as_view(), name='appointment-detail'),
    path('create/', AppointmentCreateView.as_view(), name='appointment-create'),
    path('create/<int:illness_history_id>/', AppointmentCreateView.as_view(), name='appointment-create-for-history'),
    path('<int:pk>/update/', AppointmentUpdateView.as_view(), name='appointment-update'),
    path('<int:pk>/delete/', AppointmentDeleteView.as_view(), name='appointment-delete'),
]