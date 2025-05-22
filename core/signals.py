# core/signals.py
from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from django.conf import settings # For accessing AUTH_USER_MODEL if needed directly
from .models import User, ClienteProfile, Documento, ProcessoHolding, ChatMessage, Holding
from .whatsapp_service import send_whatsapp_message
import logging

logger = logging.getLogger(__name__)

@receiver(post_save, sender=User)
def create_or_update_user_profile(sender, instance, created, **kwargs):
    if instance.user_type == 'cliente':
        if created:
            ClienteProfile.objects.create(user=instance)
        else:
            try:
                instance.cliente_profile.save()
            except ClienteProfile.DoesNotExist:
                ClienteProfile.objects.create(user=instance)

# --- WhatsApp Notification Signals ---

def get_holding_participants_numbers(holding: Holding, exclude_user: User = None):
    logger.info(f"[get_holding_participants_numbers] Called for Holding ID: {holding.id}, excluding User ID: {exclude_user.id if exclude_user else 'None'}")
    participants_numbers = []
    
    logger.info(f"Holding '{holding.nome_holding}' - Clients:")
    for user in holding.clientes.all():
        logger.info(f"  Checking client: {user.email} (ID: {user.id}), WhatsApp: '{user.whatsapp_number}'")
        if user != exclude_user and user.whatsapp_number:
            participants_numbers.append(user.whatsapp_number)
            logger.info(f"    Added client {user.email}'s number: {user.whatsapp_number}")
        elif user == exclude_user:
            logger.info(f"    Skipped client {user.email} (is exclude_user).")
        elif not user.whatsapp_number:
            logger.info(f"    Skipped client {user.email} (no WhatsApp number).")

    logger.info(f"Holding '{holding.nome_holding}' - Consultants:")
    for user in holding.consultores.all():
        logger.info(f"  Checking consultant: {user.email} (ID: {user.id}), WhatsApp: '{user.whatsapp_number}'")
        if user != exclude_user and user.whatsapp_number:
            participants_numbers.append(user.whatsapp_number)
            logger.info(f"    Added consultant {user.email}'s number: {user.whatsapp_number}")
        elif user == exclude_user:
            logger.info(f"    Skipped consultant {user.email} (is exclude_user).")
        elif not user.whatsapp_number:
            logger.info(f"    Skipped consultant {user.email} (no WhatsApp number).")
            
    unique_numbers = list(set(participants_numbers))
    logger.info(f"[get_holding_participants_numbers] Returning unique numbers: {unique_numbers} for Holding ID: {holding.id}")
    return unique_numbers

def get_process_participants_numbers(processo: ProcessoHolding, exclude_user: User = None):
    """Helper to get WhatsApp numbers for process participants."""
    participants_numbers = []
    # Cliente Principal
    if processo.cliente_principal and processo.cliente_principal.whatsapp_number:
        if processo.cliente_principal != exclude_user:
            participants_numbers.append(processo.cliente_principal.whatsapp_number)

    # Consultores and other clients from the associated Holding
    if processo.holding_associada:
        holding_users_numbers = get_holding_participants_numbers(processo.holding_associada, exclude_user)
        participants_numbers.extend(holding_users_numbers)

    return list(set(participants_numbers))


@receiver(post_save, sender=Documento)
def notify_on_new_document(sender, instance: Documento, created, **kwargs):
    if created: # Notify only on new document creation for simplicity
        try:
            processo = instance.processo_holding
            uploader_name = instance.enviado_por.get_full_name() if instance.enviado_por else "Sistema"

            message = (
                f"📄 Novo documento adicionado ao processo da holding '{processo.holding_associada.nome_holding if processo.holding_associada else 'N/A'}'.\n"
                f"Nome: {instance.nome_documento_logico} (v{instance.versao})\n"
                f"Categoria: {instance.get_categoria_display()}\n"
                f"Enviado por: {uploader_name}\n"
                f"Pasta: {instance.pasta.nome if instance.pasta else 'Raiz do Processo'}"
            )

            # Get client principal and consultants
            recipients_numbers = get_process_participants_numbers(processo, exclude_user=instance.enviado_por)

            for number in recipients_numbers:
                logger.info(f"Attempting to send new document notification to {number} for doc ID {instance.id}")
                send_whatsapp_message(number, message)
        except Exception as e:
            logger.error(f"Error in notify_on_new_document signal for doc ID {instance.id}: {e}")


