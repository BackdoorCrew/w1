from django.urls import path
from . import views

urlpatterns = [
    path('', views.advantages, name='advantages'),
]