import os
from datetime import datetime
from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from apscheduler.schedulers.background import BackgroundScheduler
import feedparser

app = Flask(__name__)

# ---------------- CONFIG ----------------

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev")

DATABASE_URL = os.getenv("DATABASE_URL")

if DATABASE_URL and DATABASE_URL.startswith("postgres://"):
    DATABASE_URL = DATABASE_URL.replace("postgres://", "postgresql://", 1)

app.config["SQLALCHEMY_DATABASE_URI"] = DATABASE_URL
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

    with app.app_context():

        if not Issue.query.filter_by(date=today).first():

            issue = Issue(
                date=today,
                content="\n\n".join(articles)
            )

            db.session.add(issue)
            db.session.commit()

# ---------------- SCHEDULER ----------------

scheduler = BackgroundScheduler()

scheduler.add_job(
    generate_news,
    "cron",
    hour=5,
    minute=0
)

scheduler.start()

# ---------------- ROUTES ----------------

@app.route("/")
def home():

    today = datetime.now().strftime("%Y-%m-%d")

    issue = Issue.query.filter_by(date=today).first()

    if not issue:
        content = "Today's briefing is being prepared."
    else:
        content = issue.content

    return render_template(
        "index.html",
        content=content
    )

# ---------------- START ----------------

if __name__ == "__main__":

    with app.app_context():
        db.create_all()

    app.run(
        host="0.0.0.0",
        port=5000
    )
