import feedparser
from transformers import pipeline
import schedule
import time
import logging
from datetime import datetime
from collections import defaultdict
from bs4 import BeautifulSoup
import threading

# Set up logging
logging.basicConfig(filename='news_summary.log', level=logging.INFO)

# Define categories and keywords
categories = {
    "Politics": ["government", "election", "parliament", "president", "politics"],
    "Sports": ["football", "basketball", "tennis", "olympics", "sports"],
    "Technology": ["AI", "computer", "software", "internet", "technology"],
    "Business": ["economy", "stock", "market", "company", "business"],
    "Entertainment": ["movie", "music", "celebrity", "entertainment"]
}

# Define RSS feeds
rss_feeds = [
    "http://feeds.bbci.co.uk/news/rss.xml",
    "https://rss.nytimes.com/services/xml/rss/nyt/HomePage.xml",
    "https://www.aljazeera.com/xml/rss/all.xml",
    "https://rss.cnn.com/rss/edition.rss",
    "https://www.npr.org/rss/rss.php?id=1001",
    "https://www.theguardian.com/world/rss",
    "https://feeds.a.dj.com/rss/RSSWorldNews.xml",
    "https://www.washingtonpost.com/arcio/rss/category/world/",
]

# Lazy-load summarization model
summarizer = None
def load_summarizer():
    global summarizer
    if summarizer is None:
        logging.info("Loading BART model...")
        summarizer = pipeline("summarization", model="facebook/bart-large-cnn")
        logging.info("BART model loaded.")
    return summarizer

def categorize_article(title, summary, categories):
    for category, keywords in categories.items():
        if any(keyword.lower() in title.lower() or keyword.lower() in summary.lower() for keyword in keywords):
            return category
    return "General"

def get_summary(entry):
    if hasattr(entry, "summary"):
        summary = entry.summary
    elif hasattr(entry, "description"):
        summary = entry.description
    else:
        summary = "No summary available"
    return BeautifulSoup(summary, "html.parser").get_text()

def generate_daily_summary():
    try:
        logging.info("Starting daily summary generation")
        today = datetime.utcnow().date()
        category_summaries = defaultdict(list)

        for feed_url in rss_feeds:
            logging.info(f"Fetching feed: {feed_url}")
            feed = feedparser.parse(feed_url)
            for entry in feed.entries:
                published_date = datetime(*entry.published_parsed[:6]).date()
                if published_date == today:
                    title = entry.title
                    summary = get_summary(entry)
                    category = categorize_article(title, summary, categories)
                    category_summaries[category].append(summary)

        category_final_summaries = {}
        summarizer = load_summarizer()
        for category, summaries in category_summaries.items():
            combined_summary = " ".join(summaries)
            combined_summary = " ".join(combined_summary.split()[:1000])
            category_summary = summarizer(combined_summary, max_length=100, min_length=50, do_sample=False)[0]['summary_text']
            category_final_summaries[category] = category_summary

        all_category_summaries = " ".join(category_final_summaries.values())
        daily_summary = summarizer(all_category_summaries, max_length=150, min_length=100, do_sample=False)[0]['summary_text']

        with open("daily_summary.txt", "w") as f:
            f.write(daily_summary)
        logging.info("Daily summary generated successfully")
    except Exception as e:
        logging.error(f"Error generating summary: {e}")

def start_scheduler():
    """Run the scheduler in a separate thread."""
    schedule.every().day.at("08:00").do(generate_daily_summary)
    logging.info("Scheduler started.")
    while True:
        schedule.run_pending()
        time.sleep(1)