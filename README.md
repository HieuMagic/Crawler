# arXiv Paper Scraper

A Python tool for scraping arXiv papers with LaTeX source files and reference information from Semantic Scholar.

## Requirements

- **Python**: 3.8 or higher
- **Operating System**: Linux, macOS, or Windows

## Installation

### 1. Clone the repository

```bash
git clone https://github.com/HieuMagic/Crawler.git
cd Crawler
```

### 2. Install dependencies

Using pip:
```bash
cd src/
pip install -r requirements.txt
```

Using conda:
```bash
conda create -n arxiv-scraper python=3.8
conda activate arxiv-scraper
cd src/
pip install -r requirements.txt
```

**Dependencies include:**
- `arxiv` - for accessing arXiv API
- `requests` - for HTTP requests
- `psutil` - for resource monitoring
- `python-dotenv` - for environment variables
- `matplotlib` - for generating visualization graphs

### 3. Configure environment variables (Optional)

Create a `.env` file for Semantic Scholar API key (optional but recommended for higher rate limits):
```
SEMANTIC_SCHOLAR_API_KEY=your_api_key_here
```

**Note**: If no API key is provided, the scraper will still work but with stricter rate limiting (3s between requests vs 1s with key).

## Configuration

Edit `src/config.py` to set scraping parameters:

```python
CONFIG = {
    'start_id': '2311.05222',      # First arXiv ID to scrape
    'end_id': '2311.05232',        # Last arXiv ID to scrape
    'student_id': '23120258',      # Student ID (output folder name)
    
    'output_dir': './data',        # Output directory
    'stats_file': './statistics.json',
    'progress_file': './progress.json',
    
    'num_workers': 5,              # Number of parallel workers
    
    'max_retries': 3,              # Max API retry attempts
    'timeout': 30,                 # Request timeout (seconds)
    
    'resume': True                 # Resume from previous progress
}
```

### Key Parameters

- **`start_id` / `end_id`**: Define the range of arXiv IDs to scrape (format: `YYMM.NNNNN`)
- **`student_id`**: Your student ID, used as the output folder name
- **`num_workers`**: Number of parallel threads (1-7 recommended, default: 5)
- **`resume`**: Set to `True` to continue from last saved progress, `False` to start fresh

## Usage

### Basic Usage

Run the scraper with default settings from `src/config.py`:

```bash
python -m src.main
```

### Monitor Progress

The scraper saves progress automatically:
- **Progress file**: `progress.json` - tracks which papers have been processed
- **Statistics file**: `statistics.json` - contains scraping statistics and performance metrics
- **Log file**: `scraper.log` - detailed execution logs

### Statistics Output

After completion, check `statistics.json` for:
- Total papers processed
- Success/failure counts by error type
- Performance metrics (CPU, RAM, disk usage)
- Processing time statistics
- File type distribution (%.tex, %.bib, %.json)

### Visualization Graphs

The scraper automatically generates **11 visualization graphs** (PNG format):

1. **`resource_ram.png`** - RAM usage over time (line graph)
2. **`resource_cpu.png`** - CPU usage over time (line graph)
3. **`resource_disk.png`** - Disk usage over time (line graph)
4. **`resource_errors.png`** - Error breakdown by type (pie chart)
5. **`resource_filetypes.png`** - File type distribution for .tex, .bib, .json (pie chart)
6. **`resource_sizes_before.png`** - Paper size before extraction per paper (bar chart)
7. **`resource_sizes_after.png`** - Paper size after extraction per paper (bar chart)
8. **`resource_entry_times.png`** - Entry discovery time per paper (bar chart)
9. **`resource_process_times.png`** - Total processing time per paper (bar chart)
10. **`resource_references.png`** - Number of references per paper (bar chart)  


## Google Colab

To run in Google Colab, use the provided notebook:

1. Upload `ArXiv_Scraper_Colab.ipynb` to Colab
2. Run cells in order
3. Download the generated ZIP file

## File Descriptions

- `src/main.py` - Main entry point and orchestration
- `src/scraper.py` - Core scraping logic
- `src/statistics.py` - Statistics tracking and reporting 
- `src/monitor.py` - Resource monitoring (CPU, RAM, disk)
- `src/visualizer.py` - Graph generation for reports
- `src/utils.py` - Helper functions
- `src/config.py` - Configuration settings
- `requirements.txt` - Python dependencies
- `ArXiv_Scraper_Colab.ipynb` - Google Colab notebook

## License

This project is for educational purposes.
