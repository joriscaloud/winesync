from typing import Dict, Optional, Any
import anthropic
import json

from utils.logger import logger


class WineLLMExtractor:
    """Extract wine order information using Claude."""
    
    def __init__(self, api_key: str):
        """Initialize LLM extractor.
        
        Args:
            api_key: Anthropic API key
        """
        self.client = anthropic.Anthropic(api_key=api_key)
        self.call_count = 0
    
    def extract_wine_order(self, text: str, max_calls: int) -> Optional[Dict]:
        """Extract wine order information from text using Claude."""
        if self.call_count >= max_calls:
            logger.warning(f"Reached maximum LLM calls limit ({max_calls})")
            return None
        
        if not text or len(text.strip()) < 50:
            return None
        
        prompt = self._build_extraction_prompt(text)
        
        try:
            self.call_count += 1
            
            message = self.client.messages.create(
                model="claude-sonnet-4-5",
                max_tokens=2000,
                temperature=0,
                messages=[
                    {
                        "role": "user",
                        "content": prompt
                    }
                ]
            )
            
            if not message.content or not message.content[0].text:
                logger.error("LLM returned empty content")
                return None
            
            response_text = message.content[0].text
            
            parsed = self._parse_response_json(response_text)
            if not parsed:
                return None
            
            return parsed
            
        except anthropic.APIError as exc:
            logger.error(f"Anthropic API error: {exc}")
            return None
        except Exception as exc:
            logger.error(f"Unexpected error calling LLM: {exc}")
            return None
    
    def _build_extraction_prompt(self, text: str) -> str:
        """Build prompt for wine order extraction.
        
        Args:
            text: Source text
            
        Returns:
            Formatted prompt
        """
        prompt = f"""Analyse cet email (peut être en HTML - ignore les balises/CSS).

ÉTAPE 1: Est-ce une VRAIE commande de vin (confirmation d'achat, facture) ?
- Si c'est une newsletter, promo, ou autre → réponds avec is_wine_order: false
- Si c'est une vraie commande → réponds avec is_wine_order: true et extrais les vins

ÉTAPE 2: Si c'est une commande, extrais pour chaque vin:
- cuvée: nom complet du vin
- producteur: domaine/château  
- millésime: année
- région: région viticole
- aoc: appellation
- couleur: Rouge/Blanc/Rosé
- format: 75cl par défaut
- quantité: nombre de bouteilles
- prix_unitaire: prix unitaire

Réponds UNIQUEMENT avec ce JSON:
{{
    "is_wine_order": true/false,
    "order_number": "",
    "total_price": "",
    "wines": [
        {{
            "cuvée": "",
            "producteur": "",
            "millésime": "",
            "région": "",
            "aoc": "",
            "couleur": "",
            "format": "",
            "quantité": "",
            "prix_unitaire": ""
        }}
    ]
}}

Email:
{text[:12000]}
"""
        
        return prompt
    
    def _parse_response_json(self, response_text: str) -> Optional[Dict[str, Any]]:
        """Parse and validate LLM JSON response."""
        text = response_text.strip()
        
        if text.startswith("```"):
            lines = text.split("\n")
            lines = [l for l in lines if not l.strip().startswith("```")]
            text = "\n".join(lines)
        
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            text = text[start:end]
        
        try:
            data = json.loads(text)
        except json.JSONDecodeError as exc:
            logger.error(f"Failed to parse LLM JSON: {exc}")
            return None
        
        if not isinstance(data, dict):
            logger.error("LLM response is not a JSON object")
            return None
        
        wines = data.get('wines', [])
        if wines is None:
            wines = []
        if not isinstance(wines, list):
            logger.error("LLM response 'wines' is not a list")
            return None
        
        sanitized_wines = []
        for wine in wines:
            if not isinstance(wine, dict):
                continue
            sanitized_wines.append({
                'région': str(wine.get('région', '') or ''),
                'aoc': str(wine.get('aoc', '') or ''),
                'producteur': str(wine.get('producteur', '') or ''),
                'millésime': str(wine.get('millésime', '') or ''),
                'cuvée': str(wine.get('cuvée', '') or ''),
                'couleur': str(wine.get('couleur', '') or ''),
                'pays': str(wine.get('pays', '') or ''),
                'format': str(wine.get('format', '') or ''),
                'quantité': str(wine.get('quantité', '') or ''),
                'prix_unitaire': str(wine.get('prix_unitaire', '') or ''),
            })
        
        data['wines'] = sanitized_wines
        data['order_number'] = str(data.get('order_number', '') or '')
        data['total_price'] = str(data.get('total_price', '') or '')
        
        return data
    
    def reset_counter(self) -> None:
        """Reset the call counter."""
        self.call_count = 0
    
    def get_call_count(self) -> int:
        """Get current call count.
        
        Returns:
            Number of calls made
        """
        return self.call_count
