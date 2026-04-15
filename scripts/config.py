"""
Configuration Module
P0: Centralized configuration management with all risk/signal/ensemble settings
"""
import os
import json
from pathlib import Path
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

# ============ Environment Configuration ============
APP_ENV = os.getenv("APP_ENV", "dev")  # dev/staging/prod
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# ============ Runtime Configuration ============
REQUEST_TIMEOUT_SEC = int(os.getenv("REQUEST_TIMEOUT_SEC", "20"))
MAX_RETRY = int(os.getenv("MAX_RETRY", "3"))
RETRY_BACKOFF_SEC = float(os.getenv("RETRY_BACKOFF_SEC", "0.5"))

# ============ Data Configuration ============
TIMEZONE = os.getenv("TIMEZONE", "UTC")
DATA_ALIGN_TOLERANCE_SEC = int(os.getenv("DATA_ALIGN_TOLERANCE_SEC", "60"))
MIN_DATA_COMPLETENESS = float(os.getenv("MIN_DATA_COMPLETENESS", "0.98"))
MAX_DATA_STALENESS_SEC = int(os.getenv("MAX_DATA_STALENESS_SEC", "120"))

# ============ Risk Configuration ============
ENABLE_RISK_GATE = os.getenv("ENABLE_RISK_GATE", "true").lower() == "true"
MAX_POSITION_PCT = float(os.getenv("MAX_POSITION_PCT", "0.10"))
MAX_LEVERAGE = float(os.getenv("MAX_LEVERAGE", "2.0"))
STOP_LOSS_PCT = float(os.getenv("STOP_LOSS_PCT", "0.02"))
TAKE_PROFIT_PCT = float(os.getenv("TAKE_PROFIT_PCT", "0.04"))
MAX_DAILY_DRAWDOWN_PCT = float(os.getenv("MAX_DAILY_DRAWDOWN_PCT", "0.03"))
MAX_CONSECUTIVE_LOSSES = int(os.getenv("MAX_CONSECUTIVE_LOSSES", "4"))
COOLDOWN_MINUTES = int(os.getenv("COOLDOWN_MINUTES", "60"))

# ============ Signal Configuration ============
MIN_SIGNAL_CONFIDENCE = float(os.getenv("MIN_SIGNAL_CONFIDENCE", "0.60"))
BULLISH_THRESHOLD = float(os.getenv("BULLISH_THRESHOLD", "0.65"))
BEARISH_THRESHOLD = float(os.getenv("BEARISH_THRESHOLD", "0.35"))

# ============ Ensemble Configuration ============
ENSEMBLE_MODE = os.getenv("ENSEMBLE_MODE", "dynamic_weighted")  # vote/weighted/dynamic_weighted
WEIGHT_KRONOS = float(os.getenv("WEIGHT_KRONOS", "0.30"))
WEIGHT_CHRONOS2 = float(os.getenv("WEIGHT_CHRONOS2", "0.25"))
WEIGHT_TIMESFM = float(os.getenv("WEIGHT_TIMESFM", "0.25"))
WEIGHT_FINBERT = float(os.getenv("WEIGHT_FINBERT", "0.20"))
CALIBRATION_METHOD = os.getenv("CALIBRATION_METHOD", "isotonic")

# ============ Sentiment Configuration ============
SENTIMENT_ENABLE = os.getenv("SENTIMENT_ENABLE", "true").lower() == "true"
SENTIMENT_HALF_LIFE_MIN = int(os.getenv("SENTIMENT_HALF_LIFE_MIN", "180"))
SENTIMENT_MIN_SOURCES = int(os.getenv("SENTIMENT_MIN_SOURCES", "2"))
SENTIMENT_SOURCE_WEIGHTS = json.loads(os.getenv("SENTIMENT_SOURCE_WEIGHTS", 
    '{"news":0.5,"reddit":0.3,"rss":0.2}'))
SENTIMENT_SPAM_FILTER = os.getenv("SENTIMENT_SPAM_FILTER", "true").lower() == "true"

# ============ Execution Configuration ============
ORDER_TYPE_DEFAULT = os.getenv("ORDER_TYPE_DEFAULT", "limit")
SLIPPAGE_BPS = int(os.getenv("SLIPPAGE_BPS", "8"))
FEE_BPS = int(os.getenv("FEE_BPS", "10"))
MAX_ORDER_SPLITS = int(os.getenv("MAX_ORDER_SPLITS", "3"))

