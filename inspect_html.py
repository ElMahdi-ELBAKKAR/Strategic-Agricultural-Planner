import requests
from bs4 import BeautifulSoup

url = "https://www.agrimaroc.ma/categorie/actualites-agriculture-maroc/"
headers = {'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/120.0.0.0 Safari/537.36'}

print(f"Connecting to {url}...")
response = requests.get(url, headers=headers)
soup = BeautifulSoup(response.content, 'html.parser')

# Find the first article using the selector we know works
article = soup.select_one('.timeline-post')

if article:
    print("\n✅ Found the first article! Here is its HTML structure:\n")
    print("-" * 50)
    # Print the pretty HTML so we can read the classes
    print(article.prettify())
    print("-" * 50)
    
    # Try to guess the date element
    print("\n🔍 Quick Date Check:")
    for selector in ['.timeline-date', '.date', 'time', '.post-date', '.meta-date', 'small']:
        element = article.select_one(selector)
        if element:
            print(f"   Found '{selector}': {element.get_text().strip()}")
        else:
            print(f"   Did not find '{selector}'")
else:
    print("❌ Could not find any element with class '.timeline-post'.")