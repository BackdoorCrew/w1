from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from allauth.account.forms import LoginForm, SignupForm
from .forms import HoldingForm, SimulationForm
from .models import Holding, ProcessoHolding, AnaliseEconomia, User, Documento # Garanta que Documento está importado
from datetime import date
from django.core.mail import send_mail
from django.conf import settings
from decimal import Decimal
from .forms import HoldingCreationUserForm, SimulationForm, ConsultantCreationForm, AssignConsultantToHoldingForm # Linha nova
from .decorators import superuser_required 
from django.urls import reverse
from .forms import ConsultantCreationForm
from django.contrib import messages
from django.db.models import Q

# Tax rates for calculations
INVENTORY_COST_RATE = Decimal('0.08')  # 8% (Inventory cost for properties)
RENTAL_TAX_PF = Decimal('0.275')  # 27.5% (Rental tax as individual)
RENTAL_TAX_PJ = Decimal('0.11')   # 11% (Rental tax with holding)
PROFIT_TAX_PF = Decimal('0.275')  # 27.5% (Profit tax as individual)

def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.user
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            if user.is_superuser:
                resolved_url = reverse('management_dashboard')
                print(f"DEBUG: Superuser login, redirecting to URL name 'management_dashboard', resolved path: {resolved_url}")
                return redirect('management_dashboard')
            return redirect('dashboard')
        print("Form errors:", form.errors)
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            user.user_type = 'cliente'
            user.save()
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def dashboard(request):
    form = SimulationForm()
    return render(request, 'core/simulation_input.html', {'form': form, 'user': request.user})

