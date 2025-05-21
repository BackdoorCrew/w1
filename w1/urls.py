# w1/w1/urls.py
from django.contrib import admin
from django.urls import path, include
from core import views 
from django.conf import settings
from django.conf.urls.static import static

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', views.index, name='index'),
    path('login/', views.login, name='login'), # Sua view customizada
    path('signup/', views.signup, name='signup'), # Sua view customizada
    
    # Fluxo do Cliente:
    path('dashboard/', views.dashboard, name='dashboard'), 
    path('simulation/', views.simulation, name='simulation'),
    path('create-holding/', views.create_holding, name='create_holding'),
    path('dashboard-final/', views.dashboard_final, name='dashboard_final'), 
    
    path('invite-partners/', views.invite_partners, name='invite_partners'),
    
    # allauth URLs (inclui rotas como /accounts/logout/, /accounts/password/reset/, etc.)
    path('accounts/', include('allauth.urls')), # Mantenha isso para funcionalidades do allauth

    # Painel de Gestão
    path('management/', views.management_dashboard, name='management_dashboard'),
    path('management/users/', views.management_list_users, name='management_list_users'),
    path('management/user/<int:user_id>/', views.management_user_detail, name='management_user_detail'),
    path('management/consultants/create/', views.management_create_consultant, name='management_create_consultant'),
    
    path('management/holdings/', views.management_list_holdings, name='management_list_holdings'),
    path('management/holding/<int:holding_id>/', views.management_holding_detail, name='management_holding_detail'),
    # ### URL ATUALIZADA ### (ou mantenha o nome antigo se preferir, mas a view foi renomeada)
    path('management/holding/<int:holding_id>/manage-details-consultants/', views.management_manage_holding_details_and_consultants, name='management_manage_holding_details_and_consultants'),
    # Se você preferir manter o nome da URL antigo por consistência com os templates atuais:
    # path('management/holding/<int:holding_id>/assign-consultant/', views.management_manage_holding_details_and_consultants, name='management_assign_consultant_to_holding'),
    
    path('management/holding/<int:holding_id>/documents/', views.management_holding_documents, name='management_holding_documents'), # Esta view redireciona
    path('management/holding/<int:holding_id>/manage-clients/', views.management_holding_manage_clients, name='management_holding_manage_clients'),
    path('management/holding/<int:holding_id>/chat/', views.management_holding_chat, name='management_holding_chat'), # <-- ADD THIS LINE
    path('api/chat_com_gpt/', views.chat_with_gpt, name='chat_with_gpt'),

]

if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    # urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) # Geralmente não necessário se Whitenoise estiver configurado corretamente