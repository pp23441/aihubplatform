def sample_jobs():
    return [
        {
            "title": "AI Engineer",
            "company": "Google",
            "location": "Remote",
            "type": "Full-Time",
            "apply_url": "https://careers.google.com/jobs/results/",
            "career_url": "https://careers.google.com/",
            "verified": True,
            "government": False
        },
        {
            "title": "Data Scientist",
            "company": "Amazon",
            "location": "New York",
            "type": "Full-Time",
            "apply_url": "",
            "career_url": "https://www.amazon.jobs/",
            "verified": True,
            "government": False
        },
        {
            "title": "MLOps Developer",
            "company": "Lightning AI",
            "location": "San Francisco",
            "type": "Full-Time",
            "apply_url": "",
            "career_url": "https://lightning.ai/jobs",
            "verified": True,
            "government": False
        },
        {
            "title": "Data Analyst",
            "company": "UK Government",
            "location": "London",
            "type": "Full-Time",
            "apply_url": "https://www.gov.uk/find-a-job",
            "career_url": "https://www.gov.uk/find-a-job",
            "verified": True,
            "government": True
        }
    ]


def company_career_link(company):
    if not company:
        return ""

    company = company.lower().strip()

    known = {
        "google": "https://careers.google.com/",
        "amazon": "https://www.amazon.jobs/",
        "microsoft": "https://careers.microsoft.com/",
        "tata": "https://www.tata.com/careers",
        "infosys": "https://www.infosys.com/careers/",
        "wipro": "https://careers.wipro.com/",
        "accenture": "https://www.accenture.com/careers",
        "ibm": "https://www.ibm.com/careers",
    }

    return known.get(company, f"https://www.google.com/search?q={company}+careers")


def location_job_search(company, location):
    query = f"{company} jobs in {location}".strip()
    return f"https://www.google.com/search?q={query.replace(' ', '+')}"
