import os
import json


def arxiv_id_to_folder_name(arxiv_id):
    """
    Convert arxiv ID to folder name format
    Example: 2311.05222 -> 2311-05222
    """
    return arxiv_id.replace('.', '-')


def folder_name_to_arxiv_id(folder_name):
    """
    Convert folder name back to arxiv ID
    Example: 2311-05222 -> 2311.05222
    """
    return folder_name.replace('-', '.')


def generate_paper_ids(start_id, end_id):
    """
    Generate list of paper IDs in range
    Example: 2311.05222 to 2311.05225 -> ['2311.05222', '2311.05223', '2311.05224', '2311.05225']
    """
    # Parse the IDs
    start_parts = start_id.split('.')
    end_parts = end_id.split('.')
    
    prefix = start_parts[0]  # e.g., '2311'
    start_num = int(start_parts[1])  # e.g., 5222
    end_num = int(end_parts[1])      # e.g., 10221
    
    # Generate IDs
    paper_ids = []
    for num in range(start_num, end_num + 1):
        paper_id = f"{prefix}.{num:05d}"
        paper_ids.append(paper_id)
    
    return paper_ids


def get_directory_size(path):
    """Calculate total size of directory in bytes"""
    total = 0
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    total += os.path.getsize(filepath)
    except Exception:
        pass
    return total


def save_json(data, filepath):
    """Save data to JSON file"""
    os.makedirs(os.path.dirname(filepath), exist_ok=True)
    with open(filepath, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)


def load_json(filepath):
    """Load data from JSON file"""
    if not os.path.exists(filepath):
        return None
    with open(filepath, 'r', encoding='utf-8') as f:
        return json.load(f)


def format_time(seconds):
    """Format seconds to human readable time"""
    hours = int(seconds // 3600)
    minutes = int((seconds % 3600) // 60)
    secs = int(seconds % 60)
    
    if hours > 0:
        return f"{hours}h {minutes}m {secs}s"
    elif minutes > 0:
        return f"{minutes}m {secs}s"
    else:
        return f"{secs}s"
