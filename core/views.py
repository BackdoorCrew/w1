# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Max
from django.conf import settings
from datetime import date
# from django.core.mail import send_mail # Removido se não usado
from django.db import connection
from .decorators import superuser_required, consultant_or_superuser_required
from django.utils import timezone
from .forms import (
    HoldingCreationUserForm, SimulationForm,
    ConsultantCreationForm, AssignConsultantToHoldingForm,
    CustomSignupForm,
    ProcessStatusUpdateForm, HoldingOfficializeForm,
    AddClientToHoldingForm,
    DocumentUploadForm, # <<< CERTIFIQUE-SE QUE ESTÁ AQUI
    ManagementDocumentUploadForm # <<< E ESTE TAMBÉM, PARA OUTRA VIEW
)
from allauth.account.forms import LoginForm
from allauth.account.utils import complete_signup
from allauth.socialaccount.models import SocialAccount

from .models import (
    User, Holding, ProcessoHolding, AnaliseEconomia, Documento,
    ClienteProfile, SimulationResult
)
# Removida importação duplicada de Forms

from decimal import Decimal

# Constantes de Taxas
INVENTORY_COST_RATE = Decimal('0.08')
RENTAL_TAX_PF = Decimal('0.275')
RENTAL_TAX_PJ = Decimal('0.1133')
PROFIT_TAX_PF = Decimal('0.275')

# --- Views Públicas e de Autenticação ---
def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('management_dashboard')
        return redirect('dashboard_final')

    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.user
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            if user.is_superuser:
                messages.success(request, f"Bem-vindo de volta, {user.get_full_name() or user.email}!")
                return redirect('management_dashboard')
            messages.success(request, f"Login bem-sucedido, {user.get_full_name() or user.email}!")
            return redirect('dashboard_final')
        else:
            messages.error(request, "O endereço de e-mail e/ou senha especificados não estão corretos.")
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.user.is_authenticated:
        if request.user.is_superuser:
            return redirect('management_dashboard')
        return redirect('dashboard_final')

    if request.method == 'POST':
        form = CustomSignupForm(request.POST)
        if form.is_valid():
            user = form.save()
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            messages.success(request, "Cadastro realizado com sucesso! Bem-vindo(a)!")
            return redirect('dashboard') 
        else:
            messages.error(request, "Por favor, corrija os erros abaixo para prosseguir.")
    else:
        form = CustomSignupForm()
    return render(request, 'core/signup.html', {'form': form})

