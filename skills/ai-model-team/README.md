# AI Model Team

**Version:** 2.9.0
**Release Date:** 2026-04-16

---

## v2.9.0 CL数据源路由修复 (2026-04-16)

### 🐛 Bug 修复

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| **CL 原油价格** | Yahoo Finance `CL`=Colgate股票 $83 | OKX 原生价格 $88 |
| **Kronos 数据不足** | 84 bars (误路由) | 254 bars (OKX数据) |

### ⚠️ Kronos 数据不足说明

**不调低 lookback 阈值，保持 400 根 K线要求。**

某些标的（如 CL-USDT-SWAP）在 OKX 上线时间较短，历史数据不足 400 根 4H K线。Kronos 会直接返回"数据不足"而不强行计算，以保护预测准确性。

这不是 bug，是**有意为之的设计决策**：宁可缺少一个模型信号，也不牺牲准确率。

---

## v2.8.0 ETH数据源路由修复 (2026-04-16)

### 🐛 严重 Bug 修复

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| **ETH 价格错误** | `$22` (Yahoo Finance Grayscale ETF) | `$2,350` (OKX 原生价格) |
| **数据源路由** | ETH 被错误送入 Yahoo Finance | ETH → OKX，股票 → Yahoo Finance |
| **影响范围** | Chronos-2 / TimesFM 对 ETH 的全部预测 | 预测价格已修正 |

### 🔍 根因分析

Yahoo Finance 的 `ETH` 符号代表 **Grayscale Ethereum Mini Trust ETF**，价格约 `$22`，而非 ETH 加密货币本身（`$2,350`）。两者相差 **100 倍**。

原代码将 `ETH` 错误地放在 `STOCK_SYMBOLS` 集合中（注释写"明确不是股票"），导致 `get_data()` 将 ETH 判定为"股票"并送往 Yahoo Finance。

### 📡 数据源路由规则

| 资产类型 | 数据来源 | 说明 |
|---------|---------|------|
| 加密货币 (BTC/ETH/SOL/DOGE/XRP/ADA/AVAX/DOT/LINK/MATIC/UNI/ATOM) | **OKX** | 走 OKX API，永续合约/现货 |
| 美股 (NVDA/AAPL/MSFT/GOOGL/AMZN/TSLA/META/...) | **Yahoo Finance** | 通过 `yfinance` 接口 |

### ✅ 修复内容

- 新增 `CRYPTO_EXCLUSIONS` 排除列表（明确加密货币不走 Yahoo Finance）
- 修复 `CRYPTO_EXCLUSIONS` 逻辑：`is_stock = symbol NOT IN CRYPTO_EXCLUSIONS`
- 扩展排除列表：`LINK`, `MATIC`, `UNI`, `ATOM`, `USDC`

---

## v2.7.0 单元测试 + 缓存 + 重试 (2026-04-16)  
**Release Date:** 2026-04-15  
**Author:** NeoQuasar AI Lab

多模型协同预测系统 —— 整合 Kronos、Chronos-2、TimesFM、VADER 四大 AI/规则模型，对 OKX 加密货币进行多角度分析，输出综合交易信号。

---

## v2.2.0 可复现性修复 (2026-04-15)

### 🐛 严重问题修复

| 问题 | 修复前 | 修复后 |
|------|--------|--------|
| **timesfm 安装方式** | `file:///tmp/timesfm` (本地路径) | `git+https://github.com/google-research/timesfm.git@f085b90` |
| **Chronos 安装方式** | 仅注释，无安装指令 | `git+https://github.com/amazon-science/chronos-forecasting.git@<commit>` |
| **Python 版本要求** | `3.14+` (过于激进) | `3.11+` (扩大兼容范围) |

### 📝 依赖管理改进

```diff
# timesfm
- timesfm @ file:///tmp/timesfm
+ timesfm @ git+https://github.com/google-research/timesfm.git@f085b90

# chronos-forecasting
- # Chronos - Amazon T5-based time series model
+ chronos-forecasting @ git+https://github.com/amazon-science/chronos-forecasting.git@6d68ed7c4ed2805d122d77b4660765b4089de5ca

# Python
- # Python: 3.14+
+ # Python: 3.11+ (recommended: 3.11-3.14)
```

