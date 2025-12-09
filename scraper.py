import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import dateparser
import time
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed
from config import NEWS_SOURCES, SCRAPER_CONFIG
from utils import logger

class ArticleDeduplicator:
    """Prevents processing the same article twice."""
    def __init__(self):
        self.seen_urls = set()
        self.seen_hashes = set()

    def _get_hash(self, title):
        # Normalize: lowercase, remove spaces/punctuation
        clean = "".join(e for e in title.lower() if e.isalnum())
        return hashlib.md5(clean.encode()).hexdigest()

    def is_duplicate(self, url, title):
        # Check 1: URL
        normalized_url = url.split('?')[0].strip('/')
        if normalized_url in self.seen_urls:
            return True
        
        # Check 2: Content Hash (Title)
        title_hash = self._get_hash(title)
        if title_hash in self.seen_hashes:
            return True
            
        self.seen_urls.add(normalized_url)
        self.seen_hashes.add(title_hash)
        return False

class NewsScraperMaroc:
    def __init__(self, parallel=True):
        self.articles = []
        self.deduplicator = ArticleDeduplicator()
        self.session = self._create_session()
        self.parallel = parallel
        
    def _create_session(self):
        session = requests.Session()
        retry = Retry(total=3, backoff_factor=1, status_forcelist=[429, 500, 502])
        adapter = HTTPAdapter(max_retries=retry)
        session.mount("http://", adapter)
        session.mount("https://", adapter)
        session.headers.update({'User-Agent': SCRAPER_CONFIG['user_agent']})
        return session

    def scrape_source(self, source):
        logger.info(f"   ↳ Scraping {source['name']}...")
        source_articles = []
        
        try:
            response = self.session.get(source['url'], timeout=SCRAPER_CONFIG['timeout'])
            response.raise_for_status()
            response.encoding = response.apparent_encoding
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.select(source['selector'])
            
            for article in articles:
                # 1. Title Extraction
                title_tag = article.select_one('.post-box-title') or article.find('h2')
                if not title_tag: continue
                title = title_tag.get_text().strip()

                # 2. Link Extraction
                link_tag = title_tag.find('a')
                if not link_tag: continue
                link = urljoin(source['url'], link_tag.get('href', ''))

                # 3. Deduplication Check
                if self.deduplicator.is_duplicate(link, title):
                    continue

                # 4. Content Extraction
                content_tag = article.select_one('.entry') or article.select_one('.td-excerpt')
                content = content_tag.get_text().strip() if content_tag else ""

                # 5. Date Extraction
                date = self.extract_date(article, source)
                
                if date and self.is_within_last_week(date):
                    source_articles.append({
                        'title': title,
                        'url': link,
                        'content': content,
                        'source': source['name'],
                        'date': date
                    })
            
            logger.info(f"     ✓ {source['name']}: {len(source_articles)} recent items")
            return source_articles

        except Exception as e:
            logger.error(f"     ✗ Failed {source['name']}: {e}")
            return []

    def extract_date(self, article, config):
        try:
            selector = config.get('date_selector')
            if not selector: return None
            
            el = article.select_one(selector)
            if not el: return None
            
            # Try attribute first
            raw = el.get('datetime') or el.get('content') or el.get_text().strip()
            # Clean text
            raw = raw.replace('Publié le', '').strip()
            
            parsed = dateparser.parse(raw, languages=['fr'])
            return parsed.strftime('%Y-%m-%d') if parsed else None
        except:
            return None

    def is_within_last_week(self, date_str):
        try:
            dt = datetime.strptime(date_str, '%Y-%m-%d')
            return dt >= datetime.now() - timedelta(days=7)
        except:
            return True

    def scrape_all(self):
        logger.info(f"🕷️  Starting {'Parallel' if self.parallel else 'Sequential'} Scrape ({len(NEWS_SOURCES)} sources)...")
        all_articles = []
        
        if self.parallel and len(NEWS_SOURCES) > 1:
            # Parallel Execution
            with ThreadPoolExecutor(max_workers=SCRAPER_CONFIG.get('parallel_workers', 3)) as executor:
                futures = [executor.submit(self.scrape_source, src) for src in NEWS_SOURCES]
                
                for future in as_completed(futures):
                    all_articles.extend(future.result())
        else:
            # Sequential Execution
            for source in NEWS_SOURCES:
                all_articles.extend(self.scrape_source(source))
        
        logger.info(f"✅ Total unique articles found: {len(all_articles)}")
        return all_articles