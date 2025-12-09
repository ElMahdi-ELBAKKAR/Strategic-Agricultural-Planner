import os
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib.colors import HexColor
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, 
    KeepTogether, Image
)
from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT

# Setup Logger
logger = logging.getLogger(__name__)

class WeekCalculator:
    """Handle week calculations accurately for the report header."""
    
    @staticmethod
    def get_week_info(date: datetime = None) -> Dict:
        if date is None:
            date = datetime.now()
            
        # Calculate week number (1-5)
        week_num = (date.day - 1) // 7 + 1
        
        # Calculate week start (Monday) and end (Sunday)
        day_of_week = date.weekday()
        week_start = date - timedelta(days=day_of_week)
        week_end = week_start + timedelta(days=6)
        
        month_names = {
            1: 'JANVIER', 2: 'FÉVRIER', 3: 'MARS', 4: 'AVRIL',
            5: 'MAI', 6: 'JUIN', 7: 'JUILLET', 8: 'AOÛT',
            9: 'SEPTEMBRE', 10: 'OCTOBRE', 11: 'NOVEMBRE', 12: 'DÉCEMBRE'
        }
        
        week_ordinals = {
            1: 'PREMIÈRE', 2: 'DEUXIÈME', 3: 'TROISIÈME', 
            4: 'QUATRIÈME', 5: 'CINQUIÈME'
        }
        
        month_name = month_names.get(date.month, str(date.month))
        week_ordinal = week_ordinals.get(week_num, 'PREMIÈRE')
        
        return {
            'week_num': week_num,
            'week_label': f"{week_ordinal} SEMAINE DE {month_name} {date.year}",
            'simple_label': f"SEMAINE {week_num} - {month_name} {date.year}",
            'date_range': f"{week_start.strftime('%d/%m')} - {week_end.strftime('%d/%m/%Y')}"
        }

