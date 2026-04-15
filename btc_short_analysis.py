#!/usr/bin/env python3
"""
BTC 快速分析脚本 — 三模型协同预测
Kronos + Chronos-2 + TimesFM 三大AI模型对OKX BTC进行多角度分析
"""
import os, sys

# 使用环境变量或默认路径
AI_HEDGE = os.environ.get('AI_HEDGE_PATH', os.path.join(os.path.expanduser('~'), '.agents/skills/ai-hedge-fund-skill'))
AI_MODEL_TEAM_DIR = os.path.dirname(os.path.abspath(__file__)) if '__file__' in dir() else os.getcwd()
VENV_PYTHON = os.path.join(AI_MODEL_TEAM_DIR, ".venv", "bin", "python3")

# 信号阈值配置（可调）
BULLISH_THRESHOLD = 2.0
BEARISH_THRESHOLD = -2.0

# 路径配置
VENV_SITE_PACKAGES = os.path.join(AI_MODEL_TEAM_DIR, ".venv", "lib", "python3.14", "site-packages")
HF_CACHE = os.path.join(os.path.expanduser("~"), ".cache", "huggingface")


def get_cur_price(symbol="BTC-USDT-SWAP"):
    """获取当前价格"""
    import requests
    url = "https://www.okx.com/api/v5/market/history-candles"
    try:
        r = requests.get(url, params={"instId": symbol, "bar": "4H", "limit": 5}, timeout=30)
        r.raise_for_status()
        d = r.json()
        if d.get("code") == "0" and d.get("data"):
            return float(d["data"][-1][4])
    except:
        pass
    return None


def run_timesfm(prices, cur_price):
    """运行 TimesFM 预测"""
    print('🔮 TimesFM-2.5-200M 预测中...')
    code = f"""
import sys
sys.path.insert(0, '{VENV_SITE_PACKAGES}')
import numpy as np
from timesfm import TimesFM_2p5_200M_torch, ForecastConfig

tfm = TimesFM_2p5_200M_torch.from_pretrained('google/timesfm-2.5-200m-pytorch')
fc = ForecastConfig(max_context=512, max_horizon=128, per_core_batch_size=4)
tfm.compile(forecast_config=fc)
fcast = tfm.forecast(horizon=24, inputs=[prices])[0][0]
avg_f = float(np.mean(fcast))
pct = (avg_f / {cur_price} - 1) * 100
direction = 'bullish' if pct > {BULLISH_THRESHOLD} else 'bearish' if pct < {BEARISH_THRESHOLD} else 'neutral'
up = sum(1 for p in fcast if p > {cur_price})
print(f"RESULT:tfm:{{direction}}:{{pct:.2f}}:{{avg_f:.2f}}:{{up}}")
"""
    import subprocess
    result = subprocess.run([VENV_PYTHON, "-c", code], capture_output=True, text=True, timeout=300)
    for line in result.stdout.strip().split("\n"):
        if line.startswith("RESULT:tfm:"):
            _, direction, pct, avg, up = line.split(":")
            print(f'   预测24周期均价: ${float(avg):,.2f} ({float(pct):+.2f}%)')
            print(f'   信号: {direction.upper()}')
            return {"direction": direction, "pct": float(pct), "avg": float(avg), "up": int(up)}
    print(f'   ❌ TimesFM 预测失败')
    return None


def run_chronos(prices, cur_price):
    """运行 Chronos-2 预测"""
    print('📊 Chronos-2 预测中...')
    code = f"""
import sys
sys.path.insert(0, '{VENV_SITE_PACKAGES}')
import numpy as np
import torch
from chronos import Chronos2Pipeline

pipeline = Chronos2Pipeline.from_pretrained('amazon/chronos-2', device_map='cpu', dtype=torch.float32)
context = torch.tensor(prices[-512:], dtype=torch.float32)
forecast = pipeline.predict([context], prediction_length=24)
# chronos-2 returns shape: (batch=1, n_quantiles=21, pred_len=24)
forecast_arr = forecast[0].cpu().numpy()  # (1, 21, 24)
median_fcast = np.median(forecast_arr[0], axis=1).flatten()  # median across quantiles -> (24,)
fcast = median_fcast.flatten()
avg_f = float(np.mean(fcast))
pct = (avg_f / {cur_price} - 1) * 100
direction = 'bullish' if pct > {BULLISH_THRESHOLD} else 'bearish' if pct < {BEARISH_THRESHOLD} else 'neutral'
up = sum(1 for p in fcast if p > {cur_price})
print(f"RESULT:chr:{{direction}}:{{pct:.2f}}:{{avg_f:.2f}}:{{up}}")
"""
    import subprocess
    result = subprocess.run([VENV_PYTHON, "-c", code], capture_output=True, text=True, timeout=600)
    for line in result.stdout.strip().split("\n"):
        if line.startswith("RESULT:chr:"):
            _, direction, pct, avg, up = line.split(":")
            print(f'   预测24周期均价: ${float(avg):,.2f} ({float(pct):+.2f}%)')
            print(f'   信号: {direction.upper()}')
            return {"direction": direction, "pct": float(pct), "avg": float(avg), "up": int(up)}
    print(f'   ❌ Chronos 预测失败')
    return None


