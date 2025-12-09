import os
from dotenv import load_dotenv

load_dotenv()

# --- 1. Database Configuration ---
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'agrimarket'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# --- 2. Scraper Configuration ---
SCRAPER_CONFIG = {
    'user_agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'timeout': 20,       # Increased timeout for slower sites
    'max_retries': 3,
    'request_delay': 3,  # Base delay between requests
    'parallel_workers': 3 # Number of concurrent threads
}

# --- 3. News Sources ---
NEWS_SOURCES = [
    {
        'name': 'AgriMaroc - Maroc',
        'url': 'https://www.agrimaroc.ma/categorie/actualites-agriculture-maroc/',
        'selector': '.timeline-post', 
        'date_selector': '.timeline-date', 
        'language': 'fr'
    },
    {
        'name': 'AgriMaroc - International',
        'url': 'https://www.agrimaroc.ma/categorie/actualites-agriculture-internationales/',
        'selector': '.timeline-post', 
        'date_selector': '.timeline-date', 
        'language': 'fr'
    },
    {
        'name': 'AgriMaroc - Général',
        'url': 'https://www.agrimaroc.ma/categorie/actualite-agricole/',
        'selector': '.timeline-post', 
        'date_selector': '.timeline-date', 
        'language': 'fr'
    },
    {
        'name': 'AgriMaroc - Machinisme',
        'url': 'https://www.agrimaroc.ma/categorie/machinisme/',
        'selector': '.timeline-post', 
        'date_selector': '.timeline-date', 
        'language': 'fr'
    },
    {
        'name': 'AgriMaroc - Dossier Marché',
        'url': 'https://www.agrimaroc.ma/categorie/dossier-marche/',
        'selector': '.timeline-post', 
        'date_selector': '.timeline-date', 
        'language': 'fr'
    }
]

# --- 4. AI & API Configuration ---
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "google/gemini-2.0-flash-exp:free"

AI_CONFIG = {
    'single_summary': {
        'max_tokens': 300, 
        'temperature': 0.4
    },
    'executive_summary': {
        'max_tokens': 400,
        'temperature': 0.3
    }
}

# --- 5. Email & Reporting Configuration ---
SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.getenv('SMTP_PORT', 587)),
    'email': os.getenv('SMTP_EMAIL'),
    'password': os.getenv('SMTP_PASSWORD')
}

EMAIL_RECIPIENTS = [
    'bekkarmahdi702@gmail.com',
]

REPORTS_DIR = "reports"