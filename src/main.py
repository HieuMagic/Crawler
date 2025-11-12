import os
import sys
import time
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed

# Add parent directory to path for imports to work when running directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.config import CONFIG
from src.utils import generate_paper_ids, get_directory_size, load_json, save_json
from src.monitor import ResourceMonitor
from src.statistics import Statistics
from src.scraper import ArxivScraper


def setup_logging():
    """Setup logging configuration"""
    log_format = '[%(asctime)s] %(levelname)s: %(message)s'
    date_format = '%Y-%m-%d %H:%M:%S'
    
    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # File handler
    file_handler = logging.FileHandler('scraper.log', encoding='utf-8')
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(logging.Formatter(log_format, date_format))
    
    # Root logger
    logging.basicConfig(
        level=logging.DEBUG,
        handlers=[console_handler, file_handler]
    )


def load_progress():
    """Load progress from file"""
    progress = load_json(CONFIG['progress_file'])
    if progress:
        return set(progress.get('processed', []))
    return set()


def save_progress(processed_papers):
    """Save progress to file"""
    save_json({'processed': list(processed_papers)}, CONFIG['progress_file'])


def process_single_paper(paper_id, scraper, stats, processed_papers):
    """Process a single paper and update statistics"""
    try:
        result = scraper.process_paper(paper_id)
        
        if result.get('success'):
            stats.add_successful_paper(
                versions_count=result['versions'],
                size_before=result['size_before'],
                size_after=result['size_after'],
                references_count=result['references'],
                processing_time=result['time'],
                peak_disk=result['peak_disk']
            )
            processed_papers.add(paper_id)
            save_progress(processed_papers)
            return True, None
        else:
            error_type = result.get('error', 'network_error')
            stats.add_failed_paper(error_type)
            return False, error_type
            
    except Exception as e:
        logging.error(f"Unexpected error processing {paper_id}: {e}")
        stats.add_failed_paper('network_error')
        return False, str(e)


def main():
    """Main entry point"""
    print("=" * 70)
    print("ArXiv Paper Scraper")
    print("=" * 70)
    print()
    
    # Setup logging
    setup_logging()
    logging.info("Starting scraper")
    
    # Generate paper IDs
    print(f"Generating paper IDs from {CONFIG['start_id']} to {CONFIG['end_id']}...")
    entry_discovery_start = time.time()
    paper_ids = generate_paper_ids(CONFIG['start_id'], CONFIG['end_id'])
    entry_discovery_time = time.time() - entry_discovery_start
    
    total_papers = len(paper_ids)
    print(f"Total papers to process: {total_papers}")
    print()
    
    # Load progress
    processed_papers = set()
    if CONFIG['resume']:
        processed_papers = load_progress()
        if processed_papers:
            print(f"Resuming: {len(processed_papers)} papers already processed")
    
    # Filter out already processed
    remaining_papers = [pid for pid in paper_ids if pid not in processed_papers]
    print(f"Papers to process: {len(remaining_papers)}")
    print()
    
    if not remaining_papers:
        print("All papers already processed!")
        return
    
    # Initialize components
    stats = Statistics()
    stats.set_total_papers(total_papers)
    
    monitor = ResourceMonitor(output_dir=CONFIG['output_dir'])
    monitor.start()
    
    scraper = ArxivScraper(CONFIG)
    
    # Start processing
    start_time = time.time()
    num_workers = CONFIG['num_workers']
    
    print(f"Processing with {num_workers} workers...")
    print("-" * 70)
    print()
    
    try:
        with ThreadPoolExecutor(max_workers=num_workers) as executor:
            # Submit all tasks
            future_to_paper = {
                executor.submit(process_single_paper, paper_id, scraper, stats, processed_papers): paper_id
                for paper_id in remaining_papers
            }
            
            # Process as they complete
            completed = len(processed_papers)
            for future in as_completed(future_to_paper):
                paper_id = future_to_paper[future]
                completed += 1
                
                try:
                    success, error = future.result()
                    
                    if success:
                        print(f"[{completed}/{total_papers}] SUCCESS: {paper_id}")
                    else:
                        print(f"[{completed}/{total_papers}] FAILED: {paper_id} ({error})")
                        
                except Exception as e:
                    print(f"[{completed}/{total_papers}] ERROR: {paper_id} - {e}")
                    stats.add_failed_paper('network_error')
    
    except KeyboardInterrupt:
        print()
        print("Interrupted by user. Progress has been saved.")
        logging.info("Scraping interrupted by user")
    
    finally:
        # Stop monitoring
        monitor.stop()
        
        # Calculate final statistics
        total_runtime = time.time() - start_time
        resource_stats = monitor.get_stats()
        
        # Get disk usage
        output_dir = os.path.join(CONFIG['output_dir'], CONFIG['student_id'])
        if os.path.exists(output_dir):
            output_size_bytes = get_directory_size(output_dir)
            output_size_mb = output_size_bytes / (1024 * 1024)
        else:
            output_size_mb = 0
        
        # Set final statistics
        stats.set_timing(total_runtime, entry_discovery_time)
        stats.set_resources(
            max_ram=resource_stats['max_ram_mb'],
            avg_ram=resource_stats['avg_ram_mb'],
            max_cpu=resource_stats['max_cpu_percent'],
            avg_cpu=resource_stats['avg_cpu_percent'],
            disk_usage=0,  # Will be calculated from paper peaks
            output_size=output_size_mb  # Final output size
        )
        
        # Save statistics
        stats.save(CONFIG['stats_file'])
        
        # Print summary
        print()
        print("=" * 70)
        print("SUMMARY")
        print("=" * 70)
        
        final_stats = stats.get_stats()
        print(f"Total papers: {final_stats['total_papers']}")
        print(f"Successful: {final_stats['successful_papers']}")
        print(f"Failed: {final_stats['failed_papers']}")
        print(f"Success rate: {final_stats['success_rate_percent']:.1f}%")
        print()
        print(f"Total runtime: {total_runtime:.1f}s")
        print(f"Average time per paper: {final_stats['avg_time_per_paper_seconds']:.1f}s")
        print()
        print(f"Max RAM: {resource_stats['max_ram_mb']:.1f} MB")
        print(f"Max CPU: {resource_stats['max_cpu_percent']:.1f}%")
        print(f"Output size: {output_size_mb:.1f} MB")
        print()
        print(f"Statistics saved to: {CONFIG['stats_file']}")
        print("=" * 70)
        
        logging.info("Scraping completed")


if __name__ == '__main__':
    main()
