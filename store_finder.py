import os
import requests
from geopy.distance import geodesic
import random

GOOGLE_API_KEY = os.getenv("GOOGLE_MAPS_API_KEY")


def reverse_geocode(lat, lon):
    url = "https://maps.googleapis.com/maps/api/geocode/json"
    params = {"latlng": f"{lat},{lon}", "key": GOOGLE_API_KEY}
    res = requests.get(url, params=params).json()

    if not res.get("results"):
        return "Your Location"

    city = country = ""
    for c in res["results"][0]["address_components"]:
        if "locality" in c["types"]:
            city = c["long_name"]
        if "country" in c["types"]:
            country = c["long_name"]

    return f"{city}, {country}".strip(", ")


def get_store_details(place_id):
    url = "https://maps.googleapis.com/maps/api/place/details/json"
    params = {
        "place_id": place_id,
        "fields": "website,formatted_address,rating,opening_hours",
        "key": GOOGLE_API_KEY
    }
    res = requests.get(url, params=params).json()
    return res.get("result", {})


def estimate_price(product):
    # AI-style estimation (placeholder until real APIs)
    base = random.randint(50, 500)
    return f"${base} – ${base + random.randint(20, 200)}"


def find_relevant_stores(lat, lon, product, radius_meters, min_rating=0, open_now=False):
    url = "https://maps.googleapis.com/maps/api/place/nearbysearch/json"
    params = {
        "location": f"{lat},{lon}",
        "radius": radius_meters,
        "keyword": product,
        "key": GOOGLE_API_KEY,
        "opennow": open_now
    }

    res = requests.get(url, params=params).json()
    stores = []

    for r in res.get("results", [])[:8]:
        details = get_store_details(r["place_id"])
        rating = details.get("rating", 0)

        if rating < min_rating:
            continue

        store_lat = r["geometry"]["location"]["lat"]
        store_lon = r["geometry"]["location"]["lng"]

        distance = round(
            geodesic((lat, lon), (store_lat, store_lon)).km, 2
        )

        stores.append({
            "name": r.get("name"),
            "address": details.get("formatted_address", "N/A"),
            "website": details.get("website"),
            "rating": rating,
            "open_now": details.get("opening_hours", {}).get("open_now", False),
            "estimated_price": estimate_price(product),
            "distance_km": distance,
            "lat": store_lat,
            "lon": store_lon
        })

    stores.sort(key=lambda x: (x["distance_km"], -x["rating"]))
    return stores


def ai_recommendation(stores, product):
    if not stores:
        return None

    best = stores[0]
    return {
        "product": product,
        "store": best["name"],
        "reason": (
            f"{best['name']} is nearby ({best['distance_km']} km), "
            f"has a rating of {best['rating']}⭐, "
            f"is currently {'open' if best['open_now'] else 'closed'}, "
            f"and offers an estimated price of {best['estimated_price']}."
        )
    }
