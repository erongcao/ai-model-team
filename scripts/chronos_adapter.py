"""
Chronos adapter for AI Model Team
Chronos: Amazon's T5-based time series foundation model
"""
import sys, os, requests, pandas as pd, numpy as np
from datetime import timedelta
from typing import Dict

AI_HEDGE_FUND = "/Users/yirongcao/.agents/skills/ai-hedge-fund-skill"
sys.path.insert(0, f"{AI_HEDGE_FUND}")

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
            df = df.sort_values("ts").reset_index(drop=True)
            return df
    raise ValueError(f"Cannot fetch data for {symbol}")

MODEL_CONFIGS = {
    "chronos-t5-small": {
        "hf": "amazon/chronos-t5-small", "params": "~20M",
        "institution": "Amazon", "desc": "Chronos T5 Small (轻量通用)"
    },
    "chronos-t5-base": {
        "hf": "amazon/chronos-t5-base", "params": "~100M",
        "institution": "Amazon", "desc": "Chronos T5 Base (通用)"
    },
}


class ChronosAdapter:
    """Chronos T5-based time series model"""
    _models = {}

    def __init__(self, variant: str = "chronos-t5-base"):
        self.variant = variant
        cfg = MODEL_CONFIGS.get(variant, MODEL_CONFIGS["chronos-t5-base"])
        self.name = cfg["hf"].split("/")[1]
        self.institution = cfg["institution"]
        self.params = cfg["params"]
        self.hf_name = cfg["hf"]
        self.specialty = "通用时序"
        self._pipeline = None

    def load(self):
        if self.variant not in ChronosAdapter._models:
            from chronos import ChronosPipeline
            ChronosAdapter._models[self.variant] = ChronosPipeline.from_pretrained(
                self.hf_name,
                torch_dtype=torch.bfloat16 if torch.cuda.is_available() else torch.float32,
            )
        return ChronosAdapter._models[self.variant]

    def predict(self, symbol: str, bar: str = "4H",
                 lookback: int = 128,  # Chronos recommended lookback
                 pred_len: int = 24) -> Dict:
        import torch
        # Ensure torch is available in this context
        try:
            from chronos import ChronosPipeline
        except ImportError:
            return self._error_result("chronos not installed")

        pipeline = self.load()
        df = get_klines(symbol, bar=bar, limit=lookback + pred_len + 50)
        df = df.tail(lookback + pred_len).reset_index(drop=True)

        # Normalize to per-minute for Chronos
        # Chronos expects (N,) context, we'll use closing prices
        context = df["close"].values[-lookback:].tolist()

        # Chronos context preparation
        context_window = context[-lookback:]

        try:
            # Chronos prediction
            forecast = pipeline.predict(context_window, prediction_length=pred_len)
            forecast_samples = forecast[0]  # shape: (n_samples, pred_len)

            # Use median forecast
            median_fcast = np.median(forecast_samples, axis=0)
            mean_fcast = np.mean(forecast_samples, axis=0)

            cur = float(df["close"].iloc[-1])
            avg_fcast = float(np.mean(median_fcast))
            pct = (avg_fcast / cur - 1) * 100

            # Confidence from spread
            std = float(np.std(forecast_samples))
            conf_from_spread = max(30, min(95, 100 - std / cur * 500))

            if pct > 2:
                direction, conf = "bullish", min(95, 50 + abs(pct) * 3)
            elif pct < -2:
                direction, conf = "bearish", min(95, 50 + abs(pct) * 3)
            else:
                direction, conf = "neutral", 50

            up = sum(1 for p in median_fcast if p > cur)
            trend = abs(up / len(median_fcast) - 0.5) * 200

            return {
                "model": self.name, "institution": self.institution,
                "params": self.params, "specialty": self.specialty,
                "signal": direction, "confidence": round(conf, 1),
                "trend_strength": round(float(trend), 1),
                "current_price": cur,
                "forecast_price": round(avg_fcast, 2),
                "price_change_pct": round(pct, 2),
                "forecast_low": round(float(np.min(median_fcast)), 2),
                "forecast_high": round(float(np.max(median_fcast)), 2),
                "up_bars": int(up), "total_bars": int(len(median_fcast)),
                "reasoning": f"Chronos({self.name})预测: ${cur:.2f}→${avg_fcast:.2f} ({pct:+.2f}%), "
                             f"趋势强度{trend:.0f}/100, 样本数:{forecast_samples.shape[0]}"
            }
        except Exception as e:
            return self._error_result(str(e))

    def _error_result(self, msg):
        return {
            "model": self.name, "institution": self.institution,
            "params": self.params, "specialty": self.specialty,
            "signal": "neutral", "confidence": 30,
            "trend_strength": 0, "current_price": 0, "forecast_price": 0,
            "price_change_pct": 0, "forecast_low": 0, "forecast_high": 0,
            "up_bars": 0, "total_bars": 0,
            "reasoning": f"Chronos预测出错: {str(msg)}"
        }
