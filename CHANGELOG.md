# AI Model Team Changelog

## [2.0.0] - 2026-04-15

### 🆕 Added

#### 模型层
- **FinBERT Adapter** - 新增 FinBERT 金融情绪分析模型
  - `finbert-base` (ProsusAI/finbert)
  - `finbert-crypto` (burakutf/finetuned-finbert-crypto)
  - `finbert-twitter` (StephanAkkerman/FinTwitBERT-sentiment)
- **Four-Model Ensemble** - 四模型协同预测
  - Kronos-base, TimesFM-2.5, Chronos-2, FinBERT-sentiment

#### 数据层
- **OKX Data Provider** - 丰富的市场数据源
  - K线、订单簿、资金费率、持仓量、70+ 技术指标
- **Social Sentiment Provider (增强版)** - 社会情绪数据
  - CryptoPanic 新闻聚合 + 社区投票
  - Reddit r/cryptocurrency 情绪分析
  - CoinDesk/Cointelegraph RSS
  - **去重机制** (精确匹配 + 相似度)
  - **垃圾过滤** (推广帖、机器人检测)
  - **来源权重** (不同来源不同权重)
  - **时间衰减** (半衰期 180 分钟)

#### P0 基础设施 (生产级)
- **CI/CD** - GitHub Actions 冒烟测试
  - 全新环境安装测试
  - 端到端预测链路测试
  - Lock 文件生成
- **data_quality.py** - 数据质量与校验
  - UTC 时区统一
  - 数据完整率检查 (≥98%)
  - Schema 校验 (OHLC 关系)
  - 多源时间对齐 (容忍 60s)
- **risk_control.py** - 风控闸门与熔断
  - 仓位限制 (单标 10%)
  - 止损/止盈 (2%/4%)
  - 日内回撤熔断 (3%)
  - 连亏熔断 (4次 → 60min冷却)
- **observability.py** - 可观测性
  - JSON 结构化日志
  - trace_id/request_id 追踪
  - 指标埋点 (延迟/失败率/新鲜度)
  - Webhook 告警系统
  - 敏感信息脱敏
- **retry.py** - 重试策略
  - 指数退避 (base × 2^attempt)
  - 超时控制 (默认 20s)
  - 熔断模式
- **config.py** - 统一配置管理
  - 所有参数支持环境变量
  - 运行时配置校验
  - 生产环境检查

#### P1 策略增强
- **trading_cost.py** - 交易成本模型
  - 手续费计算 (双向收取)
  - 滑点估算 (按流动性分层)
  - 市场冲击成本
  - 成本后盈利判断
- **validation.py** - Walk-Forward 验证
  - 时序交叉验证 (无数据泄漏)
  - 方向准确率
  - Brier Score (概率校准)
  - Sharpe Ratio / 最大回撤
- **ensemble.py** - 动态加权融合
  - Isotonic 置信度校准
  - 市场状态检测 (趋势/震荡/高波动)
  - 动态权重调整
  - 各模型贡献分析

#### P2 生产级
- **model_registry.py** - 模型注册表
  - 版本追踪 (version/训练数据区间)
  - 特征签名 (SHA256)
  - 状态管理 (active/deprecated)
  - 元数据存储
- **drift_detection.py** - 漂移检测
  - PSI (Population Stability Index)
  - KL 散度
  - 命中率漂移监控
  - 连续漂移告警 (3次触发)
- **execution.py** - 智能订单执行
  - 订单类型选择 (limit/market/post_only)
  - 大单拆分优化
  - 滑点估算
  - 执行重试
- **security.py** - 安全与合规
  - API Key 轮换 (90天)
  - 最小权限原则
  - 审计日志
  - 敏感数据脱敏
- **runbook.py** - 运行手册
  - 常见故障排查指南
  - 配置回滚管理
  - 值班健康检查清单
  - 升级联系人

#### 依赖
- **requirements.txt** - 精确版本锁定
  - 所有依赖使用 `==` 精确版本
  - 可重现构建环境

### 🔧 Changed

- **Chronos Adapter** - 完整重写
  - 支持 `Chronos2Pipeline` (amazon/chronos-2)
  - 正确处理 3D tensor 输出
  - 修复 `torch_dtype` → `dtype`
- **OKX Data Provider** - 修复数据格式兼容
  - 支持 list 和 dict 返回格式
- **All Adapters** - 移除硬编码路径
  - 使用环境变量
- **Error Handling** - 增强错误处理
  - try/except 全覆盖
  - raise_for_status() 检查

### 🐛 Fixed

- `timesfm_adapter.py` - `ForecastConfig` 导入, `tfm.compile()`
- `kronos_adapter.py` - 时间戳列名兼容
- `moirai_adapter.py` - `torch_dtype` 弃用警告
- `model_team.py` - `--social` 参数

### 📦 Files Structure

```
ai-model-team/
├── .github/workflows/ci.yml          # NEW: CI 冒烟测试
├── scripts/
│   ├── data_quality.py              # NEW: P0 数据质量
│   ├── risk_control.py             # NEW: P0 风控
│   ├── observability.py             # NEW: P0 可观测
│   ├── retry.py                    # NEW: P0 重试
│   ├── trading_cost.py              # NEW: P1 成本
│   ├── validation.py                # NEW: P1 验证
│   ├── ensemble.py                 # NEW: P1 融合
│   ├── model_registry.py           # NEW: P2 注册表
│   ├── drift_detection.py          # NEW: P2 漂移
│   ├── execution.py                 # NEW: P2 执行
│   ├── security.py                 # NEW: P2 安全
│   └── runbook.py                  # NEW: P2 手册
```

## [1.0.0] - 2024-XX-XX

### 🎉 Initial Release
- Kronos-base 模型支持
- Chronos-t5-base 模型支持
- TimesFM-2.5 模型支持
- MOIRAI 模型支持
- 基础三模型协同预测
