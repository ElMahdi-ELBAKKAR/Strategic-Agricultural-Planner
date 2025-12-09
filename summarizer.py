import json
import os
import time
from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL, AI_CONFIG
from utils import logger, rate_limiter

CACHE_FILE = "cache_summaries.json"

class NewsSummarizer:
    def __init__(self):
        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
        self.cache = self._load_cache()

    def _load_cache(self):
        if os.path.exists(CACHE_FILE):
            try:
                with open(CACHE_FILE, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return {}
        return {}

    def _save_cache(self):
        try:
            with open(CACHE_FILE, 'w', encoding='utf-8') as f:
                json.dump(self.cache, f, ensure_ascii=False, indent=2)
        except Exception as e:
            logger.error(f"Cache save failed: {e}")

    def _api_call_with_retry(self, prompt, settings):
        """Centralized API call with rate limit handling"""
        for attempt in range(3):
            try:
                rate_limiter.wait_for_slot()
                
                response = self.client.chat.completions.create(
                    model=OPENROUTER_MODEL,
                    messages=[{"role": "user", "content": prompt}],
                    max_tokens=settings['max_tokens'], 
                    temperature=settings['temperature'] 
                )
                content = response.choices[0].message.content.strip()
                if content: return content
                
            except Exception as e:
                error_msg = str(e)
                if "429" in error_msg:
                    rate_limiter.handle_429(attempt)
                else:
                    logger.warning(f"API Error (Attempt {attempt+1}): {e}")
                    time.sleep(2)
        return None

    def summarize_news(self, article):
        url = article.get('url')
        if url and url in self.cache:
            logger.info(f"✅ Cache Hit: {article['title'][:30]}...")
            return self.cache[url]

        content = article.get('content', '') or "Pas de contenu."
        prompt = f"""
        Rédige une analyse DÉTAILLÉE (60 mots) de cet article agricole.
        TITRE: {article['title']}
        EXTRAIT: {content[:1000]}
        """
        
        settings = AI_CONFIG['single_summary']
        summary = self._api_call_with_retry(prompt, settings)
        
        if summary:
            if url:
                self.cache[url] = summary
                self._save_cache()
            return summary
        return f"{article['title']} (Analyse indisponible)"

    def generate_executive_summary(self, summarized_list):
        if not summarized_list: return "Pas d'actualité."
        
        # Use top 10 articles only
        top_news = summarized_list[:10]
        context = "\n".join([f"- {item['text'][:150]}..." for item in top_news])
        
        prompt = f"""
        Rédige une note de synthèse stratégique (3-4 phrases) sur ces actualités agricoles.
        Commence directement par le texte.
        
        CONTEXTE:
        {context}
        """
        
        logger.info("Drafting Executive Summary...")
        rate_limiter.wait_for_slot() # Ensure delay before big request
        
        settings = AI_CONFIG['executive_summary']
        return self._api_call_with_retry(prompt, settings) or "Synthèse indisponible."

    def process_all_news(self, ranked_news):
        summarized = []
        total = len(ranked_news)
        
        for i, item in enumerate(ranked_news):
            if i % 5 == 0:
                logger.info(f"📊 Progress: {i}/{total} articles...")
                
            summary = self.summarize_news(item)
            summarized.append({
                **item, # Unpack all existing fields (title, url, date, etc)
                'text': summary
            })
            
        return summarized