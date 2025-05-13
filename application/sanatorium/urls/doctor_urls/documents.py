from django.urls import path

from application.sanatorium.views.doctors_viewset import documents as views

urlpatterns = [
    path('history/<int:pk>/', views.documents_view, name='documents_view'),
    path('history/<int:pk>/upload/', views.document_upload, name='document_upload'),
    path('documents/<int:document_id>/delete/', views.document_delete, name='document_delete'),
]