### ✅ 其他改进

- `psutil` 依赖已锁定版本 (`7.2.2`) — 无需修复
- 所有 GitHub 安装使用明确 commit hash，确保可复现性
- 新增 `post_install.py` — 自动修复 timesfm 兼容性问题
- 新增 `docs/KRONOS_MODEL_CARD.md` — Kronos 模型透明度文档

---

## v2.1.0 社会情绪增强 (2026-04-15)

### 🆕 新增功能

| 功能 | 说明 |
|------|------|
| **Multi-Subreddit Reddit** | 股票/加密货币多板块搜索 (stocks/investing/wallstreetbets/crypto) |
| **通用财经/国际新闻** | Reuters, BBC World/US, CNN Business, Guardian Business |
| **四大新闻社 RSS** | Bloomberg, WSJ, CNBC, FT 实时新闻 |
| **FinBERT 情感分析** | VADER金融增强 (<1秒加载) + 可选神经网络备选 |
| **数据泄漏审计** | leak_audit.py 检测时间戳/窗口/特征泄漏 |

### 🔧 修复改进

- ✅ 修复 `torch_dtype` 弃用警告 → 改用 `dtype`
- ✅ 修复硬编码路径 → 使用环境变量 `os.path.expanduser('~')`
- ✅ 修复数据格式兼容性（OKX CLI 返回 list vs dict）
- ✅ 添加错误处理（try/except + raise_for_status）
- ✅ 新增 `requirements.txt` 依赖管理
- ✅ API 密钥安全存储在 `.env` 文件（不在版本控制中）
- ✅ 创建 `CHANGELOG.md` 版本更新记录

---

## 模型分工

| 模型 | 机构 | 专长 | 数据类型 | 权重 |
|------|------|------|---------|------|
| **Kronos-base** | NeoQuasar | 加密K线专精（庄家行为/洗盘识别） | 价格走势 | 30% |
| **Chronos-2** | Amazon | 泛领域宏观周期（数学/概率模型） | 分位数预测 | 25% |
| **TimesFM-2.5** | Google | 通用时序节奏（上下文感知） | 时序预测 | 25% |
| **FinBERT-sentiment** | HuggingFace/VADER | 金融文本情绪分析 | VADER+金融关键词 | 20% |

### 模型详情

#### 1. Kronos-base (NeoQuasar)
- **模型路径**: `~/.agents/skills/ai-hedge-fund-skill/models/kronos-base`
- **输入**: OKX K线数据 (OHLCV)
- **输出**: 价格方向、涨跌百分比、趋势强度
- **特点**: 专门针对加密货币K线训练，识别庄家行为
- **模型卡**: [docs/KRONOS_MODEL_CARD.md](docs/KRONOS_MODEL_CARD.md)  
#### 2. Chronos-2 (Amazon)
- **模型ID**: `amazon/chronos-2` (HuggingFace)
- **输入**: 时间序列数值 (float32)
- **输出**: 21个分位数的预测序列
- **特点**: T5架构，通用时序预测，支持长周期

#### 3. TimesFM-2.5-200M (Google)
- **模型ID**: `google/timesfm-2.5-200m-pytorch` (HuggingFace)
- **输入**: 时间序列数值
- **输出**: 点预测 + 置信区间
- **特点**: 200M参数，通用时序模型，支持零样本预测

#### 4. FinBERT-sentiment (VADER + 金融关键词增强)
- **模型**: `VADER` (Valence Aware Dictionary) + 金融关键词增强
- **输入**: 文本（新闻标题、社交媒体内容）
- **输出**: 情绪分类 (positive/negative/neutral) + 置信度
- **特点**: <1秒加载，70% VADER + 30% 金融关键词综合评分

---

## 社会情绪数据源

### 数据源详情

