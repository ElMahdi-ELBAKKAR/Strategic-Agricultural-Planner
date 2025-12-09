

# config.py
import os
import dateparser
from dotenv import load_dotenv

load_dotenv()

# Database configuration
DB_CONFIG = {
    'host': os.getenv('DB_HOST', 'localhost'),
    'database': os.getenv('DB_NAME', 'agrimarket'),
    'user': os.getenv('DB_USER', 'postgres'),
    'password': os.getenv('DB_PASSWORD', '')
}

# Moroccan agricultural news sources
NEWS_SOURCES = [
    {
        'name': 'AgriMaroc',
        'url': 'https://www.agrimaroc.ma/',
        'selector': '#top',  # Update with actual selectors
        'date_selector': '.date' , # Update with actual date selector
    },

]

# OpenRouter API Configuration
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')
OPENROUTER_BASE_URL = "https://openrouter.ai/api/v1"
OPENROUTER_MODEL = "deepseek/deepseek-r1:free"

SMTP_CONFIG = {
    'server': os.getenv('SMTP_SERVER', 'smtp.gmail.com'),
    'port': int(os.getenv('SMTP_PORT', 587)),
    'email': os.getenv('SMTP_EMAIL'),
    'password': os.getenv('SMTP_PASSWORD')
}

# scraper.py
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
from config import NEWS_SOURCES

import dateparser 

