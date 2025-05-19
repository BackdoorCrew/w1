from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings

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

class ClienteProfile(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='cliente_profile')
    patrimonio_total_estimado = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    rendimentos_estimados_anuais = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)

    def __str__(self):
        return f"Perfil de {self.user.email}"

class Holding(models.Model):
    nome_holding = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    clientes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='holdings_participadas', limit_choices_to={'user_type': 'cliente'})
    consultor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='holdings_assessoradas',
        limit_choices_to={'user_type': 'consultor'}
    )
    data_criacao_registro = models.DateField(null=True, blank=True)
    has_bank_savings = models.BooleanField(default=False)
    bank_savings_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    has_heirs = models.BooleanField(default=False)
    heir_count = models.PositiveIntegerField(null=True, blank=True)
    has_succession_plan = models.BooleanField(default=False)
    has_paid_inventory = models.BooleanField(default=False)
    has_rental_properties = models.BooleanField(default=False)
    rental_property_count = models.PositiveIntegerField(null=True, blank=True)
    rental_income_monthly = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    rental_expenses_monthly = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    has_litigation_concerns = models.BooleanField(default=False)
    has_legal_issues = models.BooleanField(default=False)
    wants_asset_protection = models.BooleanField(default=False)
    protected_assets = models.TextField(blank=True, help_text="Descrição dos bens a proteger")
    has_companies = models.BooleanField(default=False)
    company_count = models.PositiveIntegerField(null=True, blank=True)
    company_profit_annual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    distributes_profits = models.BooleanField(default=False)
    has_multiple_assets = models.BooleanField(default=False)
    wants_efficient_management = models.BooleanField(default=False)
    has_management_difficulties = models.BooleanField(default=False)

    def __str__(self):
        return self.nome_holding

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
    data_inicio_processo = models.DateTimeField(auto_now_add=True)
    data_ultima_atualizacao = models.DateTimeField(auto_now=True)
    observacoes = models.TextField(blank=True, null=True)

    def __str__(self):
        return f"Processo de {self.cliente_principal.email} - Status: {self.get_status_atual_display()}"

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

class AnaliseEconomia(models.Model):
    holding = models.OneToOneField(Holding, on_delete=models.CASCADE, related_name='analise_economia')
    ano_referencia = models.PositiveIntegerField()
    economia_tributaria_estimada = models.DecimalField(max_digits=15, decimal_places=2)
    patrimonio_liquido_projetado = models.DecimalField(max_digits=15, decimal_places=2)
    data_calculo = models.DateField(auto_now_add=True)

    def __str__(self):
        return f"Análise Holding {self.holding.nome_holding} - Ano {self.ano_referencia}"

class SimulationResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='simulation_results')
    number_of_properties = models.IntegerField(default=0)
    total_property_value = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    inventory_cost_without = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    inventory_cost_with = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    number_of_companies = models.IntegerField(default=0)
    monthly_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    annual_profit = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    profit_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    monthly_rent = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    annual_rent = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    rental_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    inventory_time_without = models.IntegerField(default=0)
    inventory_time_with = models.IntegerField(default=0)
    receives_rent = models.BooleanField(default=False)
    has_companies = models.BooleanField(default=False)
    number_of_heirs = models.IntegerField(default=0)
    company_tax_regime = models.CharField(max_length=50, default='simples')
    inventory_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    total_savings = models.DecimalField(max_digits=15, decimal_places=2, default=0.0)
    conflict_risk = models.CharField(max_length=50, default='Nenhum')
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Simulação de {self.user.email} em {self.created_at}"