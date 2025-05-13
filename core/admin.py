from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as BaseUserAdmin # Importar UserAdmin base
from .models import User, ClienteProfile, Holding, ProcessoHolding, Documento, AnaliseEconomia

# Customização para o modelo User no Admin
class UserAdmin(BaseUserAdmin):
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'user_type')}), # Adicionar user_type
        ('Permissions', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    add_fieldsets = BaseUserAdmin.add_fieldsets + (
        (None, {'fields': ('user_type',)}),
    )
    list_display = ('email', 'first_name', 'last_name', 'is_staff', 'user_type') # Adicionar user_type
    search_fields = ('email', 'first_name', 'last_name')
    ordering = ('email',)

class ClienteProfileInline(admin.StackedInline): # Ou TabularInline
    model = ClienteProfile
    can_delete = False
    verbose_name_plural = 'Perfil do Cliente'

# Conectar ClienteProfile ao UserAdmin
class CustomUserAdmin(UserAdmin):
    inlines = (ClienteProfileInline,)

# Desregistrar o User padrão se estiver usando um customizado
# admin.site.unregister(User) # Se o User padrão foi previamente registrado
admin.site.register(User, CustomUserAdmin) # Registrar seu User customizado

class DocumentoInline(admin.TabularInline):
    model = Documento
    extra = 1 # Quantos formulários de documento em branco mostrar

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ('nome_holding', 'consultor_responsavel', 'data_criacao_registro', 'valor_patrimonio_integralizado')
    search_fields = ('nome_holding', 'clientes__email', 'consultor_responsavel__email')
    filter_horizontal = ('clientes',) # Melhor interface para ManyToMany

@admin.register(ProcessoHolding)
class ProcessoHoldingAdmin(admin.ModelAdmin):
    list_display = ('cliente_principal', 'status_atual', 'consultor_designado', 'data_ultima_atualizacao')
    list_filter = ('status_atual', 'consultor_designado')
    search_fields = ('cliente_principal__email', 'consultor_designado__email')
    inlines = [DocumentoInline]

@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome_documento', 'processo_holding', 'categoria', 'enviado_por', 'data_upload')
    list_filter = ('categoria', 'data_upload', 'enviado_por')
    search_fields = ('nome_documento', 'processo_holding__cliente_principal__email')

@admin.register(AnaliseEconomia)
class AnaliseEconomiaAdmin(admin.ModelAdmin):
    list_display = ('holding', 'ano_referencia', 'economia_tributaria_estimada', 'data_calculo')
    search_fields = ('holding__nome_holding',)