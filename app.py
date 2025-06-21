from flask import Flask, render_template, request, redirect, url_for, flash, session
from news_fetcher import load_news, get_all_news, search_news
from summarizer import summarize_text
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import os

# Flask App Initialization
app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "fallback_secret_key")

# MySQL Database Configuration
app.config['MYSQL_HOST'] = 'localhost'
app.config['MYSQL_USER'] = os.getenv("MYSQL_USER", "root")
app.config['MYSQL_PASSWORD'] = os.getenv("MYSQL_PASSWORD", "Jmoney1231$#2!")
app.config['MYSQL_DB'] = 'news_ai'

# Initialize MySQL, Bcrypt, and Flask-Login
mysql = MySQL(app)
bcrypt = Bcrypt(app)
login_manager = LoginManager(app)
login_manager.login_view = "login"

# User Class for Authentication
class User(UserMixin):
    def __init__(self, id, username, password):
        self.id = id
        self.username = username
        self.password = password

@login_manager.user_loader
def load_user(user_id):
    cur = mysql.connection.cursor()
    cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
    user = cur.fetchone()
    cur.close()
    return User(user[0], user[1], user[2]) if user else None

# News Categories
NEWSAPI_CATEGORIES = [
    "business", "entertainment", "general", "health",
    "science", "sports", "technology"
]

# Load news once at startup
load_news()

# Utility to summarize and categorize articles
def process_article(article):
    text = article.get('content') or article.get('description') or article.get('title') or ""
    text = " ".join(text.split()[:500])
    return {
        "title": article['title'],
        "summary": summarize_text(text),
        "source": article.get('source', "Unknown"),
        "url": article.get('url', "#")
    }

# Homepage - Display all articles
@app.route("/")
def index():
    print("🏠 Homepage accessed")  # Debug
    articles = get_all_news()
    summarized_articles = [process_article(article) for article in articles] if articles else []
    if not articles:
        flash("No articles available. Please try again later.", "warning")
    return render_template(
        "index.html",
        articles=summarized_articles,
        categories=NEWSAPI_CATEGORIES
    )

# Category Filter - Display articles by category
@app.route("/category/<category>")
def category_filter(category):
    if category.lower() not in [c.lower() for c in NEWSAPI_CATEGORIES]:
        flash("Invalid category.", "danger")
        return redirect(url_for("index"))

    print(f"Filtering category: {category}")  # Debug
    articles = get_all_news()
    summarized_articles = [process_article(article) for article in articles] if articles else []
    if not articles:
        flash("No articles available for this category.", "warning")
        return render_template("index.html", articles=[], categories=NEWSAPI_CATEGORIES, selected_category=category)

    filtered_articles = [a for a in summarized_articles if a["title"].lower().find(category.lower()) != -1]
    return render_template(
        "index.html",
        articles=filtered_articles,
        categories=NEWSAPI_CATEGORIES,
        selected_category=category
    )

# Search - Display all matching articles
@app.route("/search")
def search():
    query = request.args.get("query", "").strip()
    print(f"Search query: {query}")  # Debug
    articles = search_news(query) if query else get_all_news()
    summarized_articles = [process_article(article) for article in articles] if articles else []
    if not articles:
        flash("No matching articles found.", "warning")
    return render_template(
        "index.html",
        articles=summarized_articles,
        categories=NEWSAPI_CATEGORIES
    )

# Register
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        hashed_pw = bcrypt.generate_password_hash(password).decode("utf-8")

        try:
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (username, hashed_pw))
            mysql.connection.commit()
            cur.close()
            flash("Registration successful. Please log in.", "success")
            return redirect(url_for("login"))
        except Exception as e:
            flash(f"Error: {str(e)}", "danger")
    return render_template("register.html")

# Login
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        cur = mysql.connection.cursor()
        cur.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cur.fetchone()
        cur.close()

        if user and bcrypt.check_password_hash(user[2], password):
            user_obj = User(user[0], user[1], user[2])
            login_user(user_obj)
            flash("Login successful.", "success")
            return redirect(url_for("index"))
        else:
            flash("Invalid username or password.", "danger")

    return render_template("login.html")

# Logout
@app.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Logged out successfully.", "info")
    return redirect(url_for("login"))

# Save Article
@app.route("/save/<string:article_url>")
@login_required
def save_article(article_url):
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO saved_articles (user_id, article_url) VALUES (%s, %s)", (current_user.id, article_url))
    mysql.connection.commit()
    cur.close()
    flash("Article saved!", "success")
    return redirect(url_for("index"))

# View Saved Articles
@app.route("/saved")
@login_required
def saved_articles():
    cur = mysql.connection.cursor()
    cur.execute("SELECT article_url FROM saved_articles WHERE user_id = %s", (current_user.id,))
    saved = cur.fetchall()
    cur.close()
    return render_template("saved.html", saved_articles=saved)

# Profile
@app.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        selected_categories = request.form.getlist("categories")
        categories_str = ",".join(selected_categories)

        cur = mysql.connection.cursor()
        cur.execute("UPDATE users SET preferences = %s WHERE id = %s", (categories_str, current_user.id))
        mysql.connection.commit()
        cur.close()
        flash("Preferences updated.", "success")

    return render_template("profile.html", categories=NEWSAPI_CATEGORIES)

# Favicon
@app.route('/favicon.ico')
def favicon():
    return '', 204

# Run Flask App
import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))  # required for Render
    app.run(host="0.0.0.0", port=port)
