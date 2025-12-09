from difflib import SequenceMatcher

class ImportanceRanker:
    def __init__(self, articles):
        self.articles = articles
        
    def rank_news(self):
        # Since the Scraper now handles deduplication strictly, 
        # we can just sort by date (newest first) or return as is.
        # For a simple ranking, we assume articles appearing multiple times 
        # (if deduplication wasn't perfect) are important.
        
        # But for now, let's just return them, maybe sorted by date string reverse
        return sorted(self.articles, key=lambda x: x['date'], reverse=True)