| 数据源 | 类型 | API/URL | 更新频率 | 内容 |
|--------|------|---------|---------|------|
| **CryptoPanic** | 新闻聚合 | cryptopanic.com | 实时 | 加密货币新闻 + 社区投票(up/down) |
| **Reddit** | 社区讨论 | reddit.com/r/cryptocurrency | 实时 | 热门帖子标题 + 情绪关键词统计 |
| **CoinDesk RSS** | 主流媒体 | coindesk.com/rss | 定时 | 新闻标题 + 情绪分类 |
| **CoinTelegraph RSS** | 主流媒体 | cointelegraph.com/rss | 定时 | 新闻标题 + 情绪分类 |

### 情绪关键词识别

| 类型 | 关键词 |
|------|--------|
| 🟢 看涨 | bull, bullish, moon, pump, hodl, buy, long, breakout, ATH |
| 🔴 看跌 | bear, bearish, dump, crash, sell, short, bottom, capitulation |
| ⚠️ FOMO | FOMO, getting in, jump in, don't miss |
| ⚠️ 恐惧 | panic, scared, worried, crash coming, bubble, scam, rug pull |

---

## OKX CEX 数据源

### 集成功能

| 功能 | 说明 |
|------|------|
| **K线数据** | 历史OHLCV，支持1M/5M/15M/30M/1H/4H/1D |
| **订单簿** | 买卖盘深度，不平衡度计算 |
| **资金费率** | 永续合约资金费率历史 |
| **持仓量** | Open Interest 变化 |
| **技术指标** | RSI, MACD, EMA, MA, BB, KDJ 等 70+ |

---

## 信号阈值配置

默认配置（可调）：

```python
# 各 adapter 文件顶部
BULLISH_THRESHOLD = 2.0   # 看多阈值: +2.0% 以上
BEARISH_THRESHOLD = -2.0  # 看空阈值: -2.0% 以下
# ±2.0% 区间内为中性信号
```

---

## 目录结构

```
ai-model-team/
├── SKILL.md                      # Skill 定义文件
├── README.md                      # 本文档
├── CHANGELOG.md                  # 版本更新记录
├── requirements.txt               # Python 依赖（精确版本）
├── .gitignore                    # Git 忽略配置
├── .env                          # 环境变量（API密钥，不在版本控制）
├── .github/
│   └── workflows/
│       └── ci.yml                 # CI 冒烟测试
├── btc_short_analysis.py         # 快速分析脚本（BTC专用）
│
└── scripts/
    ├── model_team.py              # ⭐ 主入口（多模型可配置）
    ├── run_team.py                # 统一 1H×24 预测脚本
    ├── config.py                  # 统一配置管理
    │
    ├── 【模型适配器】
    ├── kronos_adapter.py          # Kronos 模型适配器
    ├── chronos_adapter.py         # Chronos 模型适配器
    ├── timesfm_adapter.py        # TimesFM 模型适配器
    ├── moirai_adapter.py         # MOIRAI 模型适配器
    ├── finbert_adapter.py         # FinBERT 模型适配器
    │
    ├── 【数据提供】
    ├── okx_data_provider.py      # OKX 数据提供模块
    └── social_sentiment_provider.py  # 社会情绪数据模块
    │
    ├── 【P0 基础设施】
    ├── data_quality.py            # 数据质量校验、时区、schema
    ├── risk_control.py            # 风控闸门、熔断、仓位管理
    ├── observability.py            # 结构化日志、指标、告警
    ├── retry.py                   # 重试策略、超时
    └── config.py                  # 统一配置管理
    │
    ├── 【P1 策略增强】
    ├── trading_cost.py            # 交易成本模型
    ├── validation.py              # Walk-forward 验证
    └── ensemble.py                # 动态加权融合、置信度校准
    │
    └── 【P2 生产级】
    ├── model_registry.py          # 模型注册表、版本管理
    ├── drift_detection.py         # 漂移检测
    ├── execution.py              # 智能订单执行
    ├── security.py               # 安全与合规
    ├── runbook.py                # 运行手册
    ├── leak_audit.py             # 泄漏审计 (P3)
    └── post_install.py           # 安装后自动修复脚本
```

---

## 使用方式

### 1. 主入口 (model_team.py) ⭐

