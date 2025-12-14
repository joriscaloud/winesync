from typing import List, Dict
import json

from services.gmail_client import GmailClient
from services.wine_detector import WineOrderDetector
from services.llm_extractor import WineLLMExtractor
from utils.logger import logger
from services.sheets_client import append_wines_to_sheet
import config


def fetch_wine_orders(max_results: int = 100) -> List[Dict]:
    """Fetch and detect wine orders from Gmail.
    
    Args:
        max_results: Maximum number of emails to check
        
    Returns:
        List of detected wine orders with details
    """
    logger.info("Initializing Gmail client...")
    gmail_client = GmailClient(config.GMAIL_EMAIL, config.GMAIL_PASSWORD)
    
    logger.info("Initializing LLM extractor...")
    llm_extractor = None
    if config.ANTHROPIC_API_KEY:
        llm_extractor = WineLLMExtractor(config.ANTHROPIC_API_KEY)
        logger.info(f"LLM extraction enabled (max {config.MAX_LLM_CALLS_PER_RUN} calls)")
    else:
        logger.warning("No Anthropic API key found. LLM extraction disabled.")
    
    logger.info("Initializing wine order detector...")
    detector = WineOrderDetector(
        keywords=[],
        merchant_domains=config.WINE_MERCHANT_DOMAINS,
        llm_extractor=llm_extractor
    )
    
    logger.info(f"Fetching up to {max_results} messages...")
    messages = gmail_client.fetch_messages(
        query='ALL',
        max_results=max_results
    )
    
    logger.info(f"Found {len(messages)} messages. Analyzing...")
    
    wine_orders = []
    
    for i, msg in enumerate(messages, 1):
        if i % 10 == 0:
            if llm_extractor:
                logger.info(f"Processed {i}/{len(messages)} messages (LLM calls: {llm_extractor.get_call_count()}/{config.MAX_LLM_CALLS_PER_RUN})")
            else:
                logger.info(f"Processed {i}/{len(messages)} messages")
        
        message_data = gmail_client.extract_message_data(msg)
        
        if detector.is_wine_order(message_data):
            order_details = detector.extract_order_details(
                message_data, 
                max_llm_calls=config.MAX_LLM_CALLS_PER_RUN
            )
            if order_details:
                wine_orders.append(order_details)
    
    gmail_client.close()
    
    if llm_extractor:
        logger.info(f"Total LLM calls made: {llm_extractor.get_call_count()}/{config.MAX_LLM_CALLS_PER_RUN}")
    
    logger.info(f"Found {len(wine_orders)} wine orders!")
    return wine_orders


def display_wine_orders(wine_orders: List[Dict]) -> None:
    """Display wine orders in a readable format.
    
    Args:
        wine_orders: List of wine order dictionaries
    """
    if not wine_orders:
        logger.info("No wine orders found.")
        return
    
    logger.info("="*80)
    logger.info("WINE ORDERS DETECTED")
    logger.info("="*80)
    
    for i, order in enumerate(wine_orders, 1):
        logger.info(f"\n--- Order {i} ---")
        logger.info(f"Date: {order.get('date', 'N/A')}")
        logger.info(f"From: {order.get('from', 'N/A')}")
        logger.info(f"Subject: {order.get('subject', 'N/A')}")
        
        if order.get('order_number'):
            logger.info(f"Order Number: {order['order_number']}")
        
        if order.get('total_price'):
            logger.info(f"Total Price: {order['total_price']}")
        
        if order.get('wines'):
            logger.info(f"\nWines ({len(order['wines'])}):")
            for j, wine in enumerate(order['wines'], 1):
                logger.info(f"\n  Wine {j}:")
                logger.info(f"    Région:     {wine.get('région', 'N/A')}")
                logger.info(f"    AOC:        {wine.get('aoc', 'N/A')}")
                logger.info(f"    Producteur: {wine.get('producteur', 'N/A')}")
                logger.info(f"    Millésime:  {wine.get('millésime', 'N/A')}")
                logger.info(f"    Cuvée:      {wine.get('cuvée', 'N/A')}")
                logger.info(f"    Couleur:    {wine.get('couleur', 'N/A')}")
                logger.info(f"    Pays:       {wine.get('pays', 'N/A')}")
                logger.info(f"    Format:     {wine.get('format', 'N/A')}")
                if wine.get('quantity'):
                    logger.info(f"    Quantité:   {wine.get('quantity', 'N/A')}")
                if wine.get('unit_price'):
                    logger.info(f"    Prix unit:  {wine.get('unit_price', 'N/A')}")
        
        logger.info(f"\n  Source: {order.get('source', 'N/A')}")
        
        logger.info("-" * 80)


def save_wine_orders_to_json(wine_orders: List[Dict], filename: str = 'wine_orders.json') -> None:
    """Save wine orders to a JSON file.
    
    Args:
        wine_orders: List of wine order dictionaries
        filename: Output filename
    """
    with open(filename, 'w', encoding='utf-8') as f:
        json.dump(wine_orders, f, indent=2, ensure_ascii=False)
    
    logger.info(f"Wine orders saved to {filename}")


def export_to_csv(wine_orders: List[Dict], filename: str = 'wine_orders.csv') -> None:
    """Export wine orders to CSV format for Google Sheets.
    
    Args:
        wine_orders: List of wine order dictionaries
        filename: Output CSV filename
    """
    import csv
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        fieldnames = ['date', 'order_number', 'région', 'aoc', 'producteur', 
                     'millésime', 'cuvée', 'couleur', 'pays', 'format', 'quantity', 'unit_price']
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        
        writer.writeheader()
        
        for order in wine_orders:
            order_date = order.get('date', '')
            order_number = order.get('order_number', '')
            
            for wine in order.get('wines', []):
                row = {
                    'date': order_date,
                    'order_number': order_number,
                    'région': wine.get('région', ''),
                    'aoc': wine.get('aoc', ''),
                    'producteur': wine.get('producteur', ''),
                    'millésime': wine.get('millésime', ''),
                    'cuvée': wine.get('cuvée', ''),
                    'couleur': wine.get('couleur', ''),
                    'pays': wine.get('pays', ''),
                    'format': wine.get('format', ''),
                    'quantity': wine.get('quantity', ''),
                    'unit_price': wine.get('unit_price', ''),
                }
                writer.writerow(row)
    
    logger.info(f"Wine orders exported to {filename}")


def main():
    """Main entry point for the script."""
    logger.info("WineSync - Wine Order Detector")
    logger.info("="*80)
    
    wine_orders = fetch_wine_orders(max_results=config.GMAIL_MAX_RESULTS)
    
    display_wine_orders(wine_orders)
    append_wines_to_sheet(wine_orders)


if __name__ == '__main__':
    main()
