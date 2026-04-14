"""
TimesFM adapter for AI Model Team
TimesFM 2.5: Google's time series foundation model (200M params)
"""
import sys, os, requests, pandas as pd, numpy as np
from typing import Dict

AI_MODEL_TEAM_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
VENV_PYTHON = os.path.join(AI_MODEL_TEAM_DIR, ".venv", "bin", "python3")

# TimesFM uses its own venv with torch
TIMESFM_AVAILABLE = False
try:
    import subprocess
    result = subprocess.run(
        [VENV_PYTHON, "-c", 
         "from timesfm import TimesFM_2p5_200M_torch; print('ok')"],
        capture_output=True, text=True, timeout=10,
        env={**os.environ, "PYTHONPATH": ""}
    )
    if result.returncode == 0 and "ok" in result.stdout:
        TIMESFM_AVAILABLE = True
except:
    pass

OKX_BASE = "https://www.okx.com/api/v5"

def get_klines(symbol: str, bar: str = "4H", limit: int = 500) -> pd.DataFrame:
    for inst in [symbol, f"{symbol}-SWAP"]:
        url = f"{OKX_BASE}/market/history-candles"
        r = requests.get(url, params={"instId": inst, "bar": bar, "limit": limit}, timeout=30)
        d = r.json()
        if d.get("code") == "0" and d.get("data"):
            cols = ["ts", "open", "high", "low", "close", "vol", "vol2", "vol3", "confirm"]
            df = pd.DataFrame(d["data"], columns=cols)
            for c in ["open", "high", "low", "close", "vol"]:
                df[c] = pd.to_numeric(df[c])
            df["ts"] = pd.to_datetime(df["ts"].astype(float), unit="ms")
            return df.sort_values("ts").reset_index(drop=True)
    raise ValueError(f"Cannot fetch data for {symbol}")


MODEL_CONFIGS = {
    "timesfm-2.5-200m": {
        "hf": "google/timesfm-2.5-200m-pytorch", "params": "200M",
        "institution": "Google", "desc": "TimesFM 2.5 200M"
    },
}


