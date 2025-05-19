from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('forms/', views.forms, name='forms'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('simulation/', views.simulation, name='simulation'),
    path('accounts/', include('allauth.urls')),  # Allauth URLs for login/logout
]