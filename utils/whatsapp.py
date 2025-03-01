from io import BytesIO

import qrcode
from django.conf import settings
from twilio.rest import Client


def send_whatsapp_message(to_number: str, message: str, console: bool = False):
    if not console:
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
    else:
        # Just print to console
        print(f'Console mode - Message content: {message}')


def send_whatsapp_qr_code(to_number, code_unique, date_validite):
    """
    Generate a QR code for the unique code and send a WhatsApp message 
    with the QR code image and a message to the provided number.
    """

    # Generate the QR code image
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(str(code_unique))
    qr.make(fit=True)
    img = qr.make_image(fill='black', back_color='white')

    # Convert the image to a file-like object in memory
    img_byte_arr = BytesIO()
    img.save(img_byte_arr, format='PNG')
    img_byte_arr.seek(0)

    # Twilio client setup (ensure you have set up your Twilio SID, Auth Token, and WhatsApp number in settings.py)
    client = Client(settings.TWILIO_ACCOUNT_SID, settings.TWILIO_AUTH_TOKEN)

    # Message body
    message_body = f"Your unique QR code is: {code_unique}\nValid until: {date_validite}"

    # Upload the QR code image to Twilio's media API
    message = client.messages.create(
        body=message_body,
        from_=f"whatsapp:{settings.TWILIO_WHATSAPP_FROM}",
        to=f"whatsapp:{to_number}",
        media_url=["data:image/png;base64," +
                   img_byte_arr.getvalue().encode("base64")],
    )

    # You can return the message SID or handle it as needed
    return message.sid
