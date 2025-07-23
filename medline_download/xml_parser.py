# =============================================================================
# medline_download/xml_parser.py
# =============================================================================
"""
Medline XML tartalom feldolgozása
"""
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Any
import re
from dataclasses import dataclass

@dataclass
class MedlineTopicContent:
    """Strukturált Medline topic tartalom"""
    title: str
    organization: str
    url: str
    full_summary: str
    also_called: List[str]
    related_topics: List[str]
    mesh_terms: List[str]
    groups: List[str]
    primary_institute: Optional[str] = None
    see_references: List[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Dictionary konverzió"""
        return {
            'title': self.title,
            'organization': self.organization,
            'url': self.url,
            'full_summary': self.full_summary,
            'also_called': self.also_called,
            'related_topics': self.related_topics,
            'mesh_terms': self.mesh_terms,
            'groups': self.groups,
            'primary_institute': self.primary_institute,
            'see_references': self.see_references or []
        }

class MedlineXMLParser:
    """
    Medline XML válaszok feldolgozása
    """
    
    def parse_topic_xml(self, xml_content: str) -> Optional[MedlineTopicContent]:
        """
        Topic XML feldolgozása strukturált adattá
        
        Args:
            xml_content: XML string a Medline API-tól
            
        Returns:
            MedlineTopicContent vagy None
        """
        try:
            root = ET.fromstring(xml_content)
            
            # Keressük meg a health-topic elemet
            health_topic = root.find('.//health-topic')
            if health_topic is None:
                # Próbáljuk meg a document/content struktúrát
                return self._parse_search_result_format(root)
            
            # Standard health-topic formátum feldolgozása
            return self._parse_health_topic_format(health_topic)
            
        except ET.ParseError as e:
            print(f"XML parse hiba: {e}")
            return None
        except Exception as e:
            print(f"Feldolgozási hiba: {e}")
            return None
    
    def _parse_health_topic_format(self, health_topic: ET.Element) -> MedlineTopicContent:
        """Health-topic formátum feldolgozása"""
        
        # Alapadatok
        title = self._get_text(health_topic, 'title') or "Unknown Topic"
        url = health_topic.get('url', '')
        
        # Összefoglaló - több helyen lehet
        full_summary = self._get_full_summary(health_topic)
        
        # Also called (alternatív nevek)
        also_called = []
        for alt in health_topic.findall('.//also-called'):
            text = alt.text or alt.get('text', '')
            if text:
                also_called.append(text.strip())
        
        # MeSH terms
        mesh_terms = []
        for mesh in health_topic.findall('.//mesh-heading/descriptor'):
            if mesh.text:
                mesh_terms.append(mesh.text.strip())
        
        # Groups
        groups = []
        for group in health_topic.findall('.//group'):
            if group.text:
                groups.append(group.text.strip())
        
        # Related topics
        related_topics = []
        for related in health_topic.findall('.//related-topic'):
            topic_text = related.text or related.get('text', '')
            if topic_text:
                related_topics.append(topic_text.strip())
        
        # Organization
        organization = self._get_text(health_topic, './/organization') or "National Library of Medicine"
        
        # Primary institute
        primary_institute = self._get_text(health_topic, './/primary-institute')
        
        # See references
        see_references = []
        for see_ref in health_topic.findall('.//see-reference'):
            if see_ref.text:
                see_references.append(see_ref.text.strip())
        
        return MedlineTopicContent(
            title=title,
            organization=organization,
            url=url,
            full_summary=full_summary,
            also_called=also_called,
            related_topics=related_topics,
            mesh_terms=mesh_terms,
            groups=groups,
            primary_institute=primary_institute,
            see_references=see_references
        )
    
    def _parse_search_result_format(self, root: ET.Element) -> Optional[MedlineTopicContent]:
        """Search result formátum feldolgozása"""
        
        # Keressük a document elemet
        document = root.find('.//document')
        if document is None:
            return None
        
        # Gyűjtsük össze a content elemeket
        contents = {}
        for content in document.findall('content'):
            name = content.get('name', '')
            text = self._clean_html(content.text or '')
            
            if name and text:
                if name in contents:
                    # Ha már van ilyen, listává alakítjuk
                    if not isinstance(contents[name], list):
                        contents[name] = [contents[name]]
                    contents[name].append(text)
                else:
                    contents[name] = text
        
        # Építsük fel a MedlineTopicContent objektumot
        return MedlineTopicContent(
            title=contents.get('title', 'Unknown Topic'),
            organization=contents.get('organizationName', 'National Library of Medicine'),
            url=document.get('url', ''),
            full_summary=contents.get('FullSummary', ''),
            also_called=self._ensure_list(contents.get('altTitle', [])),
            related_topics=[],  # Nem érhető el ebben a formátumban
            mesh_terms=self._ensure_list(contents.get('mesh', [])),
            groups=self._ensure_list(contents.get('groupName', [])),
            primary_institute=None,
            see_references=[]
        )
    
    def _get_text(self, element: ET.Element, path: str) -> Optional[str]:
        """Biztonságos szöveg kinyerés"""
        found = element.find(path)
        if found is not None and found.text:
            return found.text.strip()
        return None
    
    def _get_full_summary(self, element: ET.Element) -> str:
        """Teljes összefoglaló kinyerése"""
        # Próbáljuk különböző helyeken
        summary_paths = [
            './/full-summary',
            './/summary',
            './/full-summary-section',
            './/summary-section'
        ]
        
        full_text = []
        for path in summary_paths:
            for summary_elem in element.findall(path):
                text = self._extract_all_text(summary_elem)
                if text and text.strip():
                    full_text.append(text)
        
        return '\n\n'.join(full_text) if full_text else ""
    
    def _extract_all_text(self, element: ET.Element) -> str:
        """Rekurzívan kivonja az összes szöveget egy elemből"""
        texts = []
        
        # Elem saját szövege
        if element.text and element.text.strip():
            texts.append(element.text.strip())
        
        # Gyerek elemek szövege
        for child in element:
            child_text = self._extract_all_text(child)
            if child_text and child_text.strip():
                texts.append(child_text)
            # Gyerek után következő szöveg
            if child.tail and child.tail.strip():
                texts.append(child.tail.strip())
        
        # Filter out None and empty strings
        filtered_texts = [text for text in texts if text and text.strip()]
        return ' '.join(filtered_texts)
    
    def _clean_html(self, text: str) -> str:
        """HTML tagek eltávolítása"""
        if text is None:
            return ""
        
        text = str(text)
        # Egyszerű HTML tag eltávolítás
        text = re.sub(r'<[^>]+>', '', text)
        # Többszörös szóközök
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
    
    def _ensure_list(self, value: Any) -> List[str]:
        """Biztosítja, hogy lista legyen"""
        if isinstance(value, list):
            return value
        elif isinstance(value, str):
            return [value]
        else:
            return []