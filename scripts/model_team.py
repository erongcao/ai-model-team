#!/usr/bin/env python3
"""
AI Model Prediction Team
=======================
Multi-model协同预测系统：Kronos + Chronos + TimesFM + MOIRAI
对OKX加密货币进行多角度AI预测，输出综合意见

Usage:
  python3 model_team.py BTC-USDT-SWAP --signal-only
  python3 model_team.py CL-USDT-SWAP --models kronos,chronos-base
  python3 model_team.py ETH-USDT-SWAP --full
"""

import sys, os, argparse, json
from datetime import datetime
from typing import List, Dict

# Add scripts dir to path
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, SCRIPT_DIR)

OKX_BASE = "https://www.okx.com/api/v5"


def get_klines(symbol: str, bar: str = "4H", limit: int = 200) -> Dict:
    """Fetch OKX K-line data"""
    import requests, pandas as pd
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
            return df.sort_values("ts").to_dict()
    return {}


def fuse_signals(results: List[Dict]) -> Dict:
    """投票融合多模型信号"""
    bullish = sum(1 for r in results if r["signal"] == "bullish")
    bearish = sum(1 for r in results if r["signal"] == "bearish")
    neutral = sum(1 for r in results if r["signal"] == "neutral")
    total = len(results)

    # 加权置信度
    avg_conf = sum(r["confidence"] for r in results) / total

    # 平均预测变化
    avg_pct = sum(r["price_change_pct"] for r in results) / total

    if bullish >= 3:
        fused = "bullish"
        conf = min(95, int(avg_conf * (bullish / total) * 1.2))
    elif bearish >= 3:
        fused = "bearish"
        conf = min(95, int(avg_conf * (bearish / total) * 1.2))
    elif bullish > bearish:
        fused = "bullish"
        conf = int(avg_conf * 0.8)
    elif bearish > bullish:
        fused = "bearish"
        conf = int(avg_conf * 0.8)
    else:
        fused = "neutral"
        conf = int(avg_conf * 0.7)

    # 共识支撑/阻力
    all_lows = [r["forecast_low"] for r in results if r["forecast_low"] > 0]
    all_highs = [r["forecast_high"] for r in results if r["forecast_high"] > 0]

    support = max(all_lows) if all_lows else 0
    resistance = min(all_highs) if all_highs else 0

    return {
        "signal": fused, "confidence": conf,
        "avg_price_change_pct": round(avg_pct, 2),
        "support": round(support, 2), "resistance": round(resistance, 2),
        "vote": f"{bullish}🔴 {neutral}⚪ {bearish}🟢",
        "details": {"bullish": bullish, "neutral": neutral, "bearish": bearish}
    }


def run_model(model_name: str, symbol: str, bar: str) -> Dict:
    """Run a single model and return result"""
    try:
        if model_name == "kronos":
            from kronos_adapter import KronosAdapter
            adapter = KronosAdapter()
            return adapter.predict(symbol, bar=bar, lookback=400, pred_len=24)
        elif model_name == "chronos-base":
            from chronos_adapter import ChronosAdapter
            adapter = ChronosAdapter("chronos-t5-base")
            return adapter.predict(symbol, bar=bar, lookback=128, pred_len=24)
        elif model_name == "chronos-small":
            from chronos_adapter import ChronosAdapter
            adapter = ChronosAdapter("chronos-t5-small")
            return adapter.predict(symbol, bar=bar, lookback=64, pred_len=24)
        elif model_name == "timesfm":
            from timesfm_adapter import TimesFMAdapter
            adapter = TimesFMAdapter("timesfm-2.5-200m")
            return adapter.predict(symbol, bar=bar, lookback=256, pred_len=24)
        elif model_name == "timesfm-fin":
            from timesfm_adapter import TimesFMAdapter
            adapter = TimesFMAdapter("timesfm-1.0-200m-fin")
            return adapter.predict(symbol, bar=bar, lookback=256, pred_len=24)
        elif model_name == "moirai":
            from moirai_adapter import MOIRAIAdapter
            adapter = MOIRAIAdapter()
            return adapter.predict(symbol, bar=bar, lookback=256, pred_len=24)
        else:
            return {
                "model": model_name, "signal": "neutral", "confidence": 30,
                "reasoning": f"Unknown model: {model_name}",
                "current_price": 0, "forecast_price": 0, "price_change_pct": 0
            }
    except Exception as e:
        return {
            "model": model_name, "signal": "neutral", "confidence": 30,
            "reasoning": f"Error: {str(e)[:100]}",
            "current_price": 0, "forecast_price": 0, "price_change_pct": 0,
            "trend_strength": 0, "forecast_low": 0, "forecast_high": 0,
            "up_bars": 0, "total_bars": 0
        }


