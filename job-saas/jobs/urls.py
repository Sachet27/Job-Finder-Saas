from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_job_view, name='search')
]
