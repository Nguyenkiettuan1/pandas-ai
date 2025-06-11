import logging
import sys
from datetime import datetime
import os
from app.core.config import settings

def setup_logging():
    """Setup logging configuration for the application"""
    
    # Create logs directory if not exists
    logs_dir = "logs"
    os.makedirs(logs_dir, exist_ok=True)
    
    # Create log filename with timestamp
    log_filename = f"logs/pandasai_{datetime.now().strftime('%Y%m%d')}.log"
    
    # Configure logging format
    log_format = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(funcName)s:%(lineno)d - %(message)s'
    )
    
    # Setup file handler
    file_handler = logging.FileHandler(log_filename, encoding='utf-8')
    file_handler.setFormatter(log_format)
    file_handler.setLevel(logging.DEBUG)
    
    # Setup console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(log_format)
    console_handler.setLevel(logging.INFO if not settings.DEBUG else logging.DEBUG)
    
    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Setup specific loggers
    loggers = [
        'app.agents',
        'app.services', 
        'app.routes',
        'app.models',
        'pandasai',
        'sqlalchemy.engine'
    ]
    
    for logger_name in loggers:
        logger = logging.getLogger(logger_name)
        logger.setLevel(logging.DEBUG if settings.DEBUG else logging.INFO)
    
    # Reduce noise from some libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('httpx').setLevel(logging.WARNING)
    
    return root_logger

def get_logger(name: str) -> logging.Logger:
    """Get a logger for a specific module"""
    return logging.getLogger(name)