```bash
# 基础用法
python3 scripts/model_team.py BTC-USDT-SWAP

# 指定时间周期
python3 scripts/model_team.py ETH-USDT-SWAP --timeframe 1H
python3 scripts/model_team.py CL-USDT-SWAP --timeframe 4H

# 指定运行的模型（逗号分隔）
python3 scripts/model_team.py BTC-USDT-SWAP --models kronos,timesfm,chronos-2,finbert

# 仅输出信号（简洁模式）
python3 scripts/model_team.py BTC-USDT-SWAP --signal-only

# JSON 输出（程序化使用）
python3 scripts/model_team.py BTC-USDT-SWAP --json

# 显示社会情绪分析
python3 scripts/model_team.py BTC-USDT-SWAP --social

# 四模型 + 社会情绪完整分析
python3 scripts/model_team.py BTC-USDT-SWAP --models kronos,timesfm,chronos-2,finbert --social
```

### 2. 快速分析 (btc_short_analysis.py)

```bash
# BTC 快速双模型分析
python3 btc_short_analysis.py
```

### 3. 统一预测 (run_team.py)

```bash
# 1H 周期 × 24 步预测
python3 scripts/run_team.py

# 自定义周期
python3 scripts/run_team.py --timeframe 4H
```

---

## 输出示例

### 四模型 + 社会情绪完整分析

```
============================================================
🤖 AI 模型预测团队报告 — BTC-USDT-SWAP (4H)
   生成时间: 2026-04-15 17:00:00
============================================================

【综合信号】⚪ NEUTRAL | 置信度: 35/100
【模型投票】0🔴 4⚪ 0🟢
【平均预测变化】+0.23%
【关键价位】支撑: $67,450 | 阻力: $68,200

📊 社会情绪分析 (BTC)
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
  ⚪ 综合情绪: NEUTRAL (得分: +0.150)
     ├─ 新闻情绪: +0.200
     └─ Reddit情绪: +0.080

  📈 数据统计:
     ├─ 新闻: 15+ / 8- / 12=
     └─ Reddit: 25 帖分析

  🔥 热门话题:
     • Bitcoin surges past $68K as ETF inflows continue... (👍2.3k)
     • SEC delays decision on spot Bitcoin ETF... (👍890)

  📰 最新头条:
     • Bitcoin surges past $68K as ETF inflows continue
     • Crypto market cap reaches $2.5 trillion
     • Ethereum foundation announces grants for DeFi
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

------------------------------------------------------------
模型                   机构        信号       置信度     预测变化
------------------------------------------------------------
Kronos-base            NeoQuasar   ⚪ neutral   50/100   +1.54%
TimesFM-200M           Google      ⚪ neutral   50/100   +0.18%
chronos-2              Amazon     ⚪ neutral   53/100   +1.21%
FinBERT-sentiment      HuggingFace ⚪ neutral   30/100   N/A

------------------------------------------------------------
【各模型详细意见】

  ⚪ Kronos-base (NeoQuasar, 102M)
     信号: neutral (50/100)
     Kronos预测: $67,850→$68,895 (+1.54%), 趋势强度100/100

  ⚪ TimesFM-200M (Google, 200M)
     信号: neutral (50/100)
     TimesFM预测: $67,850→$67,972 (+0.18%), 趋势强度100/100

  ⚪ chronos-2 (Amazon, ~120M)
     信号: neutral (53/100)
     Chronos(chronos-2)预测: $67,850→$68,672 (+1.21%), 趋势强度14/100

  ⚪ FinBERT-sentiment (HuggingFace, 110M)
     信号: neutral (30/100)
     FinBERT文本情绪分析: 25条新闻, 情绪得分+0.150, 整体NEUTRAL

============================================================
⚠️  仅供参考，不构成投资建议。模型预测存在不确定性。
============================================================
```

### 信号模式 (--signal-only)

```
⚪ 综合: neutral (35/100)
   投票: 0🔴 4⚪ 0🟢
   ⚪ Kronos-base: neutral (50%)
   ⚪ TimesFM-200M: neutral (50%)
   ⚪ chronos-2: neutral (53%)
   ⚪ FinBERT-sentiment: neutral (30%)
```

### JSON 输出 (--json)

