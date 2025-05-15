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
    clientes = models.ManyToManyField(settings.AUTH_USER_MODEL, related_name='holdings_participadas', limit_choices_to={'user_type': 'cliente'})
    consultor_responsavel = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='holdings_assessoradas', limit_choices_to={'user_type': 'consultor'})
    data_criacao_registro = models.DateField(null=True, blank=True)
    # Sucessão
    has_successors = models.BooleanField(default=False)
    successor_count = models.PositiveIntegerField(null=True, blank=True)
    successor_age_range = models.CharField(max_length=50, choices=[
        ('<18', 'Menores de 18 anos'),
        ('18-40', '18 a 40 anos'),
        ('>40', 'Acima de 40 anos'),
    ], blank=True)
    has_existing_plan = models.BooleanField(default=False)
    # Renda de Aluguéis
    has_rental_income = models.BooleanField(default=False)
    rental_property_count = models.PositiveIntegerField(null=True, blank=True)
    rental_details = models.TextField(blank=True, help_text="JSON com endereços, valores de aluguel e despesas")
    # Empreendimentos/Empresas
    has_companies = models.BooleanField(default=False)
    company_count = models.PositiveIntegerField(null=True, blank=True)
    company_details = models.TextField(blank=True, help_text="JSON com receita/lucro e regime tributário")
    # Proteção Patrimonial
    has_protection_concerns = models.BooleanField(default=False)
    has_litigation_risk = models.BooleanField(default=False)
    protected_assets = models.TextField(blank=True, help_text="Descrição dos bens a proteger")
    # Vantagens Fiscais
    irpf_bracket = models.CharField(max_length=50, choices=[
        ('isento', 'Até R$22.847,76 – Isento'),
        ('7.5', 'R$22.847,77 a R$33.919,80 – 7,5%'),
        ('15', 'R$33.919,81 a R$45.012,60 – 15%'),
        ('22.5', 'R$45.012,61 a R$55.976,16 – 22,5%'),
        ('27.5', 'Acima de R$55.976,16 – 27,5%'),
    ], blank=True)
    has_dividends = models.BooleanField(default=False)
    dividend_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True)
    # Platform
    update_frequency = models.CharField(max_length=50, choices=[
        ('daily', 'Diária'),
        ('weekly', 'Semanal'),
        ('monthly', 'Mensal'),
    ], default='weekly')

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
    consultor_designado = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name='processos_designados', limit_choices_to={'user_type': 'consultor'})
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