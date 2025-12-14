"""Wine order detection service."""

from typing import Dict, List, Optional
from services.pdf_parser import extract_text_from_pdf, is_wine_order_pdf
from services.llm_extractor import WineLLMExtractor


class WineOrderDetector:
    """Detector for wine orders in email messages."""
    
    def __init__(
        self, 
        keywords: List[str], 
        merchant_domains: List[str],
        llm_extractor: Optional[WineLLMExtractor] = None
    ):
        self.merchant_domains = [d.lower() for d in merchant_domains]
        self.llm_extractor = llm_extractor
    
    def is_wine_order(self, message_data: Dict) -> bool:
        """Quick pre-filter: only process emails from known wine merchants."""
        from_email = message_data.get('from', '').lower()
        return any(domain in from_email for domain in self.merchant_domains)
    
    def extract_order_details(self, message_data: Dict, max_llm_calls: int = 50) -> Optional[Dict]:
        """Extract order details using LLM."""
        body = message_data.get('body', '')
        attachments = message_data.get('attachments', [])
        
        pdf_text = ""
        for filename, content in attachments:
            if filename.lower().endswith('.pdf'):
                extracted = extract_text_from_pdf(content)
                if is_wine_order_pdf(extracted):
                    pdf_text = extracted
                    break
        
        text_to_parse = pdf_text if pdf_text else body
        
        if not self.llm_extractor:
            return None
        
        llm_result = self.llm_extractor.extract_wine_order(text_to_parse, max_llm_calls)
        
        if not llm_result:
            return None
        
        if not llm_result.get('is_wine_order', False):
            return None
        
        wines = llm_result.get('wines', [])
        
        for wine in wines:
            if 'quantité' in wine:
                wine['quantity'] = wine.pop('quantité')
            if 'prix_unitaire' in wine:
                wine['unit_price'] = wine.pop('prix_unitaire')
        
        return {
            'message_id': message_data.get('id'),
            'date': message_data.get('date'),
            'from': message_data.get('from'),
            'subject': message_data.get('subject'),
            'order_number': llm_result.get('order_number', ''),
            'total_price': llm_result.get('total_price', ''),
            'wines': wines,
            'source': 'llm_' + ('pdf' if pdf_text else 'email'),
        }