# --- Área do Cliente ---
@login_required
def dashboard(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')
    form = SimulationForm()
    return render(request, 'core/simulation_input.html', {'form': form, 'user': request.user})

@login_required
def simulation(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')
    if request.method == 'POST':
        form = SimulationForm(request.POST)
        if form.is_valid():
            # ... (LÓGICA DE SIMULAÇÃO MANTIDA - COPIE DO SEU ARQUIVO EXISTENTE) ...
            # Esta parte é longa, então estou omitindo para brevidade, mas ela deve permanecer como estava
            cleaned_data = form.cleaned_data
            number_of_properties = cleaned_data.get('number_of_properties', 0)
            total_property_value = cleaned_data.get('total_property_value') or Decimal('0')
            inventory_cost_without = Decimal('0')
            inventory_savings = Decimal('0')
            inventory_text = "Sem imóveis informados ou com valor zero, não há custos de inventário a calcular."
            if number_of_properties > 0 and total_property_value > 0:
                inventory_cost_without = total_property_value * INVENTORY_COST_RATE
                inventory_savings = inventory_cost_without
                inventory_text = (
                    f"Você possui {number_of_properties} imóvel(is) com valor total de R${total_property_value:,.2f}. "
                    f"Sem uma holding, o custo de inventário seria aprox. R${inventory_cost_without:,.2f}. "
                    f"Com holding, este custo é evitado, economizando R${inventory_savings:,.2f}."
                )
            has_companies = cleaned_data.get('has_companies') == 'yes'
            number_of_companies = cleaned_data.get('number_of_companies', 0) if has_companies else 0
            monthly_profit_val = cleaned_data.get('monthly_profit') if cleaned_data.get('monthly_profit') is not None else Decimal('0')
            if not has_companies: monthly_profit_val = Decimal('0')
            company_tax_regime = cleaned_data.get('company_tax_regime') if has_companies else None
            annual_profit = Decimal('0')
            profit_savings = Decimal('0')
            profit_text = "Sem empresas informadas ou lucros relevantes, não há economia sobre lucros a simular."
            tax_regime_label = {'simples': 'Simples Nacional', 'presumido': 'Lucro Presumido', 'real': 'Lucro Real'}
            if has_companies and number_of_companies > 0 and monthly_profit_val > 0:
                annual_profit = monthly_profit_val * Decimal('12')
                if company_tax_regime in ['presumido', 'real']:
                    profit_tax_pf_value = annual_profit * PROFIT_TAX_PF
                    profit_savings = profit_tax_pf_value
                    profit_text = (
                        f"Com {number_of_companies} empresa(s) no regime {tax_regime_label.get(company_tax_regime, str(company_tax_regime or '').capitalize())} "
                        f"e lucro mensal distribuído de R${monthly_profit_val:,.2f} (R${annual_profit:,.2f}/ano). "
                        f"Distribuindo para PF, o IRPF seria aprox. R${profit_savings:,.2f}. "
                        f"Com holding, a distribuição é isenta, economizando este valor."
                    )
                elif company_tax_regime == 'simples':
                    profit_text = (
                        f"{number_of_companies} empresa(s) no Simples Nacional. "
                        f"Distribuição de lucros já é isenta de IRPF. Holding oferece outras vantagens."
                    )
            receives_rent = cleaned_data.get('receives_rent') == 'yes'
            monthly_rent_val = cleaned_data.get('monthly_rent') if cleaned_data.get('monthly_rent') is not None else Decimal('0')
            if not receives_rent: monthly_rent_val = Decimal('0')
            annual_rent = Decimal('0')
            rental_savings = Decimal('0')
            rental_text = "Sem aluguéis informados, não há economia sobre aluguéis a simular."
            if receives_rent and monthly_rent_val > 0:
                annual_rent = monthly_rent_val * Decimal('12')
                tax_without_holding = annual_rent * RENTAL_TAX_PF
                tax_with_holding = annual_rent * RENTAL_TAX_PJ
                rental_savings = tax_without_holding - tax_with_holding
                rental_text = (
                    f"Com R${monthly_rent_val:,.2f}/mês em aluguéis (R${annual_rent:,.2f}/ano). "
                    f"Na PF, imposto aprox. R${tax_without_holding:,.2f} (27,5%). "
                    f"Com holding (Lucro Presumido), imposto aprox. R${tax_with_holding:,.2f} (11,33%), "
                    f"economizando R${rental_savings:,.2f}/ano."
                )
            number_of_heirs = cleaned_data.get('number_of_heirs', 0)
            avoid_conflicts = cleaned_data.get('avoid_conflicts', 'no')
            inventory_time_without = 0
            inventory_time_with = 0
            conflict_risk = "Não Aplicável"
            succession_text = "Planejamento sucessório com holding visa evitar inventário, reduzir custos e conflitos."
            if number_of_heirs > 0 and total_property_value > 0:
                inventory_time_without = 12 if number_of_heirs == 1 else (24 if number_of_heirs <= 3 else 36)
                conflict_risk = "Baixo" if number_of_heirs == 1 else ("Médio" if number_of_heirs <= 3 else "Alto")
                succession_text = (
                    f"Com {number_of_heirs} herdeiro(s) e patrimônio de R${total_property_value:,.2f}, "
                    f"inventário tradicional: até {inventory_time_without} meses, custo aprox. R${inventory_cost_without:,.2f}, risco de conflito {conflict_risk.lower()}. "
                    f"Holding permite sucessão em vida, evitando inventário dos bens na holding."
                )
            elif number_of_heirs > 0:
                 succession_text = "Com herdeiros, holding facilita o planejamento sucessório."
            if avoid_conflicts == 'yes':
                succession_text += " Você deseja evitar conflitos: holding é ideal para definir a sucessão em vida."
            total_savings = inventory_savings + profit_savings + rental_savings
            try:
                SimulationResult.objects.create(
                    user=request.user, number_of_properties=number_of_properties,
                    total_property_value=total_property_value, inventory_cost_without=inventory_cost_without,
                    inventory_cost_with=Decimal('0'), number_of_companies=number_of_companies,
                    monthly_profit=monthly_profit_val, annual_profit=annual_profit, profit_savings=profit_savings,
                    monthly_rent=monthly_rent_val, annual_rent=annual_rent, rental_savings=rental_savings,
                    inventory_time_without=inventory_time_without, inventory_time_with=inventory_time_with,
                    receives_rent=receives_rent, has_companies=has_companies, number_of_heirs=number_of_heirs,
                    company_tax_regime=company_tax_regime or '', inventory_savings=inventory_savings,
                    total_savings=total_savings, conflict_risk=conflict_risk
                )
                messages.success(request, "Simulação calculada e salva!")
            except Exception as e:
                messages.error(request, f"Erro ao salvar a simulação: {e}")
            context = {
                'user': request.user, 'number_of_properties': number_of_properties,
                'total_property_value': float(total_property_value), 'inventory_savings': float(inventory_savings),
                'inventory_text': inventory_text, 'inventory_cost_without': float(inventory_cost_without),
                'inventory_cost_with': 0.0, 'has_companies': 'yes' if has_companies else 'no',
                'number_of_companies': number_of_companies, 'company_tax_regime': company_tax_regime,
                'monthly_profit': float(monthly_profit_val), 'annual_profit': float(annual_profit),
                'profit_savings': float(profit_savings), 'profit_text': profit_text,
                'receives_rent': 'yes' if receives_rent else 'no', 'monthly_rent': float(monthly_rent_val),
                'annual_rent': float(annual_rent), 'rental_savings': float(rental_savings),
                'rental_text': rental_text, 'number_of_heirs': number_of_heirs,
                'avoid_conflicts': avoid_conflicts == 'yes', 'succession_text': succession_text,
                'inventory_time_without': inventory_time_without, 'inventory_time_with': inventory_time_with,
                'conflict_risk': conflict_risk, 'total_savings': float(total_savings),
                'RENTAL_TAX_PF': RENTAL_TAX_PF * 100, 'RENTAL_TAX_PJ': RENTAL_TAX_PJ * 100,
                'PROFIT_TAX_PF': PROFIT_TAX_PF * 100,
            }
            return render(request, 'core/simulation.html', context)
        else:
            messages.error(request, "Por favor, corrija os erros no formulário de simulação.")
            return render(request, 'core/simulation_input.html', {'form': form, 'user': request.user})
    return redirect('dashboard')

@login_required
def create_holding(request):
    # ... (lógica mantida como estava) ...
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
            messages.success(request, f"Interesse na holding '{holding.nome_holding}' registrado! Um consultor entrará em contato.")
            return redirect('dashboard_final')
        else:
            messages.error(request, "Por favor, corrija os erros no formulário.")
    else:
        form = HoldingCreationUserForm(user=request.user)
    return render(request, 'core/create_holding.html', {'form': form})

@login_required
def dashboard_final(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    latest_simulation = SimulationResult.objects.filter(user=request.user).order_by('-created_at').first()
    user_holdings_qs = Holding.objects.filter(clientes=request.user).select_related(
        'consultor_responsavel', 'processo_criacao'
    ).prefetch_related(
        'processo_criacao__documentos__enviado_por'
    )
    
    target_processo = None
    # Lógica para determinar para qual processo o upload será feito.
    # Por simplicidade, se o usuário tiver múltiplas holdings/processos,
    # vamos pegar o processo da primeira holding que tem um processo de criação.
    # Uma UI mais avançada permitiria ao usuário selecionar.
    active_holding_with_process = None
    for h in user_holdings_qs:
        if hasattr(h, 'processo_criacao') and h.processo_criacao:
            active_holding_with_process = h # Guardamos a holding para exibir o nome
            target_processo = h.processo_criacao
            break
    
    document_form = DocumentUploadForm() 

    if request.method == 'POST':
        if 'upload_document_cliente' in request.POST and target_processo: # Botão de submit específico
            form_post = DocumentUploadForm(request.POST, request.FILES)
            if form_post.is_valid():
                doc = form_post.save(commit=False)
                doc.processo_holding = target_processo
                doc.enviado_por = request.user
                doc.nome_original_arquivo = doc.arquivo.name # Salva nome original

                # Lógica de Versionamento
                latest_version_data = Documento.objects.filter(
                    processo_holding=target_processo,
                    nome_documento_logico=doc.nome_documento_logico,
                    categoria=doc.categoria # Versionamento por categoria também
                ).aggregate(max_versao=Max('versao'))
                
                current_max_version = latest_version_data.get('max_versao')
                doc.versao = (current_max_version + 1) if current_max_version is not None else 1
                
                doc.save()
                messages.success(request, f"Documento '{doc.nome_documento_logico}' (v{doc.versao}) enviado com sucesso!")
                return redirect('dashboard_final') 
            else:
                messages.error(request, "Erro ao enviar o documento. Por favor, verifique os campos.")
                document_form = form_post # Passa o formulário com erros de volta

    # Agrupar documentos para exibição no template
    grouped_documents_cliente = {}
    if target_processo:
        docs_for_process = Documento.objects.filter(processo_holding=target_processo).order_by('nome_documento_logico', 'categoria', '-versao')
        for doc in docs_for_process:
            key = (doc.nome_documento_logico, doc.categoria) # Chave para agrupar por nome e categoria
            if key not in grouped_documents_cliente:
                grouped_documents_cliente[key] = {
                    'nome_logico': doc.nome_documento_logico,
                    'categoria_display': doc.get_categoria_display(),
                    'versoes': []
                }
            grouped_documents_cliente[key]['versoes'].append(doc)
            
    context = {
        'user': request.user,
        'user_holdings': user_holdings_qs,
        'latest_simulation': latest_simulation,
        'document_form': document_form,
        'active_holding_for_docs': active_holding_with_process, # Nome da holding para o form de upload
        'target_processo_id': target_processo.id if target_processo else None,
        'grouped_documents_cliente': grouped_documents_cliente,
    }
    return render(request, 'core/dashboard.html', context)

@login_required
def invite_partners(request):
    # ... (lógica mantida como estava) ...
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
                        defaults={'user_type': 'cliente', 'first_name': email_addr.split('@')[0]}
                    )
                    if created:
                        partner_user.set_unusable_password()
                        partner_user.save()
                    if partner_user not in holding.clientes.all():
                        holding.clientes.add(partner_user)
                        messages.success(request, f"Acesso concedido para {email_addr} à holding {holding.nome_holding}.")
                        invited_count += 1
                    else:
                        messages.warning(request, f"{email_addr} já é um sócio desta holding.")
                except Exception as e:
                    messages.error(request, f"Erro ao processar o convite para {email_addr}: {e}")
            if invited_count > 0:
                return redirect('dashboard_final') 
    return render(request, 'core/invite_partners.html', {'holding': holding})

# --- Management Views ---
@login_required
@consultant_or_superuser_required
def management_dashboard(request):
    # ... (lógica mantida como estava, com filtros para consultor) ...
    search_query = request.GET.get('q', '')
    searched_users_qs = User.objects.none()
    searched_holdings_qs = Holding.objects.none()
    if request.user.is_superuser:
        total_users = User.objects.exclude(is_superuser=True).count()
        total_clients = User.objects.filter(user_type='cliente').count()
        total_consultants = User.objects.filter(user_type='consultor').count()
        total_holdings = Holding.objects.count()
        recent_processes_qs = ProcessoHolding.objects.order_by('-data_inicio_processo')[:5]
    elif request.user.user_type == 'consultor':
        user_holdings_ids = Holding.objects.filter(consultor_responsavel=request.user).values_list('id', flat=True)
        total_clients = User.objects.filter(holdings_participadas__id__in=user_holdings_ids, user_type='cliente').distinct().count()
        total_consultants = 0
        total_holdings = user_holdings_ids.count()
        total_users = total_clients
        recent_processes_qs = ProcessoHolding.objects.filter(holding_associada__id__in=user_holdings_ids).order_by('-data_inicio_processo')[:5]
    else: return redirect('login')
    recent_processes = recent_processes_qs.select_related('cliente_principal', 'holding_associada', 'holding_associada__consultor_responsavel')
    if search_query:
        base_user_query = Q(email__icontains=search_query) | Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query)
        base_holding_query = Q(nome_holding__icontains=search_query)
        if request.user.is_superuser:
            searched_users_qs = User.objects.filter(base_user_query).exclude(is_superuser=True)
            searched_holdings_qs = Holding.objects.filter(base_holding_query)
        elif request.user.user_type == 'consultor':
            client_ids_from_holdings = Holding.objects.filter(consultor_responsavel=request.user).values_list('clientes__id', flat=True).distinct()
            searched_users_qs = User.objects.filter(base_user_query, id__in=client_ids_from_holdings, user_type='cliente')
            searched_holdings_qs = Holding.objects.filter(base_holding_query, consultor_responsavel=request.user)
    context = {
        'total_users': total_users, 'total_clients': total_clients, 'total_consultants': total_consultants, 'total_holdings': total_holdings,
        'recent_processes': recent_processes, 'search_query': search_query,
        'searched_users': searched_users_qs.distinct().order_by('first_name', 'last_name') if searched_users_qs.exists() else User.objects.none(),
        'searched_holdings': searched_holdings_qs.select_related('consultor_responsavel').prefetch_related('clientes').distinct().order_by('nome_holding') if searched_holdings_qs.exists() else Holding.objects.none(),
        'page_title': 'Painel de Gestão Principal'
    }
    return render(request, 'management/management_dashboard.html', context)

@login_required
@superuser_required
def management_list_users(request):
    # ... (lógica mantida como estava) ...
    user_type_filter = request.GET.get('user_type', '')
    search_query = request.GET.get('search', '') 
    users_list = User.objects.all().order_by('first_name', 'last_name', 'email')
    if user_type_filter:
        if user_type_filter == 'admin': users_list = users_list.filter(is_superuser=True)
        else: users_list = users_list.filter(user_type=user_type_filter, is_superuser=False)
    elif request.user.is_superuser: users_list = users_list.exclude(pk=request.user.pk)
    if search_query:
        users_list = users_list.filter(Q(email__icontains=search_query) | Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query))
    context = {'users_list': users_list, 'user_types': User.USER_TYPE_CHOICES, 'selected_user_type': user_type_filter, 'search_query': search_query, 'page_title': 'Gerenciamento de Usuários'}
    return render(request, 'management/management_list_users.html', context)

