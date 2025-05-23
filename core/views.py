# core/views.py
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.urls import reverse
from django.db.models import Q, Max, Count
from django.db import IntegrityError
from django.conf import settings
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_POST
# Removido: from django.conf import settings (já importado acima)
import json
import openai
from .decorators import superuser_required, consultant_or_superuser_required
from django.utils import timezone
from .forms import (
    HoldingCreationUserForm, SimulationForm,
    ConsultantCreationForm, 
    AssignConsultantAndHoldingDetailsForm,
    CustomSignupForm,
    ProcessStatusUpdateForm, HoldingOfficializeForm,
    AddClientToHoldingForm,
    DocumentUploadForm, 
    ManagementDocumentUploadForm,
    ChatMessageForm,
    PastaDocumentoForm,
)
from allauth.account.forms import LoginForm

from .models import (
    User, Holding, ProcessoHolding, AnaliseEconomia, Documento,
    ClienteProfile, SimulationResult, ChatMessage, PastaDocumento  # Certifique-se que SimulationResult está aqui
)
from decimal import Decimal
import traceback # Para depuração de exceções

# --- Suas Constantes ---
INVENTORY_COST_RATE_DEFAULT = Decimal('0.08')
RENTAL_TAX_PF = Decimal('0.275')
RENTAL_TAX_PJ = Decimal('0.1133')
PROFIT_TAX_PF = Decimal('0.275')
CAPITAL_GAIN_TAX_PF = Decimal('0.15')
CAPITAL_GAIN_TAX_PJ = Decimal('0.06')
ITCMD_RATES = {
    'SP': Decimal('0.04'), 'RJ': Decimal('0.045'), 'MG': Decimal('0.05'),
    'BA': Decimal('0.035'), 'RS': Decimal('0.04'), '': Decimal('0.04'),
}

def _get_simulation_presentation_context(simulation_obj_or_cleaned_data, user_for_greeting=None):
    """
    Calcula e retorna o contexto de apresentação detalhado para os resultados da simulação.
    Pode receber um objeto SimulationResult ou um cleaned_data de SimulationForm.
    """
    if not simulation_obj_or_cleaned_data:
        return {}

    is_model_instance = isinstance(simulation_obj_or_cleaned_data, SimulationResult)

    # Extrair dados base
    if is_model_instance:
        sim = simulation_obj_or_cleaned_data
        number_of_properties = sim.number_of_properties
        total_property_value = sim.total_property_value
        property_state = sim.property_state
        number_of_heirs = sim.number_of_heirs
        
        has_companies = sim.has_companies
        number_of_companies = sim.number_of_companies
        monthly_profit_val = sim.monthly_profit
        company_tax_regime = sim.company_tax_regime
        
        receives_rent = sim.receives_rent
        monthly_rent_val = sim.monthly_rent

        has_investments = sim.has_investments
        total_investment_value_from_source = sim.total_investment_value

        # Valores já calculados e salvos no modelo
        inventory_cost_without = sim.inventory_cost_without
        inventory_savings = sim.inventory_savings
        inventory_time_without = sim.inventory_time_without
        conflict_risk = sim.conflict_risk # Deve ser uma string como "Baixo", "Médio", "Alto" ou "Não Aplicável"
        annual_profit = sim.annual_profit
        profit_savings = sim.profit_savings
        annual_rent = sim.annual_rent
        rental_savings = sim.rental_savings
        investment_savings = sim.investment_savings
        total_savings = sim.total_savings
    else:
        # Se for cleaned_data, a lógica de recálculo seria mais extensa aqui.
        # Para o dashboard, focamos em usar o objeto SimulationResult salvo.
        # Esta branch 'else' pode ser simplificada ou removida se a função for usada SÓ com SimulationResult.
        # Por ora, vamos assumir que o dashboard sempre usará um SimulationResult.
        # Se precisar processar cleaned_data diretamente, a lógica da view 'simulation' seria copiada aqui.
        # Para o dashboard, isso não é necessário.
        # Apenas para exemplo, se precisasse do avoid_conflicts do form:
        # avoid_conflicts_form = simulation_obj_or_cleaned_data.get('avoid_conflicts', 'no')
        pass


    # --- Cálculo de Textos e Valores Adicionais para Apresentação ---
    itcmd_rate = ITCMD_RATES.get(property_state, INVENTORY_COST_RATE_DEFAULT)

    property_succession_text = "Sem imóveis informados ou com valor zero, não há custos de inventário ou benefícios sucessórios a calcular."
    if number_of_properties > 0 and total_property_value > 0:
        # Tenta obter o nome do estado a partir dos choices do SimulationForm
        _temp_form = SimulationForm() # Instância temporária para acessar choices
        state_display_choices = dict(_temp_form.fields['property_state'].choices)
        state_display = state_display_choices.get(property_state, property_state or "estado não informado")

        if number_of_heirs > 0:
            conflict_risk_display = str(conflict_risk or "Não Aplicável").lower() # Garante que é string
            property_succession_text = (
                f"Você possui {number_of_properties} imóvel(is) em {state_display} com valor total de R$ {total_property_value:,.2f}. "
                f"Sem uma holding, o custo de inventário (ITCMD de {itcmd_rate*100:.1f}%, taxas, honorários) seria aproximadamente R$ {inventory_cost_without:,.2f}, "
                f"e o processo poderia levar até {inventory_time_without} meses com risco de conflito familiar {conflict_risk_display}. "
                f"Com uma holding, você economiza cerca de R$ {inventory_savings:,.2f} e planeja a sucessão em vida, reduzindo custos e disputas."
            )
            # avoid_conflicts não está no modelo SimulationResult, então não podemos adicionar essa parte do texto facilmente
            # se estivermos usando apenas o objeto do modelo.
        else:
            property_succession_text = (
                f"Você possui {number_of_properties} imóvel(is) em {state_display} com valor total de R$ {total_property_value:,.2f}. "
                f"Sem uma holding, o custo de inventário (ITCMD de {itcmd_rate*100:.1f}%, taxas, honorários) seria aproximadamente R$ {inventory_cost_without:,.2f}. "
                f"Com uma holding, você economiza cerca de R$ {inventory_savings:,.2f} na sucessão, planejando a transferência de bens de forma ágil."
            )
    elif number_of_heirs > 0 :
         property_succession_text = (
            f"Com {number_of_heirs} herdeiro(s), mesmo sem imóveis informados, uma holding organiza a sucessão, "
            f"evitando burocracias e conflitos familiares no futuro."
        )
    
    _temp_form_company = SimulationForm()
    company_tax_regime_choices_dict = dict(_temp_form_company.fields['company_tax_regime'].choices)
    regime_display = company_tax_regime_choices_dict.get(company_tax_regime, str(company_tax_regime or '').capitalize())

    profit_text = "Sem empresas informadas ou lucros mensais relevantes, não há economia sobre lucros a simular."
    if has_companies and number_of_companies > 0 and monthly_profit_val > 0:
        if company_tax_regime in ['presumido', 'real']:
            profit_text = (
                f"Com {number_of_companies} empresa(s) no regime {regime_display} "
                f"e um lucro mensal distribuído de R$ {monthly_profit_val:,.2f} (totalizando R$ {annual_profit:,.2f}/ano), "
                f"o IRPF como Pessoa Física seria aproximadamente R$ {profit_savings:,.2f} anuais. "
                f"Através da holding, a distribuição de lucros é isenta de IRPF, economizando R$ {profit_savings:,.2f} por ano."
            )
        elif company_tax_regime == 'simples':
            profit_text = (
                f"Para {number_of_companies} empresa(s) no Simples Nacional ({regime_display}), a distribuição de lucros já é isenta de IRPF. "
                f"Uma holding ainda pode oferecer vantagens na organização societária, proteção patrimonial e planejamento sucessório."
            )
    
    rental_text = "Sem aluguéis informados, não há economia sobre aluguéis a simular."
    if receives_rent and monthly_rent_val > 0:
        tax_without_holding_rent = annual_rent * RENTAL_TAX_PF
        tax_with_holding_rent = annual_rent * RENTAL_TAX_PJ
        if rental_savings > 0:
            rental_text = (
                f"Com uma renda mensal de aluguéis de R$ {monthly_rent_val:,.2f} (totalizando R$ {annual_rent:,.2f}/ano), "
                f"o imposto de renda como Pessoa Física seria aproximadamente R$ {tax_without_holding_rent:,.2f} (alíquota de até 27,5%). "
                f"Através de uma holding (Lucro Presumido), o imposto seria cerca de R$ {tax_with_holding_rent:,.2f} (alíquota efetiva ~11,33%), "
                f"economizando R$ {rental_savings:,.2f} por ano."
            )
        else:
            rental_text = (
                f"Com uma renda mensal de aluguéis de R$ {monthly_rent_val:,.2f}, os impostos na Pessoa Jurídica (Holding) e Pessoa Física são similares ou até maiores na PJ neste cenário específico. "
                f"Uma análise detalhada é recomendada, pois outros fatores podem influenciar."
            )

    investment_text = "Sem investimentos informados, não há economia sobre ganhos de capital a simular."
    if has_investments and total_investment_value_from_source > 0:
        estimated_annual_gain_for_text = total_investment_value_from_source * Decimal('0.10') 
        tax_without_holding_investment_for_text = estimated_annual_gain_for_text * CAPITAL_GAIN_TAX_PF
        tax_with_holding_investment_for_text = estimated_annual_gain_for_text * CAPITAL_GAIN_TAX_PJ
        if investment_savings > 0:
            investment_text = (
                f"Com investimentos de R$ {total_investment_value_from_source:,.2f}, estimamos um ganho anual de R$ {estimated_annual_gain_for_text:,.2f} (10% a.a.). "
                f"O imposto sobre ganhos de capital como Pessoa Física seria aproximadamente R$ {tax_without_holding_investment_for_text:,.2f} (alíquota de 15%). "
                f"Através de uma holding, o imposto seria cerca de R$ {tax_with_holding_investment_for_text:,.2f} (alíquota efetiva ~6%), "
                f"economizando R$ {investment_savings:,.2f} por ano."
            )
        else:
            investment_text = (
                f"Com investimentos de R$ {total_investment_value_from_source:,.2f}, os impostos sobre ganho de capital na Pessoa Jurídica (Holding) e Pessoa Física são similares ou até maiores na PJ neste cenário. "
                f"Consulte um especialista para uma análise detalhada, considerando o tipo de investimento e a estrutura da holding."
            )
        
    context = {
        'user_for_greeting': user_for_greeting,
        'simulation_instance': simulation_obj_or_cleaned_data if is_model_instance else None,
        'number_of_properties': number_of_properties,
        'total_property_value': float(total_property_value or 0), # Garantir float
        'property_state': property_state,
        'inventory_savings': float(inventory_savings or 0),
        'property_succession_text': property_succession_text,
        'inventory_cost_without': float(inventory_cost_without or 0),
        'inventory_cost_with': 0.0,
        'has_companies': 'yes' if has_companies else 'no',
        'number_of_companies': number_of_companies,
        'company_tax_regime_display': regime_display,
        'company_tax_regime': company_tax_regime,
        'monthly_profit': float(monthly_profit_val or 0),
        'annual_profit': float(annual_profit or 0),
        'profit_savings': float(profit_savings or 0),
        'profit_text': profit_text,
        'receives_rent': 'yes' if receives_rent else 'no',
        'monthly_rent': float(monthly_rent_val or 0),
        'annual_rent': float(annual_rent or 0),
        'rental_savings': float(rental_savings or 0),
        'rental_text': rental_text,
        'has_investments': 'yes' if has_investments else 'no',
        'total_investment_value': float(total_investment_value_from_source or 0),
        'investment_savings': float(investment_savings or 0),
        'investment_text': investment_text,
        'number_of_heirs': number_of_heirs,
        'inventory_time_without': inventory_time_without,
        'inventory_time_with': 0,
        'conflict_risk': conflict_risk,
        'total_savings': float(total_savings or 0),
        'RENTAL_TAX_PF_RATE': float(RENTAL_TAX_PF * 100), # JS espera taxa percentual
        'RENTAL_TAX_PJ_RATE': float(RENTAL_TAX_PJ * 100),
        'PROFIT_TAX_PF_RATE': float(PROFIT_TAX_PF * 100),
        'CAPITAL_GAIN_TAX_PF_RATE': float(CAPITAL_GAIN_TAX_PF * 100),
        'CAPITAL_GAIN_TAX_PJ_RATE': float(CAPITAL_GAIN_TAX_PJ * 100),
        'INVENTORY_COST_RATE': float(itcmd_rate * 100),
    }
    return context

