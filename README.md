# AI Model Team

**Version:** 2.0.0  
**Release Date:** 2026-04-15  

多模型协同预测系统 —— 整合 Kronos、Chronos、TimesFM、FinBERT 四大 AI 模型，对 OKX 加密货币进行多角度分析，输出综合意见。

## v2.0.0 更新亮点

### 新增功能
- 🆕 **FinBERT 情绪分析模型** - 基于 HuggingFace FinBERT，分析新闻/社交媒体情绪
- 🆕 **社会情绪数据模块** - 整合 CryptoPanic + Reddit + RSS 三数据源
- 🆕 **四模型协同预测** - Kronos + TimesFM + Chronos-2 + FinBERT
- 🆕 **OKX CEX 数据集成** - 订单簿、资金费率、持仓量、技术指标

### 修复改进
- ✅ 修复 `torch_dtype` 弃用警告 → 改用 `dtype`
- ✅ 修复硬编码路径 → 使用环境变量
- ✅ 修复数据格式兼容性（list vs dict）
- ✅ 添加错误处理（try/except + raise_for_status）
- ✅ 新增 requirements.txt 依赖管理
- ✅ API 密钥安全存储在 .env 文件

## 模型分工

| 模型 | 机构 | 专长 | 权重 |
|------|------|------|------|
| **Kronos-base** | NeoQuasar | 加密K线专精（庄家行为/洗盘识别） | 30% |
| **Chronos-2** | Amazon | 泛领域宏观周期（数学/概率模型） | 25% |
| **TimesFM-2.5** | Google | 通用时序节奏（上下文感知） | 25% |
| **FinBERT-sentiment** | HuggingFace | 金融文本情绪分析（新闻/社交媒体） | 20% |

## 新增模型参数

### FinBERT 模型
```python
# 基础金融情绪分析
from finbert_adapter import FinBERTAdapter
adapter = FinBERTAdapter("finbert-base")  # ProsusAI/finbert

# 加密货币专用
adapter = FinBERTAdapter("finbert-crypto")  # burakutf/finetuned-finbert-crypto

# Twitter/社交媒体专用
adapter = FinBERTAdapter("finbert-twitter")  # StephanAkkerman/FinTwitBERT-sentiment
```

### 社会情绪数据源
| 数据源 | 类型 | 内容 |
|--------|------|------|
| **CryptoPanic** | 新闻聚合 | 加密货币新闻 + 社区投票情绪 |
| **Reddit** | 社区讨论 | r/cryptocurrency 帖子情绪关键词分析 |
| **RSS** | 主流媒体 | CoinDesk、Cointelegraph 头条新闻 |

## 信号阈值配置

默认配置（可调）：
- **看多阈值**: +2.0% 以上
- **看空阈值**: -2.0% 以下
- **区间**: ±2.0% 为中性

修改方式：在各 adapter 文件顶部修改 `BULLISH_THRESHOLD` 和 `BEARISH_THRESHOLD` 常量。

## 目录结构

```
ai-model-team/
├── SKILL.md                    # Skill 定义
├── README.md                   # 本文档
├── btc_short_analysis.py       # 快速分析脚本（双模型）
└── scripts/
    ├── model_team.py           # 主入口（多模型可配置）
    ├── run_team.py             # 统一1H×24预测脚本
    ├── kronos_adapter.py       # Kronos 适配器
    ├── chronos_adapter.py      # Chronos 适配器
    ├── timesfm_adapter.py      # TimesFM 适配器
    └── moirai_adapter.py      # MOIRAI 适配器
```

## 使用方式

### 快速双模型分析（BTC）
```bash
python3 btc_short_analysis.py
```

### 多模型分析（可配置）
```bash
# 默认分析 BTC
python3 scripts/model_team.py BTC-USDT-SWAP

# 指定交易对和时间周期
python3 scripts/model_team.py ETH-USDT-SWAP --timeframe 1H

# 指定运行的模型
python3 scripts/model_team.py BTC-USDT-SWAP --models kronos,chronos-base

# 仅输出信号
python3 scripts/model_team.py BTC-USDT-SWAP --signal-only

# JSON 输出
python3 scripts/model_team.py BTC-USDT-SWAP --json
```

### 统一 1H×24 预测
```bash
python3 scripts/run_team.py
```

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_HEDGE_PATH` | ai-hedge-fund-skill 路径 | `~/.agents/skills/ai-hedge-fund-skill` |
| `OBSIDIAN_VAULT` | Obsidian 笔记库路径 | `~/Obsidian/我的远程库` |

## 依赖

- Python 3.10+
- numpy, pandas, requests
- torch (for TimesFM, Chronos)
- timesfm (`pip install timesfm`)
- chronos (`pip install chronos-forest`)
- kronos (from ai-hedge-fund-skill)

## 注意事项

⚠️ 仅供参考，不构成投资建议。模型预测存在不确定性。
