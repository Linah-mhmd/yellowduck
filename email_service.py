"""Email sending for verification and password reset."""
import logging
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

from config import Config

logger = logging.getLogger(__name__)


def _build_message(to_email: str, subject: str, html_body: str, text_body: str) -> MIMEMultipart:
    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = Config.MAIL_FROM
    msg['To'] = to_email
    msg.attach(MIMEText(text_body, 'plain', 'utf-8'))
    msg.attach(MIMEText(html_body, 'html', 'utf-8'))
    return msg


def send_email(to_email: str, subject: str, html_body: str, text_body: str) -> dict:
    """Send email via SMTP. In dev without SMTP, log link and return preview."""
    if not Config.SMTP_ENABLED:
        logger.info('DEV EMAIL → %s | %s', to_email, subject)
        logger.info('Body: %s', text_body)
        return {'sent': False, 'dev_mode': True, 'preview': text_body}

    try:
        msg = _build_message(to_email, subject, html_body, text_body)
        with smtplib.SMTP(Config.SMTP_HOST, Config.SMTP_PORT) as server:
            if Config.SMTP_USE_TLS:
                server.starttls()
            if Config.SMTP_USER and Config.SMTP_PASSWORD:
                server.login(Config.SMTP_USER, Config.SMTP_PASSWORD)
            server.sendmail(Config.MAIL_FROM, [to_email], msg.as_string())
        return {'sent': True}
    except Exception as e:
        logger.exception('Email send failed')
        return {'sent': False, 'error': str(e)}


def send_verification_email(to_email: str, name: str, link: str, lang: str = 'en') -> dict:
    if lang == 'ar':
        subject = 'Yellow Duck — تأكيد البريد الإلكتروني'
        text = f'مرحباً {name},\n\nاضغط على الرابط لتأكيد بريدك:\n{link}\n\nصالح لمدة 24 ساعة.'
        html = f'<p>مرحباً <strong>{name}</strong>,</p><p><a href="{link}">اضغط هنا لتأكيد بريدك</a></p>'
    else:
        subject = 'Yellow Duck — Verify your email'
        text = f'Hi {name},\n\nVerify your email:\n{link}\n\nValid for 24 hours.'
        html = f'<p>Hi <strong>{name}</strong>,</p><p><a href="{link}">Click here to verify your email</a></p>'
    return send_email(to_email, subject, html, text)


def send_reset_email(to_email: str, name: str, link: str, lang: str = 'en') -> dict:
    if lang == 'ar':
        subject = 'Yellow Duck — إعادة تعيين كلمة المرور'
        text = f'مرحباً {name},\n\nلإعادة تعيين كلمة المرور:\n{link}\n\nصالح لمدة ساعة واحدة.'
        html = f'<p>مرحباً <strong>{name}</strong>,</p><p><a href="{link}">إعادة تعيين كلمة المرور</a></p>'
    else:
        subject = 'Yellow Duck — Reset your password'
        text = f'Hi {name},\n\nReset your password:\n{link}\n\nValid for 1 hour.'
        html = f'<p>Hi <strong>{name}</strong>,</p><p><a href="{link}">Reset your password</a></p>'
    return send_email(to_email, subject, html, text)