@login_required
@consultant_or_superuser_required
def management_user_detail(request, user_id):
    # ... (lógica mantida como estava, com verificação de permissão interna) ...
    user_to_view = get_object_or_404(User, pk=user_id)
    can_view = False
    if request.user.is_superuser: can_view = True
    elif request.user.user_type == 'consultor':
        if user_to_view.id == request.user.id: can_view = True
        elif user_to_view.user_type == 'cliente':
            if Holding.objects.filter(consultor_responsavel=request.user, clientes=user_to_view).exists(): can_view = True
    if not can_view:
        messages.error(request, "Você não tem permissão para ver detalhes deste usuário.")
        return redirect('management_dashboard') 
    client_profile = None; client_holdings = []; client_processes = []; client_documents = []; consultant_assigned_holdings = []
    if user_to_view.user_type == 'cliente':
        try: client_profile = user_to_view.cliente_profile
        except ClienteProfile.DoesNotExist: pass
        client_holdings = user_to_view.holdings_participadas.all().select_related('consultor_responsavel').prefetch_related('clientes')
        client_processes = ProcessoHolding.objects.filter(cliente_principal=user_to_view).select_related('holding_associada', 'holding_associada__consultor_responsavel')
        process_ids = [p.id for p in client_processes if p and p.id is not None]
        client_documents = Documento.objects.filter(processo_holding_id__in=process_ids).select_related('enviado_por', 'processo_holding__holding_associada')
    elif user_to_view.user_type == 'consultor':
        consultant_assigned_holdings = user_to_view.holdings_assessoradas.all().prefetch_related('clientes', 'processo_criacao__documentos')
    context = {
        'user_obj': user_to_view, 'client_profile': client_profile, 'client_holdings': client_holdings,
        'client_processes': client_processes, 'client_documents': client_documents,
        'consultant_assigned_holdings': consultant_assigned_holdings,
        'page_title': f'Detalhes: {user_to_view.get_full_name() or user_to_view.email}'
    }
    return render(request, 'management/management_user_details.html', context)