@login_required
def simulation(request):
    if request.method == 'POST':
        form = SimulationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # Property Inventory Savings (Questions 1 & 2)
            inventory_savings = Decimal('0')
            inventory_text = ""
            number_of_properties = cleaned_data.get('number_of_properties', 0)
            total_property_value = cleaned_data.get('total_property_value', Decimal('0'))
            if number_of_properties > 0 and total_property_value > 0:
                inventory_cost_without = total_property_value * INVENTORY_COST_RATE
                inventory_cost_with = Decimal('0')
                inventory_savings = inventory_cost_without
                inventory_text = (
                    f"Você possui {number_of_properties} imóvel(is) em seu nome, com valor total de R${total_property_value:,.2f}. "
                    f"Sem uma holding, o custo de inventário seria de R${inventory_cost_without:,.2f} (8% do valor). "
                    f"Com uma holding, você evita esse custo, economizando R${inventory_savings:,.2f} e facilitando a sucessão."
                )
            else:
                inventory_text = "Sem imóveis em seu nome, não há custos de inventário a considerar."

            # Company Profit Savings (Questions 3, 4, & 5)
            profit_savings = Decimal('0')
            profit_text = ""
            annual_profit = Decimal('0')
            tax_regime_label = {'simples': 'Simples', 'presumido': 'Presumido', 'real': 'Real'}
            if cleaned_data.get('has_companies') == 'yes':
                number_of_companies = cleaned_data.get('number_of_companies', 0)
                monthly_profit = cleaned_data.get('monthly_profit', Decimal('0'))
                company_tax_regime = cleaned_data.get('company_tax_regime')
                annual_profit = monthly_profit * Decimal('12')
                if company_tax_regime in ['presumido', 'real']:
                    profit_savings = annual_profit * PROFIT_TAX_PF
                    profit_text = (
                        f"Você possui {number_of_companies} empresa(s) no regime {tax_regime_label.get(company_tax_regime, 'Presumido')}, "
                        f"com lucro mensal de R${monthly_profit:,.2f} (R${annual_profit:,.2f} por ano). "
                        f"Sem uma holding, o imposto sobre lucros seria de R${profit_savings:,.2f} (27,5%). "
                        f"Com uma holding, a distribuição de lucros é isenta, economizando R${profit_savings:,.2f} por ano."
                    )
                else:
                    profit_text = (
                        f"Você possui {number_of_companies} empresa(s) no regime Simples, "
                        f"com lucro mensal de R${monthly_profit:,.2f}. No regime Simples, a distribuição de lucros já é isenta, "
                        f"mas uma holding pode proteger sua estrutura societária."
                    )
            else:
                profit_text = "Sem empresas em seu nome, não há economia tributária sobre lucros a considerar."

            # Rental Tax Savings (Question 6)
            rental_savings = Decimal('0')
            rental_text = ""
            annual_rent = Decimal('0')
            if cleaned_data.get('receives_rent') == 'yes':
                monthly_rent = cleaned_data.get('monthly_rent', Decimal('0'))
                annual_rent = monthly_rent * Decimal('12')
                tax_without_holding = annual_rent * RENTAL_TAX_PF
                tax_with_holding = annual_rent * RENTAL_TAX_PJ
                rental_savings = tax_without_holding - tax_with_holding
                rental_text = (
                    f"Você recebe R${monthly_rent:,.2f} por mês em aluguéis (R${annual_rent:,.2f} por ano). "
                    f"Sem uma holding, o imposto seria de R${tax_without_holding:,.2f} (27,5%). "
                    f"Com uma holding, o imposto cai para R${tax_with_holding:,.2f} (11%), "
                    f"economizando R${rental_savings:,.2f} por ano."
                )
            else:
                rental_text = "Sem aluguéis, não há economia tributária sobre aluguéis a considerar."

            # Succession Planning (Questions 7 & 8)
            succession_text = ""
            inventory_time_without = 0
            inventory_cost_without = Decimal('0')
            inventory_time_with = 0
            conflict_risk = "Nenhum"
            number_of_heirs = cleaned_data.get('number_of_heirs', 0)
            avoid_conflicts = cleaned_data.get('avoid_conflicts', False)
            if number_of_heirs > 0:
                if number_of_heirs == 1:
                    inventory_time_without = 12  # 6-12 months, using max for simplicity
                    inventory_cost_without = total_property_value * INVENTORY_COST_RATE  # 8% of property value
                    conflict_risk = "Baixo"
                elif number_of_heirs == 3:
                    inventory_time_without = 24  # 18-24 months, using max
                    inventory_cost_without = Decimal('150000')  # Fixed R$150,000
                    conflict_risk = "Médio"
                else:  # 5 or more heirs
                    inventory_time_without = 36  # 24-36 months, using max
                    inventory_cost_without = Decimal('250000')  # Fixed R$250,000
                    conflict_risk = "Alto"
                inventory_time_with = 0
                succession_text = (
                    f"Com {number_of_heirs} herdeiro(s), um inventário tradicional pode levar até {inventory_time_without} meses, "
                    f"custar R${inventory_cost_without:,.2f} e ter risco de conflito {conflict_risk.lower()}. "
                    f"Com uma holding, a transição é imediata, sem custos de inventário e sem disputas, "
                    f"garantindo que seu patrimônio seja transferido de forma segura e rápida para quem você ama."
                )
            else:
                succession_text = "Sem herdeiros especificados, o planejamento sucessório não se aplica."

            if avoid_conflicts:
                succession_text += (
                    " Você indicou que deseja evitar conflitos familiares. "
                    "Uma holding garante paz e segurança, organizando seu patrimônio de forma clara e protegida."
                )

            # Total Savings
            total_savings = inventory_savings + profit_savings + rental_savings

            # Context for template
            context = {
                'number_of_properties': number_of_properties,
                'total_property_value': float(total_property_value),
                'inventory_savings': float(inventory_savings),
                'inventory_text': inventory_text,
                'inventory_cost_without': float(inventory_cost_without),
                'inventory_cost_with': 0.0,
                'has_companies': cleaned_data.get('has_companies'),
                'number_of_companies': cleaned_data.get('number_of_companies', 0),
                'company_tax_regime': cleaned_data.get('company_tax_regime'),
                'monthly_profit': float(cleaned_data.get('monthly_profit', 0)),
                'annual_profit': float(annual_profit),
                'profit_savings': float(profit_savings),
                'profit_text': profit_text,
                'receives_rent': cleaned_data.get('receives_rent'),
                'monthly_rent': float(cleaned_data.get('monthly_rent', 0)),
                'annual_rent': float(annual_rent),
                'rental_savings': float(rental_savings),
                'rental_text': rental_text,
                'number_of_heirs': number_of_heirs,
                'avoid_conflicts': avoid_conflicts,
                'succession_text': succession_text,
                'inventory_time_without': inventory_time_without,
                'inventory_time_with': inventory_time_with,
                'conflict_risk': conflict_risk,
                'total_savings': float(total_savings),
            }
            print("Context:", context)
            return render(request, 'core/simulation.html', context)
        else:
            print("Form errors:", form.errors)
            return render(request, 'core/simulation_input.html', {'form': form, 'user': request.user})
    return redirect('dashboard')