class NewsScraperMaroc:
    def __init__(self):
        self.articles = []
        
    def scrape_source(self, source):
        """Scrape a single news source"""
        try:
            headers = {
                'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
            }
            response = requests.get(source['url'], headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            articles = soup.select(source['selector'])
            
            for article in articles:
                title = article.get_text().strip()
                
                # Try to find the link (handle <a> tags inside the container)
                if article.name == 'a':
                    link = article.get('href', '')
                else:
                    link_tag = article.find('a')
                    link = link_tag.get('href', '') if link_tag else ''

                # --- CHANGE HERE: Pass the 'source' config to extract_date ---
                date = self.extract_date(article, source)
                
                if self.is_within_last_week(date):
                    self.articles.append({
                        'title': title,
                        'url': link,
                        'source': source['name'],
                        'date': date,
                        'scraped_at': datetime.now().isoformat()
                    })
            
            print(f"✓ Scraped {len(articles)} articles from {source['name']}")
            
        except Exception as e:
            print(f"✗ Error scraping {source['name']}: {str(e)}")
    
    def extract_date(self, article_element, source_config):
        """
        Extract publication date using dateparser.
        Returns format: YYYY-MM-DD
        """
        try:
            # 1. Get the selector from the config (default to empty if missing)
            date_selector = source_config.get('date_selector')
            
            if not date_selector:
                # If no selector is defined, we can't find the date. 
                # Be careful: returning 'today' might confuse your filter.
                return datetime.now().strftime('%Y-%m-%d')

            # 2. Find the date element in the HTML
            date_element = article_element.select_one(date_selector)
            
            if date_element:
                date_text = date_element.get_text().strip()
                
                # 3. Use dateparser to magically figure out the date
                # It handles "Il y a 2 heures", "Yesterday", "26/11/2025"
                parsed_date = dateparser.parse(date_text)
                
                if parsed_date:
                    return parsed_date.strftime('%Y-%m-%d')
            
            # Fallback if parsing fails
            return datetime.now().strftime('%Y-%m-%d')
            
        except Exception:
            return datetime.now().strftime('%Y-%m-%d')
    
    def extract_date(self, article_element):
        """Extract publication date from article"""
        # Implement based on your sources' HTML structure
        # For now, return current date
        return datetime.now().strftime('%Y-%m-%d')
    
    def is_within_last_week(self, date_str):
        """Check if date is within the last 7 days"""
        try:
            article_date = datetime.strptime(date_str, '%Y-%m-%d')
            week_ago = datetime.now() - timedelta(days=7)
            return article_date >= week_ago
        except:
            return True
    
    def scrape_all(self):
        """Scrape all configured sources"""
        print("🕷️  Starting weekly scrape...")
        for source in NEWS_SOURCES:
            self.scrape_source(source)
        
        print(f"\n✅ Total articles scraped: {len(self.articles)}")
        return self.articles

# importance_ranker.py
from difflib import SequenceMatcher
from collections import defaultdict

class ImportanceRanker:
    def __init__(self, articles):
        self.articles = articles
        self.similarity_threshold = 0.7
        
    def calculate_similarity(self, text1, text2):
        """Calculate similarity between two texts"""
        return SequenceMatcher(None, text1.lower(), text2.lower()).ratio()
    
    def group_similar_articles(self):
        """Group similar articles and count occurrences"""
        groups = []
        processed = set()
        
        for i, article1 in enumerate(self.articles):
            if i in processed:
                continue
                
            # Start a new group
            group = {
                'articles': [article1],
                'sources': [article1['source']],
                'importance': 1
            }
            
            # Find similar articles
            for j, article2 in enumerate(self.articles):
                if i >= j or j in processed:
                    continue
                    
                similarity = self.calculate_similarity(
                    article1['title'], 
                    article2['title']
                )
                
                if similarity >= self.similarity_threshold:
                    group['articles'].append(article2)
                    group['sources'].append(article2['source'])
                    group['importance'] += 1
                    processed.add(j)
            
            processed.add(i)
            groups.append(group)
        
        # Sort by importance (number of sources)
        groups.sort(key=lambda x: x['importance'], reverse=True)
        return groups
    
    def rank_news(self):
        """Rank news by importance"""
        grouped = self.group_similar_articles()
        
        ranked_news = []
        for group in grouped:
            # Pick the best version (longest/most detailed title)
            best_article = max(group['articles'], key=lambda x: len(x['title']))
            
            ranked_news.append({
                'article': best_article,
                'importance': group['importance'],
                'sources': list(set(group['sources'])),
                'source_count': len(set(group['sources']))
            })
        
        return ranked_news

from openai import OpenAI
from config import OPENROUTER_API_KEY, OPENROUTER_BASE_URL, OPENROUTER_MODEL
import json

class NewsSummarizer:
    def __init__(self):
        # Initializes the OpenAI client, redirecting traffic to the OpenRouter API endpoint
        self.client = OpenAI(
            api_key=OPENROUTER_API_KEY,
            base_url=OPENROUTER_BASE_URL
        )
    
    def summarize_news(self, article_data):
        """
        Generates a concise (2-3 sentence) summary for a single ranked news item
        using the AI model, tailored for the weekly bulletin.
        """
        
        # --- PROMPT FOR SINGLE ARTICLE SUMMARY ---
        prompt = f"""
AGIS en tant qu'analyste de marché agricole principal pour un bulletin hebdomadaire destiné à des professionnels.
Ta tâche est de condenser le titre fourni en un résumé concis et percutant.

DIRECTIVES DE FORMAT:
1. Longueur: STRICTEMENT 2 phrases (2-3 lignes maximum).
2. Tonalité: Professionnelle et informative.
3. Langue: Français standard.
4. Sortie: Ne pas utiliser de puces, de tirets, ou de mise en forme Markdown.

TITRE A RESUMER: {article_data['article']['title']}
SOURCE PRINCIPALE: {article_data['article']['source']}

RESUME FINAL (commence immédiatement par la première phrase):
"""
        # --- END OF PROMPT ---

        try:
            response = self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=80,  # Optimized for conciseness
                temperature=0.5  # Optimized for factual consistency
            )
            
            summary = response.choices[0].message.content.strip()
            return summary
            
        except Exception as e:
            print(f"Error summarizing: {str(e)}")
            # Fallback is the original title in case of API error
            return article_data['article']['title']
    
    def generate_executive_summary(self, summarized_news_list):
        """Generates a single, overarching executive summary based on all news."""
        
        # Format the list of short summaries into a readable string for the LLM
        summaries_text = "\n".join([f"- {item['text']} (Importance: {item['importance']})" for item in summarized_news_list])
        
        # --- PROMPT FOR EXECUTIVE SUMMARY ---
        prompt = f"""
AGIS en tant qu'analyste de marché agricole principal.
Ton objectif est de rédiger une synthèse exécutive pour le bulletin hebdomadaire.

DIRECTIVES DE SYNTHÈSE:
1. Analyse la liste des actualités résumées ci-dessous.
2. Identifie les 2 à 3 thèmes ou événements les plus importants (ceux avec la plus haute 'Importance').
3. Rédige un seul paragraphe de 100 mots maximum en français standard.
4. Le ton doit être professionnel, concis et mettre en évidence les implications majeures pour le marché marocain.

ACTUALITÉS A ANALYSER:
---
{summaries_text}
---

SYNTHESE EXÉCUTIVE:
"""
        # --- END OF PROMPT ---
        
        try:
            response = self.client.chat.completions.create(
                model=OPENROUTER_MODEL,
                messages=[
                    {"role": "user", "content": prompt}
                ],
                max_tokens=150, # Sufficient for 100 words (approx. 130 tokens)
                temperature=0.3 # Low temperature for high precision/coherence
            )
            
            executive_summary = response.choices[0].message.content.strip()
            return executive_summary
        
        except Exception as e:
            print(f"Error generating executive summary: {str(e)}")
            return "Synthèse exécutive non disponible suite à une erreur de communication avec le modèle IA."
    
    def process_all_news(self, ranked_news):
        """Iterates through all ranked news items to generate individual summaries."""
        summarized = []
        
        for news_item in ranked_news:
            summary = self.summarize_news(news_item) 
            
            summarized.append({
                'text': summary,
                'importance': news_item['importance'],
                'sources': news_item['sources'],
                'date': news_item['article']['date']
            })
        
        return summarized
    

