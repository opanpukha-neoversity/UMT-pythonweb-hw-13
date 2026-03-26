"""Outgoing email helper functions for verification and password reset."""

from email.message import EmailMessage
import smtplib

from src.conf.config import get_settings

settings = get_settings()


class EmailService:
    """Simple SMTP email sender for Mailpit or any SMTP relay."""

    def send(self, recipient: str, subject: str, body: str) -> None:
        """Send a plain-text email via SMTP."""

        message = EmailMessage()
        message['Subject'] = subject
        message['From'] = settings.mail_from
        message['To'] = recipient
        message.set_content(body)

        with smtplib.SMTP(settings.mail_server, settings.mail_port) as server:
            server.send_message(message)

    def send_verification_email(self, recipient: str, token: str) -> None:
        """Email a verification link to the user."""

        verify_link = f"{settings.frontend_base_url}/api/auth/verify-email/{token}"
        self.send(recipient, 'Verify your email', f'Open this link to verify your email: {verify_link}')

    def send_reset_email(self, recipient: str, token: str) -> None:
        """Email a password reset link to the user."""

        reset_link = f"{settings.frontend_base_url}/reset-password?token={token}"
        self.send(recipient, 'Reset your password', f'Open this link to reset your password: {reset_link}')


email_service = EmailService()
