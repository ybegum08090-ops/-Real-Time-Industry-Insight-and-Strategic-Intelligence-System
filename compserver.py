import os
from dotenv import load_dotenv
load_dotenv()
serp = os.getenv("SERP_API_KEY")

from fastmcp import FastMCP
from serpapi import GoogleSearch


mcp = FastMCP("Brand Comparison Server")

@mcp.tool()
def get_brand_data(brand_name: str, product_type: str = "shoes") -> list:
    """
    Fetches real-time shopping data for a specific brand and product type.
    """
    params = {
        "engine": "google_shopping",
        "q": f"{brand_name} {product_type}",
        "api_key": serp,
        "num": 3
    }
    search = GoogleSearch(params)
    results = search.get_dict().get("shopping_results", [])
    
    return [
        {"title": r.get("title"), "price": r.get("price"), "rating": r.get("rating")} 
        for r in results
    ]

# @mcp.prompt()
# def compare_brands_prompt(brand_a: str, brand_b: str, data: str) -> str:
#     return f"You are a shopping expert. Compare {brand_a} and {brand_b} using this data: {data}"


if __name__ == "__main__":
    mcp.run()
