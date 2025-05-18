from django.urls import path, include

app_name = 'massagist'

urlpatterns = [
    path('dashboard/', include('application.sanatorium.urls.massagist_urls.dashboard')),

]


