import os
import traceback
import smtplib
from datetime import datetime
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.base import MIMEBase
from email import encoders

from utils import logger
from scraper import NewsScraperMaroc
from importance_ranker import ImportanceRanker
from summarizer import NewsSummarizer
from report_generator import ReportGenerator
import config

# Defensive configuration loading
SMTP_CONFIG = getattr(config, 'SMTP_CONFIG', {})
EMAIL_RECIPIENTS = getattr(config, 'EMAIL_RECIPIENTS', [])
REPORTS_DIR = getattr(config, 'REPORTS_DIR', 'reports')


def send_email_with_report(pdf_filepath: str, recipients: list):
    """Send the generated PDF report via email."""
    
    if not recipients:
        logger.warning("No email recipients configured. Skipping email.")
        return

    if not os.path.exists(pdf_filepath):
        logger.error(f"PDF file not found at {pdf_filepath}. Aborting email.")
        return

    if not SMTP_CONFIG or not SMTP_CONFIG.get('password'):
        logger.error("SMTP configuration is missing or incomplete. Cannot send email.")
        return

    try:
        logger.info(f"📧 Preparing email for {len(recipients)} recipient(s)...")
        
        msg = MIMEMultipart()
        msg['From'] = SMTP_CONFIG['email']
        msg['To'] = ', '.join(recipients)
        
        # Use filename in subject
        filename = os.path.basename(pdf_filepath)
        msg['Subject'] = f"Bulletin Hebdomadaire - {filename}"
        
        # --- UPDATED BODY TEXT ---
        body = """Bonjour,

Veuillez trouver en pièce jointe le rapport de cette semaine des différentes actualités.

Bonne lecture!

Plateforme De Veille Stratégique"""
        # -------------------------

        msg.attach(MIMEText(body, 'plain'))
        
        # Attach PDF
        with open(pdf_filepath, 'rb') as attachment:
            part = MIMEBase('application', 'octet-stream')
            part.set_payload(attachment.read())
            encoders.encode_base64(part)
            part.add_header('Content-Disposition', f'attachment; filename={filename}')
            msg.attach(part)
        
        # Send email
        server = smtplib.SMTP(SMTP_CONFIG['server'], SMTP_CONFIG['port'])
        server.starttls()
        server.login(SMTP_CONFIG['email'], SMTP_CONFIG['password'])
        server.send_message(msg)
        server.quit()
        
        logger.info(f"✅ Email sent successfully to: {', '.join(recipients)}")
        
    except Exception:
        logger.error("✗ Error sending email:", exc_info=True)


def generate_weekly_report():
    logger.info("🚀 STARTING PIPELINE")
    
    try:
        # Step 0: Setup
        os.makedirs(REPORTS_DIR, exist_ok=True)
        
        # Step 1: Scrape (Parallel)
        scraper = NewsScraperMaroc(parallel=True)
        articles = scraper.scrape_all()
        
        if not articles:
            logger.warning("No articles found.")
            return
        
        # Step 2: Rank
        logger.info("Ranking news...")
        ranker = ImportanceRanker(articles)
        ranked_news = ranker.rank_news()
        
        # Step 3: Summarize (Cached & Rate-Limited)
        summarizer = NewsSummarizer()
        summarized_news = summarizer.process_all_news(ranked_news)
        executive_summary = summarizer.generate_executive_summary(summarized_news)
        
        # Step 4: PDF Generation
        logger.info("Generating PDF...")
        generator = ReportGenerator()
        
        # Generate filename in reports directory
        filename = f"Bulletin_hebdo_{datetime.now().strftime('%Y%m%d')}.pdf"
        pdf_path = os.path.join(REPORTS_DIR, filename)
        
        pdf_file = generator.generate_pdf(
            news_items=summarized_news, 
            executive_summary=executive_summary, 
            filename=pdf_path
        )
        
        # Step 5: Email Distribution
        if pdf_file:
            send_email_with_report(pdf_file, EMAIL_RECIPIENTS)
        
        logger.info("✅ PIPELINE FINISHED")
            
    except Exception:
        logger.error("Critical Failure", exc_info=True)


if __name__ == "__main__":
    generate_weekly_report()