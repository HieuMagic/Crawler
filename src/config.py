import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    # Paper range
    'start_id': '2311.05222',
    'end_id': '2311.05322',
    'student_id': '23120258',
    
    # Directories
    'output_dir': './data',
    'stats_file': './statistics.json',
    'progress_file': './progress.json',
    
    # Parallel processing
    'num_workers': 5,
    
    # Semantic Scholar API
    'ss_api_key': os.getenv('SEMANTIC_SCHOLAR_API_KEY'),
    'ss_rate_with_key': 1,  # requests per second
    'ss_rate_no_key': 0.5,     # requests per second (conservative to avoid burst limits)
    
    # Retry settings
    'max_retries': 3,
    'timeout': 30,
    
    # Resume capability
    'resume': True
}
