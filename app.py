from flask import Flask, render_template, request, redirect, url_for, flash
from news_fetcher import load_news, get_all_news, search_news
from summarizer import summarize_text

# Flask App Initialization
app = Flask(__name__)

# Load news once at startup
load_news()

# Utility to summarize articles with a limit
def process_article(article):
    text = article.get('content') or article.get('description') or article.get('title') or ""
    text = " ".join(text.split()[:500])
    return {
        "title": article['title'],
        "summary": summarize_text(text),
        "source": article.get('source', "Unknown"),
        "url": article.get('url', "#")
    }

# Homepage - Display all articles (limited to 20 for memory)
@app.route("/")
def index():
    print("🏠 Homepage accessed")  # Debug
    articles = get_all_news()[:20]  # Limit to 20 articles
    summarized_articles = [process_article(article) for article in articles] if articles else []
    if not articles:
        flash("No articles available. Please try again later.", "warning")
    return render_template(
        "index.html",
        articles=summarized_articles,
        categories=["business", "entertainment", "general", "health", "science", "sports", "technology"]
    )

# Category Filter - Display articles by category (limited to 20)
@app.route("/category/<category>")
def category_filter(category):
    if category.lower() not in ["business", "entertainment", "general", "health", "science", "sports", "technology"]:
        flash("Invalid category.", "danger")
        return redirect(url_for("index"))

    print(f"Filtering category: {category}")  # Debug
    articles = get_all_news()[:20]  # Limit to 20 articles
    summarized_articles = [process_article(article) for article in articles] if articles else []
    if not articles:
        flash("No articles available for this category.", "warning")
        return render_template("index.html", articles=[], categories=["business", "entertainment", "general", "health", "science", "sports", "technology"], selected_category=category)

    filtered_articles = [a for a in summarized_articles if a["title"].lower().find(category.lower()) != -1]
    return render_template(
        "index.html",
        articles=filtered_articles,
        categories=["business", "entertainment", "general", "health", "science", "sports", "technology"],
        selected_category=category
    )

# Search - Display all matching articles (limited to 20)
@app.route("/search")
def search():
    query = request.args.get("query", "").strip()
    print(f"Search query: {query}")  # Debug
    articles = search_news(query)[:20] if query else get_all_news()[:20]  # Limit to 20 articles
    summarized_articles = [process_article(article) for article in articles] if articles else []
    if not articles:
        flash("No matching articles found.", "warning")
    return render_template(
        "index.html",
        articles=summarized_articles,
        categories=["business", "entertainment", "general", "health", "science", "sports", "technology"]
    )

# Favicon
@app.route('/favicon.ico')
def favicon():
    return '', 204

# Run Flask App
import os
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # Required for Render
    app.run(host="0.0.0.0", port=port)