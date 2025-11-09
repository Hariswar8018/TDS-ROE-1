from fastapi import FastAPI, Query
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse
import requests
from bs4 import BeautifulSoup
import urllib.parse

app = FastAPI(title="Wikipedia Country Outline API")

# Enable CORS for all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["GET"],
    allow_headers=["*"],
)

def fetch_wikipedia_page(country: str) -> str:
    """Fetch Wikipedia page HTML for a given country."""
    # Format country name for Wikipedia URL
    country_formatted = country.strip().replace(" ", "_")
    url = f"https://en.wikipedia.org/wiki/{urllib.parse.quote(country_formatted)}"
    
    headers = {
        'User-Agent': 'GlobalEdu Educational Platform/1.0 (Educational Purpose)'
    }
    
    response = requests.get(url, headers=headers)
    response.raise_for_status()
    return response.text

def extract_headings(html_content: str) -> list:
    """Extract all headings (H1-H6) from HTML content."""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    headings = []
    # Find all heading tags in order
    for tag in soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6']):
        # Get heading level (1-6)
        level = int(tag.name[1])
        # Get text content, stripping extra whitespace
        text = tag.get_text().strip()
        
        # Skip empty headings or edit links
        if text and '[edit]' not in text:
            # Remove [edit] suffix if present
            text = text.replace('[edit]', '').strip()
            headings.append((level, text))
    
    return headings

def generate_markdown_outline(country: str, headings: list) -> str:
    """Generate Markdown-formatted outline from headings."""
    markdown_lines = []
    
    # Add title
    markdown_lines.append("## Contents\n")
    
    for level, text in headings:
        # Convert heading level to Markdown format
        # H1 becomes #, H2 becomes ##, etc.
        markdown_prefix = "#" * level
        markdown_lines.append(f"{markdown_prefix} {text}")
    
    return "\n\n".join(markdown_lines)

@app.get("/api/outline", response_class=PlainTextResponse)
async def get_country_outline(country: str = Query(..., description="Name of the country")):
    """
    Fetch Wikipedia page for a country and return a Markdown outline of its headings.
    
    Args:
        country: Name of the country to fetch (e.g., "Vanuatu", "United States")
    
    Returns:
        Markdown-formatted outline of the Wikipedia page structure
    """
    try:
        # Fetch Wikipedia page
        html_content = fetch_wikipedia_page(country)
        
        # Extract headings
        headings = extract_headings(html_content)
        
        # Generate Markdown outline
        outline = generate_markdown_outline(country, headings)
        
        return outline
    
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 404:
            return f"Error: Wikipedia page not found for '{country}'"
        else:
            return f"Error fetching Wikipedia page: {str(e)}"
    except Exception as e:
        return f"Error: {str(e)}"

@app.get("/")
async def root():
    """Root endpoint with API information."""
    return {
        "message": "Wikipedia Country Outline API",
        "usage": "GET /api/outline?country=<country_name>",
        "example": "/api/outline?country=Vanuatu"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)