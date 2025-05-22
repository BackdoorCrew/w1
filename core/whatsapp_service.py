# core/whatsapp_service.py
import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(recipient_phone: str, message_text: str) -> bool:
    """
    Envia uma mensagem de WhatsApp usando a Z-API.
    - Usa ZAPI_INSTANCE_ID e ZAPI_CLIENT_TOKEN para a URL.
    - Usa ZAPI_SECURITY_TOKEN para o cabeçalho Client-Token, conforme exigido pela API.
    """
    logger.info(f"Attempting to send WhatsApp to {recipient_phone} with message: '{message_text[:50]}...'")

    # Verifica se as configurações essenciais da instância foram carregadas
    if not settings.ZAPI_INSTANCE_ID or not settings.ZAPI_CLIENT_TOKEN or not settings.ZAPI_SECURITY_TOKEN:
        logger.error("CRITICAL: ZAPI_INSTANCE_ID, ZAPI_CLIENT_TOKEN, or ZAPI_SECURITY_TOKEN "
                     "is not configured correctly in environment variables. Please check your .env file.")
        return False

    # Constroi a URL da API diretamente, usando o token da instância
    api_url = f"{settings.ZAPI_BASE_URL}/{settings.ZAPI_INSTANCE_ID}/token/{settings.ZAPI_CLIENT_TOKEN}/send-text"
    logger.info(f"Constructed Z-API URL: {api_url}")

    # Cabeçalhos da requisição
    # Usa ZAPI_SECURITY_TOKEN (Account Security Token) para o cabeçalho Client-Token
    headers = {
        "Content-Type": "application/json",
        "Client-Token": settings.ZAPI_SECURITY_TOKEN
    }
    logger.info(f"Z-API Headers: {json.dumps(headers)}")

    # Limpa o número de telefone
    cleaned_phone_number = "".join(filter(str.isdigit, recipient_phone))
    if not (10 <= len(cleaned_phone_number) <= 15):
        logger.warning(f"Potentially invalid phone number after cleaning: '{cleaned_phone_number}'. Original: '{recipient_phone}'")

    payload = {
        "phone": cleaned_phone_number,
        "message": message_text
    }
    logger.info(f"Z-API Payload: {json.dumps(payload)}")

    try:
        response = requests.post(api_url, json=payload, headers=headers, timeout=30)

        logger.info(f"Z-API Response Status Code: {response.status_code}")
        logger.info(f"Z-API Response Raw Text (first 500 chars): {response.text[:500]}")

        if 200 <= response.status_code < 300:
            try:
                response_data = response.json()
                logger.info(f"Message successfully sent/queued by Z-API. Response: {response_data}")
                return True
            except json.JSONDecodeError:
                logger.error("Failed to decode JSON from successful Z-API response.")
                return False
        else:
            logger.error(f"Failed to send message. Status Code: {response.status_code}")
            try:
                error_details = response.json()
                logger.error(f"Error Details (JSON): {error_details}")
            except json.JSONDecodeError:
                logger.error(f"Error Response (not JSON): {response.text}")
            return False

    except requests.exceptions.Timeout:
        logger.error(f"Timeout error sending WhatsApp to {cleaned_phone_number}")
        return False
    except requests.exceptions.ConnectionError:
        logger.error(f"Connection error sending WhatsApp to {cleaned_phone_number}. Check API URL and network.")
        return False
    except requests.exceptions.RequestException as e:
        logger.error(f"An error occurred during the API request to {cleaned_phone_number}: {e}")
        return False
    except Exception as e:
        logger.error(f"An unexpected error occurred in send_whatsapp_message for {cleaned_phone_number}: {e.__class__.__name__} - {e}", exc_info=True)
        return False