def run_kronos(symbol, lookback, pred_len):
    """运行 Kronos 预测"""
    print('🎯 Kronos 预测中...')
    sys.path.insert(0, f'{AI_HEDGE}/Kronos')
    sys.path.insert(0, AI_HEDGE)
    try:
        from kronos_distilled import forecast_with_kronos
        kr = forecast_with_kronos(symbol, lookback=lookback, pred_len=pred_len)
        direction = kr.forecast_direction
        pct = kr.key_metrics['price_change_pct']
        print(f'   预测涨跌: {pct:+.2f}%')
        print(f'   信号: {direction.upper()}')
        return {"direction": direction, "pct": pct}
    except Exception as e:
        print(f'   ❌ Kronos 预测失败: {e}')
        return None


def fuse_signals(results):
    """三模型投票融合"""
    # 统计信号
    bullish = sum(1 for r in results if r and r.get("direction") == "bullish")
    bearish = sum(1 for r in results if r and r.get("direction") == "bearish")
    neutral = sum(1 for r in results if r and r.get("direction") == "neutral")
    total = len(results)

    # 加权投票（等权重）
    if bullish >= 2:
        fused = "bullish"
        confidence = 90 if bullish == 3 else 75
    elif bearish >= 2:
        fused = "bearish"
        confidence = 90 if bearish == 3 else 75
    elif bullish > bearish:
        fused = "bullish"
        confidence = 60
    elif bearish > bullish:
        fused = "bearish"
        confidence = 60
    else:
        fused = "neutral"
        confidence = 50

    return {
        "signal": fused,
        "confidence": confidence,
        "bullish": bullish,
        "bearish": bearish,
        "neutral": neutral,
        "total": total
    }


def main():
    print('='*55)
    print('  🤖 BTC AI三模型协同预测 — TimesFM + Chronos-2 + Kronos')
    print('='*55)
    print()

    # 获取当前价格
    cur_price = get_cur_price()
    if cur_price is None:
        print('❌ 无法获取当前价格')
        sys.exit(1)
    print(f'📈 当前 BTC 价格: ${cur_price:,.2f}')
    print()

    # 获取K线数据（用于TimesFM和Chronos）
    import requests, pandas as pd
    url = 'https://www.okx.com/api/v5/market/history-candles'
    try:
        r = requests.get(url, params={'instId': 'BTC-USDT-SWAP', 'bar': '4H', 'limit': 300}, timeout=30)
        r.raise_for_status()
        data = r.json()
        if data.get('code') != '0' or not data.get('data'):
            raise ValueError(f"OKX API error")
        df = pd.DataFrame(data['data'], columns=['ts','open','high','low','close','vol','vol2','vol3','confirm'])
        df['close'] = pd.to_numeric(df['close'])
        prices = df['close'].values[-200:].astype("float32")
    except Exception as e:
        print(f'❌ 数据获取失败: {e}')
        sys.exit(1)

    results = {}

    # 1. TimesFM 预测
    tfm_result = run_timesfm(prices, cur_price)
    results["TimesFM"] = tfm_result

    # 2. Chronos-2 预测
    chr_result = run_chronos(prices, cur_price)
    results["Chronos-2"] = chr_result

    # 3. Kronos 预测
    kr_result = run_kronos('BTC-USDT-SWAP', lookback=200, pred_len=24)
    results["Kronos"] = kr_result

    # 融合信号
    fused = fuse_signals(results)

    # 输出结果
    print()
    print('='*55)
    print(f'📊 综合信号: {fused["signal"].upper()} (置信度: {fused["confidence"]}%)')
    print(f'📈 投票: 🟢{fused["bullish"]}  ⚪{fused["neutral"]}  🔴{fused["bearish"]}')
    print('='*55)

    # 各模型详情
    print()
    print('【各模型意见】')
    emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
    for name, r in results.items():
        if r:
            e = emoji.get(r.get("direction", "neutral"), "⚪")
            pct = r.get("pct", 0)
            print(f'  {e} {name}: {r.get("direction", "unknown")} ({pct:+.2f}%)')
        else:
            print(f'  ⚠️ {name}: 预测失败')

    print()
    print('⚠️ 仅供参考，不构成投资建议。')


if __name__ == "__main__":
    main()