@login_required
@superuser_required
def management_create_consultant(request):
    # ... (lógica mantida como estava) ...
    if request.method == 'POST':
        form = ConsultantCreationForm(request.POST)
        if form.is_valid():
            consultant = form.save()
            messages.success(request, f'A conta para o consultor {consultant.email} foi criada com sucesso!')
            return redirect('management_list_users')
        else: messages.error(request, 'Houve um erro no formulário. Verifique os dados inseridos.')
    else: form = ConsultantCreationForm()
    context = {'form': form, 'page_title': 'Criar Novo Consultor', 'form_title': 'Dados do Novo Consultor', 'submit_button_text': 'Criar Consultor'}
    return render(request, 'management/management_form_page.html', context)

@login_required
@superuser_required 
def management_assign_consultant_to_holding(request, holding_id):
    # ... (lógica mantida como estava) ...
    holding = get_object_or_404(Holding, pk=holding_id)
    if request.method == 'POST':
        form = AssignConsultantToHoldingForm(request.POST, instance=holding)
        if form.is_valid():
            form.save()
            messages.success(request, f'Consultor e detalhes da holding {holding.nome_holding} atualizados.')
            return redirect('management_holding_detail', holding_id=holding.id)
        else: messages.error(request, "Erro ao atualizar a holding.")
    else: form = AssignConsultantToHoldingForm(instance=holding)
    context = {'form': form, 'holding': holding, 'page_title': f'Editar Holding: {holding.nome_holding}', 'form_title': f'Editar Dados Básicos de {holding.nome_holding}', 'submit_button_text': 'Salvar Alterações'}
    return render(request, 'management/management_form_page.html', context)

