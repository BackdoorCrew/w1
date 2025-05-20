# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.conf import settings
from decimal import Decimal
from django.utils import timezone
# Removido import os, não será usado diretamente aqui para upload_to

class User(AbstractUser):
    USER_TYPE_CHOICES = (
        ('admin', 'Administrador'),
        ('consultor', 'Consultor'),
        ('cliente', 'Cliente'),
    )
    username = None
    email = models.EmailField(unique=True, verbose_name='Endereço de e-mail')
    user_type = models.CharField(
        max_length=10,
        choices=USER_TYPE_CHOICES,
        default='cliente',
        verbose_name='Tipo de Usuário'
    )
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['first_name', 'last_name']

    def __str__(self):
        return self.email

class ClienteProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='cliente_profile',
        verbose_name='Usuário Cliente'
    )
    patrimonio_total_estimado = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Patrimônio Total Estimado (R$)'
    )
    rendimentos_estimados_anuais = models.DecimalField(
        max_digits=15, decimal_places=2, null=True, blank=True,
        verbose_name='Rendimentos Anuais Estimados (R$)'
    )

    def __str__(self):
        return f"Perfil de {self.user.email}"

    class Meta:
        verbose_name = "Perfil do Cliente"
        verbose_name_plural = "Perfis de Clientes"

class Holding(models.Model):
    nome_holding = models.CharField(max_length=255, verbose_name='Nome da Holding')
    description = models.TextField(blank=True, null=True, verbose_name='Descrição')
    clientes = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='holdings_participadas',
        limit_choices_to={'user_type': 'cliente'},
        verbose_name='Clientes/Sócios'
    )
    consultor_responsavel = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='holdings_assessoradas',
        limit_choices_to={'user_type': 'consultor'},
        verbose_name='Consultor Responsável'
    )
    data_criacao_registro = models.DateField(null=True, blank=True, verbose_name='Data de Criação/Registro')
    has_bank_savings = models.BooleanField(default=False, verbose_name='Possui Poupança/Dinheiro em Banco?')
    bank_savings_amount = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Valor em Banco (R$)')
    has_heirs = models.BooleanField(default=False, verbose_name='Possui Herdeiros?')
    heir_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Quantidade de Herdeiros')
    has_succession_plan = models.BooleanField(default=False, verbose_name='Já Pensou no Plano Sucessório?')
    has_paid_inventory = models.BooleanField(default=False, verbose_name='Já Pagou Inventário de Parente?')
    has_rental_properties = models.BooleanField(default=False, verbose_name='Possui Imóveis Alugados?')
    rental_property_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Quantidade de Imóveis Alugados')
    rental_income_monthly = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Renda Mensal de Aluguéis (R$)')
    rental_expenses_monthly = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Despesas Mensais com Imóveis Alugados (R$)')
    has_litigation_concerns = models.BooleanField(default=False, verbose_name='Receio de Ações Judiciais?')
    has_legal_issues = models.BooleanField(default=False, verbose_name='Já Teve Problemas Legais / Setor de Risco?')
    wants_asset_protection = models.BooleanField(default=False, verbose_name='Quer Proteger Patrimônio Familiar?')
    protected_assets = models.TextField(blank=True, null=True, help_text="Descrição dos bens a proteger", verbose_name='Bens a Proteger')
    has_companies = models.BooleanField(default=False, verbose_name='É Sócio de Empresas?')
    company_count = models.PositiveIntegerField(null=True, blank=True, verbose_name='Quantidade de Empresas')
    company_profit_annual = models.DecimalField(max_digits=15, decimal_places=2, null=True, blank=True, verbose_name='Lucro Anual Aproximado das Empresas (R$)')
    distributes_profits = models.BooleanField(default=False, verbose_name='Costuma Distribuir Lucros ou Reinvestir?')
    has_multiple_assets = models.BooleanField(default=False, verbose_name='Possui Muitos Bens em Seu Nome?')
    wants_efficient_management = models.BooleanField(default=False, verbose_name='Gostaria de Facilitar Gestão/Venda de Bens?')
    has_management_difficulties = models.BooleanField(default=False, verbose_name='Já Teve Dificuldades com Controle Patrimonial?')
    is_legally_official = models.BooleanField(
        default=False,
        verbose_name='Holding Oficializada Legalmente',
        help_text='Marque se a holding foi constituída legalmente e está operacional.'
    )
    data_oficializacao = models.DateField(
        null=True, blank=True,
        verbose_name='Data de Oficialização Legal'
    )

    def __str__(self):
        return self.nome_holding

    class Meta:
        verbose_name = "Holding"
        verbose_name_plural = "Holdings"
        ordering = ['nome_holding']