def print_report(symbol: str, bar: str, results: List[Dict], fused: Dict, prices: Dict):
    """Print full team report"""
    emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
    f_emoji = emoji.get(fused["signal"], "⚪")

    print("=" * 62)
    print(f"🤖 AI 模型预测团队报告 — {symbol} ({bar})")
    print(f"   生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M')}")
    print("=" * 62)

    print(f"\n【综合信号】{f_emoji} {fused['signal'].upper()} | 置信度: {fused['confidence']}/100")
    print(f"【模型投票】{fused['vote']}")
    print(f"【平均预测变化】{fused['avg_price_change_pct']:+.2f}%")
    print(f"【关键价位】支撑: ${fused['support']} | 阻力: ${fused['resistance']}")

    print(f"\n{'━' * 62}")
    print(f"{'模型':<25} {'机构':<12} {'信号':<10} {'置信度':<8} {'预测变化'}")
    print(f"{'━' * 62}")
    for r in results:
        m_emoji = emoji.get(r["signal"], "⚪")
        pct = r.get("price_change_pct", 0)
        cur = r.get("current_price", 0)
        fcast = r.get("forecast_price", 0)
        chg = f"{pct:+.2f}%" if cur and fcast else "N/A"
        print(f"{r['model']:<25} {r.get('institution',''):<12} "
              f"{m_emoji}{r['signal']:<8} {r['confidence']:>5}/100  {chg}")

    print(f"\n{'━' * 62}")
    print("【各模型详细意见】")
    for r in results:
        m_emoji = emoji.get(r["signal"], "⚪")
        print(f"\n  {m_emoji} {r['model']} ({r.get('institution','')}, {r.get('params','')})")
        print(f"     信号: {r['signal']} ({r['confidence']}/100)")
        print(f"     {r.get('reasoning', 'N/A')[:100]}")

    print(f"\n{'=' * 62}")
    print("⚠️  仅供参考，不构成投资建议。模型预测存在不确定性。")
    print("=" * 62)


def main():
    parser = argparse.ArgumentParser(description="AI Model Prediction Team")
    parser.add_argument("symbol", help="交易对，如 BTC-USDT-SWAP")
    parser.add_argument("--timeframe", "--tf", default="4H", help="周期 (默认: 4H)")
    parser.add_argument("--models", default="kronos,chronos-base,chronos-small,timesfm,moirai",
                        help="逗号分隔的模型列表")
    parser.add_argument("--signal-only", "-s", action="store_true", help="只输出信号")
    parser.add_argument("--json", "-j", action="store_true", help="JSON格式输出")
    args = parser.parse_args()

    model_list = [m.strip() for m in args.models.split(",")]

    # Get current prices first
    import requests
    for inst in [args.symbol, f"{args.symbol}-SWAP"]:
        url = f"{OKX_BASE}/market/ticker"
        r = requests.get(url, params={"instId": inst}, timeout=10)
        d = r.json()
        if d.get("code") == "0" and d.get("data"):
            current_price = float(d["data"][0]["last"])
            break
    else:
        current_price = 0

    print(f"\n🔄 运行AI模型团队 ({len(model_list)}个模型)...")
    results = []
    for mn in model_list:
        print(f"  ▶ {mn}...", end=" ", flush=True)
        r = run_model(mn, args.symbol, args.timeframe)
        results.append(r)
        status = "✅" if "Error" not in r.get("reasoning","") else "❌"
        print(f"{status} {r['signal']} ({r['confidence']}%)")

    fused = fuse_signals(results)

    if args.json:
        output = {
            "symbol": args.symbol, "timeframe": args.timeframe,
            "timestamp": datetime.now().isoformat(),
            "fused": fused,
            "models": results,
            "current_price": current_price
        }
        print(json.dumps(output, ensure_ascii=False, indent=2))
    elif args.signal_only:
        emoji = {"bullish": "🟢", "bearish": "🔴", "neutral": "⚪"}
        f_emoji = emoji.get(fused["signal"], "⚪")
        print(f"\n{f_emoji} 综合: {fused['signal']} ({fused['confidence']}/100)")
        print(f"   投票: {fused['vote']}")
        for r in results:
            m_e = emoji.get(r["signal"], "⚪")
            print(f"   {m_e} {r['model']}: {r['signal']} ({r['confidence']}%)")
    else:
        print_report(args.symbol, args.timeframe, results, fused,
                    {"current": current_price})


if __name__ == "__main__":
    main()
