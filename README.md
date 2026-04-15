# AI Model Team

**Version:** 2.0.0  
**Release Date:** 2026-04-15  
**Author:** NeoQuasar AI Lab

多模型协同预测系统 —— 整合 Kronos、Chronos-2、TimesFM、FinBERT 四大 AI 模型，对 OKX 加密货币进行多角度分析，输出综合交易信号。

---

## v2.0.0 更新亮点

### 🆕 新增功能

| 功能 | 说明 |
|------|------|
| **FinBERT 情绪分析** | 基于 HuggingFace FinBERT，分析新闻/社交媒体情绪，输出交易信号 |
| **社会情绪数据模块** | 整合 CryptoPanic + Reddit + RSS 三数据源 |
| **OKX CEX 数据集成** | 订单簿、资金费率、持仓量、70+ 技术指标 |
| **四模型协同预测** | Kronos + TimesFM + Chronos-2 + FinBERT 投票融合 |

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
| **FinBERT-sentiment** | HuggingFace | 金融文本情绪分析 | 新闻/社交情绪 | 20% |

### 模型详情

#### 1. Kronos-base (NeoQuasar)
- **模型路径**: `~/.agents/skills/ai-hedge-fund-skill/models/kronos-base`
- **输入**: OKX K线数据 (OHLCV)
- **输出**: 价格方向、涨跌百分比、趋势强度
- **特点**: 专门针对加密货币K线训练，识别庄家行为

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

#### 4. FinBERT-sentiment (HuggingFace)
- **模型ID**: `ProsusAI/finbert` (HuggingFace)
- **输入**: 文本（新闻标题、社交媒体内容）
- **输出**: 情绪分类 (positive/negative/neutral) + 置信度
- **特点**: 专门针对金融文本训练

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
├── requirements.txt               # Python 依赖
├── .gitignore                    # Git 忽略配置
├── .env                          # 环境变量（API密钥，不在版本控制）
├── btc_short_analysis.py         # 快速分析脚本（BTC专用）
│
└── scripts/
    ├── model_team.py              # ⭐ 主入口（多模型可配置）
    ├── run_team.py                # 统一 1H×24 预测脚本
    ├── config.py                  # 配置管理（环境变量加载）
    │
    ├── kronos_adapter.py          # Kronos 模型适配器
    ├── chronos_adapter.py         # Chronos 模型适配器
    ├── timesfm_adapter.py         # TimesFM 模型适配器
    ├── moirai_adapter.py          # MOIRAI 模型适配器
    ├── finbert_adapter.py         # FinBERT 模型适配器
    │
    ├── okx_data_provider.py      # OKX 数据提供模块
    └── social_sentiment_provider.py  # 社会情绪数据模块
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

## 依赖

### 核心依赖

| 包 | 版本 | 用途 |
|----|------|------|
| Python | 3.10+ | 运行环境 |
| numpy | latest | 数值计算 |
| pandas | latest | 数据处理 |
| requests | latest | HTTP 请求 |
| torch | latest | 深度学习框架 |

### 模型依赖

| 包 | 版本 | 用途 |
|----|------|------|
| timesfm | latest | Google TimesFM 模型 |
| chronos-forest | ≥3.0 | Amazon Chronos 模型 |
| transformers | ≥4.57 | HuggingFace 模型加载 |
| feedparser | latest | RSS 新闻解析 |

### 安装方式

```bash
# 方式1: 使用 requirements.txt
pip install -r requirements.txt

# 方式2: 单独安装
pip install numpy pandas requests torch transformers feedparser
pip install timesfm
pip install "git+https://github.com/amazon-science/chronos-forecasting.git"
```

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
