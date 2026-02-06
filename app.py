import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
from dotenv import load_dotenv
import os
import requests
import markdown
from uuid import uuid4


# Load environment variables
load_dotenv()

# Modules
from app_modules import (
    ai_chatbot,
    github_integration,
    aws_tools,
    wiki_search,
    job_finder,
    store_finder
)



app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.permanent_session_lifetime = timedelta(days=30)

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- AI CHAT ----------------
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'history' not in session:
        session['history'] = []

    current_answer = None

    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        if question:
            answer = ai_chatbot.get_answer(question)
            answer_html = markdown.markdown(
                answer, extensions=['fenced_code', 'codehilite']
            )

            session['history'].append({
                "id": str(uuid4()),
                "question": question,
                "answer": answer_html
            })
            session.modified = True
            current_answer = answer_html

    return render_template(
        'chat.html',
        history=session['history'],
        current_answer=current_answer
    )

# ---------------- GITHUB ----------------
user_repos = []

@app.route('/github')
def github():
    username = "pp23441"
    api_url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(api_url)
    repos = response.json() if response.status_code == 200 else []

    return render_template(
        "github.html",
        repos=user_repos + repos
    )

@app.route('/add_repo', methods=['POST'])
def add_repo():
    user_repos.append({
        "name": request.form['name'],
        "html_url": request.form['url'],
        "description": request.form.get('description', '')
    })
    return redirect(url_for('github'))

# ---------------- AWS DASHBOARD ----------------
@app.route("/aws")
def aws_dashboard():
    try:
        identity = aws_tools.get_identity()
        ec2_instances = aws_tools.list_ec2()
    except Exception:
        identity = None
        ec2_instances = []

    return render_template(
        "aws.html",
        identity=identity,
        services=["EC2", "S3", "IAM", "CloudWatch", "RDS"],
        ec2_instances=ec2_instances
    )

# ---------------- WIKI ----------------
@app.route("/wiki", methods=["GET"])
def wiki():
    session.permanent = True

    if "wiki_history" not in session:
        session["wiki_history"] = []

    query = request.args.get("q")
    results = []

    if query:
        results = wiki_search.search_wikipedia(query)

        if query not in session["wiki_history"]:
            session["wiki_history"].insert(0, query)

        session["wiki_history"] = session["wiki_history"][:10]
        session.modified = True

    return render_template(
        "wiki.html",
        query=query,
        result=results,
        history=session["wiki_history"]
    )

@app.route("/wiki/delete/<query>", methods=["POST"])
def delete_wiki_search(query):
    session["wiki_history"] = [
        q for q in session.get("wiki_history", []) if q != query
    ]
    session.modified = True
    return redirect("/wiki")

@app.route("/wiki/clear", methods=["POST"])
def clear_wiki_history():
    session["wiki_history"] = []
    session.modified = True
    return redirect("/wiki")

# ---------------- JOBS ----------------
@app.route('/jobs')
def jobs():
    all_jobs = job_finder.sample_jobs()

    title = request.args.get("title", "").lower()
    company = request.args.get("company", "").lower()
    location = request.args.get("location", "").lower()
    job_type = request.args.get("type", "").lower()

    filtered = []
    for job in all_jobs:
        if title and title not in job["title"].lower():
            continue
        if company and company not in job["company"].lower():
            continue
        if location and location not in job["location"].lower():
            continue
        if job_type and job_type not in job.get("type", "").lower():
            continue
        filtered.append(job)

    if not filtered and (company or location):
        filtered.append({
            "title": f"Jobs at {company.title() or 'this company'}",
            "company": company.title() if company else "Multiple Companies",
            "location": location.title() if location else "Various Locations",
            "type": "Multiple",
            "apply_url": "",
            "career_url": job_finder.company_career_link(company),
            "verified": True,
            "government": False
        })

    return render_template("jobs.html", jobs=filtered)

# ---------------- STORE ----------------
@app.route('/store')
def store():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    product = request.args.get('product')

    unit = request.args.get('unit', 'km')
    range_value = float(request.args.get('range', 5))
    min_rating = float(request.args.get('rating', 0))
    open_now = request.args.get('open_now') == "1"

    radius_meters = range_value * (1609.34 if unit == "mile" else 1000)

    stores = []
    ai_product = None
    location_label = "Your Location"

    if lat and lon and product:
        lat, lon = float(lat), float(lon)
        location_label = store_finder.reverse_geocode(lat, lon)

        stores = store_finder.find_relevant_stores(
            lat, lon, product, int(radius_meters),
            min_rating=min_rating,
            open_now=open_now
        )
        ai_product = store_finder.ai_recommendation(stores, product)

    return render_template(
        "store.html",
        stores=stores,
        location=location_label,
        product=product,
        ai_product=ai_product,
        unit=unit,
        range_value=range_value,
        rating=min_rating,
        open_now=open_now
    )

# ---------------- RUN ----------------
if __name__ == "__main__":
    app.run(debug=True)