# report_generator.py
from reportlab.lib import colors

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_JUSTIFY
from datetime import datetime, timedelta

class ReportGenerator:
    def __init__(self):
        self.styles = getSampleStyleSheet()
        self.setup_styles()
    
    def setup_styles(self):
        """Setup custom styles for the PDF report"""
        
        # 1. Custom Title Style (Cover Page)
        self.styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor='#059669', # Deep Green
            spaceAfter=15,
            alignment=TA_CENTER
        ))
        
        # 2. Week Label Style (Cover Page) - Updated to be concise
        self.styles.add(ParagraphStyle(
            name='WeekLabel',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor='#047857', # Slightly darker green
            spaceAfter=25,
            alignment=TA_CENTER
        ))
        
        # 3. Executive Summary Text Style (New addition for Page 1)
        self.styles.add(ParagraphStyle(
            name='ExecutiveSummaryText',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=30,
            leading=14,
            alignment=TA_JUSTIFY,
        ))
        
        # 4. High Importance Summary Style (Content Pages)
        self.styles.add(ParagraphStyle(
            name='HighImportance',
            parent=self.styles['Normal'],
            fontSize=12,
            spaceAfter=15,
            leading=15, 
            leftIndent=0.5*cm, 
            textColor='#059669', 
        ))

        # 5. Normal Summary Style (Content Pages)
        self.styles.add(ParagraphStyle(
            name='NormalSummary',
            parent=self.styles['Normal'],
            fontSize=11,
            spaceAfter=15,
            leading=14,
            leftIndent=0.5*cm,
        ))
        
        # 6. Source Metadata Style
        self.styles.add(ParagraphStyle(
            name='Metadata',
            parent=self.styles['Normal'],
            fontSize=9,
            textColor='#6b7280', 
            spaceBefore=0,
            spaceAfter=5,
            leftIndent=0.5*cm,
        ))
    
    def get_week_label(self):
        """Generate week label in the format: 'SEMAINE X - MOIS YYYY'"""
        now = datetime.now()
        # Calculate week number (1, 2, 3, 4, or 5)
        week_num = (now.day - 1) // 7 + 1
        
        month_names = {
            1: 'JANVIER', 2: 'FÉVRIER', 3: 'MARS', 4: 'AVRIL',
            5: 'MAI', 6: 'JUIN', 7: 'JUILLET', 8: 'AOÛT',
            9: 'SEPTEMBRE', 10: 'OCTOBRE', 11: 'NOVEMBRE', 12: 'DÉCEMBRE'
        }
        
        month_name = month_names.get(now.month, str(now.month))
        
        # Example output: "SEMAINE 2 - MAI 2025"
        week_label = f"SEMAINE {week_num} - {month_name} {now.year}"
        return week_label
    
    def generate_pdf(self, news_items, executive_summary, filename='bulletin_hebdomadaire.pdf'):
        """Generate the PDF report using categorized styles."""
        doc = SimpleDocTemplate(filename, pagesize=A4, 
                                topMargin=1.5*cm, bottomMargin=1.5*cm,
                                leftMargin=2.5*cm, rightMargin=2.5*cm)
        story = []
        
        # --- Page 1: Cover and Executive Summary ---
        story.append(Spacer(1, 4*cm))
        story.append(Paragraph("BULLETIN HEBDOMADAIRE", self.styles['CustomTitle']))
        story.append(Paragraph(self.get_week_label(), self.styles['WeekLabel']))
        
        # Executive Summary Title
        story.append(Paragraph("<br/><b>SYNTHÈSE EXÉCUTIVE</b>", self.styles['Heading2']))
        story.append(Spacer(1, 0.2*cm))
        
        # Executive Summary Content (Placeholder for AI-generated summary)
        story.append(Paragraph(executive_summary, self.styles['ExecutiveSummaryText']))

        # Footer info
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("Préparé par : AgriMaroc Insights", self.styles['Normal']))
        story.append(Paragraph(f"Généré le : {datetime.now().strftime('%d %B %Y')}", self.styles['Normal']))
        story.append(PageBreak())
        
        # --- Pages 2-X: Detailed News items ---
        story.append(Paragraph("Actualités de la semaine (Classées par Importance)", self.styles['Heading1']))
        story.append(Spacer(1, 0.5*cm))
        
        for i, item in enumerate(news_items, 1):
            
            # 1. Determine style based on importance (sources covering the story)
            if item['importance'] >= 2:
                style = self.styles['HighImportance']
                bullet = f"<b>• [TOP ACTU] </b>"
            else:
                style = self.styles['NormalSummary']
                bullet = "• "
            
            # 2. Add the summarized text
            summary_text = f"{bullet}{item['text']}"
            story.append(Paragraph(summary_text, style))
            
            # 3. Add the metadata (sources and date) below the summary
            sources_list = ", ".join(item['sources'])
            metadata_text = f"<i><font color='#9ca3af'>Sources: {sources_list} | Date clé: {item['date']}</font></i>"
            
            story.append(Paragraph(metadata_text, self.styles['Metadata']))
            story.append(Spacer(1, 0.2*cm))
        
        # Build PDF
        doc.build(story)
        print(f"✅ PDF generated: {filename}")
        return filename

