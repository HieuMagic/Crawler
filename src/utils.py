import os
import json


def arxiv_id_to_folder_name(arxiv_id):
    """Convert arxiv ID to folder name (2311.05222 -> 2311-05222)"""
    return arxiv_id.replace('.', '-')


def generate_paper_ids(start_id, end_id):
    """Generate list of paper IDs in range"""
    start_parts = start_id.split('.')
    end_parts = end_id.split('.')
    
    prefix = start_parts[0]
    start_num = int(start_parts[1])
    end_num = int(end_parts[1])
    
    return [f"{prefix}.{num:05d}" for num in range(start_num, end_num + 1)]


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


def get_file_sizes_by_type(path):
    """Calculate total size of files by extension in MB"""
    tex_size = 0
    bib_size = 0
    json_size = 0
    
    try:
        for dirpath, dirnames, filenames in os.walk(path):
            for filename in filenames:
                filepath = os.path.join(dirpath, filename)
                if os.path.exists(filepath):
                    size = os.path.getsize(filepath)
                    if filename.endswith('.tex'):
                        tex_size += size
                    elif filename.endswith('.bib'):
                        bib_size += size
                    elif filename.endswith('.json'):
                        json_size += size
    except Exception:
        pass
    
    return (
        tex_size / (1024 * 1024),
        bib_size / (1024 * 1024),
        json_size / (1024 * 1024)
    )
