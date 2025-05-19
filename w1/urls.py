from django.contrib import admin
from django.urls import path, include
from core import views

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    path('dashboard/', views.dashboard, name='dashboard'),
    path('create-holding/', views.create_holding, name='create_holding'),
    path('simulation/', views.simulation, name='simulation'),
    path('invite-partners/', views.invite_partners, name='invite_partners'),
    path('accounts/', include('allauth.urls')),  # Allauth URLs for login/logout

    # Novas URLs para o Painel de Gestão do Superuser
    path('management/', views.management_dashboard, name='management_dashboard'),
    path('management/users/', views.management_list_users, name='management_list_users'),
    path('management/user/<int:user_id>/', views.management_user_detail, name='management_user_detail'),
    path('management/consultants/create/', views.management_create_consultant, name='management_create_consultant'),
    path('management/holding/<int:holding_id>/assign-consultant/', views.management_assign_consultant_to_holding, name='management_assign_consultant_to_holding'),
    path('management/holding/<int:holding_id>/documents/', views.management_holding_documents, name='management_holding_documents'),
    path('management/holdings/', views.management_list_holdings, name='management_list_holdings'), # <<< NOVA URL


]