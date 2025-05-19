# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required, user_passes_test
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q
from django.conf import settings # For settings like DEFAULT_FROM_EMAIL
from datetime import date # For date operations if needed
from django.core.mail import send_mail # For sending emails

from allauth.account.forms import LoginForm, SignupForm # Allauth forms

from .models import (
    User, Holding, ProcessoHolding, AnaliseEconomia, Documento,
    ClienteProfile, SimulationResult # Assuming SimulationResult is defined in your models.py
)
from .forms import (
    HoldingCreationUserForm, SimulationForm, # Your primary forms
    ConsultantCreationForm, AssignConsultantToHoldingForm, # Management forms
    CustomSignupForm # Your custom signup form if used
)
from .decorators import superuser_required

from decimal import Decimal

# Tax rates for calculations
INVENTORY_COST_RATE = Decimal('0.08')
RENTAL_TAX_PF = Decimal('0.275')
RENTAL_TAX_PJ = Decimal('0.11')
PROFIT_TAX_PF = Decimal('0.275')

# --- Public and Authentication Views ---
def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('management_dashboard')
        return redirect('dashboard')

    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.user
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            if user.is_superuser:
                messages.success(request, f"Bem-vindo de volta, {user.get_full_name() or user.email}!")
                return redirect('management_dashboard')
            messages.success(request, f"Login bem-sucedido, {user.get_full_name() or user.email}!")
            return redirect('dashboard') # Redirects to simulation_input page for clients
        else:
            messages.error(request, "O endereço de e-mail e/ou senha especificados não estão corretos.")
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.user.is_authenticated:
        return redirect('dashboard')

    if request.method == 'POST':
        # Decide whether to use allauth's SignupForm or your CustomSignupForm
        # For consistency with allauth, using its form is often simpler.
        # If CustomSignupForm is used, ensure it handles all necessary fields and logic.
        form = SignupForm(request.POST) # Using allauth's SignupForm
        # form = CustomSignupForm(request.POST) # Or your custom one
        if form.is_valid():
            user = form.save(request) # allauth's form.save() needs the request
            user.user_type = 'cliente'
            user.save()
            # auth_login is often handled by allauth after signup if ACCOUNT_LOGIN_ON_SIGNUP = True
            # but explicitly calling it ensures the session is set with the correct backend.
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            messages.success(request, "Cadastro realizado com sucesso! Você foi logado.")
            return redirect('dashboard') # Redirects to simulation_input page
        else:
            messages.error(request, "Por favor, corrija os erros abaixo para prosseguir.")
    else:
        form = SignupForm() # Or CustomSignupForm()
    return render(request, 'core/signup.html', {'form': form})

# --- Client Area Views ---
@login_required
def dashboard(request): # This view now serves as the entry point to the simulation form
    if request.user.is_superuser:
        return redirect('management_dashboard')
    
    # If you want a different dashboard for consultants:
    # if request.user.user_type == 'consultor':
    #     return render(request, 'core/consultant_dashboard.html', {})

    form = SimulationForm()
    return render(request, 'core/simulation_input.html', {'form': form, 'user': request.user})

