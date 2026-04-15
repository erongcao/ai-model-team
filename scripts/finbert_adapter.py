"""
FinBERT Adapter for AI Model Team
FinBERT: 金融文本情绪分析模型
基于HuggingFace FinBERT，分析新闻/社交媒体情绪
输出交易信号
"""
import sys
import os
import torch
import numpy as np
from typing import Dict, List
from datetime import datetime

# 导入社会情绪数据模块
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from social_sentiment_provider import get_news_sentiment, get_social_sentiment


class FinBERTAdapter:
    """FinBERT金融情绪分析模型"""
    name = "FinBERT-sentiment"
    institution = "HuggingFace"
    params = "110M"
    specialty = "文本情绪/金融新闻"
    _model = None
    _tokenizer = None
    
    # 情绪阈值配置
    BULLISH_THRESHOLD = 0.3  # 积极情绪阈值
    BEARISH_THRESHOLD = -0.3  # 消极情绪阈值
    
    def __init__(self, variant: str = "finbert-base"):
        self.variant = variant
        self.model_name = self._get_model_name(variant)
        
    def _get_model_name(self, variant: str) -> str:
        """获取模型名称"""
        models = {
            "finbert-base": "ProsusAI/finbert",
            "finbert-crypto": "burakutf/finetuned-finbert-crypto",
            "finbert-twitter": "StephanAkkerman/FinTwitBERT-sentiment",
        }
        return models.get(variant, "ProsusAI/finbert")
    
    def load(self):
        """加载FinBERT模型 (带15秒超时)"""
        if FinBERTAdapter._model is None:
            import threading
            import sys
            
            result = {"success": False, "error": None}
            
            def _try_load():
                try:
                    from transformers import AutoTokenizer, AutoModelForSequenceClassification, pipeline
                    import os
                    
                    os.environ['HF_HUB_DISABLE_SYMLINKS'] = '1'
                    os.environ['HF_HUB_DISABLE_TELEMETRY'] = '1'
                    
                    tokenizer = AutoTokenizer.from_pretrained(self.model_name, timeout=15)
                    model = AutoModelForSequenceClassification.from_pretrained(self.model_name, timeout=15)
                    
                    FinBERTAdapter._tokenizer = tokenizer
                    FinBERTAdapter._model = model
                    FinBERTAdapter._classifier = pipeline(
                        "sentiment-analysis",
                        model=model,
                        tokenizer=tokenizer,
                        device=0 if torch.cuda.is_available() else -1
                    )
                    result["success"] = True
                except Exception as e:
                    result["error"] = str(e)
            
            print(f"  加载 {self.model_name}...", end=" ", flush=True)
            
            thread = threading.Thread(target=_try_load, daemon=True)
            thread.start()
            thread.join(timeout=15)  # 最多等待15秒
            
            if thread.is_alive():
                # 超时 - 回退到关键词分析
                print(f"❌ 加载超时")
                FinBERTAdapter._model = "fallback"
            elif result["success"]:
                print(f"✅")
            else:
                print(f"❌ {result['error'][:50]}")
                FinBERTAdapter._model = "fallback"
                
        return FinBERTAdapter._model
    
    def analyze_texts(self, texts: List[str]) -> Dict:
        """分析文本列表的情绪"""
        if not texts:
            return {"sentiment": "neutral", "score": 0, "confidence": 30}
        
        model = self.load()
        
        if model == "fallback":
            # 回退到关键词分析
            return self._keyword_analysis(texts)
        
        try:
            # 使用FinBERT分析
            results = []
            for text in texts[:10]:  # 限制分析数量避免超时
                if len(text) > 512:
                    text = text[:512]  # 截断长文本
                result = FinBERTAdapter._classifier(text)[0]
                results.append(result)
            
            # 计算平均情绪
            positive_score = 0
            negative_score = 0
            neutral_score = 0
            
            for r in results:
                label = r['label'].lower()
                score = r['score']
                
                if 'positive' in label or 'bull' in label:
                    positive_score += score
                elif 'negative' in label or 'bear' in label:
                    negative_score += score
                else:
                    neutral_score += score
            
            total = len(results)
            if total > 0:
                avg_positive = positive_score / total
                avg_negative = negative_score / total
                
                # 计算净情绪得分 (-1 到 1)
                net_sentiment = avg_positive - avg_negative
                
                # 判断信号
                if net_sentiment > self.BULLISH_THRESHOLD:
                    signal = "bullish"
                    confidence = min(95, 50 + int(net_sentiment * 50))
                elif net_sentiment < self.BEARISH_THRESHOLD:
                    signal = "bearish"
                    confidence = min(95, 50 + int(abs(net_sentiment) * 50))
                else:
                    signal = "neutral"
                    confidence = 50
                    
                return {
                    "sentiment": signal,
                    "score": round(net_sentiment, 3),
                    "confidence": confidence,
                    "positive_ratio": round(avg_positive, 3),
                    "negative_ratio": round(avg_negative, 3),
                    "samples_analyzed": total
                }
            
        except Exception as e:
            print(f"FinBERT分析失败: {e}")
            return self._keyword_analysis(texts)
        
        return {"sentiment": "neutral", "score": 0, "confidence": 30}
    
    def _keyword_analysis(self, texts: List[str]) -> Dict:
        """关键词回退分析"""
        bullish_words = ['surge', 'rally', 'bull', 'pump', 'moon', 'breakout', 'adoption', 'partnership', 'growth']
        bearish_words = ['crash', 'dump', 'bear', 'fall', 'decline', 'ban', 'hack', 'fear', 'panic']
        
        pos_count = 0
        neg_count = 0
        
        for text in texts:
            text_lower = text.lower()
            for word in bullish_words:
                if word in text_lower:
                    pos_count += 1
            for word in bearish_words:
                if word in text_lower:
                    neg_count += 1
        
        total = pos_count + neg_count
        if total > 0:
            net_sentiment = (pos_count - neg_count) / total
            if net_sentiment > 0.3:
                signal = "bullish"
                confidence = min(95, 50 + int(net_sentiment * 40))
            elif net_sentiment < -0.3:
                signal = "bearish"
                confidence = min(95, 50 + int(abs(net_sentiment) * 40))
            else:
                signal = "neutral"
                confidence = 50
        else:
            signal = "neutral"
            confidence = 30
            net_sentiment = 0
        
        return {
            "sentiment": signal,
            "score": round(net_sentiment, 3),
            "confidence": confidence,
            "method": "keyword_fallback",
            "samples_analyzed": len(texts)
        }
    
    def predict(self, symbol: str, bar: str = "4H", lookback: int = 24, pred_len: int = 24) -> Dict:
        """
        FinBERT预测：基于新闻和社交媒体情绪
        
        注意：FinBERT不预测价格，而是分析市场情绪
        """
        try:
            # 提取货币代码
            currency = symbol.split("-")[0] if "-" in symbol else symbol
            
            # 获取新闻数据
            print(f"  获取{currency}新闻数据...", end=" ", flush=True)
            news_data = get_news_sentiment(currency)
            print(f"✅ {len(news_data)}条")
            
            if not news_data:
                return self._error_result("无法获取新闻数据")
            
            # 提取文本内容
            texts = [n.get("title", "") for n in news_data if n.get("title")]
            
            # 分析情绪
            print(f"  FinBERT分析中...", end=" ", flush=True)
            sentiment_result = self.analyze_texts(texts)
            print(f"✅")
            
            # 转换为统一格式
            signal = sentiment_result.get("sentiment", "neutral")
            confidence = sentiment_result.get("confidence", 50)
            score = sentiment_result.get("score", 0)
            
            # 模拟价格变化（基于情绪强度）
            # 实际应用中，FinBERT不提供价格预测，只提供情绪
            price_change = score * 2  # 简单映射：情绪得分 -> 价格变化
            
            # 获取当前价格（从社会情绪模块）
            try:
                social_data = get_social_sentiment(currency)
                current_price = 0  # FinBERT不关注具体价格
            except:
                current_price = 0
            
            # 计算趋势强度
            trend_strength = min(100, abs(score) * 100)
            
            # 分析样本统计
            samples = sentiment_result.get("samples_analyzed", 0)
            method = sentiment_result.get("method", "finbert")
            
            return {
                "model": self.name,
                "institution": self.institution,
                "params": self.params,
                "specialty": self.specialty,
                "signal": signal,
                "confidence": confidence,
                "trend_strength": round(trend_strength, 1),
                "current_price": current_price,
                "forecast_price": current_price * (1 + price_change/100) if current_price else 0,
                "price_change_pct": round(price_change, 2),
                "forecast_low": 0,
                "forecast_high": 0,
                "up_bars": 0,
                "total_bars": 0,
                "reasoning": f"FinBERT文本情绪分析: {samples}条新闻, 情绪得分{score:+.3f} ({method}), 整体{signal.upper()}",
                "details": {
                    "sentiment_score": score,
                    "positive_ratio": sentiment_result.get("positive_ratio", 0),
                    "negative_ratio": sentiment_result.get("negative_ratio", 0),
                    "sample_headlines": texts[:3]
                }
            }
            
        except Exception as e:
            return self._error_result(str(e))
    
    def _error_result(self, msg: str) -> Dict:
        return {
            "model": self.name,
            "institution": self.institution,
            "params": self.params,
            "specialty": self.specialty,
            "signal": "neutral",
            "confidence": 30,
            "trend_strength": 0,
            "current_price": 0,
            "forecast_price": 0,
            "price_change_pct": 0,
            "forecast_low": 0,
            "forecast_high": 0,
            "up_bars": 0,
            "total_bars": 0,
            "reasoning": f"FinBERT分析失败: {str(msg)[:100]}"
        }


# 便捷函数
def get_finbert_sentiment(texts: List[str]) -> Dict:
    """快速获取FinBERT情绪分析"""
    adapter = FinBERTAdapter()
    return adapter.analyze_texts(texts)


if __name__ == "__main__":
    # 测试
    adapter = FinBERTAdapter()
    result = adapter.predict("BTC-USDT-SWAP")
    print("\n" + "="*60)
    print(f"FinBERT信号: {result['signal'].upper()}")
    print(f"置信度: {result['confidence']}")
    print(f"分析: {result['reasoning']}")
