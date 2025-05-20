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


def consultant_or_superuser_required(view_func):
    """
    Decorator for views that checks that the user is active and is a superuser OR an active consultant.
    """
    def check_user(user):
        if not user.is_authenticated or not user.is_active:
            return False
        if user.is_superuser:
            return True
        # Apenas consultores ativos podem acessar
        if user.user_type == 'consultor':
            return True
        return False
    return user_passes_test(check_user, login_url='login')(view_func)