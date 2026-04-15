"""
Social Sentiment Data Provider - 完整版 (P1 Enhanced)
整合多渠道社会情绪数据,含去噪、来源权重、时间衰减
"""
import requests
import feedparser
import re
import hashlib
from typing import List, Dict, Set, Optional
from datetime import datetime, timedelta, timezone
from collections import Counter

# P1 配置
SENTIMENT_SOURCE_WEIGHTS = {"news": 0.5, "reddit": 0.3, "rss": 0.2}
SENTIMENT_HALF_LIFE_MIN = 180  # 3小时半衰期
SENTIMENT_SPAM_FILTER = True


class ContentDeduplicator:
    """内容去重"""

    def __init__(self):
        self.seen_hashes: Set[str] = set()
        self.seen_titles: Set[str] = set()

    def normalize(self, text: str) -> str:
        """标准化文本用于比较"""
        return re.sub(r'[^\w\s]', '', text.lower()).strip()[:100]

    def is_duplicate(self, text: str) -> bool:
        """检查是否重复"""
        normalized = self.normalize(text)

        # 精确匹配
        if normalized in self.seen_titles:
            return True

        # 相似度匹配 (简单hash)
        text_hash = hashlib.md5(normalized.encode()).hexdigest()[:16]
        if text_hash in self.seen_hashes:
            return True

        # 添加到已见集合
        self.seen_titles.add(normalized)
        self.seen_hashes.add(text_hash)
        return False

    def reset(self):
        self.seen_hashes.clear()
        self.seen_titles.clear()


class SpamFilter:
    """垃圾内容过滤"""

    SPAM_PATTERNS = [
        r'click here', r'buy now', r'limited time',
        r'Act now', r'discount', r'free money',
        r'guaranteed', r'100% winning',
        r'bot account', r'auto-trading bot'
    ]

    LOW_QUALITY_KEYWORDS = [
        r'^RT @', r'follow me', r'subscribe',
        r'check my profile', r'dm me'
    ]

    @classmethod
    def is_spam(cls, title: str) -> bool:
        """判断是否为垃圾内容"""
        title_lower = title.lower()

        # 检查垃圾模式
        for pattern in cls.SPAM_PATTERNS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True

        # 检查低质量模式
        for pattern in cls.LOW_QUALITY_KEYWORDS:
            if re.search(pattern, title_lower, re.IGNORECASE):
                return True

        return False


