from django.contrib import admin
from django.conf.urls import include
from django.urls import path

from health_assessment import views
from rest_framework.authtoken import views as rest_user_view

urlpatterns = [
    path('run/', views.file, name='run'),
    path('read/', views.s3_file, name='read_s3'),
    path('source-connector/', views.SourceConnector.as_view(), name='source_connector'),
    path('availability/<str:run_id>', views.data_availability, name='availability'),
    path('assessment/<str:run_id>', views.metrics_assessment, name='assessment'),
    path('availability', views.Availability.as_view(), name='availability_form'),
    path('reports/<str:run_id>', views.report_manager, name='reports_manager'),
    path('download/<str:report_id>', views.download, name='download_data'),
    path('availability-chart/<str:run_id>', views.AvailabilityChart.as_view(), name='availability_chart'),
    path('metrics-assessment/<str:run_id>', views.MetricsAssessment.as_view(), name='metrics_assessment'),
    path('runs/', views.RunList.as_view()),
    path('runs/<int:pk>/', views.RunDetail.as_view())
]
