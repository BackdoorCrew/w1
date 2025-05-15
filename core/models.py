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
    descricao = models.TextField(blank=True, help_text="Descrição do propósito da holding")
    clientes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='holdings_participadas', limit_choices_to={'user_type': 'cliente'})
    consultor_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='holdings_assessoradas', limit_choices_to={'user_type': 'consultor'})
    data_criacao_registro = models.DateField(null=True, blank=True)
    valor_patrimonio_integralizado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    primary_goal = models.CharField(max_length=100, choices=[
        ('asset_protection', 'Asset Protection'),
        ('tax_optimization', 'Tax Optimization'),
        ('succession', 'Succession Planning'),
        ('investment', 'Investment Management'),
    ], blank=True)
    asset_types = models.TextField(blank=True, help_text="e.g., Real estate, businesses")
    industry_focus = models.CharField(max_length=255, blank=True)
    jurisdiction = models.CharField(max_length=100, blank=True, help_text="e.g., Brazil, Cayman Islands")
    legal_structure = models.CharField(max_length=50, choices=[
        ('llc', 'LLC'),
        ('corporation', 'Corporation'),
        ('trust', 'Trust'),
        ('undecided', 'Undecided'),
    ], default='undecided')
    subsidiaries = models.TextField(blank=True, help_text="List subsidiaries, if any")
    update_frequency = models.CharField(max_length=50, choices=[
        ('daily', 'Daily'),
        ('weekly', 'Weekly'),
        ('monthly', 'Monthly'),
    ], default='weekly')
    milestones = models.TextField(blank=True, help_text="e.g., Legal registration, asset transfer")

    def __str__(self):
        return self.nome_holding

# ProcessoHolding
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

# Documento
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

# AnaliseEconomia
class AnaliseEconomia(models.Model):
    holding = models.OneToOneField(Holding, on_delete=models.CASCADE, related_name='analise_economia')
    ano_referencia = models.PositiveIntegerField()
    economia_tributaria_estimada = models.DecimalField(max_digits=15, decimal_places=2)
    patrimonio_liquido_projetado = models.DecimalField(max_digits=15, decimal_places=2)
    data_calculo = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Análise Holding {self.holding.nome_holding} - Ano {self.ano_referencia}"