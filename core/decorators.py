from django.contrib.auth.decorators import user_passes_test
from django.shortcuts import redirect # Adicione esta linha

def superuser_required(view_func):
    """
    Decorator for views that checks that the user is a superuser.
    """
    decorated_view_func = user_passes_test(
        lambda u: u.is_active and u.is_superuser,
        login_url='login'  # Ou uma página de 'acesso negado'
    )(view_func)
    return decorated_view_func