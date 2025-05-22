# core/admin.py
from django.contrib import admin
from .models import User, ClienteProfile, Holding, ProcessoHolding, Documento, AnaliseEconomia, SimulationResult, ChatMessage,PastaDocumento 

@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ['email', 'first_name', 'last_name', 'user_type', 'whatsapp_number', 'is_active', 'is_staff', 'is_superuser'] # Added whatsapp_number
    list_filter = ['user_type', 'is_active', 'is_staff', 'is_superuser']
    search_fields = ['email', 'first_name', 'last_name', 'whatsapp_number'] # Added whatsapp_number
    ordering = ['email']
    readonly_fields = ['date_joined', 'last_login']
    fieldsets = (
        (None, {'fields': ('email', 'password')}),
        ('Informações Pessoais', {'fields': ('first_name', 'last_name', 'whatsapp_number')}), # Added whatsapp_number
        ('Permissões', {'fields': ('is_active', 'is_staff', 'is_superuser', 'user_type', 'groups', 'user_permissions')}),
        ('Datas Importantes', {'fields': ('last_login', 'date_joined')}),
    )

@admin.register(ClienteProfile)
class ClienteProfileAdmin(admin.ModelAdmin):
    list_display = ['user_email', 'patrimonio_total_estimado', 'rendimentos_estimados_anuais']
    search_fields = ['user__email', 'user__first_name']
    raw_id_fields = ['user']

    def user_email(self, obj):
        return obj.user.email
    user_email.short_description = 'Email do Cliente'
    user_email.admin_order_field = 'user__email'

@admin.register(PastaDocumento)
class PastaDocumentoAdmin(admin.ModelAdmin):
    list_display = ('nome', 'processo_holding_link', 'parent_folder_link', 'created_by_link', 'created_at_formatted', 'document_count_display')
    list_filter = ('processo_holding__holding_associada__nome_holding', 'created_by__email', 'created_at')
    search_fields = ('nome', 'processo_holding__holding_associada__nome_holding', 'created_by__email')
    raw_id_fields = ('processo_holding', 'parent_folder', 'created_by')
    ordering = ('processo_holding__holding_associada__nome_holding', 'parent_folder__nome', 'nome')
    list_select_related = ('processo_holding__holding_associada', 'parent_folder', 'created_by')

    def processo_holding_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.processo_holding and obj.processo_holding.holding_associada:
            link = reverse("admin:core_processoholding_change", args=[obj.processo_holding.id])
            return format_html('<a href="{}">Proc. {} (Holding: {})</a>', link, obj.processo_holding.id, obj.processo_holding.holding_associada.nome_holding)
        elif obj.processo_holding:
            link = reverse("admin:core_processoholding_change", args=[obj.processo_holding.id])
            return format_html('<a href="{}">Proc. {}</a>', link, obj.processo_holding.id)
        return "N/A"
    processo_holding_link.short_description = 'Processo da Holding'
    processo_holding_link.admin_order_field = 'processo_holding__holding_associada__nome_holding'

    def parent_folder_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.parent_folder:
            link = reverse("admin:core_pastadocumento_change", args=[obj.parent_folder.id])
            return format_html('<a href="{}">{}</a>', link, obj.parent_folder.nome)
        return "Raiz"
    parent_folder_link.short_description = 'Pasta Pai'
    parent_folder_link.admin_order_field = 'parent_folder__nome'
    
    def created_by_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.created_by:
            link = reverse("admin:core_user_change", args=[obj.created_by.id])
            return format_html('<a href="{}">{}</a>', link, obj.created_by.email)
        return 'N/A'
    created_by_link.short_description = 'Criado por'
    created_by_link.admin_order_field = 'created_by__email'

    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_formatted.short_description = 'Criado em'
    created_at_formatted.admin_order_field = 'created_at'
    
    def document_count_display(self, obj):
        return obj.documentos_contidos.count()
    document_count_display.short_description = 'Nº Docs na Pasta'

