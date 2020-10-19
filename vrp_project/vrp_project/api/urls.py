from django.urls import path, re_path
from . import views
from .models import Vehicle, Customer

urlpatterns = [

    # vehicle related URLs
    path('vehicles/', views.VehicleList.as_view()),
    path('available_vehicles/',
         views.VehicleList.as_view(queryset=Vehicle.objects.filter(availability=True))),
    path('not_available_vehicles/',
         views.VehicleList.as_view(queryset=Vehicle.objects.filter(availability=False))),
    path('vehicles/<int:pk>/', views.VehicleDetail.as_view()),

    # customer related URLs
    path('customers/', views.CustomerList.as_view()),
    path('customers/<int:pk>/', views.CustomerDetail.as_view()),
    re_path('customers/(?P<batch_name>.+)/', views.CustomerList.as_view()),

    # batch related URLs
    path('batch/', views.BatchList.as_view()),
    path('batch/<int:pk>/', views.BatchDetail.as_view()),

    # solver related URLs
    path('solve/<str:batch_name>/<int:time_limit>/', views.SolverView.as_view()),

    # solution related URLs
    path('solution/<str:batch_name>/', views.SolutionView.as_view()),

    # address related URLs
    path('address/', views.AddressList.as_view()),
    path('address/<int:pk>/', views.AddressDetail.as_view()),

]
