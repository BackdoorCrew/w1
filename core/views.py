from django.shortcuts import render, redirect
from django.contrib.auth import login
from allauth.account.forms import LoginForm, SignupForm
from allauth.account.views import LoginView, SignupView

def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            response = form.login(request)  # Autentica e faz login
            if request.user.is_authenticated and request.user.is_superuser:
                return redirect('/admin/')
            return redirect('/dashboard/')
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            return redirect('/dashboard/')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def dashboard(request):
    return render(request, 'core/dashboard.html')