@login_required
def create_holding(request):
    if request.method == 'POST':
        # Use HoldingCreationUserForm aqui
        form = HoldingCreationUserForm(request.POST, user=request.user)
        if form.is_valid():
            holding = form.save(commit=False)
            holding.save() # Salva a holding para obter um ID
            holding.clientes.add(request.user)

            ProcessoHolding.objects.create(
                cliente_principal=request.user,
                holding_associada=holding,
                status_atual='aguardando_documentos'
            )
            messages.success(request, f"Holding '{holding.nome_holding}' criada com sucesso e processo iniciado!")
            return redirect('dashboard_final')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        # Use HoldingCreationUserForm aqui
        form = HoldingCreationUserForm(user=request.user)
    return render(request, 'core/create_holding.html', {'form': form})

@login_required
def dashboard_final(request):
    return render(request, 'core/dashboard.html', {'user': request.user})

@login_required
def invite_partners(request):
    holding = Holding.objects.filter(clientes=request.user).first()
    if not holding:
        return redirect('create_holding')
    if request.method == 'POST':
        emails = request.POST.get('emails', '').split(',')
        for email in emails:
            email = email.strip()
            if email:
                try:
                    user, created = User.objects.get_or_create(
                        email=email,
                        defaults={'user_type': 'cliente', 'first_name': email.split('@')[0]}
                    )
                    holding.clientes.add(user)
                    send_mail(
                        subject='Convite para Colaborar na Holding',
                        message=f'Você foi convidado por {request.user.first_name} para colaborar na holding {holding.nome_holding}. Acesse: http://127.0.0.1:8000/simulation/',
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[email],
                    )
                except Exception as e:
                    print(f"Error inviting {email}: {e}")
        return redirect('dashboard_final')
    return render(request, 'core/invite_partners.html')

@login_required
@superuser_required
def management_list_holdings(request):
    """
    Lista todas as holdings com opção de pesquisa por nome, cliente ou consultor.
    """
    search_query = request.GET.get('q', '')
    # Otimiza as queries buscando dados relacionados de uma vez
    holdings_list = Holding.objects.all().select_related(
        'consultor_responsavel'
    ).prefetch_related(
        'clientes' # Para contagem e possível listagem de nomes de clientes
    ).order_by('nome_holding')

    if search_query:
        holdings_list = holdings_list.filter(
            Q(nome_holding__icontains=search_query) |
            Q(clientes__email__icontains=search_query) |
            Q(clientes__first_name__icontains=search_query) |
            Q(clientes__last_name__icontains=search_query) |
            Q(consultor_responsavel__email__icontains=search_query) |
            Q(consultor_responsavel__first_name__icontains=search_query) |
            Q(consultor_responsavel__last_name__icontains=search_query)
        ).distinct() # distinct() é importante ao filtrar por campos de tabelas relacionadas (M2M)

    context = {
        'holdings_list': holdings_list,
        'search_query': search_query,
        'page_title': 'Gerenciamento de Holdings'
    }
    return render(request, 'management/management_list_holdings.html', context)


