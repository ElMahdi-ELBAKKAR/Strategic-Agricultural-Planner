🌾 AgriMaroc Strategic Planner & News Digest

An automated intelligence pipeline for monitoring, summarizing, and reporting on the Moroccan agricultural market.

📖 Overview

The Strategic Planner is a Python-based automation suite designed to streamline the process of strategic watch ("Veille Stratégique"). It scrapes targeted news sources, filters for relevance, uses advanced AI (LLMs) to synthesize insights, and delivers a professional PDF bulletin directly to stakeholders via email.

✨ System Architecture & Innovations

🕷️ Intelligent Scraping Engine

I designed a sophisticated news scraper capable of monitoring multiple agricultural news sources simultaneously (AgriMaroc Local, International, Machinery, etc.), filtering content for relevance (last 7 days), and ensuring data integrity.

Smart Deduplication: I implemented an innovative deduplication engine that uses content hashing (MD5) to identify and remove redundant articles across different URLs, ensuring only unique stories are processed.

Robust Rate-Limiting: The system features a custom rate-limiting protocol with exponential backoff, allowing it to respect website constraints and avoid IP bans while maximizing throughput.

Multi-Strategy Extraction: I designed a resilient extraction logic that intelligently falls back between HTML metadata, specific CSS selectors, and semantic text analysis to accurately capture dates and content even when website layouts shift.

🧠 AI-Powered Summarization Core

I designed a context-aware summarization engine capable of transforming raw news feeds into tiered strategic insights.

Multi-Model Architecture (Model Routing): I implemented an innovative routing system that assigns specific tasks to the most appropriate AI models—using Gemini 2.0 Flash for rapid, low-cost analysis of individual articles, and Llama 3.3 70B for high-level strategic synthesis.

Dual-Layer Prompting: The system generates both deep-dive analyses for individual articles and a high-level macro-economic executive summary without human intervention.

Self-Healing Mechanisms: I included an adaptive retry protocol that automatically recovers from transient AI failures or empty responses, guaranteeing report completeness even under unstable network conditions.

📄 Professional Report Generator

I designed a specialized reports generator capable of synthesizing automated weekly bulletins with a clean, executive-focused layout.

Smart Layout Logic: The generator uses innovative page-breaking algorithms (KeepTogether) to prevent news items from splitting awkwardly across pages, maintaining a professional reading experience.

Dynamic Visual Hierarchy: I implemented a modular style management class that enforces consistent branding (typography, color palettes) and visually distinguishes the executive summary from detailed news items.

Automated Statistics: The cover page features a dynamic executive summary engine that aggregates top news trends and provides automated statistics on article volume and source diversity.

📧 Automated Distribution & Security

I designed a secure email distribution engine capable of autonomous report delivery.

Pre-Flight Validation: The system includes a validation layer that verifies file integrity and recipient configuration before attempting connection, preventing silent failures.

Secure Authentication: I utilized environment-based app passwords and secure SMTP protocols to ensure strict security compliance while automating the "final mile" of the intelligence cycle.

🚀 Installation & Usage

1. Clone the repository

git clone [https://github.com/YOUR_USERNAME/Strategic-Agricultural-Planner.git](https://github.com/YOUR_USERNAME/Strategic-Agricultural-Planner.git)
cd Strategic-Agricultural-Planner


2. Install Dependencies

pip install -r requirements.txt


3. Configuration

Create a .env file in the root directory with your credentials:

OPENROUTER_API_KEY=your_key_here
SMTP_EMAIL=your_email@gmail.com
SMTP_PASSWORD=your_app_password


4. Run the Pipeline

python main.py


🛠️ Tech Stack

Core: Python 3.9+

AI: OpenRouter (Gemini 2.0 Flash, Llama 3.3 70B)

Scraping: BeautifulSoup4, Requests, Dateparser

Reporting: ReportLab

Concurrency: ThreadPoolExecutor

📄 License

MIT License