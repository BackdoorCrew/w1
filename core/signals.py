# D:\hackaton\w1\w1\core\signals.py
from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import User, ClienteProfile # Certifique-se que User e ClienteProfile estão definidos em core.models

@receiver(post_save, sender=User) # Usar o seu modelo User customizado
def create_or_update_user_profile(sender, instance, created, **kwargs):
    """
    Cria ou atualiza o ClienteProfile quando um User do tipo 'cliente' é salvo.
    """
    if instance.user_type == 'cliente': # Verifica se o usuário é do tipo 'cliente'
        if created: # Se um novo usuário 'cliente' foi criado
            ClienteProfile.objects.create(user=instance)
        else: # Se um usuário 'cliente' existente foi atualizado
            # Garante que o perfil exista e o salva.
            # Isto é útil se, por algum motivo, o perfil não foi criado antes
            # ou se você quiser atualizar algo no perfil quando o User é salvo (embora não estejamos fazendo isso aqui).
            try:
                instance.cliente_profile.save()
            except ClienteProfile.DoesNotExist:
                ClienteProfile.objects.create(user=instance)