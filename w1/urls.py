# w1/w1/urls.py
from django.contrib import admin
from django.urls import path, include
from core import views
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login, name='login'),
    path('signup/', views.signup, name='signup'),
    
    # Fluxo do Cliente:
    # 1. Após login/signup, vai para 'dashboard' (que mostra o formulário de simulação)
    path('dashboard/', views.dashboard, name='dashboard'), 
    # 2. Formulário de simulação é submetido para 'simulation'
    path('simulation/', views.simulation, name='simulation'),
    # 3. Após simulação, pode ir para 'create_holding'
    path('create-holding/', views.create_holding, name='create_holding'),
    # 4. Após criar holding, ou ao fazer login (se já tiver passado pela simulação), vai para 'dashboard_final'
    path('dashboard-final/', views.dashboard_final, name='dashboard_final'), 
    
    path('invite-partners/', views.invite_partners, name='invite_partners'),
    path('accounts/', include('allauth.urls')),

    # Painel de Gestão do Superuser
    path('management/', views.management_dashboard, name='management_dashboard'),
    path('management/users/', views.management_list_users, name='management_list_users'),
    path('management/user/<int:user_id>/', views.management_user_detail, name='management_user_detail'),
    path('management/consultants/create/', views.management_create_consultant, name='management_create_consultant'),
    
    path('management/holdings/', views.management_list_holdings, name='management_list_holdings'),
    path('management/holding/<int:holding_id>/', views.management_holding_detail, name='management_holding_detail'),
    path('management/holding/<int:holding_id>/assign-consultant/', views.management_assign_consultant_to_holding, name='management_assign_consultant_to_holding'),
    path('management/holding/<int:holding_id>/documents/', views.management_holding_documents, name='management_holding_documents'),
    path('management/holding/<int:holding_id>/manage-clients/', views.management_holding_manage_clients, name='management_holding_manage_clients'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Para desenvolvimento, se não usar Whitenoise no runserver