class SocialSentimentProvider:
    """社会情绪数据提供者 (P1增强版)"""

    REDDIT_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}

    RSS_SOURCES = {
        # 加密货币
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "decrypt": "https://decrypt.co/feed",
        # 四大新闻社 (通用财经)
        "bloomberg": "https://feeds.bloomberg.com/markets/news.rss",
        "wsj": "https://feeds.a.dj.com/rss/RSSMarketsMain.xml",
        "cnbc": "https://www.cnbc.com/id/100003114/device/rss/rss.html",
        "ft": "https://www.ft.com/rss/home",
        # 其他主流媒体
        "bbc_business": "https://feeds.bbci.co.uk/news/business/rss.xml",
        "economist": "https://www.economist.com/finance-and-economics/rss.xml",
        "nytimes": "https://rss.nytimes.com/services/xml/rss/nyt/Business.xml",
    }

    # 来源权重
    SOURCE_WEIGHTS = {
        "reddit": 0.25,
        # 加密货币
        "coindesk": 0.15,
        "cointelegraph": 0.15,
        "decrypt": 0.05,
        # 四大新闻社
        "bloomberg": 0.10,
        "wsj": 0.08,
        "cnbc": 0.08,
        "ft": 0.05,
        # 其他媒体
        "bbc_business": 0.05,
        "economist": 0.02,
        "nytimes": 0.02
    }

    def __init__(self):
        self.dedup = ContentDeduplicator()
        self.spam_filter = SpamFilter()
        self.seen_hashes: Set[str] = set()

    def get_cryptopanic_news(self, currency: str = "BTC", limit: int = 20) -> List[Dict]:
        """获取 CryptoPanic 新闻"""
        try:
            url = f"https://cryptopanic.com/news/{currency.lower()}/"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            html = response.text
            news_items = []
            pattern = r'data-title="([^"]+)".*?data-votes-up="(\d+)".*?data-votes-down="(\d+)"'
            matches = re.findall(pattern, html, re.DOTALL)
            for title, up, down in matches[:limit]:
                # 去重
                if self.dedup.is_duplicate(title):
                    continue

                # 垃圾过滤
                if SENTIMENT_SPAM_FILTER and SpamFilter.is_spam(title):
                    continue

                up_votes = int(up) if up else 0
                down_votes = int(down) if down else 0
                total = up_votes + down_votes
                sentiment = (up_votes - down_votes) / total if total > 0 else 0
                sentiment_label = "positive" if sentiment > 0.2 else "negative" if sentiment < -0.2 else "neutral"

                news_items.append({
                    "source": "cryptopanic",
                    "title": title.strip(),
                    "sentiment_score": round(sentiment, 3),
                    "sentiment_label": sentiment_label,
                    "up_votes": up_votes,
                    "down_votes": down_votes,
                    "weight": self.SOURCE_WEIGHTS.get("cryptopanic", 0.3)
                })
            return news_items
        except:
            return []

    def get_reddit_sentiment(self, subreddit: str = "cryptocurrency", limit: int = 25) -> Dict:
        """获取 Reddit 社区情绪"""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            response = requests.get(url, headers=self.REDDIT_HEADERS, timeout=15)
            if response.status_code != 200:
                return {"error": f"HTTP {response.status_code}"}
            data = response.json()
            posts = data.get("data", {}).get("children", [])
            sentiment_data = {
                "source": "reddit",
                "subreddit": subreddit,
                "posts_analyzed": 0,
                "total_score": 0,
                "sentiment_indicators": {
                    "bullish_keywords": 0, "bearish_keywords": 0,
                    "fomo_keywords": 0, "fear_keywords": 0
                },
                "hot_topics": []
            }
            bullish_words = ['bull', 'bullish', 'moon', 'pump', 'hodl', 'buy', 'long', 'breakout', 'ath']
            bearish_words = ['bear', 'bearish', 'dump', 'crash', 'sell', 'short', 'bottom', 'capitulation']
            fomo_words = ['fomo', 'getting in', 'jump in', "don't miss"]
            fear_words = ['panic', 'scared', 'worried', 'crash coming', 'bubble', 'scam', 'rug pull']

            for post in posts:
                post_data = post.get("data", {})
                title = post_data.get("title", "").lower()
                selftext = post_data.get("selftext", "").lower()
                full_text = title + " " + selftext

                # 去重
                if self.dedup.is_duplicate(post_data.get("title", "")):
                    continue

                sentiment_data["posts_analyzed"] += 1
                sentiment_data["total_score"] += post_data.get("score", 0)

                for word in bullish_words:
                    if word in full_text:
                        sentiment_data["sentiment_indicators"]["bullish_keywords"] += 1
                for word in bearish_words:
                    if word in full_text:
                        sentiment_data["sentiment_indicators"]["bearish_keywords"] += 1
                for word in fomo_words:
                    if word in full_text:
                        sentiment_data["sentiment_indicators"]["fomo_keywords"] += 1
                for word in fear_words:
                    if word in full_text:
                        sentiment_data["sentiment_indicators"]["fear_keywords"] += 1

                if post_data.get("score", 0) > 50:
                    sentiment_data["hot_topics"].append({
                        "title": post_data.get("title", "")[:100],
                        "score": post_data.get("score", 0)
                    })

            total = sum(sentiment_data["sentiment_indicators"].values())
            if total > 0:
                b = sentiment_data["sentiment_indicators"]["bullish_keywords"] / total
                br = sentiment_data["sentiment_indicators"]["bearish_keywords"] / total
                sentiment_data["overall_sentiment"] = "bullish" if b > br * 1.5 else "bearish" if br > b * 1.5 else "mixed"
            else:
                sentiment_data["overall_sentiment"] = "neutral"

            # 添加权重
            sentiment_data["weight"] = self.SOURCE_WEIGHTS.get("reddit", 0.25)
            return sentiment_data
        except Exception as e:
            return {"error": str(e)}

    def get_rss_news(self, source: str = "coindesk", limit: int = 10) -> List[Dict]:
        """获取 RSS 新闻源"""
        rss_url = self.RSS_SOURCES.get(source)
        if not rss_url:
            return []
        try:
            feed = feedparser.parse(rss_url)
            news_items = []
            for entry in feed.entries[:limit]:
                title = entry.get("title", "").lower()

                # 去重
                if self.dedup.is_duplicate(entry.get("title", "")):
                    continue

                positive_words = ['surge', 'rally', 'gain', 'bull', 'breakout', 'adoption', 'partnership']
                negative_words = ['crash', 'dump', 'fall', 'bear', 'ban', 'hack', 'scam', 'fear']
                pos_count = sum(1 for w in positive_words if w in title)
                neg_count = sum(1 for w in negative_words if w in title)
                sentiment = "positive" if pos_count > neg_count else "negative" if neg_count > pos_count else "neutral"

                news_items.append({
                    "source": source,
                    "title": entry.get("title", ""),
                    "link": entry.get("link", ""),
                    "sentiment": sentiment,
                    "weight": self.SOURCE_WEIGHTS.get(source, 0.1)
                })
            return news_items
        except:
            return []

    @staticmethod
    def apply_time_decay(sentiment_items: List[Dict], half_life_min: int = SENTIMENT_HALF_LIFE_MIN) -> List[Dict]:
        """应用时间衰减"""
        now = datetime.now(timezone.utc)
        half_life_delta = timedelta(minutes=half_life_min)

        for item in sentiment_items:
            if "timestamp" not in item:
                item["timestamp"] = now.isoformat()

            try:
                item_time = datetime.fromisoformat(item["timestamp"].replace("Z", "+00:00"))
                age_min = (now - item_time).total_seconds() / 60
                decay = 0.5 ** (age_min / half_life_min)
                item["time_decay"] = decay
                item["age_min"] = age_min
            except:
                item["time_decay"] = 1.0
                item["age_min"] = 0

        return sentiment_items

    def get_combined_sentiment(self, currency: str = "BTC") -> Dict:
        """获取综合社会情绪 (P1增强版) - 已修复: 移除broken的CryptoPanic"""
        print(f"📊 获取 {currency} 社会情绪数据...")

        # Reddit (主要来源)
        print("  ▶ Reddit...", end=" ", flush=True)
        reddit_data = self.get_reddit_sentiment("cryptocurrency", limit=25)
        if "error" not in reddit_data:
            print(f"✅ {reddit_data.get('posts_analyzed', 0)} 帖")
        else:
            print(f"❌ {reddit_data.get('error')}")

        # RSS 源 (扩展: 加密货币 + 四大新闻社 + 主流媒体)
        print("  ▶ RSS 源...", end=" ", flush=True)
        rss_news = []
        rss_sources = [
            "coindesk", "cointelegraph", "decrypt",  # 加密货币
            "bloomberg", "wsj", "cnbc", "ft",  # 四大新闻社
            "bbc_business", "economist", "nytimes"  # 其他主流
        ]
        for source in rss_sources:
            try:
                news = self.get_rss_news(source, limit=5)
                rss_news.extend(news)
            except Exception:
                pass
        print(f"✅ {len(rss_news)} 条")

        # 应用时间衰减
        rss_news = self.apply_time_decay(rss_news)

        # 加权计算 (RSS新闻)
        weighted_sum = 0
        weight_sum = 0

        for item in rss_news:
            weight = item.get("weight", 0.2) * item.get("time_decay", 1.0)
            sentiment = item.get("sentiment_score", 0) if item.get("sentiment_score") is not None else (0.5 if item.get("sentiment") == "positive" else 0.3 if item.get("sentiment") == "negative" else 0)
            weighted_sum += sentiment * weight
            weight_sum += weight

        news_score = weighted_sum / weight_sum if weight_sum > 0 else 0

        # Reddit 情绪
        indicators = reddit_data.get("sentiment_indicators", {})
        rb = indicators.get("bullish_keywords", 0)
        rr = indicators.get("bearish_keywords", 0)
        rt = rb + rr
        reddit_score = (rb - rr) / rt if rt > 0 else 0

        # 综合得分 (RSS 60% + Reddit 40%)
        combined = news_score * 0.6 + reddit_score * 0.4

        return {
            "currency": currency,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "overall_sentiment": "bullish" if combined > 0.3 else "bearish" if combined < -0.3 else "neutral",
            "sentiment_score": round(combined, 3),
            "breakdown": {
                "news_sentiment": round(news_score, 3),
                "reddit_sentiment": round(reddit_score, 3)
            },
            "statistics": {
                "news_total": len(rss_news),
                "news_positive": sum(1 for n in rss_news if n.get("sentiment") == "positive"),
                "news_negative": sum(1 for n in rss_news if n.get("sentiment") == "negative"),
                "reddit_posts": reddit_data.get("posts_analyzed", 0)
            },
            "recent_headlines": [n.get("title", "") for n in rss_news[:5]],
            "hot_topics": reddit_data.get("hot_topics", [])[:3]
        }


def get_social_sentiment(currency: str = "BTC") -> Dict:
    return SocialSentimentProvider().get_combined_sentiment(currency)

def get_news_sentiment(currency: str = "BTC") -> List[Dict]:
    provider = SocialSentimentProvider()
    return provider.get_cryptopanic_news(currency, limit=10)

def get_reddit_discussion(subreddit: str = "cryptocurrency") -> Dict:
    return SocialSentimentProvider().get_reddit_sentiment(subreddit)
