import base64
from io import BytesIO
import logging

import qrcode
from django.conf import settings
from twilio.rest import Client
import urllib.parse

def send_whatsapp_message(to_number: str, message: str, console: bool = False):
    # Your Twilio credentials
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_NUMBER

    # Initialize Twilio client
    client = Client(account_sid, auth_token)

    # Send the WhatsApp message
    message_response = client.messages.create(
        body=message,
        from_=from_number,
        to=f'whatsapp:{to_number}'
    )
    print(f'Message sent: {message_response.sid}')

def send_whatsapp_qr_code(to_number, code_unique, date_validite):
    """
    Generate a QR code for the unique code and send a WhatsApp message 
    with the QR code image and a message to the provided number.
    """
    # Set up logging
    logger = logging.getLogger(__name__)
    
    # Start logging the process
    logger.info(f"Starting QR code generation for code: {code_unique}")
    print(f"Generating QR code for: {code_unique}")
    
    try:
        # URL encode the data for the QR code
        encoded_data = urllib.parse.quote(str(code_unique))
        
        # Generate a QR code URL using a public API service
        qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_data}"
        
        # Log the QR code URL
        logger.info(f"QR code URL generated: {qr_code_url}")
        print(f"QR code URL: {qr_code_url}")
        
        # Twilio client setup
        client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)
        
        # Log Twilio configuration (without sensitive details)
        logger.info(f"Preparing to send WhatsApp message to: {to_number}")
        print(f"Preparing to send WhatsApp message to: {to_number}")

        # Message body
        message_body = f"Your unique QR code is: {code_unique}\nValid until: {date_validite}"

        # Send WhatsApp message with the QR code URL
        message = client.messages.create(
            body=message_body,
            from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
            to=f"whatsapp:{to_number}",
            media_url=[qr_code_url],  # This is a direct URL to the QR code image
        )
        
        # Log successful message sending
        logger.info(f"WhatsApp message sent successfully! Message SID: {message.sid}")
        print(f"WhatsApp message sent successfully! Message SID: {message.sid}")

        # Return the message SID
        return message.sid
        
    except Exception as e:
        # Log any errors that occur
        error_message = f"Error in send_whatsapp_qr_code: {str(e)}"
        logger.error(error_message)
        print(error_message)
        raise