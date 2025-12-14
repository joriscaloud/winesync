import io
from PyPDF2 import PdfReader

from utils.logger import logger


def extract_text_from_pdf(pdf_content: bytes) -> str:
    """Extract text content from PDF bytes.
    
    Args:
        pdf_content: PDF file content as bytes
        
    Returns:
        Extracted text
    """
    try:
        pdf_file = io.BytesIO(pdf_content)
        reader = PdfReader(pdf_file)
        
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"
        
        return text
    except Exception as e:
        logger.error(f"Error extracting PDF: {e}")
        return ""


def is_wine_order_pdf(text: str) -> bool:
    """Check if PDF contains wine order information.
    
    Args:
        text: Extracted PDF text
        
    Returns:
        True if likely a wine order
    """
    order_indicators = [
        'devis',
        'facture',
        'commande',
        'bon de livraison',
        'invoice',
        'order',
        'quantité',
        'prix',
        'total',
    ]
    
    wine_indicators = [
        'bouteille',
        'vin',
        'domaine',
        'château',
        'appellation',
        'millésime',
        'rouge',
        'blanc',
        'rosé',
    ]
    
    text_lower = text.lower()
    
    has_order_indicator = any(indicator in text_lower for indicator in order_indicators)
    has_wine_indicator = any(indicator in text_lower for indicator in wine_indicators)
    
    return has_order_indicator and has_wine_indicator
