# core/models.py
from django.db import models
from django.contrib.auth.models import AbstractUser, UserManager
from django.conf import settings
from decimal import Decimal
from django.utils import timezone

class CustomUserManager(UserManager):
    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError('O campo email é obrigatório')
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('is_active', True)
        extra_fields.setdefault('user_type', 'admin')

        if extra_fields.get('is_staff') is not True:
            raise ValueError('Superusuário deve ter is_staff=True.')
        if extra_fields.get('is_superuser') is not True:
            raise ValueError('Superusuário deve ter is_superuser=True.')

        return self.create_user(email, password, **extra_fields)


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
    whatsapp_number = models.CharField(
        max_length=20,  # Adjust max_length as needed (e.g., for E.164 format like +55119XXXXXXXX)
        blank=True,
        null=True,
        verbose_name='Número WhatsApp',
        help_text='Número de WhatsApp no formato internacional (ex: 5511999999999).'
    )
    objects = CustomUserManager()

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
    consultores = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        blank=True,
        related_name='holdings_assessoradas',
        limit_choices_to={'user_type': 'consultor'},
        verbose_name='Consultores Responsáveis'
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

class ChatMessage(models.Model):
    holding = models.ForeignKey(Holding, on_delete=models.CASCADE, related_name='chat_messages', verbose_name='Holding')
    sender = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='sent_chat_messages', verbose_name='Remetente')
    content = models.TextField(verbose_name='Conteúdo da Mensagem')
    timestamp = models.DateTimeField(auto_now_add=True, verbose_name='Data e Hora')

    def __str__(self):
        sender_name = self.sender.get_full_name() or self.sender.email
        return f"Msg por {sender_name} em '{self.holding.nome_holding}' às {self.timestamp.strftime('%d/%m/%y %H:%M')}"

    class Meta:
        verbose_name = 'Mensagem do Chat da Holding'
        verbose_name_plural = 'Mensagens do Chat da Holding'
        ordering = ['timestamp']

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
        on_delete=models.PROTECT, # Consider models.SET_NULL or another strategy if a client can be deleted
        related_name='processos_holding',
        limit_choices_to={'user_type': 'cliente'},
        verbose_name='Cliente Principal'
    )
    holding_associada = models.OneToOneField(
        Holding,
        on_delete=models.SET_NULL, # Or models.CASCADE if process is deleted when holding is
        null=True,
        blank=True,
        related_name='processo_criacao',
        verbose_name='Holding Associada'
    )
    status_atual = models.CharField(
        max_length=30, # Increased length for 'concluido_oficializado'
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

# PastaDocumento must be defined before Documento if Documento refers to it
class PastaDocumento(models.Model):
    processo_holding = models.ForeignKey(ProcessoHolding, on_delete=models.CASCADE, related_name='pastas_documentos', verbose_name="Processo da Holding")
    parent_folder = models.ForeignKey('self', null=True, blank=True, on_delete=models.CASCADE, related_name='subpastas', verbose_name='Pasta Pai')
    nome = models.CharField(max_length=150, verbose_name='Nome da Pasta')
    created_by = models.ForeignKey(settings.AUTH_USER_MODEL, null=True, blank=True, on_delete=models.SET_NULL, related_name='pastas_criadas_por_mim', verbose_name="Criado por")
    created_at = models.DateTimeField(auto_now_add=True, verbose_name="Data de Criação")
    updated_at = models.DateTimeField(auto_now=True, verbose_name="Última Modificação")

    def __str__(self):
        path = self.nome
        current = self.parent_folder
        while current:
            path = f"{current.nome} > {path}"
            current = current.parent_folder
        # Include ProcessoHolding ID for clarity in admin or logs if needed
        return f"PH({self.processo_holding_id}): {path}"


    class Meta:
        verbose_name = 'Pasta de Documento'
        verbose_name_plural = 'Pastas de Documentos'
        ordering = ['processo_holding', 'parent_folder__nome', 'nome']
        unique_together = ('processo_holding', 'parent_folder', 'nome')

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
        related_name='documentos_processo', # Changed related_name to avoid clash if any
        verbose_name='Processo da Holding'
    )
    pasta = models.ForeignKey(
        PastaDocumento,
        on_delete=models.SET_NULL, # Or models.CASCADE if documents should be deleted with folder
        null=True,
        blank=True,
        related_name='documentos_contidos', # This matches your PastaDocumentoAdmin and get_folder_structure
        verbose_name='Pasta de Armazenamento'
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
    categoria = models.CharField(max_length=30, choices=CATEGORIA_CHOICES, verbose_name='Categoria') # Max length adjusted
    data_upload = models.DateTimeField(auto_now_add=True, verbose_name='Data de Upload')
    descricao_adicional = models.TextField(blank=True, null=True, verbose_name='Descrição Adicional (Opcional)')
    versao = models.PositiveIntegerField(default=1, verbose_name="Versão")
    nome_original_arquivo = models.CharField(max_length=255, blank=True, verbose_name="Nome Original do Arquivo Enviado")

    def save(self, *args, **kwargs):
        if self.arquivo and not self.nome_original_arquivo:
            self.nome_original_arquivo = self.arquivo.name
        # Versioning logic is typically handled in the view upon new upload
        # to correctly check against existing versions with same name, category, and pasta.
        super().save(*args, **kwargs)

    def __str__(self):
        pasta_nome = f" (Pasta: {self.pasta.nome})" if self.pasta else " (Raiz do Processo)"
        return f"{self.nome_documento_logico} (v{self.versao}) - Proc: {self.processo_holding_id if self.processo_holding else 'N/A'}{pasta_nome}"

    class Meta:
        verbose_name = "Documento"
        verbose_name_plural = "Documentos"
        ordering = ['processo_holding', 'pasta__nome', 'nome_documento_logico', '-versao', '-data_upload']
        # Ensure this unique_together constraint aligns with your versioning logic.
        # If version is per folder:
        # unique_together = ('processo_holding', 'pasta', 'nome_documento_logico', 'versao', 'categoria')
        # If version is per process regardless of folder (current):
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
    
    # Campos existentes
    number_of_properties = models.IntegerField(default=0, verbose_name="Número de Imóveis")
    total_property_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor Total dos Imóveis")
    
    # ADICIONAR ESTE CAMPO:
    property_state = models.CharField(max_length=2, blank=True, null=True, verbose_name="Estado dos Imóveis")

    inventory_cost_without = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo de Inventário (Sem Holding)")
    inventory_cost_with = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Custo de Inventário (Com Holding)")
    inventory_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Economia no Inventário")
    
    has_companies = models.BooleanField(default=False, verbose_name="Possui Empresas?")
    number_of_companies = models.IntegerField(default=0, verbose_name="Número de Empresas")
    company_tax_regime = models.CharField(max_length=50, blank=True, null=True, verbose_name="Regime Tributário das Empresas")
    monthly_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Lucro Mensal (Empresas)")
    annual_profit = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Lucro Anual (Empresas)")
    profit_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Economia sobre Lucros (Empresas)")
    
    receives_rent = models.BooleanField(default=False, verbose_name="Recebe Aluguéis?")
    monthly_rent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Renda Mensal de Aluguéis")
    annual_rent = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Renda Anual de Aluguéis")
    rental_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Economia sobre Aluguéis")

    # ADICIONAR ESTES CAMPOS:
    has_investments = models.BooleanField(default=False, verbose_name="Possui Investimentos?")
    total_investment_value = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Valor Total dos Investimentos")
    investment_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Economia sobre Ganhos de Capital (Investimentos)")

    number_of_heirs = models.IntegerField(default=0, verbose_name="Número de Herdeiros")
    inventory_time_without = models.IntegerField(default=0, verbose_name="Tempo de Inventário sem Holding (meses)")
    inventory_time_with = models.IntegerField(default=0, verbose_name="Tempo de Inventário com Holding (meses)")
    conflict_risk = models.CharField(max_length=50, default='Não Aplicável', verbose_name="Risco de Conflito Familiar")
    
    total_savings = models.DecimalField(max_digits=15, decimal_places=2, default=Decimal('0.00'), verbose_name="Economia Total Estimada")

    updated_at = models.DateTimeField(auto_now=True) # Adicionado para rastrear atualizações

    def __str__(self):
        user_identifier = self.user.get_full_name() if self.user.get_full_name() else self.user.email
        return f"Simulação de {user_identifier} em {self.created_at.strftime('%d/%m/%Y %H:%M')}"

    class Meta:
        verbose_name = "Resultado da Simulação"
        verbose_name_plural = "Resultados das Simulações"
        ordering = ['-created_at']