```json
{
  "symbol": "BTC-USDT-SWAP",
  "timeframe": "4H",
  "timestamp": "2026-04-15T17:00:00",
  "fused": {
    "signal": "neutral",
    "confidence": 35,
    "avg_price_change_pct": 0.23,
    "support": 67450.0,
    "resistance": 68200.0,
    "vote": "0🔴 4⚪ 0🟢"
  },
  "models": [
    {
      "model": "Kronos-base",
      "institution": "NeoQuasar",
      "signal": "neutral",
      "confidence": 50,
      "price_change_pct": 1.54
    },
    ...
  ],
  "social_sentiment": {
    "overall_sentiment": "neutral",
    "sentiment_score": 0.15,
    "statistics": {
      "news_total": 35,
      "news_positive": 15,
      "news_negative": 8
    }
  }
}
```

---

## 环境变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `AI_HEDGE_PATH` | ai-hedge-fund-skill 路径 | `~/.agents/skills/ai-hedge-fund-skill` |
| `AI_MODEL_TEAM_DIR` | 本技能目录 | 自动检测 |
| `OKX_API_KEY` | OKX API Key | `.env` 文件加载 |
| `OKX_SECRET_KEY` | OKX Secret Key | `.env` 文件加载 |
| `OKX_API_PASSWORD` | OKX API 密码 | `.env` 文件加载 |

### .env 文件格式

```bash
# ~/.agents/skills/ai-model-team/.env
OKX_API_KEY=your_api_key_here
OKX_SECRET_KEY=your_secret_key_here
OKX_API_PASSWORD=your_api_password_here
```

---

---

## P0 基础设施（生产级）

### data_quality.py - 数据质量与校验

| 功能 | 说明 |
|------|------|
| **时区统一** | 所有数据强制使用 UTC |
| **数据完整率** | 检查缺失值、重复数据 |
| **Schema 校验** | OHLC 关系检查、字段类型 |
| **多源对齐** | K线/订单簿/情绪数据时间对齐 |

```python
from data_quality import validate_data_quality, TimezoneHandler, SchemaValidator

# UTC 时间处理
utc_time = TimezoneHandler.now_utc()

# 数据校验
is_valid, errors = SchemaValidator.validate_kline(df)

# 完整率检查
report = DataCompletenessChecker.check_dataframe(df, DataSource.OKX_KLINE)
```

### risk_control.py - 风控闸门与熔断

| 功能 | 说明 |
|------|------|
| **仓位限制** | 单标最大仓位 10% |
| **止损/止盈** | 可配置止损 2%、止盈 4% |
| **熔断机制** | 连亏 4 次触发冷却 |
| **日内回撤** | 超 3% 回撤禁止开仓 |

```python
from risk_control import RiskGate, check_trade_risk

gate = RiskGate()
result = gate.check(
    signal_confidence=0.7,
    signal_direction="bullish",
    proposed_position_pct=0.1,
    current_equity=10000
)
print(f"决策: {result.decision}, 原因: {result.reason}")
```

### observability.py - 可观测性

| 功能 | 说明 |
|------|------|
| **结构化日志** | JSON 格式，含 trace_id/request_id |
| **指标埋点** | 延迟、失败率、数据新鲜度 |
| **告警系统** | Webhook 推送、冷却机制 |
| **敏感脱敏** | API Key 自动脱敏 |

```python
from observability import get_logger, get_metrics, get_alerts

logger = get_logger()
logger.info("预测完成", trace_id="abc123", latency_ms=150)

metrics = get_metrics()
metrics.increment("prediction.count", tags={"model": "kronos"})

alerts = get_alerts()
alerts.send("data_source_failure", "error", "OKX API timeout")
```

### retry.py - 重试与超时

| 功能 | 说明 |
|------|------|
| **指数退避** | base × 2^attempt + jitter |
| **超时控制** | 默认 20 秒 |
| **可重试异常** | ConnectionError, TimeoutError |

```python
from retry import with_retry, TimeoutContext

@with_retry(max_attempts=3, timeout=20)
def fetch_data(): ...
```

---

## P1 策略增强

### trading_cost.py - 交易成本模型

