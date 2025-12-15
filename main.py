from services.gmail_client import GmailClient
from services.wine_detector import WineOrderDetector
from services.llm_extractor import WineLLMExtractor
from services.sheets_client import append_wines_to_sheet, get_last_sync_date
from utils.logger import logger
import config


def main():
    """Fetch wine orders from Gmail and export to Google Sheets."""
    logger.info("WineSync - Starting...")
    
    last_sync = get_last_sync_date()
    if last_sync:
        logger.info(f"Last sync: {last_sync}")
    
    gmail = GmailClient(config.GMAIL_EMAIL, config.GMAIL_PASSWORD)
    
    llm = None
    if config.ANTHROPIC_API_KEY:
        llm = WineLLMExtractor(config.ANTHROPIC_API_KEY)
    
    detector = WineOrderDetector(
        keywords=[],
        merchant_domains=config.WINE_MERCHANT_DOMAINS,
        llm_extractor=llm
    )
    
    messages = gmail.fetch_messages(query='ALL', max_results=config.GMAIL_MAX_RESULTS)
    logger.info(f"Fetched {len(messages)} emails")
    
    wine_orders = []
    for msg in messages:
        message_data = gmail.extract_message_data(msg)
        
        email_date = message_data.get('date')
        if last_sync and email_date and email_date <= last_sync:
            continue
        
        if detector.is_wine_order(message_data):
            order = detector.extract_order_details(message_data, config.MAX_LLM_CALLS_PER_RUN)
            if order:
                wine_orders.append(order)
                logger.info(f"Found order: {order.get('subject', '')[:50]}")
    
    gmail.close()
    
    logger.info(f"Found {len(wine_orders)} wine orders")
    append_wines_to_sheet(wine_orders)
    
    if llm:
        logger.info(f"LLM calls: {llm.get_call_count()}")


if __name__ == '__main__':
    main()
