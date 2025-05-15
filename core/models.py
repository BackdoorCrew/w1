from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

# Modelo de Usuário Customizado
class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrador'),
        ('consultor', 'Consultor'),
        ('cliente', 'Cliente'),
    )
    username = None
    email = models.EmailField(unique=True)
    user_type = models.CharField(max_length=10, choices=USER_TYPE_CHOICES, default='cliente')

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = []

    def __str__(self):
        return self.email

# Perfil do Cliente
class ClienteProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cliente_profile')
    patrimonio_total_estimado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    rendimentos_estimados_anuais = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.email}"

# Holding
class Holding(models.Model):
    nome_holding = models.CharField(max_length=255)
    clientes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='holdings_participadas', limit_choices_to={'user_type': 'cliente'})
    consultor_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='holdings_assessoradas', limit_choices_to={'user_type': 'consultor'})
    data_criacao_registro = models.DateField(null=True, blank=True)
    valor_patrimonio_integralizado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    has_successors = models.BooleanField(default=False)
    successor_names = models.TextField(blank=True, help_text="Nomes dos sucessores, se aplicável")
    partner_count = models.PositiveIntegerField(default=1)
    partner_names = models.TextField(blank=True, help_text="Nomes dos sócios ou familiares")
    asset_types = models.CharField(max_length=255, blank=True, help_text="Tipos de bens selecionados")
    main_goal = models.CharField(max_length=100, choices=[
        ('asset_protection', 'Proteger meus bens'),
        ('tax_optimization', 'Reduzir impostos'),
        ('succession', 'Planejar herança'),
        ('investment', 'Investir melhor'),
    ], blank=True)
    has_subsidiaries = models.BooleanField(default=False)
    subsidiary_names = models.TextField(blank=True, help_text="Nomes das empresas/filiais")
    timeline = models.CharField(max_length=50, choices=[
        ('<3m', 'Menos de 3 meses'),
        ('3-6m', '3 a 6 meses'),
        ('>6m', 'Sem pressa'),
    ], default='>6m')
    has_advisors = models.BooleanField(default=False)
    advisor_info = models.TextField(blank=True, help_text="Nomes e contatos dos advogados/contadores")
    update_frequency = models.CharField(max_length=50, choices=[
        ('daily', 'Diária'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
    ], default='weekly')
    important_info = models.CharField(max_length=255, blank=True, help_text="Informações prioritárias selecionadas")

    def __str__(self):
        return self.nome_holding

# ProcessoHolding (unchanged)
class ProcessoHolding(models.Model):
    STATUS_CHOICES = (
        ('aguardando_documentos', 'Aguardando Documentos'),
        ('documentacao_em_analise', 'Documentação em Análise'),
        ('elaboracao_contrato', 'Elaboração de Contrato Social'),
        ('registro_junta', 'Registro na Junta Comercial'),
        ('providencias_pos_registro', 'Providências Pós-Registro'),
        ('concluido', 'Concluído'),
        ('cancelado', 'Cancelado'),
    )
    cliente_principal = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.PROTECT, related_name='processos_holding', limit_choices_to={'user_type': 'cliente'})
    holding_associada = models.OneToOneField(Holding, on_delete=models.SET_NULL, null=True, blank=True, related_name='processo_criacao')
    status_atual = models.CharField(max_length=30, choices=STATUS_CHOICES, default='aguardando_documentos')
    consultor_designado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processos_designados', limit_choices_to={'user_type': 'consultor'})
    data_inicio_processo = models.DateTimeField(auto_now_add=True)
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Processo de {self.cliente_principal.email} - Status: {self.get_status_atual_display()}"

# Documento (unchanged)
class Documento(models.Model):
    CATEGORIA_CHOICES = (
        ('pessoais_socios', 'Documentos pessoais dos sócios'),
        ('patrimonio_incorporado', 'Documentos do patrimônio a ser incorporado'),
        ('societarios_registro', 'Documentos societários (Junta/Cartório)'),
        ('providencias_pos_registro', 'Outras providências pós-registro'),
    )
    processo_holding = models.ForeignKey(ProcessoHolding, on_delete=models.CASCADE, related_name='documentos')
    enviado_por = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, related_name='documentos_enviados', limit_choices_to={'user_type': 'cliente'})
    nome_documento = models.CharField(max_length=255)
    arquivo = models.FileField(upload_to='documentos_holdings/%Y/%m/%d/')
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES)
    data_upload = models.DateTimeField(auto_now_add=True)
    descricao_adicional = models.TextField(blank=True, null=True)
    valor_referencia = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, help_text="Valor associado ao documento, se aplicável (ex: valor de um imóvel)")

    def __str__(self):
        return f"{self.nome_documento} ({self.processo_holding.cliente_principal.email})"

# AnaliseEconomia (unchanged)
class AnaliseEconomia(models.Model):
    holding = models.OneToOneField(Holding, on_delete=models.CASCADE, related_name='analise_economia')
    ano_referencia = models.PositiveIntegerField()
    economia_tributaria_estimada = models.DecimalField(max_digits=15, decimal_places=2)
    patrimonio_liquido_projetado = models.DecimalField(max_digits=15, decimal_places=2)
    data_calculo = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Análise Holding {self.holding.nome_holding} - Ano {self.ano_referencia}"