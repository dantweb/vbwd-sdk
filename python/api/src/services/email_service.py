import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart


class EmailService:
    """Service for sending emails."""

    def __init__(self):
        self._smtp_host = os.getenv('SMTP_HOST', 'localhost')
        self._smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self._smtp_user = os.getenv('SMTP_USER', '')
        self._smtp_password = os.getenv('SMTP_PASSWORD', '')
        self._from_email = os.getenv('FROM_EMAIL', 'noreply@vbwd.local')

    def send_result(self, to_email: str, result: dict) -> bool:
        """Send diagnostic result email."""
        subject = "Your Diagnostic Results"
        html_body = self._render_result_template(result)

        return self._send_email(to_email, subject, html_body)

    def _send_email(self, to_email: str, subject: str, html_body: str) -> bool:
        """Send email via SMTP."""
        try:
            msg = MIMEMultipart('alternative')
            msg['Subject'] = subject
            msg['From'] = self._from_email
            msg['To'] = to_email

            html_part = MIMEText(html_body, 'html')
            msg.attach(html_part)

            # Skip sending if SMTP not configured
            if not self._smtp_host or self._smtp_host == 'localhost':
                print(f'Email would be sent to {to_email}: {subject}')
                return True

            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                if self._smtp_user and self._smtp_password:
                    server.login(self._smtp_user, self._smtp_password)
                server.send_message(msg)

            return True
        except Exception as e:
            print(f'Email send error: {e}')
            return False

    def _render_result_template(self, result: dict) -> str:
        """Render HTML email template for results."""
        return f"""
        <!DOCTYPE html>
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 20px; }}
                .header {{ background: #007bff; color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .result {{ background: #f8f9fa; padding: 15px; margin: 10px 0; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>Your Diagnostic Results</h1>
            </div>
            <div class="content">
                <p>Thank you for using our diagnostic service.</p>
                <div class="result">
                    <h3>Results</h3>
                    <pre>{result}</pre>
                </div>
                <p>If you have any questions, please contact our support team.</p>
            </div>
        </body>
        </html>
        """
