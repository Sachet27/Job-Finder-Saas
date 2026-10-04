from django.urls import path
from . import views

urlpatterns = [
    path('search/', views.search_job_view, name='search'),
    path('search/<int:search_id>/status/', views.search_status_view, name='search_status'),
    path('search/<int:search_id>/results/', views.search_results_view, name='search_results'),
]
