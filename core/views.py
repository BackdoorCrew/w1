from django.shortcuts import render, redirect
from django.contrib.auth import login as auth_login
from allauth.account.forms import LoginForm, SignupForm

def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.login(request)  # Authenticate and get user
            if user:
                auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
                if user.is_superuser:
                    return redirect('/admin/')
                return redirect('/dashboard/')
        else:
            print("Form errors:", form.errors)  # Debug form errors
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)
            auth_login(request, user, backend='allauth.account.auth_backends.AuthenticationBackend')
            return redirect('/dashboard/')
        else:
            print("Form errors:", form.errors)
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def dashboard(request):
    return render(request, 'core/dashboard.html')