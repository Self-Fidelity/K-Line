"""邮件通知服务

每日优化完成后发送买入信号邮件。
使用 Jinja2 模板渲染 HTML 邮件。
"""

from __future__ import annotations

import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime
from typing import List, Dict, Any

from jinja2 import Template

from backend.app.config import settings
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 简洁版邮件模板
EMAIL_TEMPLATE = Template("""
<!DOCTYPE html>
<html>
<head><meta charset="utf-8"></head>
<body style="font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; max-width: 600px; margin: 0 auto; padding: 20px; color: #333;">
  <h2 style="color: #409eff; border-bottom: 2px solid #409eff; padding-bottom: 10px;">
    📊 K-Line 每日信号推送 — {{ date }}
  </h2>

  <p style="color: #666;">今日扫描 <strong>{{ total_stocks }}</strong> 只自选股，发现 <strong style="color: #e6a23c;">{{ buy_count }}</strong> 个买入信号。</p>

  {% if buy_signals %}
  <table style="width: 100%; border-collapse: collapse; margin-top: 15px;">
    <thead>
      <tr style="background: #f5f7fa;">
        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">股票</th>
        <th style="padding: 10px; text-align: center; border-bottom: 2px solid #ddd;">得分</th>
        <th style="padding: 10px; text-align: left; border-bottom: 2px solid #ddd;">触发策略</th>
      </tr>
    </thead>
    <tbody>
    {% for s in buy_signals %}
      <tr style="border-bottom: 1px solid #eee;">
        <td style="padding: 10px;">
          <strong>{{ s.stock_code }}</strong>
          {% if s.stock_name %}<br><span style="color: #909399; font-size: 13px;">{{ s.stock_name }}</span>{% endif %}
        </td>
        <td style="padding: 10px; text-align: center;">
          <span style="background: {% if s.score >= 0.7 %}#f0f9eb{% elif s.score >= 0.5 %}#fdf6ec{% else %}#fef0f0{% endif %}; color: {% if s.score >= 0.7 %}#67c23a{% elif s.score >= 0.5 %}#e6a23c{% else %}#f56c6c{% endif %}; padding: 4px 10px; border-radius: 12px; font-weight: bold;">
            {{ "%.2f"|format(s.score) }}
          </span>
        </td>
        <td style="padding: 10px; font-size: 13px; color: #606266;">
          {{ s.strategies|join(", ") }}
        </td>
      </tr>
    {% endfor %}
    </tbody>
  </table>
  {% else %}
  <p style="color: #909399; padding: 20px; text-align: center;">今日无符合买入条件的信号。</p>
  {% endif %}

  {% if errors %}
  <div style="margin-top: 20px; padding: 10px; background: #fef0f0; border-radius: 6px; font-size: 13px; color: #f56c6c;">
    <strong>⚠ 处理异常 ({{ errors|length }}):</strong><br>
    {% for e in errors %}{{ e }}<br>{% endfor %}
  </div>
  {% endif %}

  <hr style="margin-top: 30px; border: none; border-top: 1px solid #eee;">
  <p style="color: #c0c4cc; font-size: 12px; text-align: center;">
    K-Line Daily 自动推送 · {{ datetime }}
  </p>
</body>
</html>
""")


class NotificationService:
    """邮件通知服务"""

    def __init__(self):
        self.smtp_host = settings.SMTP_HOST
        self.smtp_port = settings.SMTP_PORT
        self.smtp_user = settings.SMTP_USER
        self.smtp_password = settings.SMTP_PASSWORD
        self.smtp_use_tls = settings.SMTP_USE_TLS
        self.recipient = os.getenv("NOTIFY_EMAIL", settings.SMTP_USER)

    def send_buy_signal_email(
        self,
        buy_signals: List[Dict[str, Any]],
        total_stocks: int,
        errors: List[str] = None,
    ) -> bool:
        """
        发送买入信号邮件

        Args:
            buy_signals: [{stock_code, stock_name, score, strategies}, ...]
            total_stocks: 总扫描股票数
            errors: 处理异常列表

        Returns:
            是否发送成功
        """
        if not self.smtp_user or not self.smtp_password:
            logger.warning("SMTP 未配置，跳过邮件发送")
            return False

        now = datetime.now()
        html = EMAIL_TEMPLATE.render(
            date=now.strftime("%Y-%m-%d"),
            datetime=now.strftime("%Y-%m-%d %H:%M"),
            total_stocks=total_stocks,
            buy_count=len(buy_signals),
            buy_signals=buy_signals,
            errors=errors or [],
        )

        subject = f"K-Line 每日信号推送 — {now.strftime('%Y-%m-%d')}"
        return self._send_email(self.recipient, subject, html)

    def _send_email(self, to: str, subject: str, html: str) -> bool:
        """发送 HTML 邮件"""
        try:
            msg = MIMEMultipart("alternative")
            msg["Subject"] = subject
            msg["From"] = self.smtp_user
            msg["To"] = to
            msg.attach(MIMEText(html, "html", "utf-8"))

            if self.smtp_use_tls:
                server = smtplib.SMTP(self.smtp_host, self.smtp_port)
                server.starttls()
            else:
                server = smtplib.SMTP_SSL(self.smtp_host, self.smtp_port)

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.smtp_user, [to], msg.as_string())
            server.quit()

            logger.info(f"邮件已发送: {to}, 主题: {subject}")
            return True

        except Exception as e:
            logger.error(f"邮件发送失败: {e}")
            return False


import os
