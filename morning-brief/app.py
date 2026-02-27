import os
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import feedparser

app = Flask(__name__)

# 🔐 Render will provide this
app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")
app.config["SQLALCHEMY_DATABASE_URI"] = os.getenv("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False

db = SQLAlchemy(app)

# ---------------- DATABASE ----------------

class Issue(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    date = db.Column(db.String(20), unique=True)
    content = db.Column(db.Text)

# ---------------- NEWS GENERATOR ----------------

def generate_news():
    feeds = [
        "https://www.skynews.com.au/rss",
        "https://www.abc.net.au/news/feed/",
        "https://www.9news.com.au/rss"
    ]

    articles = []

    for feed in feeds:
        parsed = feedparser.parse(feed)
        for entry in parsed.entries[:2]:
            articles.append(f"• {entry.title}")

    today = datetime.now().strftime("%Y-%m-%d")

    if not Issue.query.filter_by(date=today).first():
        issue = Issue(date=today, content="\n\n".join(articles))
        db.session.add(issue)
        db.session.commit()

# Run every day at 5AM (Sydney time handled by Render timezone setting)
scheduler = BackgroundScheduler()
scheduler.add_job(generate_news, "cron", hour=5, minute=0)
scheduler.start()

# ---------------- ROUTES ----------------

@app.route("/")
def home():
    today = datetime.now().strftime("%Y-%m-%d")
    issue = Issue.query.filter_by(date=today).first()
    return render_template("index.html", issue=issue)

# ---------------- START ----------------

if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(host="0.0.0.0", port=5000)