@login_required
def simulation(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    if request.method == 'POST':
        form = SimulationForm(request.POST)
        if form.is_valid():
            cleaned_data = form.cleaned_data

            # --- Start of Simulation Calculations ---
            inventory_savings = Decimal('0')
            inventory_text = ""
            number_of_properties = cleaned_data.get('number_of_properties', 0)
            total_property_value = cleaned_data.get('total_property_value') or Decimal('0') # Ensure Decimal
            inventory_cost_without = Decimal('0')

            if number_of_properties > 0 and total_property_value > 0:
                inventory_cost_without = total_property_value * INVENTORY_COST_RATE
                inventory_savings = inventory_cost_without
                inventory_text = (
                    f"Você possui {number_of_properties} imóvel(is) em seu nome, com valor total de R${total_property_value:,.2f}. "
                    f"Sem uma holding, o custo de inventário seria de aproximadamente R${inventory_cost_without:,.2f} (estimativa de 8-15% do valor, incluindo ITCMD, custas e honorários). "
                    f"Com uma holding, o processo de inventário para esses bens é evitado, gerando uma economia significativa e facilitando a sucessão."
                )
            else:
                inventory_text = "Sem imóveis informados ou com valor zero, não há custos de inventário a calcular para esta simulação."

            profit_savings = Decimal('0')
            profit_text = ""
            annual_profit = Decimal('0')
            tax_regime_label = {'simples': 'Simples Nacional', 'presumido': 'Lucro Presumido', 'real': 'Lucro Real'}
            
            has_companies = cleaned_data.get('has_companies') == 'yes'
            number_of_companies = cleaned_data.get('number_of_companies', 0) if has_companies else 0
            monthly_profit = cleaned_data.get('monthly_profit') or Decimal('0') if has_companies else Decimal('0')
            company_tax_regime = cleaned_data.get('company_tax_regime') if has_companies else None

            if has_companies and number_of_companies > 0:
                annual_profit = monthly_profit * Decimal('12')
                if company_tax_regime in ['presumido', 'real'] and annual_profit > 0:
                    profit_tax_pf_value = annual_profit * PROFIT_TAX_PF
                    profit_savings = profit_tax_pf_value
                    profit_text = (
                        f"Com {number_of_companies} empresa(s) no regime {tax_regime_label.get(company_tax_regime, str(company_tax_regime).capitalize())}, "
                        f"e lucro mensal distribuído de R${monthly_profit:,.2f} (R${annual_profit:,.2f} por ano). "
                        f"Ao distribuir para pessoa física, o imposto de renda pode chegar a 27,5%, totalizando R${profit_savings:,.2f}. "
                        f"Com uma holding, a distribuição de lucros da holding para os sócios (pessoa física) é isenta, economizando este valor anualmente."
                    )
                elif company_tax_regime == 'simples':
                    profit_text = (
                        f"Você possui {number_of_companies} empresa(s) no regime Simples Nacional. "
                        f"Neste regime, a distribuição de lucros para pessoa física já é isenta de IRPF. "
                        f"Uma holding ainda pode oferecer vantagens na organização societária, proteção patrimonial e planejamento sucessório."
                    )
                else:
                    profit_text = (
                        f"Você possui {number_of_companies} empresa(s). Se houver distribuição de lucros (especialmente em regimes de Lucro Presumido/Real), "
                        f"uma holding pode otimizar a carga tributária sobre esses valores."
                    )
            else:
                profit_text = "Sem empresas informadas (ou sem lucros distribuídos de empresas fora do Simples), não há economia tributária sobre lucros a considerar nesta simulação específica."

            rental_savings = Decimal('0')
            rental_text = ""
            annual_rent = Decimal('0')
            receives_rent = cleaned_data.get('receives_rent') == 'yes'
            monthly_rent_val = cleaned_data.get('monthly_rent') or Decimal('0') if receives_rent else Decimal('0')

            if receives_rent and monthly_rent_val > 0:
                annual_rent = monthly_rent_val * Decimal('12')
                tax_without_holding = annual_rent * RENTAL_TAX_PF
                tax_with_holding = annual_rent * RENTAL_TAX_PJ
                rental_savings = tax_without_holding - tax_with_holding
                rental_text = (
                    f"Você recebe R${monthly_rent_val:,.2f} por mês em aluguéis (R${annual_rent:,.2f} por ano). "
                    f"Na pessoa física, o imposto de renda sobre aluguéis pode chegar a 27,5% (R${tax_without_holding:,.2f}). "
                    f"Com uma holding (optante pelo Lucro Presumido), o imposto sobre a receita de aluguéis cai para aproximadamente 11,33% (R${tax_with_holding:,.2f}), "
                    f"economizando R${rental_savings:,.2f} por ano."
                )
            else:
                rental_text = "Sem aluguéis informados, não há economia tributária sobre aluguéis a considerar."

            succession_text = ""
            inventory_time_without = 0
            inventory_time_with = 0 # Tempo com holding é para planejamento, não inventário
            conflict_risk = "Não Aplicável"
            number_of_heirs = cleaned_data.get('number_of_heirs', 0)
            avoid_conflicts = cleaned_data.get('avoid_conflicts', 'no') # Default to 'no'

            if number_of_heirs > 0 and total_property_value > 0:
                # inventory_cost_without já calculado acima
                if number_of_heirs == 1:
                    inventory_time_without = 12
                    conflict_risk = "Baixo"
                elif number_of_heirs <= 3: # Exemplo de lógica, ajuste conforme necessário
                    inventory_time_without = 24
                    # inventory_cost_without *= Decimal('1.1') # Aumenta um pouco o custo estimado
                    conflict_risk = "Médio"
                else: # 4 ou mais
                    inventory_time_without = 36
                    # inventory_cost_without *= Decimal('1.2')
                    conflict_risk = "Alto"
                
                succession_text = (
                    f"Com {number_of_heirs} herdeiro(s) e patrimônio de R${total_property_value:,.2f}, um inventário tradicional pode levar até {inventory_time_without} meses, "
                    f"custar aproximadamente R${inventory_cost_without:,.2f} e ter um risco de conflito {conflict_risk.lower()}. "
                    f"Com uma holding, a sucessão é planejada em vida através da doação de cotas, geralmente com reserva de usufruto. Isso evita o processo de inventário para os bens dentro da holding, reduzindo drasticamente custos, tempo e o potencial de disputas familiares."
                )
            elif number_of_heirs > 0:
                 succession_text = "Você tem herdeiros, mas não informou o valor dos imóveis para calcular a economia com inventário. Uma holding facilita o planejamento sucessório."
            else:
                succession_text = "Mesmo sem herdeiros diretos informados, uma holding oferece proteção patrimonial e gestão centralizada, podendo ser parte de um planejamento sucessório mais amplo."

            if avoid_conflicts == 'yes':
                succession_text += (
                    " Você indicou que deseja evitar conflitos familiares. "
                    "A holding é uma excelente ferramenta para isso, permitindo a definição clara da sucessão em vida, com cláusulas de proteção e reserva de usufruto para o doador."
                )
            
            total_savings = inventory_savings + profit_savings + rental_savings
            # --- Fim dos Cálculos da Simulação ---

            # Salvar resultados da simulação (assumindo que SimulationResult está definido em models.py)
            try:
                SimulationResult.objects.create(
                    user=request.user,
                    number_of_properties=number_of_properties,
                    total_property_value=total_property_value,
                    inventory_cost_without=inventory_cost_without,
                    inventory_cost_with=Decimal('0'), # Custo de inventário com holding é evitado
                    number_of_companies=number_of_companies if has_companies else 0,
                    monthly_profit=monthly_profit if has_companies else Decimal('0'),
                    annual_profit=annual_profit if has_companies else Decimal('0'),
                    profit_savings=profit_savings,
                    monthly_rent=monthly_rent_val if receives_rent else Decimal('0'),
                    annual_rent=annual_rent if receives_rent else Decimal('0'),
                    rental_savings=rental_savings,
                    inventory_time_without=inventory_time_without,
                    inventory_time_with=inventory_time_with, # Tempo com holding é diferente
                    receives_rent=receives_rent,
                    has_companies=has_companies,
                    number_of_heirs=number_of_heirs,
                    company_tax_regime=company_tax_regime if has_companies else '',
                    inventory_savings=inventory_savings,
                    total_savings=total_savings,
                    conflict_risk=conflict_risk,
                    # Adicione outros campos do SimulationResult aqui se necessário
                )
                messages.success(request, "Simulação calculada e salva!")
            except Exception as e:
                messages.error(request, f"Erro ao salvar a simulação: {e}")
                print(f"Erro ao salvar SimulationResult: {e}")


            context = {
                'user': request.user,
                'number_of_properties': number_of_properties,
                'total_property_value': float(total_property_value), # JS espera float
                'inventory_savings': float(inventory_savings),
                'inventory_text': inventory_text,
                'inventory_cost_without': float(inventory_cost_without),
                'inventory_cost_with': 0.0,
                'has_companies': 'yes' if has_companies else 'no', # Para o template JS
                'number_of_companies': number_of_companies,
                'company_tax_regime': company_tax_regime,
                'monthly_profit': float(monthly_profit),
                'annual_profit': float(annual_profit),
                'profit_savings': float(profit_savings),
                'profit_text': profit_text,
                'receives_rent': 'yes' if receives_rent else 'no', # Para o template JS
                'monthly_rent': float(monthly_rent_val),
                'annual_rent': float(annual_rent),
                'rental_savings': float(rental_savings),
                'rental_text': rental_text,
                'number_of_heirs': number_of_heirs,
                'avoid_conflicts': avoid_conflicts == 'yes', # Passa booleano para o template
                'succession_text': succession_text,
                'inventory_time_without': inventory_time_without,
                'inventory_time_with': inventory_time_with,
                'conflict_risk': conflict_risk,
                'total_savings': float(total_savings),
            }
            return render(request, 'core/simulation.html', context)
        else:
            messages.error(request, "Por favor, corrija os erros no formulário de simulação.")
            # Passa o form com erros de volta para o template de input
            return render(request, 'core/simulation_input.html', {'form': form, 'user': request.user})
    # Se não for POST, redireciona para a página de input da simulação (dashboard)
    return redirect('dashboard')


@login_required
def create_holding(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    if request.method == 'POST':
        form = HoldingCreationUserForm(request.POST, user=request.user)
        if form.is_valid():
            holding = form.save(commit=False)
            holding.save()
            holding.clientes.add(request.user)
            
            ProcessoHolding.objects.create(
                cliente_principal=request.user,
                holding_associada=holding,
                status_atual='aguardando_documentos'
            )
            messages.success(request, f"Holding '{holding.nome_holding}' informações salvas e processo iniciado!")
            return redirect('dashboard_final')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        form = HoldingCreationUserForm(user=request.user)
    return render(request, 'core/create_holding.html', {'form': form})

@login_required
def dashboard_final(request): # Esta view pode mostrar resultados ou um resumo pós-criação
    if request.user.is_superuser:
        return redirect('management_dashboard')
    
    latest_simulation = None
    try:
        # Se SimulationResult estiver definido e você quiser mostrar a última simulação:
        latest_simulation = SimulationResult.objects.filter(user=request.user).latest('created_at')
    except SimulationResult.DoesNotExist:
        latest_simulation = None
    except NameError: # Caso SimulationResult não esteja definido ainda
        print("AVISO: Modelo SimulationResult não encontrado para dashboard_final.")
        latest_simulation = None


    user_holdings = Holding.objects.filter(clientes=request.user).select_related('consultor_responsavel')
    context = {
        'user': request.user,
        'user_holdings': user_holdings,
        'latest_simulation': latest_simulation, # Adiciona ao contexto
    }
    return render(request, 'core/dashboard.html', context) # Renderiza o template do dashboard final


@login_required
def invite_partners(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    holding = Holding.objects.filter(clientes=request.user).first()
    if not holding:
        messages.info(request, "Você precisa primeiro criar ou ter uma holding associada para convidar sócios.")
        return redirect('create_holding')

    if request.method == 'POST':
        emails_str = request.POST.get('emails', '')
        emails = [email.strip() for email in emails_str.split(',') if email.strip()]
        
        if not emails:
            messages.error(request, "Por favor, insira pelo menos um e-mail.")
        else:
            invited_count = 0
            for email_addr in emails:
                try:
                    partner_user, created = User.objects.get_or_create(
                        email=email_addr,
                        defaults={
                            'user_type': 'cliente',
                            'first_name': email_addr.split('@')[0],
                        }
                    )
                    if created:
                        partner_user.set_unusable_password()
                        partner_user.save()
                        messages.info(request, f"Conta preliminar criada para {email_addr}.")

                    if partner_user not in holding.clientes.all():
                        holding.clientes.add(partner_user)
                        # send_mail(...)
                        messages.success(request, f"Acesso concedido para {email_addr} à holding {holding.nome_holding}.")
                        invited_count += 1
                    else:
                        messages.warning(request, f"{email_addr} já é um cliente desta holding.")
                except Exception as e:
                    messages.error(request, f"Erro ao processar o convite para {email_addr}: {e}")
            if invited_count > 0:
                return redirect('dashboard_final') 
            
    return render(request, 'core/invite_partners.html', {'holding': holding})


# --- Management Views (Superuser) ---
@login_required
@superuser_required
def management_dashboard(request):
    search_query = request.GET.get('q', '')
    searched_users = User.objects.none()
    searched_holdings = Holding.objects.none()

    if search_query:
        searched_users = User.objects.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        ).exclude(is_superuser=True).distinct().order_by('first_name', 'last_name')
        searched_holdings = Holding.objects.filter(
            Q(nome_holding__icontains=search_query)
        ).select_related('consultor_responsavel').prefetch_related('clientes').distinct().order_by('nome_holding')

    total_users = User.objects.count()
    total_clients = User.objects.filter(user_type='cliente').count()
    total_consultants = User.objects.filter(user_type='consultor').count()
    total_holdings = Holding.objects.count()
    recent_processes = ProcessoHolding.objects.order_by('-data_inicio_processo')[:5].select_related(
        'cliente_principal', 'holding_associada', 'holding_associada__consultor_responsavel'
    )
    context = {
        'total_users': total_users, 'total_clients': total_clients,
        'total_consultants': total_consultants, 'total_holdings': total_holdings,
        'recent_processes': recent_processes, 'search_query': search_query,
        'searched_users': searched_users, 'searched_holdings': searched_holdings,
        'page_title': 'Painel de Gestão Principal'
    }
    return render(request, 'management/management_dashboard.html', context)

@login_required
@superuser_required
def management_list_users(request):
    user_type_filter = request.GET.get('user_type', '')
    search_query = request.GET.get('search', '')
    users_list = User.objects.all().order_by('first_name', 'last_name', 'email')
    if user_type_filter:
        users_list = users_list.filter(user_type=user_type_filter)
    if search_query:
        users_list = users_list.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
    context = {
        'users_list': users_list, 'user_types': User.USER_TYPE_CHOICES,
        'selected_user_type': user_type_filter, 'search_query': search_query,
        'page_title': 'Gerenciamento de Usuários'
    }
    return render(request, 'management/management_list_users.html', context)

@login_required
@superuser_required
def management_user_detail(request, user_id):
    user_obj = get_object_or_404(User, pk=user_id)
    client_profile = None
    client_holdings = []
    client_processes = []
    client_documents = []
    consultant_assigned_holdings = []

    if user_obj.user_type == 'cliente':
        try:
            client_profile = user_obj.cliente_profile
        except ClienteProfile.DoesNotExist:
            pass
        client_holdings = user_obj.holdings_participadas.all().select_related('consultor_responsavel').prefetch_related('clientes')
        client_processes = user_obj.processos_holding.all().select_related('holding_associada', 'holding_associada__consultor_responsavel')
        process_ids = [p.id for p in client_processes if p and p.id is not None]
        client_documents = Documento.objects.filter(processo_holding_id__in=process_ids).select_related('enviado_por', 'processo_holding__holding_associada')
    elif user_obj.user_type == 'consultor':
        consultant_assigned_holdings = user_obj.holdings_assessoradas.all().prefetch_related('clientes', 'processo_criacao__documentos')

    context = {
        'user_obj': user_obj, 'client_profile': client_profile,
        'client_holdings': client_holdings, 'client_processes': client_processes,
        'client_documents': client_documents, 'consultant_assigned_holdings': consultant_assigned_holdings,
        'page_title': f'Detalhes: {user_obj.get_full_name() or user_obj.email}'
    }
    return render(request, 'management/management_user_detail.html', context)

@login_required
@superuser_required
def management_create_consultant(request):
    if request.method == 'POST':
        form = ConsultantCreationForm(request.POST)
        if form.is_valid():
            consultant = form.save()
            messages.success(request, f'A conta para o consultor {consultant.email} foi criada com sucesso!')
            return redirect('management_list_users')
        else:
            messages.error(request, 'Houve um erro no formulário. Verifique os dados inseridos.')
    else:
        form = ConsultantCreationForm()
    context = {
        'form': form, 'page_title': 'Criar Novo Consultor',
        'form_title': 'Dados do Novo Consultor', 'submit_button_text': 'Criar Consultor'
    }
    return render(request, 'management/management_form_page.html', context)

@login_required
@superuser_required
def management_assign_consultant_to_holding(request, holding_id):
    holding = get_object_or_404(Holding, pk=holding_id)
    if request.method == 'POST':
        form = AssignConsultantToHoldingForm(request.POST, instance=holding)
        if form.is_valid():
            form.save()
            messages.success(request, f'Consultor e detalhes da holding {holding.nome_holding} atualizados.')
            first_client = holding.clientes.first()
            if first_client:
                 return redirect('management_user_detail', user_id=first_client.id)
            return redirect('management_holding_detail', holding_id=holding.id)
        else:
            messages.error(request, "Erro ao atualizar a holding.")
    else:
        form = AssignConsultantToHoldingForm(instance=holding)
    context = {
        'form': form, 'holding': holding,
        'page_title': f'Gerenciar Holding: {holding.nome_holding}',
        'form_title': f'Editar Detalhes e Atribuir Consultor para {holding.nome_holding}',
        'submit_button_text': 'Salvar Alterações na Holding'
    }
    return render(request, 'management/management_form_page.html', context)

@login_required
@superuser_required
def management_holding_detail(request, holding_id):
    holding = get_object_or_404(
        Holding.objects.select_related('consultor_responsavel').prefetch_related(
            'clientes', 'processo_criacao__documentos__enviado_por', 'analise_economia'
        ), pk=holding_id
    )
    socios = holding.clientes.all()
    processo_criacao = getattr(holding, 'processo_criacao', None)
    documentos_holding = processo_criacao.documentos.all() if processo_criacao else []
    analise = getattr(holding, 'analise_economia', None)
    context = {
        'holding': holding, 'socios': socios, 'processo_criacao': processo_criacao,
        'documentos_holding': documentos_holding, 'analise': analise,
        'page_title': f'Detalhes da Holding: {holding.nome_holding}'
    }
    return render(request, 'management/management_holding_detail.html', context)

@login_required
@superuser_required
def management_list_holdings(request):
    search_query = request.GET.get('q', '')
    holdings_list = Holding.objects.all().select_related(
        'consultor_responsavel'
    ).prefetch_related('clientes').order_by('nome_holding')
    if search_query:
        holdings_list = holdings_list.filter(
            Q(nome_holding__icontains=search_query) |
            Q(clientes__email__icontains=search_query) |
            Q(clientes__first_name__icontains=search_query) |
            Q(clientes__last_name__icontains=search_query) |
            Q(consultor_responsavel__email__icontains=search_query) |
            Q(consultor_responsavel__first_name__icontains=search_query) |
            Q(consultor_responsavel__last_name__icontains=search_query)
        ).distinct()
    context = {
        'holdings_list': holdings_list, 'search_query': search_query,
        'page_title': 'Gerenciamento de Holdings'
    }
    return render(request, 'management/management_list_holdings.html', context)

@login_required
@superuser_required
def management_holding_documents(request, holding_id):
    holding = get_object_or_404(Holding, pk=holding_id)
    documents = []
    processo = getattr(holding, 'processo_criacao', None)
    if processo:
        documents = Documento.objects.filter(processo_holding=processo).select_related('enviado_por')
    context = {
        'holding': holding, 'documents': documents, 'processo': processo,
        'page_title': f'Documentos da Holding {holding.nome_holding}'
    }
    return render(request, 'management/management_holding_documents.html', context)