@admin.register(ChatMessage)
class ChatMessageAdmin(admin.ModelAdmin):
    list_display = ('holding_link', 'sender_link', 'content_preview', 'formatted_timestamp')
    list_filter = ('holding__nome_holding', 'sender__user_type', 'timestamp')
    search_fields = ('content', 'sender__email', 'sender__first_name', 'sender__last_name', 'holding__nome_holding')
    raw_id_fields = ('holding', 'sender')
    readonly_fields = ('timestamp',)
    list_per_page = 30
    ordering = ('-timestamp',)

    def sender_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.sender:
            link = reverse("admin:core_user_change", args=[obj.sender.id])
            return format_html('<a href="{}">{}</a>', link, obj.sender.get_full_name() or obj.sender.email)
        return "-"
    sender_link.short_description = 'Remetente'
    sender_link.admin_order_field = 'sender__email'

    def holding_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.holding:
            link = reverse("admin:core_holding_change", args=[obj.holding.id])
            return format_html('<a href="{}">{}</a>', link, obj.holding.nome_holding)
        return "-"
    holding_link.short_description = 'Holding'
    holding_link.admin_order_field = 'holding__nome_holding'

    def content_preview(self, obj):
        return (obj.content[:75] + '...') if len(obj.content) > 75 else obj.content
    content_preview.short_description = 'Conteúdo'

    def formatted_timestamp(self, obj):
        return obj.timestamp.strftime('%d/%m/%Y %H:%M:%S')
    formatted_timestamp.short_description = 'Data e Hora'
    formatted_timestamp.admin_order_field = 'timestamp'

@admin.register(Holding)
class HoldingAdmin(admin.ModelAdmin):
    list_display = ['nome_holding', 'get_consultores_display', 'get_clientes_count', 'data_criacao_registro', 'is_legally_official']
    list_filter = ['is_legally_official', 'consultores', 'clientes'] # Adicionado 'consultores' ao filtro
    search_fields = ['nome_holding', 'description', 'clientes__email', 'consultores__email']
    # ### CAMPO ATUALIZADO PARA filter_horizontal ###
    filter_horizontal = ['clientes', 'consultores'] 
    date_hierarchy = 'data_criacao_registro'
    ordering = ['nome_holding']

    def get_clientes_count(self, obj):
        return obj.clientes.count()
    get_clientes_count.short_description = 'Nº Clientes'

    def get_consultores_display(self, obj):
        return ", ".join([c.get_full_name() or c.email for c in obj.consultores.all()[:3]]) + ('...' if obj.consultores.count() > 3 else '')
    get_consultores_display.short_description = 'Consultores'


@admin.register(ProcessoHolding)
class ProcessoHoldingAdmin(admin.ModelAdmin):
    list_display = ['holding_associada_link', 'cliente_principal_link', 'status_atual', 'data_inicio_processo', 'data_ultima_atualizacao']
    list_filter = ['status_atual', 'holding_associada__consultores']
    search_fields = ['cliente_principal__email', 'holding_associada__nome_holding']
    raw_id_fields = ['cliente_principal', 'holding_associada']
    date_hierarchy = 'data_inicio_processo'
    ordering = ['-data_inicio_processo']

    def holding_associada_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.holding_associada:
            link = reverse("admin:core_holding_change", args=[obj.holding_associada.id])
            return format_html('<a href="{}">{}</a>', link, obj.holding_associada.nome_holding)
        return "-"
    holding_associada_link.short_description = 'Holding Associada'
    holding_associada_link.admin_order_field = 'holding_associada__nome_holding'

    def cliente_principal_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.cliente_principal:
            link = reverse("admin:core_user_change", args=[obj.cliente_principal.id])
            return format_html('<a href="{}">{}</a>', link, obj.cliente_principal.email)
        return "-"
    cliente_principal_link.short_description = 'Cliente Principal'
    cliente_principal_link.admin_order_field = 'cliente_principal__email'


