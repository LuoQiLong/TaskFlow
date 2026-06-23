import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from ..config import SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD, SMTP_FROM_NAME


def send_reset_email(to_email: str, reset_token: str):
    """Send a password reset email with the reset token."""
    subject = f"[{SMTP_FROM_NAME}] 密码重置码"
    body = f"""<div style="max-width:480px;margin:0 auto;font-family:Arial,sans-serif;padding:24px">
  <h2 style="color:#6366f1">TaskFlow 密码重置</h2>
  <p>您好，您正在请求重置 TaskFlow 账号密码。</p>
  <p>您的重置码（15分钟内有效）：</p>
  <div style="background:#f5f3ff;border:1px solid #ddd6fe;border-radius:8px;padding:16px;text-align:center;margin:16px 0">
    <span style="font-size:22px;font-weight:700;font-family:monospace;color:#4c1d95;word-break:break-all">{reset_token}</span>
  </div>
  <p style="color:#6b7280;font-size:13px">如果您没有请求重置密码，请忽略此邮件。</p>
</div>"""

    msg = MIMEMultipart()
    msg["From"] = f"{SMTP_FROM_NAME} <{SMTP_USER}>"
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.attach(MIMEText(body, "html", "utf-8"))

    with smtplib.SMTP(SMTP_HOST, SMTP_PORT) as server:
        server.starttls()
        server.login(SMTP_USER, SMTP_PASSWORD)
        server.send_message(msg)
