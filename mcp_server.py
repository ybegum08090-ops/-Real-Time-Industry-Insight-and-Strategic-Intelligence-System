"""
Industry Intelligence MCP Server
=================================
FastMCP server exposing real-time market intelligence tools via SerpAPI.

Tools:
  - get_brand_data:       Google Shopping data for a single brand
  - get_market_trends:    Organic search brand-frequency analysis
  - get_multi_brand_data: Shopping data for multiple brands at once
"""

import os
import re
import json
from collections import Counter
from urllib.parse import urlparse

from dotenv import load_dotenv
from fastmcp import FastMCP
from serpapi.google_search import GoogleSearch

# ── Load env (resolve relative to this file so subprocess spawning works) ────
_env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", ".env")
load_dotenv(_env_path)
SERP_KEY = os.getenv("SERP_API_KEY")

# ── FastMCP instance ────────────────────────────────────────────────────────
mcp = FastMCP("Industry Intelligence Server")

# ── Constants for trend extraction ──────────────────────────────────────────
GENERIC_SITES = {
    "amazon", "wikipedia", "reddit", "youtube", "facebook",
    "instagram", "twitter", "x", "linkedin", "pinterest",
    "ebay", "target", "walmart", "quora", "medium",
    "forbes", "nytimes", "bbc", "cnn",
}

STOPWORDS = {
    "best", "buy", "shop", "official", "store", "online",
    "for", "with", "and", "the", "in", "of", "to",
    "top", "vs", "review", "reviews", "compare", "comparison",
}


# ── Helpers ─────────────────────────────────────────────────────────────────
def _normalize_brand(text: str) -> str:
    cleaned = re.sub(r"[^A-Za-z0-9& ]+", " ", text or "").strip()
    cleaned = re.sub(r"\s+", " ", cleaned)
    if not cleaned:
        return "Unknown"
    return " ".join(word.capitalize() for word in cleaned.split()[:3])


def _brand_from_link(link: str) -> str:
    if not link:
        return ""
    try:
        host = urlparse(link).netloc.lower().replace("www.", "")
    except ValueError:
        return ""
    domain = host.split(".")[0]
    if not domain or domain in GENERIC_SITES:
        return ""
    return _normalize_brand(domain)


def _brand_from_title(title: str, query: str) -> str:
    if not title:
        return "Unknown"
    segment = re.split(r"[-|:]", title)[0]
    query_words = {w.lower() for w in re.findall(r"[A-Za-z0-9]+", query)}
    words = re.findall(r"[A-Za-z0-9&]+", segment)
    filtered = [
        w for w in words
        if w.lower() not in STOPWORDS
        and w.lower() not in query_words
        and len(w) > 1
    ]
    return _normalize_brand(filtered[0]) if filtered else "Unknown"


# ── MCP Tools ───────────────────────────────────────────────────────────────

@mcp.tool()
def get_brand_data(
    brand_name: str,
    product_type: str = "shoes",
    num_results: int = 6,
) -> list:
    """
    Fetch real-time Google Shopping data for a single brand.
    Returns list of products with title, price, rating, reviews, source, link.
    """
    params = {
        "engine": "google_shopping",
        "q": f"{brand_name} {product_type}",
        "api_key": SERP_KEY,
        "num": num_results,
    }
    search = GoogleSearch(params)
    results = search.get_dict().get("shopping_results", [])

    return [
        {
            "title": r.get("title", "N/A"),
            "price": r.get("price", "N/A"),
            "rating": r.get("rating"),
            "reviews": r.get("reviews", 0),
            "source": r.get("source", "N/A"),
            "link": r.get("link", ""),
            "thumbnail": r.get("thumbnail", ""),
        }
        for r in results
    ]


@mcp.tool()
def get_market_trends(
    query: str,
    num_results: int = 20,
    location: str = "United States",
) -> dict:
    """
    Analyse market trends via Google organic search.
    Returns brand frequency map and top search results.
    """
    params = {
        "q": query,
        "engine": "google",
        "location": location,
        "hl": "en",
        "gl": "us",
        "num": num_results,
        "api_key": SERP_KEY,
    }
    search = GoogleSearch(params)
    organic = search.get_dict().get("organic_results", [])

    if not organic:
        return {"brand_frequency": {}, "result_count": 0, "results": []}

    brands: list[str] = []
    for item in organic:
        brand = _brand_from_link(item.get("link", ""))
        if not brand:
            brand = _brand_from_title(item.get("title", ""), query)
        brands.append(brand)

    freq = Counter(brands)

    return {
        "brand_frequency": dict(freq.most_common(15)),
        "result_count": len(organic),
        "results": [
            {
                "title": item.get("title", ""),
                "link": item.get("link", ""),
                "snippet": item.get("snippet", ""),
            }
            for item in organic[:10]
        ],
    }


@mcp.tool()
def get_multi_brand_data(
    brand_names_csv: str,
    product_type: str = "shoes",
    num_results: int = 6,
) -> dict:
    """
    Fetch Google Shopping data for multiple brands at once.
    brand_names_csv: comma-separated list (e.g. "Nike,Puma,Adidas").
    Returns {brand_name: [product_list]}.
    """
    names = [b.strip() for b in brand_names_csv.split(",") if b.strip()]
    out: dict[str, list] = {}

    for brand in names:
        params = {
            "engine": "google_shopping",
            "q": f"{brand} {product_type}",
            "api_key": SERP_KEY,
            "num": num_results,
        }
        search = GoogleSearch(params)
        results = search.get_dict().get("shopping_results", [])

        out[brand] = [
            {
                "title": r.get("title", "N/A"),
                "price": r.get("price", "N/A"),
                "rating": r.get("rating"),
                "reviews": r.get("reviews", 0),
                "source": r.get("source", "N/A"),
                "link": r.get("link", ""),
            }
            for r in results
        ]

    return out


# ── Run ─────────────────────────────────────────────────────────────────────
if __name__ == "__main__":
    mcp.run()
