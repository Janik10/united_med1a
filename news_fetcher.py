import requests
import feedparser
import json
import os
from summarizer import summarize_text

# API Keys
NEWSAPI_KEY = os.environ.get("NEWSAPI_KEY")
GUARDIAN_API_KEY = os.environ.get("GUARDIAN_API_KEY")
NYT_API_KEY = os.environ.get("NYT_API_KEY")

# News sources
NEWS_SOURCES = {
    "NewsAPI": f"https://newsapi.org/v2/top-headlines?country=us&pageSize=100&apiKey={NEWSAPI_KEY}",
    "Guardian": f"https://content.guardianapis.com/search?api-key={GUARDIAN_API_KEY}&show-fields=all&page-size=50",
    "NYTimes": f"https://api.nytimes.com/svc/topstories/v2/world.json?api-key={NYT_API_KEY}",
    "GoogleNewsRSS": "https://news.google.com/rss",
    "BBC": "https://feeds.bbci.co.uk/news/world/rss.xml",
    "CNN": "http://rss.cnn.com/rss/cnn_world.rss",
    "BingNewsRSS": "https://www.bing.com/news/search?q=latest&format=rss",
    "AlJazeera": "https://www.aljazeera.com/xml/rss/all.xml",
    "NPR": "https://www.npr.org/rss/rss.php?id=1001",
    "AP": "https://apnews.com/hub/ap-top-news.rss",
    "Reuters": "http://feeds.reuters.com/reuters/topNews",
    "FoxNews": "http://feeds.foxnews.com/foxnews/latest"
}

news_cache = []
CACHE_FILE = "news_cache.json"

def fetch_news_from_api(url):
    """Fetch news from an API endpoint."""
    try:
        response = requests.get(url, timeout=10)
        data = response.json()

        if "articles" in data:  # NewsAPI format
            return [{
                "title": item.get("title", "No title"),
                "description": item.get("description", ""),
                "content": item.get("content") or item.get("description") or "",
                "url": item.get("url", "#"),
                "source": item.get("source", {}).get("name", "Unknown"),
                "summary": None
            } for item in data["articles"]]

        elif "response" in data:  # Guardian API format
            return [{
                "title": item.get("webTitle", "No title"),
                "description": item["fields"].get("trailText", ""),
                "content": item["fields"].get("bodyText", "") or item["fields"].get("trailText", ""),
                "url": item.get("webUrl", "#"),
                "source": "The Guardian",
                "summary": None
            } for item in data["response"]["results"]]

        elif "results" in data:  # NYTimes format
            return [{
                "title": item.get("title", "No title"),
                "description": item.get("abstract", ""),
                "content": item.get("abstract") or item.get("title", ""),
                "url": item.get("url", "#"),
                "source": "New York Times",
                "summary": None
            } for item in data["results"]]

    except Exception as e:
        print(f"Error fetching from {url}: {e}")
    return []

def fetch_news_from_rss(url):
    """Fetch news from an RSS feed."""
    try:
        feed = feedparser.parse(url)
        return [{
            "title": entry.get("title", "No title"),
            "description": entry.get("summary", "") or entry.get("description", ""),
            "content": entry.get("summary", "") or entry.get("description", ""),
            "url": entry.get("link", "#"),
            "source": "RSS Feed",
            "summary": None
        } for entry in feed.entries[:50]]
    except Exception as e:
        print(f"Error fetching from RSS {url}: {e}")
    return []

def load_cache():
    """Load news cache from disk."""
    if os.path.exists(CACHE_FILE):
        try:
            with open(CACHE_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error loading cache: {e}")
    return []

def save_cache(cache):
    """Save news cache to disk."""
    try:
        with open(CACHE_FILE, 'w') as f:
            json.dump(cache, f)
    except Exception as e:
        print(f"Error saving cache: {e}")

def load_news():
    """Fetch news from all sources, summarize, and store in memory and disk."""
    global news_cache
    news_cache = load_cache()
    if news_cache:
        print(f"Loaded {len(news_cache)} articles from cache.")
        return

    for source, url in NEWS_SOURCES.items():
        if "http" in url:
            if "rss" in url.lower():
                news_cache.extend(fetch_news_from_rss(url))
            else:
                news_cache.extend(fetch_news_from_api(url))

    # Summarize articles and store in cache
    for article in news_cache:
        text = article.get('content') or article.get('description') or article.get('title') or ""
        article['summary'] = summarize_text(" ".join(text.split()[:500]))

    save_cache(news_cache)
    print(f"Loaded and summarized {len(news_cache)} news articles.")

def get_all_news():
    """Return all stored news."""
    return news_cache

def search_news(query):
    """Filter news based on user query."""
    query = query.lower()
    return [article for article in news_cache if query in article["title"].lower() or query in (article["description"] or "").lower()]