| 功能 | 说明 |
|------|------|
| **手续费** | 双向收取（开仓+平仓）|
| **滑点估算** | 按流动性分层（高/中/低）|
| **市场冲击** | 大单冲击成本估算 |
| **成本检测** | 判断扣除成本后是否盈利 |

```python
from trading_cost import estimate_net_pnl, LiquidityClassifier

tier = LiquidityClassifier.classify(daily_volume_usd=5_000_000)
result = estimate_net_pnl(
    entry_price=100, exit_price=105,
    quantity=1.0, side="long",
    liquidity_tier=tier
)
print(f"净盈亏: ${result.net_pnl:.2f}, 成本率: {result.cost_ratio:.2%}")
```

### validation.py - Walk-Forward 验证

| 功能 | 说明 |
|------|------|
| **时序验证** | 避免未来数据泄漏 |
| **方向准确率** | 预测方向 vs 实际方向 |
| **Brier Score** | 概率校准质量 |
| **Sharpe/回撤** | 风险调整后收益 |

```python
from validation import WalkForwardValidator

validator = WalkForwardValidator(n_splits=5, train_ratio=0.7)
results = validator.validate(df, signal_func=my_signal_generator)
summary = validator.get_summary(results)
print(f"平均方向准确率: {summary['avg_direction_accuracy']:.1%}")
```

### ensemble.py - 动态加权融合

| 功能 | 说明 |
|------|------|
| **置信度校准** | Isotonic 回归校准 |
| **市场状态检测** | 趋势/震荡/高波动 |
| **动态权重** | 根据市场状态调整 |
| **贡献分析** | 各模型权重贡献 |

```python
from ensemble import DynamicWeightedEnsemble, ModelPrediction

ensemble = DynamicWeightedEnsemble()
ensemble.update_market_state(df_price)
result = ensemble.fuse(predictions)
print(f"融合信号: {result.fused_signal}, 置信度: {result.fused_confidence:.0%}")
```

---

## P2 生产级模块

### model_registry.py - 模型注册表

| 功能 | 说明 |
|------|------|
| **版本追踪** | 模型版本、训练数据区间 |
| **特征签名** | SHA256 哈希校验 |
| **状态管理** | active/deprecated/retired |
| **元数据** | 精度、训练数据、创建者 |

```python
from model_registry import get_model_registry, register_default_models

registry = get_model_registry()
register_default_models()  # 注册默认模型

model = registry.get_active("kronos-base")
print(f"版本: {model.version}, 精度: {model.metrics['directional_accuracy']}")
```

### drift_detection.py - 漂移检测

| 功能 | 说明 |
|------|------|
| **PSI 指数** | Population Stability Index |
| **KL 散度** | 分布漂移检测 |
| **命中率监控** | 性能下降告警 |
| **连续告警** | N 次漂移后触发 |

```python
from drift_detection import DriftMonitor

monitor = DriftMonitor()
reports = monitor.check_all_inputs({"close": price_data})
for r in reports:
    if r.drift_detected:
        print(f"漂移告警: {r.feature_name}, PSI: {r.current_value}")
```

### execution.py - 智能订单执行

| 功能 | 说明 |
|------|------|
| **订单类型选择** | limit/market/post_only |
| **拆分优化** | 大单拆分减少冲击 |
| **滑点估算** | 基于订单簿深度 |
| **重试机制** | 未成交自动重试 |

```python
from execution import ExecutionOptimizer, estimate_execution_cost

optimizer = ExecutionOptimizer()
result = optimizer.execute_smart(
    symbol="BTC-USDT-SWAP", side="buy",
    quantity=1.0, price=67000,
    orderbook_depth=ob_data, urgency="normal"
)
print(f"成交率: {result.fill_ratio:.1%}, 滑点: {result.slippage_bps:.1f}bps")
```

### security.py - 安全与合规

| 功能 | 说明 |
|------|------|
| **密钥轮换** | 90 天自动轮换 |
| **最小权限** | 按任务分配权限 |
| **审计日志** | 操作追踪、不可篡改 |
| **敏感脱敏** | 日志自动脱敏 |