# --- Views Públicas e de Autenticação ---
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
            return redirect('dashboard')
        else:
            non_field_errors = form.non_field_errors()
            if non_field_errors:
                for error in non_field_errors:
                    messages.error(request, error)
            else:
                messages.error(request, "O endereço de e-mail e/ou senha especificados não estão corretos.")
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.user.is_authenticated:
        # if request.user.is_superuser: # Removido, pois superuser não deveria se cadastrar assim
        #     return redirect('management_dashboard')
        # Ajuste: se já autenticado, vá para o dashboard principal que decide o fluxo
        return redirect('dashboard') 

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
    user = request.user
    print(f"[DEBUG] DASHBOARD: Usuário '{user.email}' acessou o dashboard.")

    if user.user_type == 'admin' or user.user_type == 'consultor':
        return redirect('management_dashboard')

    if user.user_type == 'cliente':
        fez_simulacao = SimulationResult.objects.filter(user=user).exists()
        
        # ALTERADO: Verifica se o usuário é membro (cliente) de ALGUMA holding.
        is_member_of_any_holding = Holding.objects.filter(clientes=user).exists()
        
        print(f"[DEBUG] DASHBOARD: Usuário '{user.email}' - fez_simulacao: {fez_simulacao}, is_member_of_any_holding: {is_member_of_any_holding}")

        if is_member_of_any_holding: # Se é membro de alguma holding, vai para o dashboard detalhado.
            print(f"[DEBUG] DASHBOARD: Redirecionando '{user.email}' para 'dashboard_final'.")
            return redirect('dashboard_final')
        elif fez_simulacao: # Se não é membro de holding mas já fez simulação, pode criar uma.
            print(f"[DEBUG] DASHBOARD: Redirecionando '{user.email}' para 'create_holding'.")
            return redirect('create_holding')
        else: # Senão, começa pela simulação.
            print(f"[DEBUG] DASHBOARD: Redirecionando '{user.email}' para 'simulation' (input).")
            return redirect('simulation')
    
    # Fallback para outros tipos de usuário ou situações inesperadas
    return redirect('index')