# To track status changes, we need the old value.
# We can store the old value on the instance before saving.
@receiver(pre_save, sender=ProcessoHolding)
def store_old_status_processo(sender, instance: ProcessoHolding, **kwargs):
    if instance.pk: # Only for existing instances
        try:
            instance._old_status_atual = ProcessoHolding.objects.get(pk=instance.pk).status_atual
        except ProcessoHolding.DoesNotExist:
            instance._old_status_atual = None # New instance, no old status

@receiver(post_save, sender=ProcessoHolding)
def notify_on_process_status_change(sender, instance: ProcessoHolding, created, **kwargs):
    if not created and hasattr(instance, '_old_status_atual') and instance._old_status_atual != instance.status_atual:
        try:
            old_status_display = instance._old_status_atual # Or get display name if you stored it
            new_status_display = instance.get_status_atual_display()

            message = (
                f"🔄 Atualização no processo da holding '{instance.holding_associada.nome_holding if instance.holding_associada else 'N/A'}'.\n"
                f"Status alterado de '{old_status_display}' para '{new_status_display}'.\n"
                f"Cliente: {instance.cliente_principal.get_full_name() if instance.cliente_principal else 'N/A'}"
            )

            recipients_numbers = get_process_participants_numbers(instance)

            for number in recipients_numbers:
                logger.info(f"Attempting to send process status change notification to {number} for process ID {instance.id}")
                send_whatsapp_message(number, message)
        except Exception as e:
            logger.error(f"Error in notify_on_process_status_change signal for process ID {instance.id}: {e}")


@receiver(post_save, sender=ChatMessage)
def notify_on_new_chat_message(sender, instance: ChatMessage, created, **kwargs):
    logger.info(f"--- ChatMessage Signal Triggered (notify_on_new_chat_message) ---")
    logger.info(f"ChatMessage ID: {instance.id}, Created: {created}")
    if created:
        logger.info(f"New ChatMessage created. Proceeding with notification logic.")
        try:
            holding = instance.holding
            sender_user = instance.sender
            
            if not holding:
                logger.warning(f"ChatMessage ID {instance.id} has no associated holding. Cannot send notification.")
                return
            if not sender_user:
                logger.warning(f"ChatMessage ID {instance.id} has no sender. Cannot reliably exclude or name sender.")
                return # Or handle as "System" if that's possible

            sender_name = sender_user.get_full_name() or sender_user.email.split('@')[0]
            logger.info(f"Holding: '{holding.nome_holding}' (ID: {holding.id}), Sender: '{sender_name}' (ID: {sender_user.id}, Email: {sender_user.email})")
            
            message_content = (
                f"💬 Nova mensagem no chat da holding '{holding.nome_holding}':\n"
                f"De: {sender_name}\n"
                f"Mensagem: {instance.content}"
            )
            logger.info(f"Notification message prepared: '{message_content[:100]}...'")
            
            recipients_numbers = get_holding_participants_numbers(holding, exclude_user=sender_user)
            logger.info(f"Final list of recipient phone numbers for holding '{holding.nome_holding}' (excluding sender '{sender_name}'): {recipients_numbers}")

            if not recipients_numbers:
                logger.info(f"No recipients found (after exclusion or none have WhatsApp numbers) for holding '{holding.nome_holding}'. No notifications will be sent.")
                return

            for number in recipients_numbers:
                logger.info(f"Attempting to send chat notification to number: '{number}' for message in holding '{holding.nome_holding}' from sender '{sender_name}'")
                send_whatsapp_message(number, message_content)
            
            logger.info(f"Finished processing notifications for ChatMessage ID: {instance.id}")

        except Exception as e:
            logger.error(f"Error in notify_on_new_chat_message signal for ChatMessage ID {instance.id}: {e.__class__.__name__} - {e}", exc_info=True) # exc_info=True for traceback
    else:
        logger.info(f"ChatMessage ID {instance.id} was updated, not created. No notification sent.")
    logger.info(f"--- ChatMessage Signal Finished ---")