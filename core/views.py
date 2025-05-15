from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from allauth.account.forms import LoginForm, SignupForm
from .forms import HoldingForm
from .models import Holding, ProcessoHolding, AnaliseEconomia
from datetime import date

def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            response = form.login(request)
            if response:
                if request.user.is_authenticated:
                    if request.user.is_superuser:
                        return redirect('/admin/')
                    if request.user.user_type == 'cliente':
                        return redirect('create_holding')
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
            return redirect('create_holding')
        else:
            print("Form errors:", form.errors)
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def dashboard(request):
    return render(request, 'core/dashboard.html')

@login_required
def create_holding(request):
    if request.method == 'POST':
        form = HoldingForm(request.POST)
        if form.is_valid():
            holding = form.save()
            holding.clientes.add(request.user)
            ProcessoHolding.objects.create(
                cliente_principal=request.user,
                holding_associada=holding,
                status_atual='aguardando_documentos'
            )
            # Basic simulation for AnaliseEconomia
            economia_tributaria = 0
            if holding.has_rental_income and holding.rental_details:
                # Placeholder: Calculate IRPF vs IRPJ/CSLL
                economia_tributaria += 10000  # Example
            if holding.has_dividends and holding.dividend_amount:
                # Placeholder: Dividend tax savings
                economia_tributaria += holding.dividend_amount * 0.15
            AnaliseEconomia.objects.create(
                holding=holding,
                ano_referencia=date.today().year,
                economia_tributaria_estimada=economia_tributaria,
                patrimonio_liquido_projetado=holding.rental_property_count * 1000000 if holding.rental_property_count else 0
            )
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)
    else:
        form = HoldingForm(initial={'nome_holding': f"{request.user.first_name} Legacy Holdings"})
    return render(request, 'core/create_holding.html', {'form': form})