@login_required
@superuser_required
def management_dashboard(request):
    """
    Dashboard principal para superusuários com funcionalidade de pesquisa.
    """
    search_query = request.GET.get('q', '')
    searched_users = User.objects.none() # Queryset vazio por padrão
    searched_holdings = Holding.objects.none() # Queryset vazio por padrão

    if search_query:
        # Pesquisa em Usuários (Clientes e Consultores)
        searched_users = User.objects.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).exclude(is_superuser=True).distinct().order_by('first_name', 'last_name') # Exclui superusuários da pesquisa rápida

        # Pesquisa em Holdings
        searched_holdings = Holding.objects.filter(
            Q(nome_holding__icontains=search_query)
        ).select_related('consultor_responsavel').prefetch_related('clientes').distinct().order_by('nome_holding')

    total_users = User.objects.count()
    total_clients = User.objects.filter(user_type='cliente').count()
    total_consultants = User.objects.filter(user_type='consultor').count()
    total_holdings = Holding.objects.count()
    recent_processes = ProcessoHolding.objects.order_by('-data_inicio_processo')[:5].select_related(
        'cliente_principal', 
        'holding_associada', 
        'holding_associada__consultor_responsavel'
    )

    context = {
        'total_users': total_users,
        'total_clients': total_clients,
        'total_consultants': total_consultants,
        'total_holdings': total_holdings,
        'recent_processes': recent_processes,
        'search_query': search_query,
        'searched_users': searched_users,
        'searched_holdings': searched_holdings,
        'page_title': 'Painel de Gestão Principal'
    }
    return render(request, 'management/management_dashboard.html', context)

@login_required
@superuser_required
def management_list_users(request):
    # Permitir filtragem por tipo de usuário
    user_type_filter = request.GET.get('user_type', '')
    users_list = User.objects.all().order_by('email')
    if user_type_filter:
        users_list = users_list.filter(user_type=user_type_filter)

    context = {
        'users_list': users_list,
        'user_types': User.USER_TYPE_CHOICES,
        'selected_user_type': user_type_filter,
        'page_title': 'Lista de Usuários'
    }
    return render(request, 'management/management_list_users.html', context)

