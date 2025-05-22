# core/whatsapp_service.py
import requests
import json
from django.conf import settings
import logging

logger = logging.getLogger(__name__)

def send_whatsapp_message(phone_number: str, message: str) -> bool:
    logger.info(f"Attempting to send WhatsApp message. Initial phone_number: '{phone_number}', Message: '{message[:50]}...'")

    if not settings.ZAPI_INSTANCE_ID or not settings.ZAPI_CLIENT_TOKEN:
        logger.error("Z-API credentials (ZAPI_INSTANCE_ID or ZAPI_CLIENT_TOKEN) are not configured in settings.")
        return False

    if not phone_number:
        logger.warning(f"Cannot send WhatsApp: phone_number is empty. Message was: '{message[:50]}...'")
        return False

    cleaned_phone_number = "".join(filter(str.isdigit, phone_number))
    logger.info(f"Cleaned phone number: '{cleaned_phone_number}' from original: '{phone_number}'")

    if not (10 <= len(cleaned_phone_number) <= 15):
         logger.warning(f"Potentially invalid phone number length after cleaning: '{cleaned_phone_number}'. Original: '{phone_number}'")

    # This URL construction is now correct with your updated .env
    api_url = f"{settings.ZAPI_BASE_URL}/{settings.ZAPI_INSTANCE_ID}/token/{settings.ZAPI_CLIENT_TOKEN}/send-text"
    logger.info(f"Constructed Z-API URL: {api_url}")

    payload = {
        "phone": cleaned_phone_number,
        "message": message
    }
    logger.info(f"Z-API Payload: {json.dumps(payload)}")

    headers = {
        "Content-Type": "application/json",
        "Client-Token": settings.ZAPI_CLIENT_TOKEN  # <--- ADD THIS LINE
    }
    logger.info(f"Z-API Headers: {json.dumps(headers)}") # Log headers to confirm token is there

    try:
        logger.info(f"Making POST request to Z-API for phone: {cleaned_phone_number}")
        response = requests.post(api_url, data=json.dumps(payload), headers=headers, timeout=15)
        logger.info(f"Z-API Response Status Code: {response.status_code}")
        logger.info(f"Z-API Response Raw Text (first 500 chars): {response.text[:500]}")

        # Try to parse JSON first, as Z-API returns JSON for both success and errors
        try:
            response_data = response.json()
        except json.JSONDecodeError:
            logger.error(f"Failed to decode JSON from Z-API response for {cleaned_phone_number}. Raw text: {response.text[:500]}")
            # If JSON decoding fails but it was an HTTP error, raise_for_status will catch it.
            # If it was 2xx but not JSON, it's an unexpected API behavior.
            if 200 <= response.status_code < 300:
                logger.error(f"Z-API returned non-JSON 2xx response for {cleaned_phone_number}.")
            else:
                response.raise_for_status() # Let it raise for 4xx/5xx if not already caught
            return False

        # Check for HTTP errors after attempting to get JSON (as error body might be JSON)
        if not (200 <= response.status_code < 300):
            error_message_from_json = response_data.get('message', response_data.get('error', 'See raw text log')) if isinstance(response_data, dict) else 'See raw text log'
            logger.error(f"Z-API request failed with status {response.status_code} for {cleaned_phone_number}. API Message: '{error_message_from_json}'")
            # No need to call response.raise_for_status() again if we've processed the JSON error.
            return False


        # Check for application-level errors within the JSON from Z-API even on 200 OK
        # (Though for a 400, this part might not be reached if the above check handles it)
        if isinstance(response_data, dict) and response_data.get('error'):
            error_message = response_data.get('message', response_data.get('error', 'Unknown Z-API error in JSON'))
            logger.error(f"Z-API returned an error in JSON response for {cleaned_phone_number}: '{error_message}' Full JSON: {response_data}")
            return False

        logger.info(f"Successfully sent/queued WhatsApp message to {cleaned_phone_number} via Z-API. Response JSON: {response_data}")
        return True

    except requests.exceptions.HTTPError as http_err: # This catches errors from response.raise_for_status() if not handled above
        logger.error(f"HTTP error occurred sending WhatsApp to {cleaned_phone_number}: {http_err}")
        if http_err.response is not None:
            logger.error(f"Z-API HTTP Error Response Content: {http_err.response.text[:500]}")
        else:
            logger.error("Z-API HTTP Error: No response object available in the exception.")
    except requests.exceptions.ConnectionError as conn_err:
        logger.error(f"Connection error sending WhatsApp to {cleaned_phone_number}: {conn_err}")
    except requests.exceptions.Timeout as timeout_err:
        logger.error(f"Timeout error sending WhatsApp to {cleaned_phone_number}: {timeout_err}")
    except requests.exceptions.RequestException as req_err:
        logger.error(f"General RequestException sending WhatsApp to {cleaned_phone_number}: {req_err}")
    except Exception as e:
        logger.error(f"An unexpected error occurred in send_whatsapp_message for {cleaned_phone_number}: {e.__class__.__name__} - {e}", exc_info=True)
    return False