import schedule
import time
import os # <-- Added for path checks
from scraper import NewsScraperMaroc
from importance_ranker import ImportanceRanker
from summarizer import NewsSummarizer
from report_generator import ReportGenerator
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders
from datetime import datetime # <-- Added for file naming and subject line
from config import SMTP_CONFIG

def send_email_with_report(pdf_filename, recipients):
    """Send weekly report via email"""
    try:
        # Check if the PDF file exists before attempting to attach
        if not os.path.exists(pdf_filename):
            print(f"✗ Error: PDF file not found at {pdf_filename}. Aborting email.")
            return

        msg = MIMEMultipart()
        msg['From'] = SMTP_CONFIG['email']
        msg['To'] = ', '.join(recipients)
        msg['Subject'] = f"Bulletin Hebdomadaire AgriMaroc - {datetime.now().strftime('%d/%m/%Y')}"
        
        body = """
        Bonjour,
        
        Veuillez trouver ci-joint le bulletin hebdomadaire du marché agricole marocain.
        
        Cordialement,
        L'équipe AgriMaroc Insights
        """
        
        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(pdf_filename, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={pdf_filename}')
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
        server.starttls()
        server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        print(f"✅ Email sent to {len(recipients)} recipients")
        
    except Exception as e:
        print(f"✗ Error sending email: {str(e)}")

def generate_weekly_report():
    """Main pipeline: scrape, rank, summarize, generate report"""
    print("\n" + "="*50)
    print("STARTING WEEKLY REPORT GENERATION")
    print("="*50 + "\n")
    
    # Step 1: Scrape news
    scraper = NewsScraperMaroc()
    articles = scraper.scrape_all()
    
    if not articles:
        print("⚠️  No articles found. Exiting...")
        return
    
    # Step 2: Rank by importance
    print("\n📊 Ranking news by importance...")
    ranker = ImportanceRanker(articles)
    ranked_news = ranker.rank_news()
    
    # Step 3a: Summarize individual articles with AI
    print("\n🤖 Generating individual summaries...")
    summarizer = NewsSummarizer()
    summarized_news = summarizer.process_all_news(ranked_news)
    
    # Step 3b: Generate Executive Summary (NEW STEP)
    print("\n✍️ Generating Executive Summary...")
    executive_summary = summarizer.generate_executive_summary(summarized_news)
    print(f"Executive Summary Draft: {executive_summary[:100]}...")
    
    # Step 4: Generate PDF
    print("\n📄 Creating PDF report...")
    generator = ReportGenerator()
    # Define dynamic filename for attachment consistency
    pdf_filename = f"bulletin_hebdomadaire_{datetime.now().strftime('%Y%m%d')}.pdf" 
    
    # Pass both the news list AND the executive summary to the generator
    pdf_file = generator.generate_pdf(summarized_news, executive_summary, filename=pdf_filename)
    
    # Step 5: Send via email
    print("\n📧 Sending email...")
    # NOTE: Update this line with actual recipient emails before deployment
    recipients = ['recipient_email@example.com'] 
    send_email_with_report(pdf_file, recipients)
    
    print("\n" + "="*50)
    print("✅ WEEKLY REPORT COMPLETED")
    print("="*50 + "\n")

if __name__ == "__main__":
    # Option 1: Run immediately (for testing)
    generate_weekly_report()
    
    # Option 2: Schedule weekly (every Monday at 6 AM)
    # schedule.every().monday.at("06:00").do(generate_weekly_report)
    # 
    # print("📅 Scheduler started. Waiting for Monday 6:00 AM...")
    # while True:
    #     schedule.run_pending()
    #     time.sleep(3600)  # Check every hour