@login_required
@consultant_or_superuser_required
def management_holding_detail(request, holding_id):
    holding_base_qs = Holding.objects.select_related(
        'consultor_responsavel', 'processo_criacao'
    ).prefetch_related(
        'clientes', 
        'processo_criacao__documentos__enviado_por',
        'analise_economia'
    )

    if request.user.is_superuser:
        holding = get_object_or_404(holding_base_qs, pk=holding_id)
    elif request.user.user_type == 'consultor':
        holding = get_object_or_404(holding_base_qs, pk=holding_id, consultor_responsavel=request.user)
    else: # Não deve acontecer devido ao decorador, mas como fallback
        messages.error(request, "Acesso negado.")
        return redirect('login') 

    processo_criacao = getattr(holding, 'processo_criacao', None)
    process_status_form, officialize_form = None, None
    management_document_form = ManagementDocumentUploadForm() # Instancia para GET

    if not processo_criacao and request.method == 'POST' and 'upload_document_management' in request.POST:
        messages.error(request, "Não é possível adicionar documentos pois esta holding não possui um processo de criação ativo.")
    elif request.method == 'POST':
        if 'upload_document_management' in request.POST and processo_criacao:
            form_post_mgmt = ManagementDocumentUploadForm(request.POST, request.FILES)
            if form_post_mgmt.is_valid():
                doc = form_post_mgmt.save(commit=False)
                doc.processo_holding = processo_criacao
                doc.enviado_por = request.user 
                doc.nome_original_arquivo = doc.arquivo.name

                latest_version_data_mgmt = Documento.objects.filter(
                    processo_holding=processo_criacao,
                    nome_documento_logico=doc.nome_documento_logico,
                    categoria=doc.categoria
                ).aggregate(max_versao=Max('versao'))
                
                current_max_version_mgmt = latest_version_data_mgmt.get('max_versao')
                doc.versao = (current_max_version_mgmt + 1) if current_max_version_mgmt is not None else 1
                
                doc.save()
                messages.success(request, f"Documento '{doc.nome_documento_logico}' (v{doc.versao}) enviado para a holding '{holding.nome_holding}'.")
                return redirect('management_holding_detail', holding_id=holding.id)
            else:
                messages.error(request, "Erro ao enviar o documento pela gestão. Verifique os campos.")
                management_document_form = form_post_mgmt # Para exibir erros
        
        elif 'update_status' in request.POST and processo_criacao:
            process_status_form = ProcessStatusUpdateForm(request.POST, instance=processo_criacao)
            if process_status_form.is_valid():
                process_status_form.save()
                messages.success(request, f"Status da holding '{holding.nome_holding}' atualizado.")
                return redirect('management_holding_detail', holding_id=holding.id)
        elif 'officialize_holding' in request.POST and not holding.is_legally_official:
            officialize_form = HoldingOfficializeForm(request.POST) 
            if officialize_form.is_valid():
                holding.is_legally_official = True
                holding.data_oficializacao = officialize_form.cleaned_data['data_oficializacao']
                holding.save() 
                if processo_criacao:
                    if any('concluido_oficializado' == choice[0] for choice in ProcessoHolding.STATUS_CHOICES):
                        processo_criacao.status_atual = 'concluido_oficializado'
                    elif processo_criacao.status_atual != 'concluido':
                        processo_criacao.status_atual = 'concluido'
                    processo_criacao.save()
                messages.success(request, f"Holding '{holding.nome_holding}' oficializada.")
                return redirect('management_holding_detail', holding_id=holding.id)
        elif 'un_officialize_holding' in request.POST and holding.is_legally_official and request.user.is_superuser:
            holding.is_legally_official = False
            holding.data_oficializacao = None # Limpar data ao reverter
            holding.save()
            if processo_criacao and processo_criacao.status_atual == 'concluido_oficializado':
                processo_criacao.status_atual = 'concluido' 
                processo_criacao.save()
            messages.info(request, f"Oficialização da holding '{holding.nome_holding}' revertida.")
            return redirect('management_holding_detail', holding_id=holding.id)

    if processo_criacao and not process_status_form: # Se não foi um POST com erro para este form
        process_status_form = ProcessStatusUpdateForm(instance=processo_criacao)
    if not holding.is_legally_official and not officialize_form:
        officialize_form = HoldingOfficializeForm(initial={'data_oficializacao': holding.data_oficializacao or timezone.now().date()})

    socios = holding.clientes.all()
    
    grouped_documents_management = {}
    documentos_holding_count = 0
    if processo_criacao:
        docs_for_mgmt = Documento.objects.filter(processo_holding=processo_criacao).order_by('nome_documento_logico', 'categoria', '-versao')
        documentos_holding_count = docs_for_mgmt.count()
        for doc in docs_for_mgmt:
            key_mgmt = (doc.nome_documento_logico, doc.categoria)
            if key_mgmt not in grouped_documents_management:
                grouped_documents_management[key_mgmt] = {
                    'nome_logico': doc.nome_documento_logico,
                    'categoria_display': doc.get_categoria_display(),
                    'versoes': []
                }
            grouped_documents_management[key_mgmt]['versoes'].append(doc)
    
    analise = getattr(holding, 'analise_economia', None)
    context = {
        'holding': holding, 'socios': socios, 'processo_criacao': processo_criacao,
        'documentos_holding_count': documentos_holding_count, # Apenas a contagem
        'grouped_documents_management': grouped_documents_management,
        'analise': analise,
        'process_status_form': process_status_form, 
        'officialize_form': officialize_form,
        'management_document_form': management_document_form,
        'page_title': f'Detalhes da Holding: {holding.nome_holding}'
    }
    return render(request, 'management/management_holding_details.html', context)



