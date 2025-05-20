from django.contrib import admin
from .models import User, ClienteProfile, Holding, ProcessoHolding, Documento, AnaliseEconomia, SimulationResult

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'user_type', 'is_active']
    list_filter = ['user_type']
    search_fields = ['email']

@admin.register(ClienteProfile)
class ClienteProfileAdmin(admin.ModelAdmin):
    list_display = ['user', 'patrimonio_total_estimado']
    search_fields = ['user__email']

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ['nome_holding', 'data_criacao_registro', 'has_heirs', 'rental_property_count']
    list_filter = ['has_heirs', 'has_rental_properties']
    search_fields = ['nome_holding']
    filter_horizontal = ['clientes']

@admin.register(ProcessoHolding)
class ProcessoHoldingAdmin(admin.ModelAdmin):
    list_display = ['cliente_principal', 'status_atual', 'data_inicio_processo']
    list_filter = ['status_atual']
    search_fields = ['cliente_principal__email']

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = [
        'nome_documento_logico', 
        'versao', 
        'categoria', 
        'processo_holding_link', # Usaremos um método para linkar ao processo
        'enviado_por', 
        'data_upload', 
        'nome_original_arquivo',
        'arquivo'
    ]
    list_filter = ['categoria', 'processo_holding__holding_associada__nome_holding', 'enviado_por__user_type']
    search_fields = [
        'nome_documento_logico', 
        'nome_original_arquivo', 
        'processo_holding__holding_associada__nome_holding', 
        'enviado_por__email'
    ]
    readonly_fields = ['data_upload', 'nome_original_arquivo', 'versao'] 
    date_hierarchy = 'data_upload'
    list_per_page = 20
    raw_id_fields = ['processo_holding', 'enviado_por']

    def processo_holding_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.processo_holding:
            link = reverse("admin:core_processoholding_change", args=[obj.processo_holding.id])
            return format_html('<a href="{}">Proc. ID: {} (Holding: {})</a>', link, obj.processo_holding.id, obj.processo_holding.holding_associada)
        return "N/A"
    processo_holding_link.short_description = 'Processo da Holding'

@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ['user', 'created_at', 'total_property_value', 'total_savings', 'number_of_heirs']
    list_filter = ['created_at', 'has_companies', 'receives_rent']
    search_fields = ['user__email', 'user__first_name']
    date_hierarchy = 'created_at'
    readonly_fields = [f.name for f in SimulationResult._meta.fields] # Torna todos os campos readonly
    list_per_page = 25

    def has_add_permission(self, request): # Impede adição pelo admin
        return False

    def has_change_permission(self, request, obj=None): # Impede edição pelo admin
        return False