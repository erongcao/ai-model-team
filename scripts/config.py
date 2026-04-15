"""
配置管理模块 - 加载环境变量和API密钥
"""
import os
from pathlib import Path
from dotenv import load_dotenv

# 加载 .env 文件
env_path = Path(__file__).parent.parent / '.env'
if env_path.exists():
    load_dotenv(env_path)

class Config:
    """配置类"""
    # OKX API 配置
    OKX_API_KEY = os.getenv('OKX_API_KEY', '')
    OKX_SECRET_KEY = os.getenv('OKX_SECRET_KEY', '')
    OKX_API_PASSWORD = os.getenv('OKX_API_PASSWORD', '')
    
    # 是否使用 API 认证（有密钥时启用更多功能）
    USE_API_AUTH = bool(OKX_API_KEY and OKX_SECRET_KEY)
    
    # 信号阈值
    BULLISH_THRESHOLD = 2.0
    BEARISH_THRESHOLD = -2.0
    
    # 模型路径
    AI_HEDGE_PATH = os.environ.get('AI_HEDGE_PATH', 
        os.path.join(os.path.expanduser('~'), '.agents/skills/ai-hedge-fund-skill'))

# 向后兼容
BULLISH_THRESHOLD = Config.BULLISH_THRESHOLD
BEARISH_THRESHOLD = Config.BEARISH_THRESHOLD