class ReportStyles:
    """Centralized style management for consistent branding."""
    
    def __init__(self):
        self.base_styles = getSampleStyleSheet()
        self.custom_styles = {}
        self._setup_all_styles()
        
    def _setup_all_styles(self):
        # --- Cover Page ---
        self.custom_styles['CoverTitle'] = ParagraphStyle(
            name='CoverTitle',
            parent=self.base_styles['Heading1'],
            fontSize=26,
            textColor=HexColor('#059669'), # Deep Green
            spaceAfter=20,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['WeekLabel'] = ParagraphStyle(
            name='WeekLabel',
            parent=self.base_styles['Heading2'],
            fontSize=18,
            textColor=HexColor('#047857'), # Darker Green
            spaceAfter=10,
            alignment=TA_CENTER,
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['DateRange'] = ParagraphStyle(
            name='DateRange',
            parent=self.base_styles['Normal'],
            fontSize=12,
            textColor=HexColor('#6b7280'), # Gray
            spaceAfter=30,
            alignment=TA_CENTER,
            fontName='Helvetica'
        )
        
        # --- Executive Summary ---
        self.custom_styles['SectionHeader'] = ParagraphStyle(
            name='SectionHeader',
            parent=self.base_styles['Heading2'],
            fontSize=14,
            textColor=HexColor('#059669'),
            spaceAfter=15,
            spaceBefore=10,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['ExecutiveSummary'] = ParagraphStyle(
            name='ExecutiveSummary',
            parent=self.base_styles['Normal'],
            fontSize=11,
            spaceAfter=20,
            leading=16,
            alignment=TA_JUSTIFY,
            fontName='Helvetica'
        )
        
        # --- News Items ---
        self.custom_styles['PageHeader'] = ParagraphStyle(
            name='PageHeader',
            parent=self.base_styles['Heading1'],
            fontSize=16,
            textColor=HexColor('#047857'),
            spaceAfter=20,
            alignment=TA_LEFT,
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['HighImportance'] = ParagraphStyle(
            name='HighImportance',
            parent=self.base_styles['Normal'],
            fontSize=11.5,
            spaceAfter=6,
            leading=15,
            textColor=HexColor('#059669'),
            fontName='Helvetica-Bold'
        )
        
        self.custom_styles['NormalImportance'] = ParagraphStyle(
            name='NormalImportance',
            parent=self.base_styles['Normal'],
            fontSize=11,
            spaceAfter=6,
            leading=14,
            fontName='Helvetica'
        )
        
        self.custom_styles['SourceLink'] = ParagraphStyle(
            name='SourceLink',
            parent=self.base_styles['Normal'],
            fontSize=9,
            textColor=HexColor('#3b82f6'), # Blue Link
            spaceBefore=2,
            spaceAfter=2,
            leftIndent=0.5*cm,
            fontName='Helvetica'
        )
        
        self.custom_styles['Metadata'] = ParagraphStyle(
            name='Metadata',
            parent=self.base_styles['Normal'],
            fontSize=8.5,
            textColor=HexColor('#9ca3af'),
            spaceBefore=2,
            spaceAfter=18,
            leftIndent=0.5*cm,
            fontName='Helvetica-Oblique'
        )
        
        # --- Footer ---
        self.custom_styles['Footer'] = ParagraphStyle(
            name='Footer',
            parent=self.base_styles['Normal'],
            fontSize=9,
            textColor=HexColor('#6b7280'),
            alignment=TA_CENTER,
            fontName='Helvetica'
        )

    def get(self, style_name: str):
        return self.custom_styles.get(style_name, self.base_styles['Normal'])

class ReportGenerator:
    """Enhanced report generator for AgriMaroc Strategic Planner."""
    
    def __init__(self, logo_path: Optional[str] = None):
        self.styles = ReportStyles()
        self.week_calc = WeekCalculator()
        self.logo_path = logo_path
        
    def _add_cover_page(self, story: List, week_info: Dict):
        """Builds the visual cover page."""
        
        # Optional: Add logo if file exists
        if self.logo_path and os.path.exists(self.logo_path):
            try:
                logo = Image(self.logo_path, width=4*cm, height=2*cm, hAlign='CENTER')
                story.append(logo)
                story.append(Spacer(1, 1.5*cm))
            except Exception as e:
                print(f"⚠️ Could not load logo: {e}")
                story.append(Spacer(1, 3*cm))
        else:
            story.append(Spacer(1, 4*cm))
            
        story.append(Paragraph("BULLETIN HEBDOMADAIRE", self.styles.get('CoverTitle')))
        story.append(Paragraph("VEILLE STRATÉGIQUE AGRICOLE", self.styles.get('CoverTitle')))
        
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph(week_info['week_label'], self.styles.get('WeekLabel')))
        story.append(Paragraph(week_info['date_range'], self.styles.get('DateRange')))
        
        story.append(Spacer(1, 1.5*cm))

    def _add_executive_summary(self, story: List, summary_text: str, count: int):
        """Adds the executive summary block."""
        story.append(Paragraph("SYNTHÈSE EXÉCUTIVE", self.styles.get('SectionHeader')))
        
        # Stats line
        stats = f"<i>Analyse basée sur {count} actualités stratégiques cette semaine.</i>"
        story.append(Paragraph(stats, self.styles.get('Metadata')))
        story.append(Spacer(1, 0.2*cm))
        
        story.append(Paragraph(summary_text, self.styles.get('ExecutiveSummary')))
        
        # Professional Separator
        story.append(Spacer(1, 1*cm))
        story.append(Paragraph("_______________________________________", self.styles.get('Footer')))
        story.append(PageBreak())

    def _add_news_item(self, story: List, item: Dict, index: int):
        """Adds a single news item using KeepTogether to prevent bad page breaks."""
        content_block = []
        
        # 1. Title/Summary
        importance = item.get('importance', 1)
        if importance >= 3:
            style = self.styles.get('HighImportance')
            bullet = f"<b>🔥 [TOP ACTU] </b>"
        else:
            style = self.styles.get('NormalImportance')
            bullet = "• "
            
        text = f"{bullet}{item['text']}"
        content_block.append(Paragraph(text, style))
        
        # 2. Source Link
        url = item.get('url', '#')
        if url and url != '#':
            link_html = f'<a href="{url}" color="#3b82f6"><u>→ Lire la source complète</u></a>'
            content_block.append(Paragraph(link_html, self.styles.get('SourceLink')))
            
        # 3. Metadata
        sources = ", ".join(item.get('sources', ['AgriMaroc']))
        date = item.get('date', 'N/A')
        meta = f"Sources: {sources} | Date: {date}"
        content_block.append(Paragraph(meta, self.styles.get('Metadata')))
        
        # Add the whole block to the story
        story.append(KeepTogether(content_block))

    def _add_footer(self, story: List):
        """Adds the document footer."""
        story.append(Spacer(1, 1*cm))
        footer_html = f"""
        Plateforme De Veille Stratégique<br/>
        <i>Document généré automatiquement le {datetime.now().strftime('%d/%m/%Y')}</i>
        """
        story.append(Paragraph(footer_html, self.styles.get('Footer')))

    def generate_pdf(self, news_items: List[Dict], executive_summary: str, filename: str, output_dir: str = 'reports'):
        """Main PDF generation orchestration."""
        
        # Safety checks
        if not news_items:
            print("⚠️ No news items to report.")
            return None
            
        if not executive_summary:
            executive_summary = "Synthèse non disponible."

        # Prepare File
        os.makedirs(output_dir, exist_ok=True)
        filepath = filename  # filename passed from main.py is usually the full path
        
        week_info = self.week_calc.get_week_info()
        
        try:
            doc = SimpleDocTemplate(
                filepath,
                pagesize=A4,
                topMargin=1.5*cm, bottomMargin=1.5*cm,
                leftMargin=2.5*cm, rightMargin=2.5*cm
            )
            
            story = []
            
            # 1. Cover Page & Executive Summary
            self._add_cover_page(story, week_info)
            self._add_executive_summary(story, executive_summary, len(news_items))
            
            # 2. Detailed News Section
            story.append(Paragraph("ACTUALITÉS DE LA SEMAINE", self.styles.get('PageHeader')))
            story.append(Spacer(1, 0.5*cm))
            
            for i, item in enumerate(news_items, 1):
                self._add_news_item(story, item, i)
                
            # 3. Footer
            self._add_footer(story)
            
            doc.build(story)
            print(f"✅ PDF generated successfully: {filepath}")
            return filepath
            
        except Exception as e:
            print(f"❌ Critical error generating PDF: {str(e)}")
            import traceback
            traceback.print_exc()
            return None