@login_required
@consultant_or_superuser_required
def management_list_holdings(request):
    # ... (lógica mantida como estava, com filtro para consultor) ...
    search_query = request.GET.get('q', '')
    base_query = Holding.objects.select_related('consultor_responsavel').prefetch_related('clientes')
    if request.user.is_superuser:
        holdings_list = base_query.all()
    elif request.user.user_type == 'consultor':
        holdings_list = base_query.filter(consultor_responsavel=request.user)
    else:
        holdings_list = Holding.objects.none()
    if search_query:
        holdings_list = holdings_list.filter(
            Q(nome_holding__icontains=search_query) |
            Q(clientes__email__icontains=search_query) |
            Q(clientes__first_name__icontains=search_query) |
            Q(clientes__last_name__icontains=search_query)
        ).distinct()
    holdings_list = holdings_list.order_by('nome_holding')
    context = {'holdings_list': holdings_list, 'search_query': search_query, 'page_title': 'Gerenciamento de Holdings'}
    return render(request, 'management/management_list_holdings.html', context)

@login_required
@consultant_or_superuser_required
def management_holding_documents(request, holding_id):
    # Esta view agora simplesmente redireciona para a página de detalhes da holding.
    # A permissão para ver a holding é verificada na view de detalhes.
    return redirect('management_holding_details.html', holding_id=holding_id)

