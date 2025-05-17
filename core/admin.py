from django.contrib import admin
from .models import User, ClienteProfile, Holding, ProcessoHolding, Documento, AnaliseEconomia

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
    list_display = ['nome_documento', 'processo_holding', 'data_upload']
    list_filter = ['categoria']
    search_fields = ['nome_documento']

@admin.register(AnaliseEconomia)
class AnaliseEconomiaAdmin(admin.ModelAdmin):
    list_display = ['holding', 'ano_referencia', 'economia_tributaria_estimada']
    search_fields = ['holding__nome_holding']