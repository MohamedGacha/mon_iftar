import time
import base64
from io import BytesIO
import logging
import qrcode
from django.conf import settings
from twilio.rest import Client
import urllib.parse

def send_whatsapp_message(to_number: str, message: str, console: bool = False):
    """
    Send an SMS message to the provided phone number.
    """
    # Your Twilio credentials
    account_sid = settings.TWILIO_ACCOUNT_SID
    auth_token = settings.TWILIO_AUTH_TOKEN
    from_number = settings.TWILIO_WHATSAPP_FROM

    # Initialize Twilio client
    client = Client(account_sid, auth_token)
    time.sleep(0.01)
    # Send the SMS message
    message_response = client.messages.create(
        body=message,
        from_=from_number,  # Your Twilio SMS number
        to=to_number  # Recipient's phone number
    )
    print(f'Message sent: {message_response.sid}')


def send_whatsapp_qr_code(to_number, code_unique, date_validite):
    """
    Generate a QR code URL for the unique code and send an SMS message 
    with the QR code URL as a link and a message to the provided number.
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
        logger.info(f"Preparing to send SMS message to: {to_number}")
        print(f"Preparing to send SMS message to: {to_number}")

        # Message body with the QR code URL as a clickable link
        message_body = f"Your unique QR code is: {code_unique}\nValid until: {date_validite}\nQR Code: {qr_code_url}"

        # Send SMS message with the QR code URL in the message body
        time.sleep(0.01)
        message = client.messages.create(
            body=message_body,
            from_=f"{settings.TWILIO_WHATSAPP_FROM}",  # Your Twilio SMS number
            to=to_number,  # Recipient's phone number
        )
        
        # Log successful message sending
        logger.info(f"SMS message sent successfully! Message SID: {message.sid}")
        print(f"SMS message sent successfully! Message SID: {message.sid}")

        # Return the message SID
        return message.sid
        
    except Exception as e:
        # Log any errors that occur
        error_message = f"Error in send_sms_qr_code: {str(e)}"
        logger.error(error_message)
        print(error_message)
        raise
