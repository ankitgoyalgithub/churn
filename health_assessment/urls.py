"""churn URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/2.1/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
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
    path('users/', views.UserList.as_view()),
    path('users/<int:pk>/', views.UserDetail.as_view()),
    path('runs/', views.RunList.as_view()),
    path('runs/<int:pk>/', views.RunDetail.as_view()),
    path('api-token-auth/', rest_user_view.obtain_auth_token)
]