@login_required
@superuser_required
@login_required
@superuser_required
def management_user_detail(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    
    client_profile = None
    client_holdings = [] # Inicializa como lista vazia
    client_processes = []
    client_documents = []
    consultant_assigned_holdings = [] # Inicializa como lista vazia

    print(f"--- Depurando detalhes para User ID: {user_id}, Email: {user_obj.email} ---")

    if user_obj.user_type == 'cliente':
        try:
            client_profile = user_obj.cliente_profile
        except ClienteProfile.DoesNotExist:
            client_profile = None
        
        # Pega o queryset
        client_holdings_qs = user_obj.holdings_participadas.all().select_related('consultor_responsavel').prefetch_related('clientes')
        
        print(f"Holdings do Cliente (User ID: {user_id}):")
        temp_client_holdings = []
        for h in client_holdings_qs:
            print(f"  -> Holding ID: {h.id}, Nome: '{h.nome_holding}'") # VERIFIQUE ESTA SAÍDA
            if h.id is None:
                print(f"    ALERTA CRÍTICO: Holding '{h.nome_holding}' (Objeto: {h}) está com ID None!")
                # Você pode optar por não adicionar holdings com ID None à lista do contexto
                # ou lidar com isso no template. Por enquanto, vamos apenas logar.
            temp_client_holdings.append(h)
        client_holdings = temp_client_holdings # Atribui a lista processada

        client_processes_qs = user_obj.processos_holding.all().select_related('holding_associada', 'holding_associada__consultor_responsavel')
        client_processes = list(client_processes_qs)
        
        process_ids = [p.id for p in client_processes if p and p.id is not None]
        client_documents = Documento.objects.filter(processo_holding_id__in=process_ids).select_related('enviado_por', 'processo_holding__holding_associada')

    elif user_obj.user_type == 'consultor':
        consultant_assigned_holdings_qs = user_obj.holdings_assessoradas.all().prefetch_related('clientes', 'processo_criacao__documentos')
        
        print(f"Holdings Assessoradas pelo Consultor (User ID: {user_id}):")
        temp_consultant_holdings = []
        for h in consultant_assigned_holdings_qs:
            print(f"  -> Holding Assessorada ID: {h.id}, Nome: '{h.nome_holding}'") # VERIFIQUE ESTA SAÍDA
            if h.id is None:
                print(f"    ALERTA CRÍTICO: Holding '{h.nome_holding}' (Objeto: {h}) está com ID None!")
            temp_consultant_holdings.append(h)
        consultant_assigned_holdings = temp_consultant_holdings


    context = {
        'user_obj': user_obj,
        'client_profile': client_profile,
        'client_holdings': client_holdings,
        'client_processes': client_processes,
        'client_documents': client_documents,
        'consultant_assigned_holdings': consultant_assigned_holdings,
        'page_title': f'Detalhes: {user_obj.get_full_name() or user_obj.email}'
    }
    return render(request, 'management/management_user_detail.html', context)


# Placeholder para criar consultor - precisará de um formulário
@login_required
@superuser_required
def management_create_consultant(request):
    # Você precisará criar um ConsultantCreationForm em forms.py
    # Exemplo:
    # if request.method == 'POST':
    #     form = ConsultantCreationForm(request.POST)
    #     if form.is_valid():
    #         user = form.save(commit=False)
    #         user.user_type = 'consultor'
    #         user.set_password(form.cleaned_data['password']) # Ou gere uma senha
    #         user.is_staff = True # Opcional, se consultores devem acessar o admin padrão
    #         user.save()
    #         # messages.success(request, 'Consultor criado com sucesso!')
    #         return redirect('management_list_users')
    # else:
    #     form = ConsultantCreationForm()
    # context = {'form': form, 'page_title': 'Criar Novo Consultor'}
    # return render(request, 'management/management_form_page.html', context)
    return render(request, 'management/management_form_page.html', {'page_title': 'Criar Consultor (Em Desenvolvimento)'})


# Placeholder para atribuir consultor - precisará de um formulário
@login_required
@superuser_required
def management_assign_consultant_to_holding(request, holding_id):
    holding = get_object_or_404(Holding, pk=holding_id)
    # Você precisará de um formulário para selecionar um consultor
    # Exemplo:
    # if request.method == 'POST':
    #     form = AssignConsultantToHoldingForm(request.POST, instance=holding)
    #     if form.is_valid():
    #         form.save()
    #         # messages.success(request, f'Consultor atribuído à holding {holding.nome_holding}')
    #         return redirect('management_user_detail', user_id=holding.clientes.first().id) # Ou para onde for apropriado
    # else:
    #     form = AssignConsultantToHoldingForm(instance=holding)
    # context = {'form': form, 'holding': holding, 'page_title': f'Atribuir Consultor a {holding.nome_holding}'}
    # return render(request, 'management/management_form_page.html', context)
    return render(request, 'management/management_form_page.html', {'holding': holding, 'page_title': f'Atribuir Consultor a {holding.nome_holding} (Em Desenvolvimento)'})

@login_required
@superuser_required
def management_holding_documents(request, holding_id):
    holding = get_object_or_404(Holding, pk=holding_id)
    documents = []
    if hasattr(holding, 'processo_criacao') and holding.processo_criacao:
        documents = Documento.objects.filter(processo_holding=holding.processo_criacao)
    # Se documentos puderem ser ligados diretamente à holding, ajuste a query
    context = {
        'holding': holding,
        'documents': documents,
        'page_title': f'Documentos da Holding {holding.nome_holding}'
    }
    return render(request, 'management/management_holding_documents.html', context)

@login_required
@superuser_required # Garante que apenas superusuários acessem
def management_create_consultant(request):
    """
    View para o superusuário criar novas contas de Consultor.
    """
    if request.method == 'POST':
        form = ConsultantCreationForm(request.POST)
        if form.is_valid():
            consultant = form.save() # O método save do form já define user_type e senha
            messages.success(request, f'A conta para o consultor {consultant.email} foi criada com sucesso!')
            # Você pode adicionar aqui o envio de um e-mail de boas-vindas para o consultor, se desejar.
            # Ex: send_welcome_email(consultant.email, form.cleaned_data["password"])
            return redirect('management_list_users') # Redireciona para a lista de usuários
        else:
            messages.error(request, 'Houve um erro no formulário. Por favor, verifique os dados inseridos.')
    else:
        form = ConsultantCreationForm()

    context = {
        'form': form,
        'page_title': 'Criar Novo Consultor',
        'form_title': 'Dados do Novo Consultor', # Título para o template genérico de formulário
        'submit_button_text': 'Criar Consultor' # Texto para o botão de submit
    }
    return render(request, 'management/management_form_page.html', context)

@login_required
@superuser_required
def management_user_detail(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id) # Agora get_object_or_404 está definido
    
    client_profile = None
    client_holdings = []
    client_processes = []
    client_documents = [] # Documentos associados ao cliente através de seus processos

    consultant_assigned_holdings = [] # Holdings pelas quais o consultor é responsável

    if user_obj.user_type == 'cliente':
        try:
            client_profile = user_obj.cliente_profile
        except ClienteProfile.DoesNotExist:
            client_profile = None # Ou crie um se fizer sentido: ClienteProfile.objects.create(user=user_obj)
        
        client_holdings = user_obj.holdings_participadas.all().select_related('consultor_responsavel').prefetch_related('clientes')
        client_processes = user_obj.processos_holding.all().select_related('holding_associada', 'holding_associada__consultor_responsavel')
        
        # Buscar documentos associados aos processos do cliente
        process_ids = [p.id for p in client_processes]
        client_documents = Documento.objects.filter(processo_holding_id__in=process_ids).select_related('enviado_por', 'processo_holding__holding_associada')

    elif user_obj.user_type == 'consultor':
        consultant_assigned_holdings = user_obj.holdings_assessoradas.all().prefetch_related('clientes', 'processo_criacao__documentos')
        # Processos onde este consultor é o consultor_responsavel da holding associada ao processo
        # client_processes = ProcessoHolding.objects.filter(holding_associada__consultor_responsavel=user_obj).select_related('cliente_principal', 'holding_associada')


    context = {
        'user_obj': user_obj,
        'client_profile': client_profile,
        'client_holdings': client_holdings,
        'client_processes': client_processes,
        'client_documents': client_documents, # Adicionado ao contexto
        'consultant_assigned_holdings': consultant_assigned_holdings,
        'page_title': f'Detalhes: {user_obj.get_full_name() or user_obj.email}'
    }
    return render(request, 'management/management_user_detail.html', context)

# Adicionar uma nova view para detalhes da Holding
@login_required
@superuser_required
def management_holding_detail(request, holding_id):
    holding = get_object_or_404(Holding.objects.select_related('consultor_responsavel').prefetch_related('clientes', 'processo_criacao__documentos'), pk=holding_id)
    
    # Clientes/Sócios desta holding
    socios = holding.clientes.all()
    
    # Processo de criação associado
    processo_criacao = None
    if hasattr(holding, 'processo_criacao'):
        processo_criacao = holding.processo_criacao
        
    # Documentos (através do processo de criação)
    documentos_holding = []
    if processo_criacao:
        documentos_holding = processo_criacao.documentos.all().select_related('enviado_por')

    # Análise econômica, se houver
    analise = None
    if hasattr(holding, 'analise_economia'):
        analise = holding.analise_economia

    context = {
        'holding': holding,
        'socios': socios,
        'processo_criacao': processo_criacao,
        'documentos_holding': documentos_holding,
        'analise': analise,
        'page_title': f'Detalhes da Holding: {holding.nome_holding}'
    }
    return render(request, 'management/management_holding_detail.html', context)