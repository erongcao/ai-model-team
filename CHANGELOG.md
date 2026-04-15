# AI Model Team Changelog

## [2.0.0] - 2026-04-15

### 🆕 Added
- **FinBERT Adapter** - 新增 FinBERT 金融情绪分析模型支持
  - 支持 `finbert-base` (ProsusAI/finbert)
  - 支持 `finbert-crypto` (burakutf/finetuned-finbert-crypto)
  - 支持 `finbert-twitter` (StephanAkkerman/FinTwitBERT-sentiment)
- **Social Sentiment Provider** - 社会情绪数据模块
  - CryptoPanic 新闻聚合 + 社区投票
  - Reddit 社区讨论情绪分析
  - CoinDesk/Cointelegraph RSS 新闻源
- **OKX Data Provider** - 丰富的市场数据源
  - 订单簿深度分析
  - 资金费率历史
  - 持仓量数据
  - 70+ 技术指标
- **Four-Model Ensemble** - 四模型协同预测
  - Kronos-base (价格走势)
  - TimesFM-2.5 (时序预测)
  - Chronos-2 (分位数预测)
  - FinBERT-sentiment (文本情绪)
- **Environment Configuration** - 环境变量支持
  - `.env` 文件存储 API 密钥
  - `.gitignore` 保护敏感信息

### 🔧 Changed
- **Chronos Adapter** - 完整重写
  - 支持 `Chronos2Pipeline` 加载 amazon/chronos-2
  - 正确处理 3D tensor 输出 (1, n_quantiles, pred_len)
  - 修复 `torch_dtype` → `dtype` 弃用警告
- **OKX Data Provider** - 修复数据格式兼容性
  - 支持 list 和 dict 两种返回格式
  - 修复 `get_klines()` 字典访问错误
- **All Adapters** - 移除硬编码路径
  - 使用 `os.environ.get()` + `os.path.expanduser('~')`
- **Error Handling** - 增强错误处理
  - 所有 `requests.get()` 添加 try/except
  - 添加 `raise_for_status()` 检查

### 📦 Added Files
- `README.md` - 项目文档
- `requirements.txt` - Python 依赖
- `.gitignore` - Git 忽略配置
- `.env` - API 密钥存储（不在版本控制中）
- `config.py` - 配置管理模块
- `okx_data_provider.py` - OKX 数据提供模块
- `social_sentiment_provider.py` - 社会情绪数据模块
- `finbert_adapter.py` - FinBERT 模型适配器
- `btc_short_analysis.py` - 快速分析脚本

### 🐛 Fixed
- `timesfm_adapter.py` - 修复 `ForecastConfig` 导入和 `tfm.compile()` 调用
- `kronos_adapter.py` - 修复时间戳列名兼容性
- `moirai_adapter.py` - 修复 `torch_dtype` 弃用警告
- `model_team.py` - 添加 `--social` 参数支持社会情绪分析

## [1.0.0] - 2024-XX-XX

### 🎉 Initial Release
- Kronos-base 模型支持
- Chronos-t5-base 模型支持
- TimesFM-2.5 模型支持
- MOIRAI 模型支持
- 基础三模型协同预测
