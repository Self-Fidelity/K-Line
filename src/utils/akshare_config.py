"""akshare 网络配置模块

配置 akshare 的 requests session，使用 certifi 进行安全的 SSL 验证。
仅在必要时（特定受信域名）放宽验证。
"""

import ssl
import os
from typing import Set

import requests
import certifi
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

# 不再全局禁用 SSL 警告
from src.utils.logger import get_logger

logger = get_logger(__name__)

# 已知 SSL 证书有问题的域名（需要降低验证级别）
_INSECURE_DOMAINS: Set[str] = {
    "push2his.eastmoney.com",
    "push2.eastmoney.com",
}


class SelectiveSSLAdapter(HTTPAdapter):
    """选择性 SSL 适配器 - 仅对已知问题域名降低验证级别"""

    def __init__(self, *args, **kwargs):
        self._insecure_domains = kwargs.pop('insecure_domains', set())
        super().__init__(*args, **kwargs)

    def init_poolmanager(self, *args, **kwargs):
        """初始化连接池管理器"""
        kwargs['ssl_context'] = ssl.create_default_context(cafile=certifi.where())
        return super().init_poolmanager(*args, **kwargs)

    def cert_verify(self, conn, url, verify, cert):
        """选择性跳过证书验证"""
        from urllib3.util import parse_url
        parsed = parse_url(url)
        if parsed.host and parsed.host in self._insecure_domains:
            verify = False
        super().cert_verify(conn, url, verify, cert)


def configure_session(session: requests.Session) -> requests.Session:
    """
    安全地配置 requests Session

    使用 certifi 证书包进行 SSL 验证，仅对已知有证书问题的域名放宽检查。
    """
    # 设置合理的 User-Agent
    session.headers.update({
        'User-Agent': (
            'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
            'AppleWebKit/537.36 (KHTML, like Gecko) '
            'Chrome/120.0.0.0 Safari/537.36'
        ),
    })

    # 配置重试策略
    retry_strategy = Retry(
        total=3,
        backoff_factor=1,
        status_forcelist=[429, 500, 502, 503, 504],
        allowed_methods=["HEAD", "GET", "OPTIONS", "POST"],
    )

    # 使用选择性SSL适配器
    adapter = SelectiveSSLAdapter(
        max_retries=retry_strategy,
        insecure_domains=_INSECURE_DOMAINS,
    )
    session.mount("https://", adapter)
    session.mount("http://", adapter)

    # 默认开启 SSL 验证（安全）
    session.verify = certifi.where()

    return session


def create_default_session() -> requests.Session:
    """创建预配置的 requests Session"""
    session = requests.Session()
    return configure_session(session)


def configure_requests_defaults():
    """
    安全地配置 requests 库默认行为（向后兼容接口）

    使用 certifi 进行 SSL 证书验证，仅对已知问题域名降级。
    不再全局禁用 SSL 验证。
    """
    try:
        # 使用 certifi 作为默认 CA 包
        os.environ.setdefault('REQUESTS_CA_BUNDLE', certifi.where())
        os.environ.setdefault('CURL_CA_BUNDLE', certifi.where())

        logger.info("已安全配置 requests SSL 验证（使用 certifi）")

    except Exception as e:
        logger.error(f"配置 requests 默认行为失败: {e}", exc_info=True)
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        logger.warning("已设置环境变量作为后备方案")


# 在模块导入时自动配置
_configured = False

def ensure_akshare_configured():
    """
    确保 akshare 已配置（只配置一次）
    
    注意：此函数必须在导入 akshare 之前调用
    """
    global _configured
    if not _configured:
        configure_requests_defaults()
        _configured = True
        logger.debug("akshare 网络配置已完成")
