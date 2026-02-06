import requests
import re

def clean_html(text):
    """Remove HTML tags from Wikipedia snippets"""
    return re.sub('<.*?>', '', text)

def search_wikipedia(query, limit=5):
    try:
        url = "https://en.wikipedia.org/w/api.php"
        params = {
            "action": "query",
            "list": "search",
            "srsearch": query,
            "format": "json",
            "utf8": "",
            "srlimit": limit
        }

        headers = {
            "User-Agent": "AI-Hub-Platform/1.0"
        }

        response = requests.get(url, params=params, headers=headers, timeout=10)
        response.raise_for_status()
        data = response.json()

        results = []
        for item in data.get("query", {}).get("search", []):
            results.append({
                "title": item["title"],
                "snippet": clean_html(item["snippet"]),
                "url": f"https://en.wikipedia.org/wiki/{item['title'].replace(' ', '_')}"
            })

        return results

    except Exception:
        return []