@admin.register(Documento)
class DocumentoAdmin(admin.ModelAdmin):
    list_display = [
        'nome_documento_logico', 
        'versao', 
        'categoria', 
        'processo_holding_link',
        'pasta_link', # ***** ADDED *****
        'enviado_por_link', 
        'data_upload', 
        'nome_original_arquivo',
        # 'arquivo' # Can make the list wide, consider removing or keeping based on need
    ]
    list_filter = ['categoria', 'processo_holding__holding_associada__nome_holding', 'enviado_por__user_type', 'pasta__nome'] # ***** ADDED pasta__nome *****
    search_fields = [
        'nome_documento_logico', 
        'nome_original_arquivo', 
        'processo_holding__holding_associada__nome_holding', 
        'enviado_por__email',
        'pasta__nome' # ***** ADDED *****
    ]
    readonly_fields = ['data_upload', 'nome_original_arquivo', 'versao'] 
    date_hierarchy = 'data_upload'
    list_per_page = 20
    raw_id_fields = ['processo_holding', 'enviado_por', 'pasta'] # ***** ADDED pasta *****
    list_select_related = ('processo_holding__holding_associada', 'enviado_por', 'pasta') # ***** ADDED pasta, and list_select_related for efficiency *****


    def processo_holding_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.processo_holding and obj.processo_holding.holding_associada:
            link = reverse("admin:core_processoholding_change", args=[obj.processo_holding.id])
            return format_html('<a href="{}">Proc. ID: {} (Holding: {})</a>', link, obj.processo_holding.id, obj.processo_holding.holding_associada.nome_holding)
        elif obj.processo_holding:
            link = reverse("admin:core_processoholding_change", args=[obj.processo_holding.id])
            return format_html('<a href="{}">Proc. ID: {} (Holding não associada)</a>', link, obj.processo_holding.id)
        return "N/A"
    processo_holding_link.short_description = 'Processo da Holding'
    processo_holding_link.admin_order_field = 'processo_holding__holding_associada__nome_holding' # Added for sorting

    def enviado_por_link(self,obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.enviado_por:
            link = reverse("admin:core_user_change", args=[obj.enviado_por.id])
            return format_html('<a href="{}">{}</a>', link, obj.enviado_por.email)
        return "N/A"
    enviado_por_link.short_description = 'Enviado Por'
    enviado_por_link.admin_order_field = 'enviado_por__email'

    # ***** NEW METHOD for pasta link *****
    def pasta_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.pasta:
            link = reverse("admin:core_pastadocumento_change", args=[obj.pasta.id])
            return format_html('<a href="{}">{}</a>', link, obj.pasta.nome)
        return "Raiz do Processo"
    pasta_link.short_description = 'Pasta'
    pasta_link.admin_order_field = 'pasta__nome'


@admin.register(SimulationResult)
class SimulationResultAdmin(admin.ModelAdmin):
    list_display = ['user_email_link', 'created_at', 'total_property_value', 'total_savings', 'number_of_heirs']
    list_filter = ['created_at', 'has_companies', 'receives_rent']
    search_fields = ['user__email', 'user__first_name', 'user__last_name']
    date_hierarchy = 'created_at'
    readonly_fields = [f.name for f in SimulationResult._meta.fields]
    list_per_page = 25

    def user_email_link(self, obj):
        from django.urls import reverse
        from django.utils.html import format_html
        if obj.user:
            link = reverse("admin:core_user_change", args=[obj.user.id])
            return format_html('<a href="{}">{}</a>', link, obj.user.email)
        return "N/A"
    user_email_link.short_description = 'Usuário'
    user_email_link.admin_order_field = 'user__email'

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False

    def has_delete_permission(self, request, obj=None): # Também impedir delete se necessário
        return False