```python
from security import get_key_storage, get_audit_logger

storage = get_key_storage()
new_id, new_secret = storage.create_key(["read_market", "trade"])

audit = get_audit_logger()
audit.log("trade", resource="BTC", result="success")
```

### runbook.py - 运行手册

| 功能 | 说明 |
|------|------|
| **故障排查** | 常见问题及解决方案 |
| **回滚管理** | 配置一键回滚 |
| **值班指南** | 健康检查清单、升级流程 |

```python
from runbook import Runbook, RollbackManager, OnCallGuide

# 健康检查
health = OnCallGuide.get_health_check()

# 故障排查
entry = Runbook.get_entry("模型加载失败")
print(entry.resolution)

# 回滚配置
RollbackManager.create_backup()
RollbackManager.rollback_config()
```

---

### leak_audit.py - 泄漏审计

| 功能 | 说明 |
|------|------|
| **时间戳审计** | 检查时间间隔一致性 |
| **窗口滑动** | 验证不使用未来数据 |
| **特征泄漏** | 检测 forward-looking 特征 |
| **随机种子** | 验证可复现性 |

```bash
# 审计 BTC-USDT-SWAP
python3 scripts/leak_audit.py --symbol BTC-USDT-SWAP --bar 4H --detailed

# 退出码
# 0 = 无泄漏
# 1 = 高严重性泄漏
# 2 = 严重泄漏
```

---

## 依赖（精确版本）


### 核心依赖

| 包 | 版本 | 用途 |
|----|------|------|
| Python | 3.14 | 运行环境 |
| numpy | 2.4.4 | 数值计算 |
| pandas | 3.0.2 | 数据处理 |
| requests | 2.33.1 | HTTP 请求 |
| torch | 2.11.0 | 深度学习框架 |

### 模型依赖

| 包 | 版本 | 用途 |
|----|------|------|
| transformers | 4.57.6 | HuggingFace 模型 |
| huggingface_hub | 0.36.2 | 模型下载 |
| feedparser | 6.0.12 | RSS 解析 |
| timesfm | (本地) | Google TimesFM |
| chronos-forest | (Git) | Amazon Chronos |

### 完整依赖列表

```bash
pip install -r requirements.txt
```

所有依赖版本已锁定在 `requirements.txt` 中。

---

## 技术规格

### 支持的交易对格式

```
BTC-USDT-SWAP    # 永续合约
ETH-USDT-SWAP    # 永续合约
SOL-USDT-SWAP    # 永续合约
CL-USDT-SWAP     # 指数永续（原油）
```

### 支持的时间周期

| 周期 | 说明 |
|------|------|
| `1M` | 1分钟 |
| `5M` | 5分钟 |
| `15M` | 15分钟 |
| `30M` | 30分钟 |
| `1H` | 1小时 |
| `4H` | 4小时 |
| `1D` | 1天 |

### 预测步长

- 默认: 24 步 (例如 4H×24 = 4天预测)
- 可配置: `--pred-len` 参数

---

## 故障排除

### 1. 模型下载慢

```bash
# 设置 HuggingFace 镜像（国内加速）
export HF_ENDPOINT=https://hf-mirror.com
```

### 2. 依赖安装失败

```bash
# 使用国内镜像
pip install -i https://pypi.tuna.tsinghua.edu.cn/simple -r requirements.txt
```

### 3. 内存不足

```bash
# 减少批处理大小
export TIMESFM_BATCH_SIZE=2
```

---

## 注意事项

⚠️ **免责声明**

1. 本工具仅供参考，不构成投资建议
2. 模型预测存在不确定性，可能与实际走势不符
3. 加密货币市场波动大，请理性投资
4. 使用前请评估风险，不要投入超过承受能力的资金

---

## 相关项目

- [ai-hedge-fund-skill](https://github.com/erongcao/ai-hedge-fund-skill) - AI 对冲基金技能（Kronos 模型）
- [okx-cex-skill](https://github.com/erongcao/okx-cex-skill) - OKX CEX 交易技能

---

## 许可证

MIT License

---

## 更新日志

详见 [CHANGELOG.md](./CHANGELOG.md)
