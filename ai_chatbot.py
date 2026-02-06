from openai import OpenAI
from dotenv import load_dotenv
import os
import logging
from datetime import datetime
from timezonefinder import TimezoneFinder
from geopy.geocoders import Nominatim
import pytz
from modules import wiki_search
from bs4 import BeautifulSoup

logging.basicConfig(level=logging.INFO)

# Load environment variables
load_dotenv()
api_key = os.getenv("OPENAI_API_KEY")
if not api_key:
    raise ValueError("❌ OPENAI_API_KEY not found. Check your .env file.")

client = OpenAI(api_key=api_key)

# Initialize timezone tools
tf = TimezoneFinder()
geolocator = Nominatim(user_agent="ai_chatbot")

# ---------------- TIMEZONE FUNCTIONS ----------------
def get_local_time(location_name: str):
    """Get local time for a given city or country name."""
    try:
        location = geolocator.geocode(location_name)
        if not location:
            return None, f"⚠️ Could not find location: '{location_name}'"
        tz_name = tf.timezone_at(lat=location.latitude, lng=location.longitude)
        if not tz_name:
            return None, f"⚠️ Could not find timezone for '{location_name}'"
        tz = pytz.timezone(tz_name)
        now_local = datetime.now(tz)
        formatted = now_local.strftime("%B %d, %Y, %I:%M %p")
        return formatted, tz_name
    except Exception as e:
        logging.error(f"Error getting local time: {e}")
        return None, "⚠️ Error getting location time."

# ---------------- CLEAN SNIPPET ----------------
def clean_snippet(snippet: str):
    """Remove HTML tags from Wikipedia snippet."""
    return BeautifulSoup(snippet, "html.parser").get_text()

# ---------------- AI + WIKI FUNCTION ----------------
def get_answer(question: str):
    question = question.strip()
    if not question:
        return "⚠️ Please enter a valid question."

    q_lower = question.lower()

    # 1️⃣ Time or date queries
    if "time" in q_lower or "date" in q_lower:
        words = q_lower.split()
        location = None
        for i, word in enumerate(words):
            if word in ["in", "at", "of"] and i + 1 < len(words):
                location = " ".join(words[i+1:])
                break
        if location:
            time_info, tz_or_err = get_local_time(location)
            if time_info:
                return f"🕒 The local date and time in **{location.title()}** is {time_info} ({tz_or_err})."
            else:
                return tz_or_err
        else:
            now = datetime.now()
            return f"📅 The current date and time is {now.strftime('%B %d, %Y, %I:%M %p')}."

    # 2️⃣ General knowledge / Wikipedia
    wiki_keywords = ["who", "what", "where", "when", "tell me about", "info on", "define", "meaning of"]
    if any(q_lower.startswith(k) for k in wiki_keywords):
        results = wiki_search.search_wikipedia(question, limit=1)
        if results and isinstance(results, list):
            snippet = clean_snippet(results[0]["snippet"])
            return f"📚 {results[0]['title']}: {snippet}"
        elif isinstance(results, dict) and results.get("error"):
            return f"❌ Wikipedia error: {results['error']}"

    # 3️⃣ Fallback to OpenAI AI
    try:
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a helpful AI assistant integrated into a tech hub website."},
                {"role": "user", "content": question}
            ],
            max_tokens=250,
            temperature=0.7
        )
        return response.choices[0].message.content
    except Exception as e:
        logging.error(f"OpenAI API error: {e}")
        return f"❌ AI error: {str(e)}"

# ---------------- TEST ----------------
if __name__ == "__main__":
    print(get_answer("What time is it in London?"))
    print(get_answer("Who is Albert Einstein?"))
    print(get_answer("Tell me about Python programming."))
    print(get_answer("What's the date now?"))
