from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from django.contrib.auth.decorators import login_required
from allauth.account.forms import LoginForm, SignupForm
from .forms import HoldingForm
from .models import Holding, ProcessoHolding

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
            user.user_type = 'cliente'  # Set default user_type for new users
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
            holding = form.save(commit=False)
            holding.save()
            holding.clientes.add(request.user)
            ProcessoHolding.objects.create(
                cliente_principal=request.user,
                holding_associada=holding,
                status_atual='aguardando_documentos'
            )
            return redirect('dashboard')
        else:
            print("Form errors:", form.errors)
    else:
        form = HoldingForm()
    return render(request, 'core/create_holding.html', {'form': form})