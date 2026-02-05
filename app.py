from flask import Flask, render_template, request, redirect, url_for, session
from datetime import timedelta
from dotenv import load_dotenv
load_dotenv()
import os
import requests
import markdown
from uuid import uuid4


# Modules
from modules import (
    ai_chatbot,
    github_integration,
    aws_tools,
    wiki_search,
    job_finder,
    store_finder
)

# Load env
load_dotenv()

app = Flask(__name__)
app.secret_key = os.getenv("SECRET_KEY", "supersecretkey")
app.permanent_session_lifetime = timedelta(days=30)

# ---------------- HOME ----------------
@app.route('/')
def home():
    return render_template('index.html')

# ---------------- CHAT ----------------
@app.route('/chat', methods=['GET', 'POST'])
def chat():
    if 'history' not in session:
        session['history'] = []

    question = ""
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
user_repos = []  # in-memory storage

@app.route('/github')
def github():
    username = "pp23441"  # your GitHub username
    api_url = f"https://api.github.com/users/{username}/repos"
    response = requests.get(api_url)
    repos = response.json() if response.status_code == 200 else []

    all_repos = user_repos + repos

    github_links = [
        {"name": "GitHub Homepage", "url": "https://github.com/"},
        {"name": "GitHub Login", "url": "https://github.com/login"}
    ]

    return render_template(
        "github.html",
        repos=all_repos,
        github_links=github_links
    )


@app.route('/add_repo', methods=['POST'])
def add_repo():
    name = request.form['name']
    url = request.form['url']
    description = request.form.get('description', '')

    user_repos.append({
        "name": name,
        "html_url": url,
        "description": description
    })

    return redirect(url_for('github'))

# ---------------- AWS DASHBOARD ----------------
@app.route("/aws")
def aws_dashboard():
    return render_template(
        "aws.html",
        identity=aws_tools.get_identity(),
        services=["EC2", "S3", "IAM", "CloudWatch", "RDS"],  # temp auto list
        ec2_instances=aws_tools.list_ec2()
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

# Delete one search
@app.route("/wiki/delete/<query>", methods=["POST"])
def delete_wiki_search(query):
    history = session.get("wiki_history", [])
    session["wiki_history"] = [q for q in history if q != query]
    session.modified = True
    return redirect("/wiki")

# Clear all history
@app.route("/wiki/clear", methods=["POST"])
def clear_wiki_history():
    session["wiki_history"] = []
    session.modified = True
    return redirect("/wiki")

# ---------------- JOBS ----------------

@app.route('/jobs')
def jobs():
    all_jobs = job_finder.sample_jobs()

    title = request.args.get("title", "")
    company = request.args.get("company", "")
    location = request.args.get("location", "")
    job_type = request.args.get("type", "")

    filtered_jobs = []

    for job in all_jobs:
        if title and title.lower() not in job["title"].lower():
            continue
        if company and company.lower() not in job["company"].lower():
            continue
        if location and location.lower() not in job["location"].lower():
            continue
        if job_type and job_type.lower() not in job["type"].lower():
            continue

        filtered_jobs.append(job)

    # 🔁 FALLBACK FOR ANY COMPANY / LOCATION
    if not filtered_jobs and (company or location):
        filtered_jobs.append({
            "title": f"Jobs at {company.title() or 'this company'}",
            "company": company.title() if company else "Multiple Companies",
            "location": location.title() if location else "Various Locations",
            "type": "Multiple",
            "apply_url": "",
            "career_url": job_finder.company_career_link(company),
            "search_url": job_finder.location_job_search(company or "Jobs", location),
            "verified": True,
            "government": False
        })

    return render_template("jobs.html", jobs=filtered_jobs)

# ---------------- STORE ----------------
from modules import store_finder

@app.route('/store')
def store():
    lat = request.args.get('lat')
    lon = request.args.get('lon')
    location = request.args.get('location')
    product = request.args.get('product')

    unit = request.args.get('unit', 'km')
    range_value = float(request.args.get('range', 5))
    min_rating = float(request.args.get('rating', 0))
    open_now = request.args.get('open_now') == "1"

    radius_meters = range_value * (1609.34 if unit == "mile" else 1000)

    stores = []
    ai_product = None
    location_label = "Your Location"

    if lat and lon:
        lat, lon = float(lat), float(lon)
        location_label = store_finder.reverse_geocode(lat, lon)

        if product:
            stores = store_finder.find_relevant_stores(
                lat, lon, product, int(radius_meters),
                min_rating=min_rating,
                open_now=open_now
            )
            ai_product = store_finder.ai_recommendation(stores, product)

    return render_template(
        "store.html",
        stores=stores,
        lat=lat,
        lon=lon,
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