@login_required
def simulation(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    print(f"[DEBUG] SIMULATION VIEW: Usuário '{request.user.email}', Método: {request.method}")

    if request.method == 'POST':
        form = SimulationForm(request.POST)
        print(f"[DEBUG] SIMULATION POST: Formulário submetido. É válido? {form.is_valid()}")
        if form.is_valid():
            cleaned_data = form.cleaned_data

            number_of_properties = cleaned_data.get('number_of_properties', 0)
            total_property_value = cleaned_data.get('total_property_value') or Decimal('0')
            property_state = cleaned_data.get('property_state', '')
            number_of_heirs = cleaned_data.get('number_of_heirs', 0)
            avoid_conflicts = cleaned_data.get('avoid_conflicts', 'no')

            has_companies = cleaned_data.get('has_companies') == 'yes'
            number_of_companies = cleaned_data.get('number_of_companies', 0) if has_companies else 0
            monthly_profit_val = cleaned_data.get('monthly_profit', Decimal('0')) if has_companies else Decimal('0')
            company_tax_regime = cleaned_data.get('company_tax_regime') if has_companies else None
            
            receives_rent = cleaned_data.get('receives_rent') == 'yes'
            monthly_rent_val = cleaned_data.get('monthly_rent', Decimal('0')) if receives_rent else Decimal('0')

            has_investments = cleaned_data.get('has_investments') == 'yes'
            # Nome da variável corrigido para corresponder ao que é usado no defaults e context
            total_investment_value_from_form = cleaned_data.get('total_investment_value', Decimal('0')) if has_investments else Decimal('0')


            inventory_cost_without = Decimal('0')
            inventory_savings = Decimal('0')
            inventory_time_without = 0
            inventory_time_with = 0
            conflict_risk = "Não Aplicável"
            property_succession_text = "Sem imóveis informados ou com valor zero, não há custos de inventário ou benefícios sucessórios a calcular."
            itcmd_rate = INVENTORY_COST_RATE_DEFAULT

            if number_of_properties > 0 and total_property_value > 0:
                itcmd_rate = ITCMD_RATES.get(property_state, INVENTORY_COST_RATE_DEFAULT)
                inventory_cost_without = total_property_value * itcmd_rate
                inventory_savings = inventory_cost_without
                state_display = property_state or "seu estado"
                if number_of_heirs > 0:
                    inventory_time_without = 12 if number_of_heirs == 1 else (24 if number_of_heirs <= 3 else 36)
                    conflict_risk_display = "Baixo" if number_of_heirs == 1 else ("Médio" if number_of_heirs <= 3 else "Alto")
                    conflict_risk = conflict_risk_display
                    property_succession_text = (
                        f"Você possui {number_of_properties} imóvel(is) em {state_display} com valor total de R$ {total_property_value:,.2f}. "
                        f"Sem uma holding, o custo de inventário (ITCMD de {itcmd_rate*100:.1f}%, taxas, honorários) seria aproximadamente R$ {inventory_cost_without:,.2f}, "
                        f"e o processo poderia levar até {inventory_time_without} meses com risco de conflito familiar {conflict_risk_display.lower()}. "
                        f"Com uma holding, você economiza cerca de R$ {inventory_savings:,.2f} e planeja a sucessão em vida, reduzindo custos e disputas."
                    )
                else:
                    property_succession_text = (
                        f"Você possui {number_of_properties} imóvel(is) em {state_display} com valor total de R$ {total_property_value:,.2f}. "
                        f"Sem uma holding, o custo de inventário (ITCMD de {itcmd_rate*100:.1f}%, taxas, honorários) seria aproximadamente R$ {inventory_cost_without:,.2f}. "
                        f"Com uma holding, você economiza cerca de R$ {inventory_savings:,.2f} na sucessão, planejando a transferência de bens de forma ágil."
                    )
                if avoid_conflicts == 'yes':
                    property_succession_text += " A holding também atende seu objetivo de evitar conflitos familiares, definindo regras claras para a sucessão."
            elif number_of_heirs > 0:
                property_succession_text = (
                    f"Com {number_of_heirs} herdeiro(s), mesmo sem imóveis informados, uma holding organiza a sucessão, "
                    f"evitando burocracias e conflitos familiares no futuro."
                )

            annual_profit = Decimal('0')
            profit_savings = Decimal('0')
            profit_text = "Sem empresas informadas ou lucros mensais relevantes, não há economia sobre lucros a simular."
            company_tax_regime_choices_dict = dict(form.fields['company_tax_regime'].choices)
            regime_display = ""

            if has_companies and number_of_companies > 0 and monthly_profit_val > 0:
                annual_profit = monthly_profit_val * Decimal('12')
                regime_display = company_tax_regime_choices_dict.get(company_tax_regime, str(company_tax_regime or '').capitalize())
                if company_tax_regime in ['presumido', 'real']:
                    profit_tax_pf_value = annual_profit * PROFIT_TAX_PF
                    profit_savings = profit_tax_pf_value
                    profit_text = (
                        f"Com {number_of_companies} empresa(s) no regime {regime_display} "
                        f"e um lucro mensal distribuído de R$ {monthly_profit_val:,.2f} (totalizando R$ {annual_profit:,.2f}/ano), "
                        f"o IRPF como Pessoa Física seria aproximadamente R$ {profit_savings:,.2f} anuais. "
                        f"Através da holding, a distribuição de lucros é isenta de IRPF, economizando R$ {profit_savings:,.2f} por ano."
                    )
                elif company_tax_regime == 'simples':
                    profit_text = (
                        f"Para {number_of_companies} empresa(s) no Simples Nacional ({regime_display}), a distribuição de lucros já é isenta de IRPF. "
                        f"Uma holding ainda pode oferecer vantagens na organização societária, proteção patrimonial e planejamento sucessório."
                    )
            
            annual_rent = Decimal('0')
            rental_savings = Decimal('0')
            rental_text = "Sem aluguéis informados, não há economia sobre aluguéis a simular."

            if receives_rent and monthly_rent_val > 0:
                annual_rent = monthly_rent_val * Decimal('12')
                tax_without_holding_rent = annual_rent * RENTAL_TAX_PF
                tax_with_holding_rent = annual_rent * RENTAL_TAX_PJ
                rental_savings = tax_without_holding_rent - tax_with_holding_rent
                if rental_savings > 0:
                    rental_text = (
                        f"Com uma renda mensal de aluguéis de R$ {monthly_rent_val:,.2f} (totalizando R$ {annual_rent:,.2f}/ano), "
                        f"o imposto de renda como Pessoa Física seria aproximadamente R$ {tax_without_holding_rent:,.2f} (alíquota de até 27,5%). "
                        f"Através de uma holding (Lucro Presumido), o imposto seria cerca de R$ {tax_with_holding_rent:,.2f} (alíquota efetiva ~11,33%), "
                        f"economizando R$ {rental_savings:,.2f} por ano."
                    )
                else:
                    rental_text = (
                        f"Com uma renda mensal de aluguéis de R$ {monthly_rent_val:,.2f}, os impostos na Pessoa Jurídica (Holding) e Pessoa Física são similares ou até maiores na PJ neste cenário específico. "
                        f"Uma análise detalhada é recomendada, pois outros fatores podem influenciar."
                    )

            investment_savings = Decimal('0')
            investment_text = "Sem investimentos informados, não há economia sobre ganhos de capital a simular."
            estimated_annual_gain = Decimal('0')

            if has_investments and total_investment_value_from_form > 0:
                estimated_annual_gain = total_investment_value_from_form * Decimal('0.10')
                tax_without_holding_investment = estimated_annual_gain * CAPITAL_GAIN_TAX_PF
                tax_with_holding_investment = estimated_annual_gain * CAPITAL_GAIN_TAX_PJ
                investment_savings = tax_without_holding_investment - tax_with_holding_investment
                if investment_savings > 0:
                    investment_text = (
                        f"Com investimentos de R$ {total_investment_value_from_form:,.2f}, estimamos um ganho anual de R$ {estimated_annual_gain:,.2f} (10% a.a.). "
                        f"O imposto sobre ganhos de capital como Pessoa Física seria aproximadamente R$ {tax_without_holding_investment:,.2f} (alíquota de 15%). "
                        f"Através de uma holding, o imposto seria cerca de R$ {tax_with_holding_investment:,.2f} (alíquota efetiva ~6%), "
                        f"economizando R$ {investment_savings:,.2f} por ano."
                    )
                else:
                    investment_text = (
                        f"Com investimentos de R$ {total_investment_value_from_form:,.2f}, os impostos sobre ganho de capital na Pessoa Jurídica (Holding) e Pessoa Física são similares ou até maiores na PJ neste cenário. "
                        f"Consulte um especialista para uma análise detalhada, considerando o tipo de investimento e a estrutura da holding."
                    )

            total_savings = inventory_savings + profit_savings + rental_savings + investment_savings

            try:
                sim_result, created = SimulationResult.objects.update_or_create(
                    user=request.user,
                    defaults={
                        'number_of_properties': number_of_properties,
                        'total_property_value': total_property_value,
                        'property_state': property_state,
                        'inventory_cost_without': inventory_cost_without,
                        'inventory_cost_with': Decimal('0'),
                        'inventory_savings': inventory_savings,
                        'has_companies': has_companies,
                        'number_of_companies': number_of_companies,
                        'company_tax_regime': company_tax_regime or '',
                        'monthly_profit': monthly_profit_val,
                        'annual_profit': annual_profit,
                        'profit_savings': profit_savings,
                        'receives_rent': receives_rent,
                        'monthly_rent': monthly_rent_val,
                        'annual_rent': annual_rent,
                        'rental_savings': rental_savings,
                        'has_investments': has_investments,
                        'total_investment_value': total_investment_value_from_form, # Usar a variável do form
                        'investment_savings': investment_savings,
                        'number_of_heirs': number_of_heirs,
                        'inventory_time_without': inventory_time_without,
                        'inventory_time_with': inventory_time_with,
                        'conflict_risk': conflict_risk,
                        'total_savings': total_savings,
                    }
                )
                print(f"[DEBUG] SIMULATION POST: SimulationResult para '{request.user.email}' salvo/atualizado. ID: {sim_result.id}, Criado: {created}, PK Existe? {sim_result.pk is not None}")
                print(f"[DEBUG] SIMULATION POST: Valores salvos - Total Savings: {sim_result.total_savings}, User: {sim_result.user.email}")
                messages.success(request, "Simulação calculada e salva com sucesso!")
            except Exception as e:
                messages.error(request, f"Ocorreu um erro ao salvar os resultados da simulação: {e}")
                print(f"[DEBUG] ERRO AO SALVAR SimulationResult para '{request.user.email}': {type(e).__name__} - {str(e)}")
                print(traceback.format_exc())


            context = {
                'page_title': "Resultado da Sua Simulação",
                'user': request.user,
                'number_of_properties': number_of_properties,
                'total_property_value': float(total_property_value),
                'property_state': property_state,
                'inventory_savings': float(inventory_savings),
                'property_succession_text': property_succession_text,
                'inventory_cost_without': float(inventory_cost_without),
                'inventory_cost_with': 0.0,
                'has_companies': 'yes' if has_companies else 'no',
                'number_of_companies': number_of_companies,
                'company_tax_regime_display': regime_display,
                'company_tax_regime': company_tax_regime,
                'monthly_profit': float(monthly_profit_val),
                'annual_profit': float(annual_profit),
                'profit_savings': float(profit_savings),
                'profit_text': profit_text,
                'receives_rent': 'yes' if receives_rent else 'no',
                'monthly_rent': float(monthly_rent_val),
                'annual_rent': float(annual_rent),
                'rental_savings': float(rental_savings),
                'rental_text': rental_text,
                'has_investments': 'yes' if has_investments else 'no',
                'total_investment_value': float(total_investment_value_from_form), # Usar a variável do form
                'investment_savings': float(investment_savings),
                'investment_text': investment_text,
                'number_of_heirs': number_of_heirs,
                'avoid_conflicts': avoid_conflicts == 'yes',
                'inventory_time_without': inventory_time_without,
                'inventory_time_with': inventory_time_with,
                'conflict_risk': conflict_risk,
                'total_savings': float(total_savings),
                'RENTAL_TAX_PF': float(RENTAL_TAX_PF * 100),
                'RENTAL_TAX_PJ': float(RENTAL_TAX_PJ * 100),
                'PROFIT_TAX_PF': float(PROFIT_TAX_PF * 100),
                'CAPITAL_GAIN_TAX_PF': float(CAPITAL_GAIN_TAX_PF * 100),
                'CAPITAL_GAIN_TAX_PJ': float(CAPITAL_GAIN_TAX_PJ * 100),
                'INVENTORY_COST_RATE': float(itcmd_rate * 100),
            }
            print(f"[DEBUG] SIMULATION POST: Renderizando simulation.html para '{request.user.email}' com contexto.")
            return render(request, 'core/simulation.html', context)
        else: 
            print(f"[DEBUG] SIMULATION POST: Formulário inválido. Erros: {form.errors.as_json()}")
            messages.error(request, "Por favor, corrija os erros no formulário de simulação.")
            return render(request, 'core/simulation_input.html', {'form': form, 'page_title': "Simulação de Benefícios", 'user': request.user})
    else: 
        form = SimulationForm()
        print(f"[DEBUG] SIMULATION GET: Renderizando simulation_input.html para '{request.user.email}'")
        return render(request, 'core/simulation_input.html', {'form': form, 'page_title': "Faça sua Simulação", 'user': request.user})
    

@login_required
def create_holding(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    print(f"[DEBUG] CREATE_HOLDING GET: Usuário '{request.user.email}' acessando.")
    latest_simulation_exists = SimulationResult.objects.filter(user=request.user).exists()
    print(f"[DEBUG] CREATE_HOLDING GET: SimulationResult.objects.filter(user=request.user).exists() = {latest_simulation_exists}")

    if not latest_simulation_exists:
        # Tentativa adicional de depuração se exists() for False
        try:
            sim = SimulationResult.objects.get(user=request.user)
            print(f"[DEBUG] CREATE_HOLDING GET: ACHOU simulação com .get() ID: {sim.id} para usuário {request.user.email}")
        except SimulationResult.DoesNotExist:
            print(f"[DEBUG] CREATE_HOLDING GET: SimulationResult.DoesNotExist para usuário {request.user.email} com .get()")
        except SimulationResult.MultipleObjectsReturned:
            sims = SimulationResult.objects.filter(user=request.user).order_by('-updated_at')
            print(f"[DEBUG] CREATE_HOLDING GET: Múltiplas simulações encontradas para {request.user.email}. Mais recente ID: {sims.first().id if sims.exists() else 'N/A'}")
        
        messages.info(request, "Por favor, complete a simulação de benefícios antes de criar uma holding.")
        print(f"[DEBUG] CREATE_HOLDING GET: Usuário '{request.user.email}' não tem simulação válida. Redirecionando para 'dashboard'.")
        return redirect('dashboard') 

    if request.method == 'POST':
        form = HoldingCreationUserForm(request.POST, user=request.user) # Passa o usuário para o form
        if form.is_valid():
            holding = form.save(commit=False)
            # Se você precisar definir outros campos na holding antes de salvar, faça aqui
            holding.save() 
            holding.clientes.add(request.user) # Adiciona o usuário logado como cliente da holding

            ProcessoHolding.objects.create(
                cliente_principal=request.user,
                holding_associada=holding,
                status_atual='aguardando_documentos' 
            )
            messages.success(request, f"Interesse na holding '{holding.nome_holding}' registrado com sucesso! Nossa equipe entrará em contato em breve para os próximos passos.")
            print(f"[DEBUG] CREATE_HOLDING POST: Holding criada para '{request.user.email}'. Redirecionando para 'dashboard_final'.")
            return redirect('dashboard_final') 
        else:
            print(f"[DEBUG] CREATE_HOLDING POST: Formulário HoldingCreationUserForm inválido. Erros: {form.errors.as_json()}")
            messages.error(request, "Houve um erro ao registrar o interesse. Por favor, verifique os dados informados.")
    else: # GET
        form = HoldingCreationUserForm(user=request.user) # Passa o usuário para o form

    print(f"[DEBUG] CREATE_HOLDING GET: Renderizando create_holding.html para '{request.user.email}'")
    return render(request, 'core/create_holding.html', {'form': form})

@login_required
@require_POST # Garante que esta view só aceita requisições POST
@csrf_exempt  # IMPORTANTE: Para este exemplo, desabilitamos a proteção CSRF para esta view
              # para facilitar a integração com Fetch API. Em um ambiente de produção,
              # você DEVE configurar o envio do token CSRF corretamente via JavaScript.
def chat_with_gpt(request):
    if not settings.OPENAI_API_KEY:
        return JsonResponse({'error': 'A configuração da API da OpenAI está ausente no servidor.'}, status=503) # Service Unavailable

    try:
        data = json.loads(request.body)
        user_message = data.get('message')
        # Para conversas mais contextuais, você pode querer receber e enviar um histórico:
        # conversation_history = data.get('history', []) # Lista de {'role': '...', 'content': '...'}

        if not user_message:
            return JsonResponse({'error': 'Nenhuma mensagem fornecida.'}, status=400)

        # Monta a lista de mensagens para enviar à API
        messages_to_send = [
            {
                "role": "system",
                "content": (
                    "Você é o Assistente IA da W1 Holding, um especialista virtual em holdings patrimoniais, "
                    "planejamento sucessório, e otimização tributária no Brasil. Seu objetivo é fornecer informações "
                    "claras e úteis para os clientes da W1 Holding. Seja cordial, profissional e objetivo. "
                    "Ao responder, mencione que as informações são para fins educativos e que para "
                    "aconselhamento específico sobre o caso do cliente, ele deve consultar um especialista da W1."
                )
            },
            # Se estiver gerenciando histórico, adicione-o aqui:
            # *conversation_history, 
            {"role": "user", "content": user_message}
        ]
        
        # Instancia o cliente OpenAI com sua chave de API
        client = openai.OpenAI(api_key=settings.OPENAI_API_KEY)

        # Faz a chamada para a API Chat Completions
        completion = client.chat.completions.create(
            model="gpt-4o-mini",  # Você pode escolher outros modelos como "gpt-4" se tiver acesso e orçamento
            messages=messages_to_send,
            max_tokens=2000  # Limite o tamanho da resposta para controlar custos e tempo
        )

        assistant_response = completion.choices[0].message.content.strip()
        
        # logger.info(f"User: {user_message}, GPT: {assistant_response}")
        return JsonResponse({'reply': assistant_response})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Formato de requisição inválido (esperado JSON).'}, status=400)
    except openai.APIConnectionError as e:
        # logger.error(f"OpenAI API Connection Error: {e}")
        return JsonResponse({'error': 'Não foi possível conectar à API da OpenAI. Verifique sua conexão.'}, status=503)
    except openai.RateLimitError as e:
        # logger.error(f"OpenAI API Rate Limit Error: {e}")
        return JsonResponse({'error': 'Limite de requisições para a API da OpenAI atingido. Tente mais tarde.'}, status=429)
    except openai.AuthenticationError as e:
        # logger.error(f"OpenAI API Authentication Error: {e}")
        return JsonResponse({'error': 'Erro de autenticação com a API da OpenAI. Verifique sua chave de API.'}, status=401)
    except openai.APIError as e: # Outros erros da API
        # logger.error(f"OpenAI API Error: {e}")
        return JsonResponse({'error': f'Ocorreu um erro com a API da OpenAI: {str(e)}'}, status=500)
    except Exception as e:
        # logger.error(f"Erro inesperado na view chat_with_gpt: {e}")
        return JsonResponse({'error': f'Ocorreu um erro inesperado no servidor: {str(e)}'}, status=500)

def get_folder_structure_with_documents(processo_holding, parent_folder=None):
    """
    Recursively fetches folder structure along with documents.
    Returns a list of folder dicts and a list of documents at the current level.
    Each folder dict contains: 'id', 'nome', 'instance', 'subpastas' (recursive call), 'documentos_contidos'.
    """
    if not processo_holding:
        return [], []

    folders_data = []
    # Get folders at the current level
    current_level_folders_qs = PastaDocumento.objects.filter(
        processo_holding=processo_holding,
        parent_folder=parent_folder
    ).prefetch_related(
        'documentos_contidos__enviado_por' # Documents directly in this folder
    ).annotate(
        doc_count=Count('documentos_contidos') # Count documents in this folder
    ).order_by('nome')

    for folder_instance in current_level_folders_qs:
        subfolders_list, _ = get_folder_structure_with_documents(processo_holding, folder_instance) # Recursive call for subfolders
        
        # Documents directly within this folder_instance are already prefetched by 'documentos_contidos'
        direct_documents_in_folder = list(folder_instance.documentos_contidos.all().select_related('enviado_por').order_by('nome_documento_logico', '-versao'))

        folders_data.append({
            'id': folder_instance.id,
            'nome': folder_instance.nome,
            'instance': folder_instance,
            'subpastas': subfolders_list,
            'documentos_contidos': direct_documents_in_folder, # Documents directly in this folder
            'doc_count': folder_instance.doc_count # From annotation
        })

    # Documents at the root of the current level (i.e., not in any subfolder of this level)
    # If parent_folder is None, these are documents at the very root of the processo_holding
    documents_at_this_level_qs = Documento.objects.filter(
        processo_holding=processo_holding,
        pasta=parent_folder # This will correctly fetch documents whose 'pasta' FK matches the current parent_folder
    ).select_related('enviado_por').order_by('nome_documento_logico', '-versao')

    return folders_data, list(documents_at_this_level_qs)


# Em core/views.py

@login_required
def dashboard_final(request):
    if request.user.is_superuser or request.user.user_type in ['admin', 'consultor']: # Simplificado
        return redirect('management_dashboard')

    # Verifica se o usuário é cliente de alguma holding. Se não, não deveria estar aqui.
    user_holdings_qs = Holding.objects.filter(clientes=request.user).prefetch_related(
        'consultores', 
        'processo_criacao__pastas_documentos__documentos_contidos__enviado_por', # Prefetch otimizado
        'processo_criacao__documentos_processo__enviado_por'
    ).select_related('processo_criacao') # select_related para OneToOne

    if not user_holdings_qs.exists():
        messages.info(request, "Você não está associado a nenhuma holding no momento. Considere criar uma ou aguarde ser adicionado por um administrador.")
        return redirect('dashboard') # Volta para o fluxo normal do dashboard

    latest_simulation_obj = SimulationResult.objects.filter(user=request.user).order_by('-created_at').first()
    
    active_holding = None
    target_processo = None # Para documentos
    
    # Lógica para determinar a holding ativa:
    # Prioriza a holding que tem um processo_criacao E da qual o usuário é cliente.
    # Se houver várias, pode ser necessário um seletor no futuro. Por ora, pega a primeira.
    for h_obj in user_holdings_qs:
        if h_obj.processo_criacao: # Se esta holding (da qual o user é cliente) tem um processo
            active_holding = h_obj
            target_processo = h_obj.processo_criacao
            break 
    
    if not active_holding and user_holdings_qs.exists(): # Se nenhuma com processo foi achada, pega a primeira da lista
        active_holding = user_holdings_qs.first()
        if active_holding and active_holding.processo_criacao: # Tenta pegar o processo dela
            target_processo = active_holding.processo_criacao
            
    if not active_holding: # Fallback, deveria ter sido pego pelo user_holdings_qs.exists() no início
        messages.error(request, "Não foi possível determinar a holding ativa para visualização.")
        return redirect('dashboard')

    # Inicialização de formulários
    document_form = DocumentUploadForm(processo_holding=target_processo) if target_processo else DocumentUploadForm()
    pasta_form = PastaDocumentoForm(processo_holding=target_processo) if target_processo else PastaDocumentoForm()
    chat_form_to_render = ChatMessageForm()  

    if request.method == 'POST':
        # Lógica de POST para upload_document_cliente, create_folder, send_chat_message
        # Certifique-se que 'target_processo' é usado para operações de documento/pasta
        # e 'active_holding' para operações de chat.
        if 'upload_document_cliente' in request.POST:
            if not target_processo:
                messages.error(request, "Não há um processo de holding ativo para anexar documentos.")
            else:
                document_form = DocumentUploadForm(request.POST, request.FILES, processo_holding=target_processo)
                if document_form.is_valid():
                    # ... (lógica de salvar documento como antes) ...
                    doc = document_form.save(commit=False)
                    doc.processo_holding = target_processo
                    doc.enviado_por = request.user
                    doc.nome_original_arquivo = doc.arquivo.name 
                    # Lógica de versionamento ...
                    latest_version_data = Documento.objects.filter(
                        processo_holding=target_processo,
                        nome_documento_logico=doc.nome_documento_logico,
                        categoria=doc.categoria,
                        pasta=doc.pasta
                    ).aggregate(max_versao=Max('versao'))
                    current_max_version = latest_version_data.get('max_versao')
                    doc.versao = (current_max_version + 1) if current_max_version is not None else 1
                    try:
                        doc.save()
                        messages.success(request, f"Documento '{doc.nome_documento_logico}' (v{doc.versao}) enviado!")
                    except IntegrityError:
                        messages.error(request, "Erro de integridade ao salvar o documento.")
                    return redirect(request.path_info + '#documentos')
                else:
                    messages.error(request, "Erro ao enviar documento. Verifique os campos.")
        
        elif 'create_folder' in request.POST:
            if not target_processo:
                messages.error(request, "Não há um processo de holding ativo para criar pastas.")
            else:
                pasta_form = PastaDocumentoForm(request.POST, processo_holding=target_processo)
                if pasta_form.is_valid():
                    # ... (lógica de salvar pasta como antes) ...
                    new_folder = pasta_form.save(commit=False)
                    new_folder.processo_holding = target_processo
                    new_folder.created_by = request.user
                    try:
                        new_folder.save()
                        messages.success(request, f"Pasta '{new_folder.nome}' criada.")
                    except IntegrityError:
                        messages.error(request, f"Já existe uma pasta com o nome '{new_folder.nome}'.")
                    return redirect(request.path_info + '#documentos')
                else:
                    messages.error(request, "Erro ao criar pasta.")

        elif 'send_chat_message' in request.POST:
            if not active_holding: # Chat é associado diretamente à Holding
                messages.error(request, "Nenhuma holding ativa para enviar a mensagem.")
            else:
                # ... (lógica de enviar chat como antes, usando 'active_holding') ...
                # Validação de permissão já existente parece correta
                posted_chat_form = ChatMessageForm(request.POST)
                if posted_chat_form.is_valid():
                    new_message = posted_chat_form.save(commit=False)
                    new_message.holding = active_holding
                    new_message.sender = request.user
                    new_message.save()
                    return redirect(request.path_info + '#mensagens')
                else:
                    chat_form_to_render = posted_chat_form 
                    messages.error(request, "Não foi possível enviar sua mensagem.")
    
    # Coleta de dados para o contexto
    folder_structure = []
    root_documents = []
    chat_messages_list = []  

    if active_holding: # Para o chat
        can_access_chat_display = (
            request.user.is_superuser or
            (active_holding.clientes.filter(id=request.user.id).exists()) or
            (active_holding.consultores.filter(id=request.user.id).exists())
        )
        if can_access_chat_display:
            chat_messages_list = ChatMessage.objects.filter(holding=active_holding).select_related('sender').order_by('timestamp')

    if target_processo: # Para documentos e pastas
        try:
            folder_structure, root_documents = get_folder_structure_with_documents(target_processo)
        except NameError:
            pass 

    context = {
        'user': request.user,
        'user_holdings': user_holdings_qs, # Lista de todas as holdings do usuário
        
        'active_holding_for_docs': active_holding if target_processo else None, # Holding ativa para contexto de documentos
        'target_processo_id': target_processo.id if target_processo else None,
        'document_form': document_form,  
        'pasta_form': pasta_form,      
        'folder_structure': folder_structure,
        'root_documents': root_documents,
        
        'active_holding_for_chat': active_holding, # Holding ativa para o chat
        'chat_form': chat_form_to_render,  
        'chat_messages': chat_messages_list,  
    }

    if latest_simulation_obj:
        try:
            simulation_details_context = _get_simulation_presentation_context(latest_simulation_obj, request.user)
            context.update(simulation_details_context)
        except NameError: 
            context['simulation_instance'] = None 
    else:
        context['simulation_instance'] = None

    return render(request, 'core/dashboard.html', context)

@login_required
@consultant_or_superuser_required # Ensures only authorized staff can access
def management_holding_chat(request, holding_id):
    holding_base_qs = Holding.objects.prefetch_related(
        'consultores', 
        'clientes', 
        # 'chat_messages__sender' # Fetch dynamically or with the holding instance below
    )
    
    try:
        if request.user.is_superuser:
            holding = holding_base_qs.get(pk=holding_id)
        elif request.user.user_type == 'consultor':
            # Consultant can access chat if they are one of the assigned consultants for this holding
            holding = holding_base_qs.get(pk=holding_id, consultores=request.user)
        else: # Should not be reached due to decorator
            messages.error(request, "Acesso negado.")
            return redirect('login') 
    except Holding.DoesNotExist:
        messages.error(request, "Holding não encontrada ou acesso negado.")
        return redirect('management_dashboard')

    chat_form = ChatMessageForm()
    
    if request.method == 'POST':
        # Make sure the button name in the template form matches "send_chat_message_management"
        if 'send_chat_message_management' in request.POST:
            posted_chat_form = ChatMessageForm(request.POST)
            if posted_chat_form.is_valid():
                new_message = posted_chat_form.save(commit=False)
                new_message.holding = holding
                new_message.sender = request.user # Sender is the logged-in admin/consultant
                new_message.save()
                # messages.success(request, "Mensagem enviada no chat da holding.") # Optional
                return redirect('management_holding_chat', holding_id=holding.id) # Redirect to refresh
            else:
                messages.error(request, "Erro ao enviar mensagem. O conteúdo não pode estar vazio.")
                chat_form = posted_chat_form # Pass form with errors back to template
    
    # Fetch all messages for this holding, ordered by timestamp
    chat_messages = ChatMessage.objects.filter(holding=holding).select_related('sender').order_by('timestamp')

    context = {
        'holding': holding,
        'chat_messages': chat_messages,
        'chat_form': chat_form,
        'page_title': f'Chat da Holding: {holding.nome_holding}',
        'submit_button_text': 'Enviar Mensagem', # For the form if using a generic template part
    }
    return render(request, 'management/management_holding_chat.html', context)

@login_required
def invite_partners(request):
    if request.user.is_superuser:
        return redirect('management_dashboard')

    # O usuário deve ter pelo menos uma holding para convidar parceiros para ela.
    # Se houver múltiplas, esta lógica pega a primeira. Uma UI mais robusta permitiria escolher.
    holding = Holding.objects.filter(clientes=request.user).first() 
    
    if not holding:
        messages.info(request, "Você precisa primeiro criar ou estar associado a uma holding para convidar sócios.")
        return redirect('create_holding') # Ou 'dashboard_final' se fizer mais sentido

    if request.method == 'POST':
        emails_str = request.POST.get('emails', '')
        emails = [email.strip().lower() for email in emails_str.split(',') if email.strip()]
        
        if not emails:
            messages.error(request, "Por favor, insira pelo menos um e-mail.")
        else:
            invited_count = 0
            error_count = 0
            for email_addr in emails:
                try:
                    # Tenta encontrar um usuário existente ou cria um novo (apenas se não existir)
                    # Idealmente, o parceiro já teria uma conta ou seria convidado a criar uma.
                    # Esta lógica é simplificada para adicionar um usuário existente ou criar um stub.
                    partner_user, created = User.objects.get_or_create(
                        email=email_addr, 
                        defaults={ # Apenas usado se 'created' for True
                            'user_type': 'cliente', 
                            'first_name': email_addr.split('@')[0], # Nome padrão
                            'last_name': '(Convidado)'
                        }
                    )
                    if created:
                        partner_user.set_unusable_password() # Garante que não pode logar sem resetar senha
                        partner_user.is_active = True # Ou False, dependendo do fluxo de convite
                        partner_user.save()
                        messages.info(request, f"Conta stub criada para {email_addr}. Ele(a) precisará definir uma senha.")

                    if partner_user.user_type != 'cliente':
                        messages.error(request, f"O usuário {email_addr} não é um cliente e não pode ser adicionado como sócio.")
                        error_count +=1
                        continue

                    if partner_user not in holding.clientes.all():
                        holding.clientes.add(partner_user)
                        # Aqui você poderia enviar um e-mail de notificação para 'partner_user'
                        messages.success(request, f"Sócio {email_addr} adicionado à holding '{holding.nome_holding}'.")
                        invited_count += 1
                    else:
                        messages.warning(request, f"{email_addr} já é um sócio desta holding.")
                
                except Exception as e: # Captura outras exceções (ex: erro de banco)
                    messages.error(request, f"Erro ao processar o convite para {email_addr}: {e}")
                    error_count += 1
            
            if invited_count > 0 and error_count == 0:
                return redirect('dashboard_final') # Ou para a seção de sócios do dashboard
            # Se houve erros ou nenhum convite bem-sucedido, permanece na página para mostrar mensagens
            
    return render(request, 'core/invite_partners.html', {'holding': holding})


# --- Management Views ---
@login_required
@consultant_or_superuser_required # Decorador genérico para área de gestão
def management_dashboard(request):
    search_query = request.GET.get('q', '')
    searched_users_qs = User.objects.none()
    searched_holdings_qs = Holding.objects.none()

    # Lógica de contagem e processos recentes baseada no tipo de usuário
    if request.user.is_superuser:
        total_users = User.objects.exclude(is_superuser=True).count()
        total_clients = User.objects.filter(user_type='cliente').count()
        total_consultants = User.objects.filter(user_type='consultor').count()
        total_holdings = Holding.objects.count()
        recent_processes_qs = ProcessoHolding.objects.select_related(
            'cliente_principal', 'holding_associada'
        ).prefetch_related('holding_associada__consultores').order_by('-data_inicio_processo')[:5] # Prefetch consultores
    
    elif request.user.user_type == 'consultor':
        # Holdings onde o consultor logado é um dos consultores responsáveis
        consultant_holdings = Holding.objects.filter(consultores=request.user)
        user_holdings_ids = consultant_holdings.values_list('id', flat=True)
        
        # Clientes distintos associados a essas holdings
        total_clients = User.objects.filter(holdings_participadas__id__in=user_holdings_ids, user_type='cliente').distinct().count()
        total_consultants = 0 # Consultor não vê contagem de outros consultores aqui
        total_holdings = consultant_holdings.count()
        total_users = total_clients # Para o dashboard do consultor, usuários são seus clientes
        recent_processes_qs = ProcessoHolding.objects.filter(holding_associada__id__in=user_holdings_ids).select_related(
            'cliente_principal', 'holding_associada'
        ).prefetch_related('holding_associada__consultores').order_by('-data_inicio_processo')[:5]
    else:
        # Caso inesperado, redireciona para login ou uma página de erro apropriada
        return redirect('login') 

    recent_processes = recent_processes_qs # Já com prefetch

    if search_query:
        base_user_query = Q(email__icontains=search_query) | Q(first_name__icontains=search_query) | Q(last_name__icontains=search_query)
        base_holding_query = Q(nome_holding__icontains=search_query) | \
                             Q(consultores__first_name__icontains=search_query) | \
                             Q(consultores__last_name__icontains=search_query) | \
                             Q(consultores__email__icontains=search_query)


        if request.user.is_superuser:
            searched_users_qs = User.objects.filter(base_user_query).exclude(is_superuser=True)
            searched_holdings_qs = Holding.objects.filter(base_holding_query).prefetch_related('consultores', 'clientes')
        elif request.user.user_type == 'consultor':
            # Consultor busca clientes das suas holdings ou as próprias holdings
            client_ids_from_consultant_holdings = User.objects.filter(
                holdings_participadas__in=Holding.objects.filter(consultores=request.user)
            ).values_list('id', flat=True).distinct()

            searched_users_qs = User.objects.filter(base_user_query, id__in=client_ids_from_consultant_holdings, user_type='cliente')
            searched_holdings_qs = Holding.objects.filter(base_holding_query, consultores=request.user).prefetch_related('consultores', 'clientes')

    context = {
        'total_users': total_users, 
        'total_clients': total_clients, 
        'total_consultants': total_consultants, 
        'total_holdings': total_holdings,
        'recent_processes': recent_processes, 
        'search_query': search_query,
        'searched_users': searched_users_qs.distinct().order_by('first_name', 'last_name') if searched_users_qs.exists() else User.objects.none(),
        'searched_holdings': searched_holdings_qs.distinct().order_by('nome_holding') if searched_holdings_qs.exists() else Holding.objects.none(),
        'page_title': 'Painel de Gestão Principal'
    }
    return render(request, 'management/management_dashboard.html', context)


@login_required
@superuser_required # Apenas superusuários podem listar todos os usuários
def management_list_users(request):
    user_type_filter = request.GET.get('user_type', '')
    search_query = request.GET.get('search', '') # Para pesquisa de nome/email
    
    users_list = User.objects.all().order_by('first_name', 'last_name', 'email')

    if user_type_filter:
        if user_type_filter == 'admin': # 'admin' pode significar is_superuser
            users_list = users_list.filter(is_superuser=True)
        else:
            users_list = users_list.filter(user_type=user_type_filter, is_superuser=False)
    elif request.user.is_superuser: # Se nenhum filtro, superuser não se vê na lista principal
         users_list = users_list.exclude(pk=request.user.pk)


    if search_query:
        users_list = users_list.filter(
            Q(email__icontains=search_query) |
            Q(first_name__icontains=search_query) |
            Q(last_name__icontains=search_query)
        )
        
    context = {
        'users_list': users_list,
        'user_types': User.USER_TYPE_CHOICES, # Para o dropdown de filtro
        'selected_user_type': user_type_filter,
        'search_query': search_query,
        'page_title': 'Gerenciamento de Usuários'
    }
    return render(request, 'management/management_list_users.html', context)


@login_required
@consultant_or_superuser_required
def management_user_detail(request, user_id):
    user_to_view = get_object_or_404(User, pk=user_id)
    can_view = False

    if request.user.is_superuser:
        can_view = True
    elif request.user.user_type == 'consultor':
        if user_to_view.id == request.user.id: # Consultor pode ver seu próprio perfil
            can_view = True
        elif user_to_view.user_type == 'cliente':
            # Consultor pode ver cliente se estiver associado a uma das holdings do cliente
            if Holding.objects.filter(consultores=request.user, clientes=user_to_view).exists():
                can_view = True
    
    if not can_view:
        messages.error(request, "Você não tem permissão para ver detalhes deste usuário.")
        return redirect('management_dashboard') 
    
    client_profile = None
    client_holdings = []
    client_processes = []
    client_documents = []
    consultant_assigned_holdings = []

    if user_to_view.user_type == 'cliente':
        try:
            client_profile = user_to_view.cliente_profile
        except ClienteProfile.DoesNotExist:
            pass # Perfil pode não existir ainda
        client_holdings = user_to_view.holdings_participadas.all().prefetch_related('consultores', 'clientes')
        client_processes = ProcessoHolding.objects.filter(cliente_principal=user_to_view).select_related('holding_associada').prefetch_related('holding_associada__consultores')
        
        process_ids = [p.id for p in client_processes if p and p.id is not None] # Evitar None se holding_associada for None
        client_documents = Documento.objects.filter(processo_holding_id__in=process_ids).select_related('enviado_por', 'processo_holding__holding_associada')

    elif user_to_view.user_type == 'consultor':
        consultant_assigned_holdings = user_to_view.holdings_assessoradas.all().prefetch_related('clientes', 'processo_criacao__documentos')
        
    context = {
        'user_obj': user_to_view,
        'client_profile': client_profile,
        'client_holdings': client_holdings,
        'client_processes': client_processes,
        'client_documents': client_documents,
        'consultant_assigned_holdings': consultant_assigned_holdings,
        'page_title': f'Detalhes: {user_to_view.get_full_name() or user_to_view.email}'
    }
    return render(request, 'management/management_user_detail.html', context)


@login_required
@superuser_required # Somente superusuários podem criar consultores
def management_create_consultant(request):
    if request.method == 'POST':
        form = ConsultantCreationForm(request.POST)
        if form.is_valid():
            consultant = form.save()
            messages.success(request, f'A conta para o consultor {consultant.email} foi criada com sucesso!')
            return redirect('management_list_users') # Redireciona para a lista de usuários
        else:
            messages.error(request, 'Houve um erro no formulário. Verifique os dados inseridos.')
    else:
        form = ConsultantCreationForm()
    
    context = {
        'form': form,
        'page_title': 'Criar Novo Consultor',
        'form_title': 'Dados do Novo Consultor', # Título específico para o template do formulário
        'submit_button_text': 'Criar Consultor'
    }
    return render(request, 'management/management_form_page.html', context)


@login_required
@superuser_required 
def management_manage_holding_details_and_consultants(request, holding_id): # RENOMEADA
    holding = get_object_or_404(Holding, pk=holding_id)
    if request.method == 'POST':
        form = AssignConsultantAndHoldingDetailsForm(request.POST, instance=holding)
        if form.is_valid():
            # ModelForm com M2M precisa de form.save(commit=False) primeiro, depois form.save_m2m()
            # ou tratar manualmente como abaixo.
            updated_holding = form.save(commit=False) # Salva nome e descrição
            updated_holding.save() # Salva a instância principal

            # O campo M2M 'consultores' é salvo automaticamente pelo form.save() se commit=True.
            # Se commit=False, você precisa chamar form.save_m2m() ou fazer manualmente:
            selected_consultores = form.cleaned_data.get('consultores')
            updated_holding.consultores.set(selected_consultores) # .set() atualiza toda a relação

            messages.success(request, f'Detalhes e consultores da holding "{holding.nome_holding}" atualizados.')
            return redirect('management_holding_detail', holding_id=holding.id)
        else:
            messages.error(request, "Erro ao atualizar a holding. Verifique os campos.")
    else:
        form = AssignConsultantAndHoldingDetailsForm(instance=holding)
    
    context = {
        'form': form, 
        'holding': holding, 
        'page_title': f'Editar Holding: {holding.nome_holding}', 
        'form_title': f'Editar Dados e Consultores de "{holding.nome_holding}"',
        'submit_button_text': 'Salvar Alterações'
    }
    return render(request, 'management/management_form_page.html', context)


@login_required
@consultant_or_superuser_required
def management_holding_detail(request, holding_id):
    # ... (initial holding fetching logic remains the same) ...
    holding_base_qs = Holding.objects.prefetch_related(
        'consultores', 'clientes', 
        'processo_criacao__pastas_documentos__documentos_contidos__enviado_por', # Deeper prefetch for folders and their docs
        'processo_criacao__documentos_processo__enviado_por' # For root documents of the process
    ).select_related('processo_criacao', 'analise_economia')

    try:
        if request.user.is_superuser:
            holding = holding_base_qs.get(pk=holding_id)
        elif request.user.user_type == 'consultor':
            holding = holding_base_qs.get(pk=holding_id, consultores=request.user)
        else: # Should not be reached due to decorator
            messages.error(request, "Acesso negado.")
            return redirect('login')
    except Holding.DoesNotExist:
        messages.error(request, "Holding não encontrada ou acesso negado.")
        return redirect('management_dashboard')

    processo_criacao = getattr(holding, 'processo_criacao', None)
    process_status_form, officialize_form = None, None
    
    # Pass processo_criacao to forms
    pasta_form_mgmt = PastaDocumentoForm(processo_holding=processo_criacao) if processo_criacao else PastaDocumentoForm()
    management_document_form = ManagementDocumentUploadForm(processo_holding=processo_criacao) if processo_criacao else ManagementDocumentUploadForm()
    
    folder_structure_mgmt = []
    root_documents_mgmt = []
    documentos_holding_count = 0

    if processo_criacao:
        folder_structure_mgmt, root_documents_mgmt = get_folder_structure_with_documents(processo_criacao)
        documentos_holding_count = Documento.objects.filter(processo_holding=processo_criacao).count()


    if request.method == 'POST':
        if 'delete_holding' in request.POST and request.user.is_superuser:
            try:
                nome_holding_deletada = holding.nome_holding
                holding.delete() # Isso irá acionar o CASCADE para ProcessoHolding (e seus Documentos/Pastas)
                                 # e para AnaliseEconomia, ChatMessage.
                messages.success(request, f"A holding '{nome_holding_deletada}' e todos os seus dados associados foram removidos com sucesso.")
                return redirect('management_list_holdings') 
            except Exception as e:
                messages.error(request, f"Ocorreu um erro ao tentar deletar a holding: {e}")
                # Permanecer na página de detalhes se houver erro
                return redirect('management_holding_detail', holding_id=holding_id)
            
        elif 'create_folder_management' in request.POST and processo_criacao:
            posted_pasta_form_mgmt = PastaDocumentoForm(request.POST, processo_holding=processo_criacao)
            if posted_pasta_form_mgmt.is_valid():
                new_folder = posted_pasta_form_mgmt.save(commit=False)
                new_folder.processo_holding = processo_criacao
                new_folder.created_by = request.user
                try:
                    new_folder.save()
                    messages.success(request, f"Pasta '{new_folder.nome}' criada com sucesso.")
                except IntegrityError:
                    messages.error(request, f"Já existe uma pasta com o nome '{new_folder.nome}' neste local para este processo.")
                return redirect('management_holding_detail', holding_id=holding.id) # Refresh page
            else:
                messages.error(request, "Erro ao criar pasta. Verifique os dados informados.")
                pasta_form_mgmt = posted_pasta_form_mgmt

        elif 'upload_document_management' in request.POST:
            if not processo_criacao:
                messages.error(request, "Não é possível adicionar documentos pois esta holding não possui um processo de criação ativo.")
            else:
                form_post_mgmt = ManagementDocumentUploadForm(request.POST, request.FILES, processo_holding=processo_criacao)
                if form_post_mgmt.is_valid():
                    doc = form_post_mgmt.save(commit=False)
                    doc.processo_holding = processo_criacao
                    doc.enviado_por = request.user 
                    doc.nome_original_arquivo = doc.arquivo.name
                    # doc.pasta is handled by form.save()

                    latest_version_data_mgmt = Documento.objects.filter(
                        processo_holding=processo_criacao,
                        nome_documento_logico=doc.nome_documento_logico,
                        categoria=doc.categoria,
                        pasta=doc.pasta # Consider pasta for versioning
                    ).aggregate(max_versao=Max('versao'))
                    current_max_version_mgmt = latest_version_data_mgmt.get('max_versao')
                    doc.versao = (current_max_version_mgmt + 1) if current_max_version_mgmt is not None else 1
                    
                    try:
                        doc.save()
                        messages.success(request, f"Documento '{doc.nome_documento_logico}' (v{doc.versao}) enviado para a holding '{holding.nome_holding}'.")
                    except IntegrityError:
                        messages.error(request, f"Erro de integridade ao salvar. Um documento com nome '{doc.nome_documento_logico}', versão {doc.versao} e categoria '{doc.categoria}' já pode existir neste processo (ou pasta).")
                    return redirect('management_holding_detail', holding_id=holding.id) # Refresh page
                else:
                    messages.error(request, "Erro ao enviar o documento pela gestão. Verifique os campos.")
                    management_document_form = form_post_mgmt
        
        # ... (rest of your POST handling for status update, officialize, etc. remains the same) ...
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
                        processo_criacao.status_atual = 'concluido' # Or some other appropriate status
                    processo_criacao.save()
                messages.success(request, f"Holding '{holding.nome_holding}' oficializada.")
                return redirect('management_holding_detail', holding_id=holding.id)
        elif 'un_officialize_holding' in request.POST and holding.is_legally_official and request.user.is_superuser:
            holding.is_legally_official = False
            holding.data_oficializacao = None
            holding.save()
            if processo_criacao and processo_criacao.status_atual == 'concluido_oficializado':
                # Revert to a suitable status, e.g., 'concluido' or 'providencias_pos_registro'
                processo_criacao.status_atual = 'concluido' 
                processo_criacao.save()
            messages.info(request, f"Oficialização da holding '{holding.nome_holding}' revertida.")
            return redirect('management_holding_detail', holding_id=holding.id)


    # Initialize forms for GET request or if POST had errors for other forms
    if processo_criacao and not process_status_form and 'update_status' not in request.POST : 
        process_status_form = ProcessStatusUpdateForm(instance=processo_criacao)
    if not holding.is_legally_official and not officialize_form and 'officialize_holding' not in request.POST:
        officialize_form = HoldingOfficializeForm(initial={'data_oficializacao': holding.data_oficializacao or timezone.now().date()})

    socios = holding.clientes.all()
    analise = getattr(holding, 'analise_economia', None)

    context = {
        'holding': holding, 
        'socios': socios, 
        'processo_criacao': processo_criacao,
        'analise': analise,
        'process_status_form': process_status_form, 
        'officialize_form': officialize_form,
        'management_document_form': management_document_form,
        'pasta_form_management': pasta_form_mgmt,
        'folder_structure_management': folder_structure_mgmt,
        'root_documents_management': root_documents_mgmt,
        'documentos_holding_count': documentos_holding_count,
        'page_title': f'Detalhes da Holding: {holding.nome_holding}',
        'can_delete_holding': request.user.is_superuser
    }
    return render(request, 'management/management_holding_details.html', context)




@login_required
@consultant_or_superuser_required
def management_list_holdings(request):
    search_query = request.GET.get('q', '')
    # Prefetch M2M para otimizar
    base_query = Holding.objects.prefetch_related('consultores', 'clientes') 

    if request.user.is_superuser:
        holdings_list = base_query.all()
    elif request.user.user_type == 'consultor':
        holdings_list = base_query.filter(consultores=request.user) # Filtra por holdings onde o user é um dos consultores
    else:
        holdings_list = Holding.objects.none() # Caso de segurança
    
    if search_query:
        holdings_list = holdings_list.filter(
            Q(nome_holding__icontains=search_query) |
            Q(clientes__email__icontains=search_query) |
            Q(clientes__first_name__icontains=search_query) |
            Q(clientes__last_name__icontains=search_query) |
            Q(consultores__email__icontains=search_query) | # Adicionado para pesquisar por email de consultor
            Q(consultores__first_name__icontains=search_query) | # Adicionado para pesquisar por nome de consultor
            Q(consultores__last_name__icontains=search_query)
        ).distinct() # .distinct() é importante com M2M em filtros Q
        
    holdings_list = holdings_list.order_by('nome_holding')
    
    context = {
        'holdings_list': holdings_list, 
        'search_query': search_query, 
        'page_title': 'Gerenciamento de Holdings'
    }
    return render(request, 'management/management_list_holdings.html', context)


@login_required
@consultant_or_superuser_required 
def management_holding_documents(request, holding_id):
    # Esta view agora simplesmente redireciona para a página de detalhes da holding,
    # que já contém a seção de documentos.
    return redirect('management_holding_detail', holding_id=holding_id)


@login_required
@consultant_or_superuser_required
def management_holding_manage_clients(request, holding_id):
    holding_base_qs = Holding.objects.prefetch_related('clientes', 'processo_criacao') # Adicionado processo_criacao
    
    if request.user.is_superuser:
        holding = get_object_or_404(holding_base_qs, pk=holding_id)
    elif request.user.user_type == 'consultor':
        holding = get_object_or_404(holding_base_qs, pk=holding_id, consultores=request.user)
    else:
        messages.error(request, "Acesso negado.")
        return redirect('login')

    add_client_form = AddClientToHoldingForm()  

    if request.method == 'POST':
        if 'add_client' in request.POST:
            add_client_form = AddClientToHoldingForm(request.POST)
            if add_client_form.is_valid():
                client_to_add = add_client_form.cleaned_data['email']  
                if client_to_add not in holding.clientes.all():
                    holding.clientes.add(client_to_add)
                    messages.success(request, f"Cliente {client_to_add.email} adicionado à holding '{holding.nome_holding}'.")
                else:
                    messages.warning(request, f"Cliente {client_to_add.email} já está associado a esta holding.")
                return redirect('management_holding_manage_clients', holding_id=holding.id)
        
        elif 'remove_client' in request.POST:
            client_id_to_remove = request.POST.get('client_id')
            if client_id_to_remove:
                try:
                    client_to_remove = User.objects.get(pk=client_id_to_remove, user_type='cliente')
                    
                    # LÓGICA DE REMOÇÃO AJUSTADA:
                    # O cliente pode ser removido da lista de 'clientes' da holding.
                    # O campo 'cliente_principal' no ProcessoHolding permanece para fins históricos.
                    if client_to_remove in holding.clientes.all():
                        holding.clientes.remove(client_to_remove)
                        messages.success(request, f"Cliente {client_to_remove.email} removido da holding '{holding.nome_holding}'.")
                        
                        # Opcional: Se o ProcessoHolding.cliente_principal for este usuário
                        # e a holding não tiver mais clientes ou precisar ser reatribuída,
                        # podem ser necessárias lógicas adicionais aqui ou na interface.
                        # Por agora, a remoção da lista de clientes é o foco.

                    else:
                        messages.warning(request, "Cliente não encontrado nesta holding para remoção.")
                except User.DoesNotExist:
                    messages.error(request, "Cliente a ser removido não encontrado no sistema.")
                return redirect('management_holding_manage_clients', holding_id=holding.id)
                
    current_clients = holding.clientes.all().order_by('first_name', 'last_name', 'email')
    # Adicionar cliente_principal ao contexto para informação, se necessário
    cliente_principal_do_processo = None
    if holding.processo_criacao:
        cliente_principal_do_processo = holding.processo_criacao.cliente_principal

    context = {
        'holding': holding,  
        'current_clients': current_clients,
        'add_client_form': add_client_form,  
        'cliente_principal_do_processo': cliente_principal_do_processo, # Para exibir no template, se útil
        'page_title': f"Gerenciar Clientes da Holding: {holding.nome_holding}"
    }
    return render(request, 'management/management_holding_manage_clients.html', context)
