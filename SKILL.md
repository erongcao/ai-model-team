---
name: ai-model-team
description: AI量化模型预测团队 — 整合Kronos（K线专用）和TimesFM（Google通用时序）对OKX加密货币进行协同预测，生成综合意见。
---

# AI 模型预测团队

**2026-04-13 更新：精简为2个核心模型**

## 团队成员

| 模型 | 机构 | 参数量 | 专业方向 | 状态 |
|------|------|--------|----------|------|
| **Kronos-base** | NeoQuasar | 102M | **K线专用** ⭐ | ✅ 就绪 |
| **TimesFM-2.5-200M** | Google | 200M | 通用时序/16k上下文 | ✅ 就绪 |

## 工作流程

```
OKX K线数据 (4H周期, 200根K线)
       ↓
  [Kronos-base 独立预测]  → K线语言模型，12亿K线预训练
       ↓
  [TimesFM-2.5-200M 独立预测] → Google通用时序模型
       ↓
  多模型投票融合
       ↓
  综合信号 + 各模型意见
```

## 使用方法

```bash
cd ~/.agents/skills/ai-model-team
source .venv/bin/activate
python3 -c "
import numpy as np, requests, pandas as pd, sys
from timesfm import TimesFM_2p5_200M_torch, ForecastConfig

AI_HEDGE = '/Users/yirongcao/.agents/skills/ai-hedge-fund-skill'
sys.path.insert(0, f'{AI_HEDGE}/Kronos')
sys.path.insert(0, AI_HEDGE)
from kronos_distilled import forecast_with_kronos

tfm = TimesFM_2p5_200M_torch.from_pretrained('google/timesfm-2.5-200m-pytorch')
fc = ForecastConfig(max_context=512, max_horizon=128, per_core_batch_size=4)
tfm.compile(forecast_config=fc)

# 获取数据
url = 'https://www.okx.com/api/v5/market/history-candles'
r = requests.get(url, params={'instId': 'BTC-USDT-SWAP', 'bar': '4H', 'limit': 300}, timeout=30)
df = pd.DataFrame(r.json()['data'], columns=['ts','open','high','low','close','vol','vol2','vol3','confirm'])
for c in ['close']: df[c] = pd.to_numeric(df[c])
prices = df['close'].values[-200:].astype(np.float32)
cur = float(prices[-1])

# TimesFM预测
fcast = tfm.forecast(horizon=24, inputs=[prices])[0][0]
tfm_avg = float(np.mean(fcast))
tfm_pct = (tfm_avg / cur - 1) * 100
tfm_dir = 'bullish' if tfm_pct > 2 else 'bearish' if tfm_pct < -2 else 'neutral'

# Kronos预测
kr = forecast_with_kronos('BTC-USDT-SWAP', lookback=200, pred_len=24)
kr_dir = kr.forecast_direction
kr_pct = kr.key_metrics['price_change_pct']

# 综合
bullish = (1 if tfm_dir=='bullish' else 0) + (1 if kr_dir=='bullish' else 0)
bearish = (1 if tfm_dir=='bearish' else 0) + (1 if kr_dir=='bearish' else 0)
fused = 'bullish' if bullish>=2 else 'bearish' if bearish>=2 else 'neutral'
print(f'综合信号: {fused}')
"
```

## 信号融合规则

- 2个模型等权重投票
- 共识信号 → 强置信度（≥80%）
- 分歧信号 → 中性（50%左右）

## 依赖

已安装于 `~/.agents/skills/ai-model-team/.venv/`：
- torch 2.11.0
- transformers
- timesfm 2.0.0（GitHub: google-research/timesfm）
- huggingface_hub
- einops
- pandas, numpy, requests

## 文件结构

```
ai-model-team/
├── SKILL.md
└── .venv/                  # 独立虚拟环境
    └── lib/python3.14/site-packages/
        ├── timesfm/         # TimesFM 2.5 (Google)
        ├── torch/
        └── ...
```
