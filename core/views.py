from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from allauth.account.forms import LoginForm, SignupForm
from .forms import SimulationForm
from .models import User, SimulationResult
from decimal import Decimal

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
                return redirect('/admin/')
            return redirect('forms')
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
            return redirect('forms')
        else:
            print("Form errors:", form.errors)
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

@login_required
def forms(request):
    form = SimulationForm()
    return render(request, 'core/forms.html', {'form': form, 'user': request.user})

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
            inventory_cost_without = Decimal('0')
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
            has_companies = cleaned_data.get('has_companies') == 'yes'
            number_of_companies = cleaned_data.get('number_of_companies', 0)
            monthly_profit = cleaned_data.get('monthly_profit', Decimal('0'))
            company_tax_regime = cleaned_data.get('company_tax_regime', 'simples')
            if has_companies:
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
            receives_rent = cleaned_data.get('receives_rent') == 'yes'
            monthly_rent = cleaned_data.get('monthly_rent', Decimal('0'))
            if receives_rent:
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

            # Save simulation results
            simulation_result = SimulationResult(
                user=request.user,
                number_of_properties=number_of_properties,
                total_property_value=total_property_value,
                inventory_cost_without=inventory_cost_without,
                inventory_cost_with=Decimal('0'),
                number_of_companies=number_of_companies,
                monthly_profit=monthly_profit,
                annual_profit=annual_profit,
                profit_savings=profit_savings,
                monthly_rent=monthly_rent,
                annual_rent=annual_rent,
                rental_savings=rental_savings,
                inventory_time_without=inventory_time_without,
                inventory_time_with=inventory_time_with,
                receives_rent=receives_rent,
                has_companies=has_companies,
                number_of_heirs=number_of_heirs,
                company_tax_regime=company_tax_regime,
                inventory_savings=inventory_savings,
                total_savings=total_savings,
                conflict_risk=conflict_risk,
            )
            simulation_result.save()

            # Context for template
            context = {
                'user': request.user,
                'number_of_properties': number_of_properties,
                'total_property_value': float(total_property_value),
                'inventory_savings': float(inventory_savings),
                'inventory_text': inventory_text,
                'inventory_cost_without': float(inventory_cost_without),
                'inventory_cost_with': 0.0,
                'has_companies': cleaned_data.get('has_companies'),
                'number_of_companies': number_of_companies,
                'company_tax_regime': company_tax_regime,
                'monthly_profit': float(monthly_profit),
                'annual_profit': float(annual_profit),
                'profit_savings': float(profit_savings),
                'profit_text': profit_text,
                'receives_rent': cleaned_data.get('receives_rent'),
                'monthly_rent': float(monthly_rent),
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
            return render(request, 'core/forms.html', {'form': form, 'user': request.user})
    return redirect('forms')

@login_required
def dashboard(request):
    try:
        latest_simulation = SimulationResult.objects.filter(user=request.user).latest('created_at')
    except SimulationResult.DoesNotExist:
        latest_simulation = None

    context = {
        'user': request.user,
        'simulation_result': latest_simulation,
    }
    return render(request, 'core/dashboard.html', context)