class ProcessoHolding(models.Model):
    STATUS_CHOICES = (
        ('aguardando_documentos', 'Aguardando Documentos'),
        ('documentacao_em_analise', 'Documentação em Análise'),
        ('elaboracao_contrato', 'Elaboração de Contrato Social'),
        ('registro_junta', 'Registro na Junta Comercial'),
        ('providencias_pos_registro', 'Providências Pós-Registro'),
        ('concluido', 'Concluído'),
        ('concluido_oficializado', 'Concluído e Oficializado Legalmente'),
        ('cancelado', 'Cancelado'),
    )
    cliente_principal = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.PROTECT,
        related_name='processos_holding',
        limit_choices_to={'user_type': 'cliente'},
        verbose_name='Cliente Principal'
    )
    holding_associada = models.OneToOneField(
        Holding,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='processo_criacao',
        verbose_name='Holding Associada'
    )
    status_atual = models.CharField(
        max_length=30, # Aumentado para acomodar 'concluido_oficializado'
        choices=STATUS_CHOICES,
        default='aguardando_documentos',
        verbose_name='Status Atual do Processo'
    )
    data_inicio_processo = models.DateTimeField(auto_now_add=True, verbose_name='Data de Início')
    data_ultima_atualizacao = models.DateTimeField(auto_now=True, verbose_name='Última Atualização')
    observacoes = models.TextField(blank=True, null=True, verbose_name='Observações Internas')

    def __str__(self):
        cliente_email = self.cliente_principal.email if self.cliente_principal else "Cliente Desconhecido"
        holding_nome = self.holding_associada.nome_holding if self.holding_associada else "Holding N/A"
        return f"Processo de {cliente_email} (Holding: {holding_nome}) - Status: {self.get_status_atual_display()}"

    class Meta:
        verbose_name = "Processo de Holding"
        verbose_name_plural = "Processos de Holding"
        ordering = ['-data_inicio_processo']

# core/models.py


# ... (outros modelos como User, ClienteProfile, Holding, ProcessoHolding) ...

# core/models.py

# ... (imports e outros modelos) ...

class Documento(models.Model):
    CATEGORIA_CHOICES = (
        ('pessoais_socios', 'Documentos pessoais dos sócios'),
        ('patrimonio_incorporado', 'Documentos do patrimônio a ser incorporado'),
        ('societarios_registro', 'Documentos societários (Junta/Cartório)'),
        ('providencias_pos_registro', 'Outras providências pós-registro'),
        ('outros', 'Outros Documentos'),
    )
    processo_holding = models.ForeignKey(
        ProcessoHolding,
        on_delete=models.CASCADE,
        related_name='documentos',
        verbose_name='Processo da Holding'
    )
    enviado_por = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.SET_NULL,
        null=True,
        related_name='documentos_enviados',
        verbose_name='Enviado Por'
    )
    nome_documento_logico = models.CharField(
        max_length=255,
        verbose_name='Nome/Tipo do Documento (Ex: Contrato Social, RG Sócio)',
        help_text="Nome descritivo para agrupar versões. Ex: 'Contrato Social', 'RG do Sócio X'.",
        default='[Nome Lógico Não Especificado]'
    )
    arquivo = models.FileField(upload_to='documentos_holdings/%Y/%m/%d/', verbose_name='Arquivo')
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, verbose_name='Categoria')
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name='Data de Upload')
    descricao_adicional = models.TextField(blank=True, null=True, verbose_name='Descrição Adicional (Opcional)')

    versao = models.PositiveIntegerField(default=1, verbose_name="Versão")
    nome_original_arquivo = models.CharField(max_length=255, blank=True, verbose_name="Nome Original do Arquivo Enviado")

    def save(self, *args, **kwargs):
        if self.arquivo and not self.nome_original_arquivo:
            self.nome_original_arquivo = self.arquivo.name
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.nome_documento_logico} (v{self.versao}) - Processo ID: {self.processo_holding_id if self.processo_holding else 'N/A'}" # Adicionado if para evitar erro se processo_holding_id for None

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['processo_holding', 'nome_documento_logico', '-versao', '-data_upload']
        unique_together = ('processo_holding', 'nome_documento_logico', 'versao', 'categoria')



class AnaliseEconomia(models.Model):
    holding = models.OneToOneField(
        Holding,
        on_delete=models.CASCADE,
        related_name='analise_economia',
        verbose_name='Holding Analisada'
    )
    ano_referencia = models.PositiveIntegerField(verbose_name='Ano de Referência')
    economia_tributaria_estimada = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Economia Tributária Estimada (R$)'
    )
    patrimonio_liquido_projetado = models.DecimalField(
        max_digits=15, decimal_places=2,
        verbose_name='Patrimônio Líquido Projetado (R$)'
    )
    data_calculo = models.DateField(auto_now_add=True, verbose_name='Data do Cálculo')

    def __str__(self):
        return f"Análise Holding {self.holding.nome_holding} - Ano {self.ano_referencia}"

    class Meta:
        verbose_name = "Análise Econômica"
        verbose_name_plural = "Análises Econômicas"

class SimulationResult(models.Model):
    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='simulation_results')
    created_at = models.DateTimeField(auto_now_add=True)
    number_of_properties = models.IntegerField(default=0)
    total_property_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    inventory_cost_without = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    inventory_cost_with = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00')) # Geralmente 0
    inventory_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    has_companies = models.BooleanField(default=False)
    number_of_companies = models.IntegerField(default=0)
    company_tax_regime = models.CharField(max_length=50, blank=True, null=True)
    monthly_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    annual_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    profit_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    receives_rent = models.BooleanField(default=False)
    monthly_rent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    annual_rent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    rental_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))
    number_of_heirs = models.IntegerField(default=0)
    inventory_time_without = models.IntegerField(default=0)
    inventory_time_with = models.IntegerField(default=0)
    conflict_risk = models.CharField(max_length=50, default='Não Aplicável')
    total_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'))

    def __str__(self):
        return f"Simulação de {self.user.email} em {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Resultado da Simulação"
        verbose_name_plural = "Resultados das Simulações"
        ordering = ['-created_at']