# ============ Observability Configuration ============
METRICS_ENABLE = os.getenv("METRICS_ENABLE", "true").lower() == "true"
ALERT_WEBHOOK = os.getenv("ALERT_WEBHOOK", "")
TRACE_SAMPLE_RATE = float(os.getenv("TRACE_SAMPLE_RATE", "0.10"))

# ============ Security Configuration ============
MASK_SENSITIVE_LOGS = os.getenv("MASK_SENSITIVE_LOGS", "true").lower() == "true"
ALLOW_WITHDRAWAL = os.getenv("ALLOW_WITHDRAWAL", "false").lower() == "true"

# ============ Release Configuration ============
MODEL_VERSION_PIN = os.getenv("MODEL_VERSION_PIN", "v2.0.0")
FEATURE_FLAGS = json.loads(os.getenv("FEATURE_FLAGS", "{}"))

# ============ Path Configuration ============
AI_HEDGE_PATH = os.environ.get('AI_HEDGE_PATH', 
    os.path.join(os.path.expanduser('~'), '.agents/skills/ai-hedge-fund-skill'))

# Model directories
KRONOS_MODEL_DIR = f"{AI_HEDGE_PATH}/models/kronos-base"
KRONOS_TOKENIZER_DIR = f"{AI_HEDGE_PATH}/models/kronos-tokenizer"

# Venv paths
AI_MODEL_TEAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(AI_MODEL_TEAM_DIR, ".venv", "bin", "python3")
VENV_SITE_PACKAGES = os.path.join(AI_MODEL_TEAM_DIR, ".venv", "lib", "python3.14", "site-packages")
HF_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")

# ============ Config Validation ============
def validate_config() -> Dict[str, Any]:
    """验证配置完整性"""
    errors = []
    warnings = []
    
    # Validate ranges
    if not (0 < MAX_POSITION_PCT <= 1):
        errors.append(f"MAX_POSITION_PCT must be 0-1, got {MAX_POSITION_PCT}")
    
    if not (0 < STOP_LOSS_PCT <= 1):
        errors.append(f"STOP_LOSS_PCT must be 0-1, got {STOP_LOSS_PCT}")
    
    if not (0 <= MIN_SIGNAL_CONFIDENCE <= 1):
        errors.append(f"MIN_SIGNAL_CONFIDENCE must be 0-1, got {MIN_SIGNAL_CONFIDENCE}")
    
    # Validate weights sum
    total_weight = WEIGHT_KRONOS + WEIGHT_CHRONOS2 + WEIGHT_TIMESFM + WEIGHT_FINBERT
    if abs(total_weight - 1.0) > 0.01:
        errors.append(f"Model weights must sum to 1.0, got {total_weight}")
    
    # Production checks
    if APP_ENV == "prod":
        if not MASK_SENSITIVE_LOGS:
            warnings.append("MASK_SENSITIVE_LOGS should be true in production")
        if ALLOW_WITHDRAWAL:
            errors.append("ALLOW_WITHDRAWAL must be false in production")
    
    return {
        "valid": len(errors) == 0,
        "errors": errors,
        "warnings": warnings
    }


def get_config_summary() -> Dict[str, Any]:
    """获取配置摘要"""
    return {
        "app_env": APP_ENV,
        "model_version": MODEL_VERSION_PIN,
        "risk_gate_enabled": ENABLE_RISK_GATE,
        "risk_limits": {
            "max_position_pct": MAX_POSITION_PCT,
            "stop_loss_pct": STOP_LOSS_PCT,
            "max_daily_drawdown_pct": MAX_DAILY_DRAWDOWN_PCT,
            "max_consecutive_losses": MAX_CONSECUTIVE_LOSSES
        },
        "ensemble_weights": {
            "kronos": WEIGHT_KRONOS,
            "chronos2": WEIGHT_CHRONOS2,
            "timesfm": WEIGHT_TIMESFM,
            "finbert": WEIGHT_FINBERT
        },
        "sentiment_enabled": SENTIMENT_ENABLE,
        "observability": {
            "metrics_enabled": METRICS_ENABLE,
            "alert_webhook_configured": bool(ALERT_WEBHOOK)
        }
    }


# ============ Environment File Loading ============
def load_env_file():
    """加载 .env 文件"""
    env_path = Path(__file__).parent.parent / '.env'
    if env_path.exists():
        with open(env_path) as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ.setdefault(key, value)


# Load .env on import
load_env_file()

# Export for convenience
BULLISH_THRESHOLD_CFG = BULLISH_THRESHOLD
BEARISH_THRESHOLD_CFG = BEARISH_THRESHOLD
