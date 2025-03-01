import base64
from io import BytesIO

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
    print(code_unique)
    
    # URL encode the data for the QR code
    encoded_data = urllib.parse.quote(str(code_unique))
    
    # Generate a QR code URL using a public API service
    # Option 1: QR Server API (free, no sign-up needed)
    qr_code_url = f"https://api.qrserver.com/v1/create-qr-code/?size=200x200&data={encoded_data}"
    
    # Option 2: Google Charts API (also free, reliable)
    # qr_code_url = f"https://chart.googleapis.com/chart?cht=qr&chs=200x200&chl={encoded_data}"
    
    # Twilio client setup
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Message body
    message_body = f"Your unique QR code is: {code_unique}\nValid until: {date_validite}"

    # Send WhatsApp message with the QR code URL
    message = client.messages.create(
        body=message_body,
        from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
        to=f"whatsapp:{to_number}",
        media_url=[qr_code_url],  # This is a direct URL to the QR code image
    )

    # Return the message SID
    return message.sid