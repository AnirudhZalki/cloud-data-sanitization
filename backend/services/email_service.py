import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

def send_sanitized_email(to_email: str, original_filename: str, sanitized_url: str):
    smtp_server = os.getenv("SMTP_SERVER", "smtp.gmail.com")
    smtp_port = int(os.getenv("SMTP_PORT", 587))
    smtp_user = os.getenv("SMTP_EMAIL")
    smtp_password = os.getenv("SMTP_PASSWORD")
    
    subject = f"Sanitization Complete: {original_filename}"
    body = f"""
    Hello,

    Your file '{original_filename}' has been successfully sanitized!
    
    You can view or download the sanitized file using the link below:
    {sanitized_url}

    Thank you for using the Cloud Data Sanitization System.
    """

    if not smtp_user or not smtp_password:
        print("====== EMAIL NOTIFICATION ======")
        print(f"To: {to_email}")
        print(f"Subject: {subject}")
        print(body)
        print("================================")
        print("Set SMTP_EMAIL and SMTP_PASSWORD in .env to send real emails.")
        return

    try:
        msg = MIMEMultipart()
        msg['From'] = smtp_user
        msg['To'] = to_email
        msg['Subject'] = subject
        msg.attach(MIMEText(body, 'plain'))
        
        server = smtplib.SMTP(smtp_server, smtp_port)
        server.starttls()
        server.login(smtp_user, smtp_password)
        server.send_message(msg)
        server.quit()
        print(f"Email sent successfully to {to_email}")
    except Exception as e:
        print(f"Failed to send email to {to_email}: {str(e)}")