@login_required
@consultant_or_superuser_required
def management_holding_manage_clients(request, holding_id):
    # ... (lógica mantida como estava, com filtro de permissão) ...
    holding_base_qs = Holding.objects.prefetch_related('clientes')
    if request.user.is_superuser:
        holding = get_object_or_404(holding_base_qs, pk=holding_id)
    elif request.user.user_type == 'consultor':
        holding = get_object_or_404(holding_base_qs, pk=holding_id, consultor_responsavel=request.user)
    else:
        messages.error(request, "Acesso negado.")
        return redirect('login')
    add_client_form = AddClientToHoldingForm() # Inicializa aqui para o contexto GET
    if request.method == 'POST':
        if 'add_client' in request.POST:
            add_client_form = AddClientToHoldingForm(request.POST)
            if add_client_form.is_valid():
                client_to_add = add_client_form.cleaned_data['email'] # 'email' aqui é o objeto User retornado pelo clean_email
                if client_to_add not in holding.clientes.all():
                    holding.clientes.add(client_to_add)
                    messages.success(request, f"Cliente {client_to_add.email} adicionado à holding '{holding.nome_holding}'.")
                else:
                    messages.warning(request, f"Cliente {client_to_add.email} já está associado a esta holding.")
                return redirect('management_holding_manage_clients', holding_id=holding.id) # Redireciona para limpar o POST
            # else: # Erros do formulário serão mostrados no template
            #    messages.error(request, "Erro ao adicionar cliente. Verifique o e-mail e as mensagens abaixo.")
        elif 'remove_client' in request.POST:
            client_id_to_remove = request.POST.get('client_id')
            if client_id_to_remove:
                try:
                    client_to_remove = User.objects.get(pk=client_id_to_remove, user_type='cliente')
                    if holding.processo_criacao and holding.processo_criacao.cliente_principal == client_to_remove:
                        messages.error(request, "Não é possível remover o cliente principal do processo da holding.")
                    elif client_to_remove in holding.clientes.all():
                        holding.clientes.remove(client_to_remove)
                        messages.success(request, f"Cliente {client_to_remove.email} removido da holding '{holding.nome_holding}'.")
                    else:
                        messages.warning(request, "Cliente não encontrado nesta holding.")
                except User.DoesNotExist:
                    messages.error(request, "Cliente a ser removido não encontrado.")
                return redirect('management_holding_manage_clients', holding_id=holding.id) # Redireciona para limpar o POST
    current_clients = holding.clientes.all()
    context = {
        'holding': holding, 'current_clients': current_clients,
        'add_client_form': add_client_form, # Passa o formulário (possivelmente com erros) para o template
        'page_title': f"Gerenciar Clientes da Holding: {holding.nome_holding}"
    }
    return render(request, 'management/management_holding_manage_clients.html', context)