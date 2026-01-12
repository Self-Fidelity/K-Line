"""akshare 网络配置模块

用于配置 akshare 的 requests session，解决 SSL 连接问题
"""

import ssl
import os
import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib3.poolmanager import PoolManager
import urllib3

# 禁用 SSL 验证警告
urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)

from src.utils.logger import get_logger

logger = get_logger(__name__)


class SSLAdapter(HTTPAdapter):
    """自定义 SSL 适配器，用于处理 SSL 连接问题"""
    
    def init_poolmanager(self, *args, **kwargs):
        """初始化连接池管理器，配置 SSL 上下文"""
        # 创建不验证证书的 SSL 上下文
        context = ssl.create_default_context()
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        # 设置更宽松的协议选项
        # 允许所有 TLS 版本
        context.options |= ssl.OP_NO_SSLv2
        context.options |= ssl.OP_NO_SSLv3
        # 不验证主机名
        context.check_hostname = False
        context.verify_mode = ssl.CERT_NONE
        
        kwargs['ssl_context'] = context
        return super().init_poolmanager(*args, **kwargs)


def configure_requests_defaults():
    """
    配置 requests 库的默认行为
    
    解决 SSL 连接问题，包括：
    1. 设置合适的 User-Agent（模拟浏览器）
    2. 配置 SSL 上下文
    3. 添加重试机制
    4. 禁用 SSL 验证（作为临时解决方案）
    """
    try:
        # 方法1: 通过 monkey patch 修改 requests.Session 的默认行为
        _original_request = requests.Session.request
        _original_init = requests.Session.__init__
        
        def _patched_init(self, *args, **kwargs):
            """修改 Session 初始化，添加自定义适配器"""
            _original_init(self, *args, **kwargs)
            # 为所有新创建的 session 添加自定义 SSL 适配器
            adapter = SSLAdapter(max_retries=Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS", "POST"]
            ))
            self.mount("https://", adapter)
            self.mount("http://", adapter)
        
        def _patched_request(self, *args, **kwargs):
            """修改后的 request 方法，自动添加 SSL 配置和 User-Agent"""
            # 设置默认的 verify=False 来避免 SSL 错误
            if 'verify' not in kwargs:
                kwargs['verify'] = False
            
            # 设置默认超时
            if 'timeout' not in kwargs:
                kwargs['timeout'] = 30
            
            # 确保有 User-Agent
            if 'headers' not in kwargs:
                kwargs['headers'] = {}
            
            if 'User-Agent' not in kwargs['headers']:
                kwargs['headers']['User-Agent'] = (
                    'Mozilla/5.0 (Windows NT 10.0; Win64; x64) '
                    'AppleWebKit/537.36 (KHTML, like Gecko) '
                    'Chrome/120.0.0.0 Safari/537.36'
                )
            
            return _original_request(self, *args, **kwargs)
        
        # 应用 monkey patch
        requests.Session.__init__ = _patched_init
        requests.Session.request = _patched_request
        
        # 方法2: 修改 urllib3 的默认 PoolManager 行为
        # 创建自定义 SSL 上下文
        ssl_context = ssl.create_default_context()
        ssl_context.check_hostname = False
        ssl_context.verify_mode = ssl.CERT_NONE
        ssl_context.options |= ssl.OP_NO_SSLv2
        ssl_context.options |= ssl.OP_NO_SSLv3
        
        # Monkey patch urllib3 的 HTTPSConnectionPool
        _original_connection_from_url = urllib3.poolmanager.PoolManager.connection_from_url
        
        def _patched_connection_from_url(self, url, *args, **kw):
            """修改连接创建，添加 SSL 上下文"""
            if url.startswith('https://'):
                kw.setdefault('ssl_context', ssl_context)
            return _original_connection_from_url(self, url, *args, **kw)
        
        urllib3.poolmanager.PoolManager.connection_from_url = _patched_connection_from_url
        
        # 禁用 SSL 验证警告
        urllib3.disable_warnings(urllib3.exceptions.InsecureRequestWarning)
        
        # 方法3: 设置环境变量（作为后备）
        os.environ['PYTHONHTTPSVERIFY'] = '0'
        os.environ['CURL_CA_BUNDLE'] = ''
        os.environ['REQUESTS_CA_BUNDLE'] = ''
        
        logger.info("已配置 requests 和 urllib3 的默认 SSL 行为（包括适配器和 PoolManager）")
        
    except Exception as e:
        logger.error(f"配置 requests 默认行为失败: {e}", exc_info=True)
        # 作为后备方案，只设置环境变量
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
