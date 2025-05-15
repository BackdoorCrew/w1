from django.shortcuts import render, redirect
from django.contrib.auth import login
from allauth.account.forms import LoginForm, SignupForm

def index(request):
    return render(request, 'core/index.html')

def login(request):
    if request.method == 'POST':
        form = LoginForm(data=request.POST, request=request)
        if form.is_valid():
            user = form.get_user()  # Get the authenticated user
            login(request, user)  # Log in the user
            if user.is_superuser:
                return redirect('/admin/')
            return redirect('/dashboard/')
    else:
        form = LoginForm(request=request)
    return render(request, 'core/login.html', {'form': form})

def signup(request):
    if request.method == 'POST':
        form = SignupForm(request.POST)
        if form.is_valid():
            user = form.save(request)  # Save the user
            login(request, user)  # Log in the user without backend
            return redirect('/dashboard/')
    else:
        form = SignupForm()
    return render(request, 'core/signup.html', {'form': form})

def dashboard(request):
    return render(request, 'core/dashboard.html')