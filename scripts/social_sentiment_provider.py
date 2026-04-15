"""
Social Sentiment Data Provider - 完整版
整合多渠道社会情绪数据
"""
import requests
import feedparser
import re
from typing import List, Dict
from datetime import datetime


class SocialSentimentProvider:
    """社会情绪数据提供者"""
    
    REDDIT_HEADERS = {"User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36"}
    
    RSS_SOURCES = {
        "coindesk": "https://www.coindesk.com/arc/outboundfeeds/rss/",
        "cointelegraph": "https://cointelegraph.com/rss",
        "decrypt": "https://decrypt.co/feed",
    }
    
    @staticmethod
    def get_cryptopanic_news(currency: str = "BTC", limit: int = 20) -> List[Dict]:
        """获取 CryptoPanic 新闻"""
        try:
            url = f"https://cryptopanic.com/news/{currency.lower()}/"
            headers = {"User-Agent": "Mozilla/5.0"}
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code != 200:
                return []
            html = response.text
            news_items = []
            # 匹配模式
            pattern = r'data-title="([^"]+)".*?data-votes-up="(\d+)".*?data-votes-down="(\d+)"'
            matches = re.findall(pattern, html, re.DOTALL)
            for title, up, down in matches[:limit]:
                up_votes = int(up) if up else 0
                down_votes = int(down) if down else 0
                total = up_votes + down_votes
                if total > 0:
                    sentiment = (up_votes - down_votes) / total
                    sentiment_label = "positive" if sentiment > 0.2 else "negative" if sentiment < -0.2 else "neutral"
                else:
                    sentiment = 0
                    sentiment_label = "neutral"
                news_items.append({
                    "source": "cryptopanic",
                    "title": title.strip(),
                    "sentiment_score": round(sentiment, 3),
                    "sentiment_label": sentiment_label,
                    "up_votes": up_votes,
                    "down_votes": down_votes,
                })
            return news_items
        except Exception as e:
            print(f"CryptoPanic 获取失败: {e}")
            return []
    
    @staticmethod
    def get_reddit_sentiment(subreddit: str = "cryptocurrency", limit: int = 25) -> Dict:
        """获取 Reddit 社区情绪"""
        try:
            url = f"https://www.reddit.com/r/{subreddit}/hot.json?limit={limit}"
            response = requests.get(url, headers=SocialSentimentProvider.REDDIT_HEADERS, timeout=15)
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
                    "bullish_keywords": 0,
                    "bearish_keywords": 0,
                    "fomo_keywords": 0,
                    "fear_keywords": 0
                },
                "hot_topics": [],
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
                        "score": post_data.get("score", 0),
                    })
            total = sum(sentiment_data["sentiment_indicators"].values())
            if total > 0:
                b_ratio = sentiment_data["sentiment_indicators"]["bullish_keywords"] / total
                br_ratio = sentiment_data["sentiment_indicators"]["bearish_keywords"] / total
                if b_ratio > br_ratio * 1.5:
                    sentiment_data["overall_sentiment"] = "bullish"
                elif br_ratio > b_ratio * 1.5:
                    sentiment_data["overall_sentiment"] = "bearish"
                else:
                    sentiment_data["overall_sentiment"] = "mixed"
            else:
                sentiment_data["overall_sentiment"] = "neutral"
            return sentiment_data
        except Exception as e:
            return {"error": str(e)}
    
    @staticmethod
    def get_rss_news(source: str = "coindesk", limit: int = 10) -> List[Dict]:
        """获取 RSS 新闻源"""
        rss_url = SocialSentimentProvider.RSS_SOURCES.get(source)
        if not rss_url:
            return []
        try:
            feed = feedparser.parse(rss_url)
            news_items = []
            for entry in feed.entries[:limit]:
                title = entry.get("title", "").lower()
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
                })
            return news_items
        except Exception as e:
            print(f"RSS {source} 获取失败: {e}")
            return []
    
    @staticmethod
    def get_combined_sentiment(currency: str = "BTC") -> Dict:
        """获取综合社会情绪"""
        print(f"📊 获取 {currency} 社会情绪数据...")
        
        # 1. CryptoPanic
        print("  ▶ CryptoPanic...", end=" ", flush=True)
        cryptopanic_news = SocialSentimentProvider.get_cryptopanic_news(currency, limit=10)
        print(f"✅ {len(cryptopanic_news)} 条")
        
        # 2. Reddit
        print("  ▶ Reddit...", end=" ", flush=True)
        reddit_data = SocialSentimentProvider.get_reddit_sentiment("cryptocurrency", limit=25)
        if "error" not in reddit_data:
            print(f"✅ {reddit_data.get('posts_analyzed', 0)} 帖")
        else:
            print(f"❌ {reddit_data.get('error')}")
        
        # 3. RSS
        print("  ▶ RSS 源...", end=" ", flush=True)
        rss_news = []
        for source in ["coindesk", "cointelegraph"]:
            news = SocialSentimentProvider.get_rss_news(source, limit=5)
            rss_news.extend(news)
        print(f"✅ {len(rss_news)} 条")
        
        all_news = cryptopanic_news + rss_news
        pos_count = sum(1 for n in all_news if n.get("sentiment") == "positive" or n.get("sentiment_label") == "positive")
        neg_count = sum(1 for n in all_news if n.get("sentiment") == "negative" or n.get("sentiment_label") == "negative")
        neutral_count = len(all_news) - pos_count - neg_count
        
        total_news = len(all_news)
        news_score = (pos_count - neg_count) / total_news if total_news > 0 else 0
        
        indicators = reddit_data.get("sentiment_indicators", {})
        rb = indicators.get("bullish_keywords", 0)
        rr = indicators.get("bearish_keywords", 0)
        rt = rb + rr
        reddit_score = (rb - rr) / rt if rt > 0 else 0
        
        combined = news_score * 0.6 + reddit_score * 0.4
        overall = "bullish" if combined > 0.3 else "bearish" if combined < -0.3 else "neutral"
        
        return {
            "currency": currency,
            "timestamp": datetime.now().isoformat(),
            "overall_sentiment": overall,
            "sentiment_score": round(combined, 3),
            "breakdown": {
                "news_sentiment": round(news_score, 3),
                "reddit_sentiment": round(reddit_score, 3),
            },
            "statistics": {
                "news_total": total_news,
                "news_positive": pos_count,
                "news_negative": neg_count,
                "news_neutral": neutral_count,
                "reddit_posts": reddit_data.get("posts_analyzed", 0),
            },
            "recent_headlines": [n.get("title", "") for n in all_news[:5]],
            "hot_topics": reddit_data.get("hot_topics", [])[:3],
            "reddit_raw": reddit_data,
        }


def get_social_sentiment(currency: str = "BTC") -> Dict:
    return SocialSentimentProvider.get_combined_sentiment(currency)

def get_news_sentiment(currency: str = "BTC") -> List[Dict]:
    cryptopanic = SocialSentimentProvider.get_cryptopanic_news(currency, limit=10)
    rss = []
    for source in ["coindesk", "cointelegraph"]:
        rss.extend(SocialSentimentProvider.get_rss_news(source, limit=5))
    return cryptopanic + rss

def get_reddit_discussion(subreddit: str = "cryptocurrency") -> Dict:
    return SocialSentimentProvider.get_reddit_sentiment(subreddit)


if __name__ == "__main__":
    sentiment = get_social_sentiment("BTC")
    print(f"综合情绪: {sentiment['overall_sentiment'].upper()}")
    print(f"情绪得分: {sentiment['sentiment_score']}")
    print(f"新闻统计: {sentiment['statistics']}")
