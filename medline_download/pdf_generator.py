# =============================================================================
# medline_download/pdf_generator.py
# =============================================================================
"""
PDF generálás Medline tartalmakból
"""
from reportlab.lib.pagesizes import A4
from reportlab.lib.units import cm
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, PageBreak
from reportlab.platypus import Table, TableStyle, KeepTogether
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_JUSTIFY, TA_CENTER
from reportlab.lib import colors
from datetime import datetime
from typing import List, Dict, Any, Optional
from pathlib import Path
from .xml_parser import MedlineTopicContent
from .config import MEDLINE_DOWNLOAD_CONFIG

class MedlinePDFGenerator:
    """
    Medline tartalmak PDF-be generálása
    """
    
    def __init__(self):
        self.config = MEDLINE_DOWNLOAD_CONFIG["pdf"]
        self.styles = self._create_styles()
    
    def _safe_paragraph_text(self, text: any) -> str:
        """Biztonságos szöveg Paragraph objektumokhoz"""
        if text is None:
            return ""
        return str(text).strip()
    
    def _create_styles(self):
        """PDF stílusok létrehozása"""
        styles = getSampleStyleSheet()
        
        # Cím stílus
        styles.add(ParagraphStyle(
            name='CustomTitle',
            parent=styles['Title'],
            fontSize=self.config["font_size_title"],
            textColor=colors.HexColor('#1e3d59'),
            spaceAfter=30
        ))
        
        # Alcím stílus
        styles.add(ParagraphStyle(
            name='CustomHeading',
            parent=styles['Heading2'],
            fontSize=self.config["font_size_subtitle"],
            textColor=colors.HexColor('#2e5266'),
            spaceBefore=20,
            spaceAfter=10
        ))
        
        # Normál szöveg
        styles.add(ParagraphStyle(
            name='CustomBody',
            parent=styles['Normal'],
            fontSize=self.config["font_size_normal"],
            alignment=TA_JUSTIFY,
            spaceBefore=6,
            spaceAfter=6
        ))
        
        # Footer stílus
        styles.add(ParagraphStyle(
            name='Footer',
            parent=styles['Normal'],
            fontSize=9,
            textColor=colors.grey,
            alignment=TA_CENTER
        ))
        
        return styles
    
    def generate_pdf(self, topic: MedlineTopicContent, output_path: str, 
                    patient_data: Optional[Dict] = None) -> bool:
        """
        Egyetlen topic PDF generálása
        
        Args:
            topic: MedlineTopicContent objektum
            output_path: Kimeneti PDF útvonal
            patient_data: Opcionális beteg adatok
            
        Returns:
            bool: Sikeres volt-e
        """
        try:
            # PDF dokumentum létrehozása
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=self.config["margin_cm"]*cm,
                leftMargin=self.config["margin_cm"]*cm,
                topMargin=self.config["margin_cm"]*cm,
                bottomMargin=self.config["margin_cm"]*cm
            )
            
            # Tartalom összeállítása
            story = []
            
            # Fedőlap
            story.extend(self._create_cover_page(topic, patient_data))
            story.append(PageBreak())
            
            # Fő tartalom
            story.extend(self._create_main_content(topic))
            
            # Disclaimer
            if self.config["include_disclaimer"]:
                story.append(PageBreak())
                story.extend(self._create_disclaimer())
            
            # PDF generálás
            doc.build(story, onFirstPage=self._add_page_number, 
                     onLaterPages=self._add_page_number)
            
            return True
            
        except Exception as e:
            print(f"PDF generálási hiba: {e}")
            return False
    
    def generate_combined_pdf(self, topics: List[MedlineTopicContent], 
                            output_path: str, patient_data: Optional[Dict] = None) -> bool:
        """
        Több topic kombinált PDF-be
        
        Args:
            topics: MedlineTopicContent lista
            output_path: Kimeneti PDF útvonal
            patient_data: Opcionális beteg adatok
            
        Returns:
            bool: Sikeres volt-e
        """
        try:
            doc = SimpleDocTemplate(
                output_path,
                pagesize=A4,
                rightMargin=self.config["margin_cm"]*cm,
                leftMargin=self.config["margin_cm"]*cm,
                topMargin=self.config["margin_cm"]*cm,
                bottomMargin=self.config["margin_cm"]*cm
            )
            
            story = []
            
            # Fedőlap
            story.extend(self._create_combined_cover_page(topics, patient_data))
            story.append(PageBreak())
            
            # Tartalomjegyzék
            if self.config["include_toc"]:
                story.extend(self._create_table_of_contents(topics))
                story.append(PageBreak())
            
            # Minden topic
            for i, topic in enumerate(topics):
                if i > 0:
                    story.append(PageBreak())
                story.extend(self._create_main_content(topic))
            
            # Disclaimer
            if self.config["include_disclaimer"]:
                story.append(PageBreak())
                story.extend(self._create_disclaimer())
            
            doc.build(story, onFirstPage=self._add_page_number, 
                     onLaterPages=self._add_page_number)
            
            return True
            
        except Exception as e:
            print(f"Kombinált PDF generálási hiba: {e}")
            return False
    
    def _create_cover_page(self, topic: MedlineTopicContent, 
                          patient_data: Optional[Dict]) -> List:
        """Fedőlap létrehozása"""
        elements = []
        
        # Cím
        elements.append(Paragraph(
            "Medical Chatbot<br/>Egészségügyi Információk",
            self.styles['CustomTitle']
        ))
        elements.append(Spacer(1, 2*cm))
        
        # Topic címe
        title_text = self._safe_paragraph_text(topic.title) or "Unknown Topic"
        elements.append(Paragraph(title_text, self.styles['CustomHeading']))
        elements.append(Spacer(1, 1*cm))
        
        # Metaadatok táblázat
        metadata = [
            ["Forrás:", "MedlinePlus - National Library of Medicine"],
            ["Generálva:", datetime.now().strftime("%Y. %m. %d. %H:%M")],
        ]
        
        if patient_data:
            case_id = patient_data.get('case_id')
            if case_id:
                safe_case_id = self._safe_paragraph_text(case_id)
                if safe_case_id:
                    metadata.append(["Eset azonosító:", safe_case_id])
        
        table = Table(metadata, colWidths=[5*cm, 10*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_combined_cover_page(self, topics: List[MedlineTopicContent], 
                                   patient_data: Optional[Dict]) -> List:
        """Kombinált PDF fedőlap"""
        elements = []
        
        # Főcím
        elements.append(Paragraph(
            "Medical Chatbot<br/>Összesített Egészségügyi Információk",
            self.styles['CustomTitle']
        ))
        elements.append(Spacer(1, 2*cm))
        
        # Témák száma
        elements.append(Paragraph(
            f"Összesen {len(topics)} témakör",
            self.styles['CustomHeading']
        ))
        elements.append(Spacer(1, 1*cm))
        
        # Metaadatok
        metadata = [
            ["Forrás:", "MedlinePlus - National Library of Medicine"],
            ["Generálva:", datetime.now().strftime("%Y. %m. %d. %H:%M")],
            ["Témák száma:", str(len(topics))],
        ]
        
        if patient_data:
            case_id = patient_data.get('case_id')
            if case_id:
                safe_case_id = self._safe_paragraph_text(case_id)
                if safe_case_id:
                    metadata.append(["Eset azonosító:", safe_case_id])
            
            diagnosis = patient_data.get('diagnosis')
            if diagnosis:
                safe_diagnosis = self._safe_paragraph_text(diagnosis)
                if safe_diagnosis:
                    metadata.append(["Diagnózis:", safe_diagnosis])
        
        table = Table(metadata, colWidths=[5*cm, 10*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 10),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.grey),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_table_of_contents(self, topics: List[MedlineTopicContent]) -> List:
        """Tartalomjegyzék generálása"""
        elements = []
        
        elements.append(Paragraph("Tartalomjegyzék", self.styles['CustomTitle']))
        elements.append(Spacer(1, 1*cm))
        
        # TOC táblázat
        toc_data = []
        for i, topic in enumerate(topics, 1):
            toc_data.append([f"{i}.", topic.title, f"{i + 2}. oldal"])
        
        table = Table(toc_data, colWidths=[1*cm, 12*cm, 2*cm])
        table.setStyle(TableStyle([
            ('FONT', (0, 0), (-1, -1), 'Helvetica', 11),
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('ALIGN', (2, 0), (2, -1), 'RIGHT'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        elements.append(table)
        
        return elements
    
    def _create_main_content(self, topic: MedlineTopicContent) -> List:
        """Fő tartalom generálása"""
        elements = []
        
        # Cím
        title = self._safe_paragraph_text(topic.title) or "Untitled"
        elements.append(Paragraph(title, self.styles['CustomTitle']))
        
        # URL
        if topic.url and str(topic.url).strip():
            url_str = self._safe_paragraph_text(topic.url)
            if url_str:
                elements.append(Paragraph(
                    f'<link href="{url_str}" color="blue">{url_str}</link>',
                    self.styles['CustomBody']
                ))
                elements.append(Spacer(1, 0.5*cm))
        
        # Alternatív nevek
        if topic.also_called:
            elements.append(Paragraph("Más néven:", self.styles['CustomHeading']))
            for alt_name in topic.also_called:
                if alt_name is not None:
                    safe_name = self._safe_paragraph_text(alt_name)
                    if safe_name:
                        elements.append(Paragraph(f"• {safe_name}", self.styles['CustomBody']))
            elements.append(Spacer(1, 0.5*cm))
        
        # Összefoglaló
        if topic.full_summary and str(topic.full_summary).strip():
            elements.append(Paragraph("Leírás:", self.styles['CustomHeading']))
            # HTML tagek tisztítása
            summary_text = self._safe_paragraph_text(topic.full_summary)
            if summary_text:
                clean_summary = summary_text.replace('<p>', '').replace('</p>', '\n\n')
                clean_summary = clean_summary.replace('<br>', '\n')
                if clean_summary.strip():  # Only add if there's actual content
                    elements.append(Paragraph(clean_summary, self.styles['CustomBody']))
                    elements.append(Spacer(1, 0.5*cm))
        
        # MeSH kifejezések
        if topic.mesh_terms:
            elements.append(Paragraph("Orvosi kifejezések (MeSH):", self.styles['CustomHeading']))
            # Filter out None values
            mesh_terms_safe = [self._safe_paragraph_text(term) for term in topic.mesh_terms if term is not None]
            mesh_terms_safe = [term for term in mesh_terms_safe if term]  # Remove empty strings
            if mesh_terms_safe:
                mesh_text = ", ".join(mesh_terms_safe)
                elements.append(Paragraph(mesh_text, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.5*cm))
        
        # Csoportok
        if topic.groups:
            elements.append(Paragraph("Kategóriák:", self.styles['CustomHeading']))
            # Filter out None values
            groups_safe = [self._safe_paragraph_text(group) for group in topic.groups if group is not None]
            groups_safe = [group for group in groups_safe if group]  # Remove empty strings
            if groups_safe:
                groups_text = ", ".join(groups_safe)
                elements.append(Paragraph(groups_text, self.styles['CustomBody']))
                elements.append(Spacer(1, 0.5*cm))
        
        # Kapcsolódó témák
        if topic.related_topics:
            elements.append(Paragraph("Kapcsolódó témák:", self.styles['CustomHeading']))
            for related in topic.related_topics:
                if related is not None:
                    safe_related = self._safe_paragraph_text(related)
                    if safe_related:
                        elements.append(Paragraph(f"• {safe_related}", self.styles['CustomBody']))
        
        # Forrás szervezet
        if topic.organization:
            elements.append(Spacer(1, 1*cm))
            org_text = self._safe_paragraph_text(topic.organization) or "Unknown"
            elements.append(Paragraph(
                f"Forrás: {org_text}",
                self.styles['Footer']
            ))
        
        return elements
    
    def _create_disclaimer(self) -> List:
        """Jogi nyilatkozat"""
        elements = []
        
        elements.append(Paragraph("Fontos információk", self.styles['CustomTitle']))
        elements.append(Spacer(1, 0.5*cm))
        
        disclaimer_text = """
        Az ebben a dokumentumban található információk a MedlinePlus.gov 
        weboldalról származnak, amely az Amerikai Nemzeti Orvostudományi Könyvtár 
        (U.S. National Library of Medicine) szolgáltatása.
        
        Ez az információ kizárólag oktatási és tájékoztatási célokat szolgál. 
        Nem helyettesíti a szakszerű orvosi tanácsadást, diagnózist vagy kezelést. 
        Mindig forduljon képzett egészségügyi szakemberhez, ha egészségügyi 
        kérdései vannak.
        
        A Medical Chatbot nem vállal felelősséget az információk használatából 
        eredő következményekért.
        """
        
        elements.append(Paragraph(disclaimer_text, self.styles['CustomBody']))
        
        return elements
    
    def _add_page_number(self, canvas, doc):
        """Oldalszám hozzáadása"""
        canvas.saveState()
        canvas.setFont('Helvetica', 9)
        canvas.setFillColor(colors.grey)
        canvas.drawCentredString(
            A4[0] / 2, 
            self.config["margin_cm"] * cm / 2,
            f"Oldal {doc.page}"
        )
        canvas.restoreState()