from django.urls import path, include

urlpatterns = [
    path('init-app/', include('application.sanatorium.urls.init_app')),
]