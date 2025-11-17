import os
from dotenv import load_dotenv

load_dotenv()

CONFIG = {
    'start_id': '2311.05332',
    'end_id': '2311.05342',
    'student_id': '23120258',
    
    'output_dir': './data',
    'stats_file': './statistics.json',
    'progress_file': './progress.json',
    
    'num_workers': 5,
    
    'ss_api_key': os.getenv('SEMANTIC_SCHOLAR_API_KEY'),
    
    'max_retries': 3,
    'timeout': 30,
    
    'resume': True
}