class TimesFMAdapter:
    """TimesFM 2.5 Google time series model"""
    _model = None

    name = "TimesFM-2.5-200M"
    institution = "Google"
    params = "200M"
    specialty = "通用时序/上下文16k"
    hf_name = "google/timesfm-2.5-200m-pytorch"

    @classmethod
    def load(cls):
        if cls._model is None:
            import subprocess, sys
            # Load within venv
            code = """
import sys
sys.path.insert(0, '/Users/yirongcao/.agents/skills/ai-model-team/.venv/lib/python3.14/site-packages')
from timesfm import TimesFM_2p5_200M_torch
model = TimesFM_2p5_200M_torch.from_pretrained('google/timesfm-2.5-200m-pytorch')
print('MODEL_LOADED')
"""
            result = subprocess.run(
                [cls._get_venv_python(), "-c", code],
                capture_output=True, text=True, timeout=120,
                cwd="/Users/yirongcao/.agents/skills/ai-model-team"
            )
            if result.returncode != 0:
                raise RuntimeError(f"TimesFM load failed: {result.stderr[-500:]}")
            cls._model = True  # Model loaded in subprocess, we use it via forecast
        return cls._model

    @staticmethod
    def _get_venv_python():
        venv = "/Users/yirongcao/.agents/skills/ai-model-team/.venv/bin/python3"
        if os.path.exists(venv):
            return venv
        return "python3"

    def predict(self, symbol: str, bar: str = "4H",
                 lookback: int = 512, pred_len: int = 24) -> Dict:
        """Run TimesFM prediction using venv subprocess"""
        import subprocess, json, sys

        code = f"""
import sys, os, json
sys.path.insert(0, '/Users/yirongcao/.agents/skills/ai-model-team/.venv/lib/python3.14/site-packages')
os.environ['HF_HOME'] = '/Users/yirongcao/.cache/huggingface'
os.environ['TRANSFORMERS_CACHE'] = '/Users/yirongcao/.cache/huggingface'

import numpy as np
import pandas as pd
from datetime import timedelta
import requests
from timesfm import TimesFM_2p5_200M_torch

OKX_BASE = "https://www.okx.com/api/v5"

def get_klines(symbol, bar="4H", limit=500):
    for inst in [symbol, f"{{symbol}}-SWAP"]:
        url = f"{{OKX_BASE}}/market/history-candles"
        r = requests.get(url, params={{"instId": inst, "bar": bar, "limit": limit}}, timeout=30)
        d = r.json()
        if d.get("code") == "0" and d.get("data"):
            cols = ["ts", "open", "high", "low", "close", "vol", "vol2", "vol3", "confirm"]
            df = pd.DataFrame(d["data"], columns=cols)
            for c in ["open", "high", "low", "close", "vol"]:
                df[c] = pd.to_numeric(df[c])
            df["ts"] = pd.to_datetime(df["ts"].astype(float), unit="ms")
            return df.sort_values("ts").reset_index(drop=True)
    raise ValueError(f"Cannot fetch {{symbol}}")

try:
    # Load model
    tfm = TimesFM_2p5_200M_torch.from_pretrained('google/timesfm-2.5-200m-pytorch')
    
    # Get data
    df = get_klines('{symbol}', bar='{bar}', limit={lookback + pred_len})
    prices = df['close'].values[-{lookback}:].astype(np.float32)
    cur = float(prices[-1])
    
    # Frequency mapping: 4H=6, 1H=5, 1D=7
    freq_map = {{"1m": 1, "5m": 2, "15m": 3, "30m": 4, "1H": 5, "4H": 6, "1D": 7}}
    freq = freq_map.get('{bar}', 6)
    
    # Forecast
    forecast = tfm.forecast(horizon={pred_len}, inputs=[prices])
    # forecast returns (mean, std) per horizon point
    fcast = forecast[0][:, 0]  # mean forecast
    
    avg_fcast = float(np.mean(fcast))
    pct = (avg_fcast / cur - 1) * 100
    
    if pct > 2:
        direction, conf = "bullish", min(95, 50 + abs(pct) * 3)
    elif pct < -2:
        direction, conf = "bearish", min(95, 50 + abs(pct) * 3)
    else:
        direction, conf = "neutral", 50
    
    up = sum(1 for p in fcast if p > cur)
    trend = abs(up / len(fcast) - 0.5) * 200
    
    result = {{
        "signal": direction,
        "confidence": round(conf, 1),
        "trend_strength": round(float(trend), 1),
        "current_price": cur,
        "forecast_price": round(avg_fcast, 2),
        "price_change_pct": round(pct, 2),
        "forecast_low": round(float(np.min(fcast)), 2),
        "forecast_high": round(float(np.max(fcast)), 2),
        "up_bars": int(up),
        "total_bars": int(len(fcast)),
        "reasoning": f"TimesFM预测: ${{cur:.2f}}→${{avg_fcast:.2f}} ({{pct:+.2f}}%), 趋势强度{{trend:.0f}}/100"
    }}
    print("RESULT:" + json.dumps(result))
except Exception as e:
    import traceback
    print(f"ERROR:{{str(e)}}\n{{traceback.format_exc()}}")
"""

        try:
            result = subprocess.run(
                [self._get_venv_python(), "-c", code],
                capture_output=True, text=True, timeout=300,
                cwd="/Users/yirongcao/.agents/skills/ai-model-team"
            )
            output = result.stdout + result.stderr
            
            if "RESULT:" in output:
                json_str = output.split("RESULT:")[1].strip()
                r = json.loads(json_str)
            else:
                return self._error_result(output[-500:])
        except subprocess.TimeoutExpired:
            return self._error_result("TimesFM prediction timed out (>5min)")
        except Exception as e:
            return self._error_result(str(e)[:200])

        return {
            "model": self.name, "institution": self.institution,
            "params": self.params, "specialty": self.specialty,
            **r
        }

    def _error_result(self, msg: str) -> Dict:
        return {
            "model": self.name, "institution": self.institution,
            "params": self.params, "specialty": self.specialty,
            "signal": "neutral", "confidence": 30,
            "trend_strength": 0, "current_price": 0, "forecast_price": 0,
            "price_change_pct": 0, "forecast_low": 0, "forecast_high": 0,
            "up_bars": 0, "total_bars": 0,
            "reasoning": f"TimesFM加载/预测失败: {str(msg)[:120]}"
        }
