import requests
from bs4 import BeautifulSoup

# URL of the category page
url = "https://www.agrimaroc.ma/categorie/actualites-agriculture-maroc/"

# Headers to look like a real browser
headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
    'Accept-Language': 'fr-FR,fr;q=0.9,en-US;q=0.8,en;q=0.7'
}

print(f"🕵️  Connecting to {url}...")
try:
    response = requests.get(url, headers=headers, timeout=10)
    
    # 1. Check Status Code
    print(f"📊 Status Code: {response.status_code}")
    if response.status_code != 200:
        print("❌ Error: The site returned an error code. You might be blocked.")
    
    soup = BeautifulSoup(response.content, 'html.parser')
    
    # 2. Check Page Title (Detects 'Access Denied' pages)
    page_title = soup.title.string.strip() if soup.title else "No Title"
    print(f"📑 Page Title: '{page_title}'")
    
    if "Cloudflare" in page_title or "Just a moment" in page_title or "403" in page_title:
        print("\n⚠️  BLOCK DETECTED: The site is presenting a security challenge instead of content.")
        exit()

    # 3. Reverse Lookup: Find a known article title
    # We look for a keyword we know exists on the page
    keyword = "Trois conventions" 
    print(f"\n🔍 Searching for known article containing: '{keyword}'...")
    
    found_elements = soup.find_all(string=lambda text: text and keyword in text)
    
    if found_elements:
        print(f"✅ Found {len(found_elements)} match(es)!")
        element = found_elements[0].parent
        
        # Traverse up to find the main container
        print("\n🧬 analyzing HTML structure (from text upwards):")
        current = element
        for i in range(5): # Go up 5 levels
            classes = current.get('class', [])
            tag = current.name
            print(f"   Level {i}: <{tag}> Class: {classes}")
            
            # Check if this looks like a good container
            if 'td_module' in str(classes) or 'post' in str(classes) or 'article' in str(classes):
                print(f"\n🎯 POTENTIAL WINNER: The class to use is likely one of: {classes}")
            
            current = current.parent
            if not current: break
    else:
        print("❌ Keyword not found in HTML. The content might be loaded via JavaScript or the article moved.")
        
        # Fallback: Print all div classes to see what IS there
        print("\n📋 Dumping classes of first 5 divs to analyze structure:")
        divs = soup.find_all('div', class_=True)[:5]
        for div in divs:
            print(f"   - {div.get('class')}")

except Exception as e:
    print(f"❌ Critical Error: {str(e)}")