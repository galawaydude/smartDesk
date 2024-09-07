from celery import shared_task
from django.core.mail import send_mail

@shared_task
def send_verification_email(email, code):
    subject = 'Verify your account'
    message = f'Your verification code is: {code}'
    from_email = 'noreply@yourapp.com'
    recipient_list = [email]
    send_mail(subject, message, from_email, recipient_list)