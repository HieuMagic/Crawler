from src.utils import save_json


class Statistics:
    """Track scraping statistics"""
    
    def __init__(self):
        self.stats = {
            # Scraping results
            'total_papers': 0,
            'successful_papers': 0,
            'failed_papers': 0,
            'success_rate_percent': 0.0,
            
            # Error breakdown
            'error_breakdown': {
                'no_tex_source_pdf_only': 0,
                'missing_versions': 0,
                'download_timeout': 0,
                'extraction_error': 0,
                'api_rate_limit': 0,
                'paper_not_found': 0,
                'semantic_scholar_error': 0,
                'invalid_archive': 0,
                'network_error': 0
            },
            
            # Paper metrics
            'total_versions_scraped': 0,
            'avg_versions_per_paper': 0.0,
            'avg_paper_size_before_bytes': 0,
            'avg_paper_size_after_bytes': 0,
            
            # Reference metrics
            'total_references_scraped': 0,
            'avg_references_per_paper': 0.0,
            'reference_success_rate_percent': 0.0,
            
            # Timing
            'total_runtime_seconds': 0.0,
            'entry_discovery_time_seconds': 0.0,
            'avg_time_per_paper_seconds': 0.0,
            
            # Memory and CPU
            'max_ram_mb': 0.0,
            'avg_ram_mb': 0.0,
            'max_cpu_percent': 0.0,
            'avg_cpu_percent': 0.0,
            
            # Disk
            'max_disk_usage_mb': 0.0,
            'final_output_size_mb': 0.0
        }
        
        # Temporary tracking
        self.paper_times = []
        self.paper_sizes_before = []
        self.paper_sizes_after = []
        self.paper_versions = []
        self.paper_references = []
        self.paper_peak_disks = []  # Track peak disk usage per paper
        self.papers_with_references = 0  # Track how many papers got references
    
    def add_successful_paper(self, versions_count, size_before, size_after, 
                           references_count, processing_time, peak_disk=0):
        """Record successful paper"""
        self.stats['successful_papers'] += 1
        self.stats['total_versions_scraped'] += versions_count
        
        self.paper_times.append(processing_time)
        self.paper_sizes_before.append(size_before)
        self.paper_sizes_after.append(size_after)
        self.paper_versions.append(versions_count)
        self.paper_references.append(references_count)
        self.paper_peak_disks.append(peak_disk)
        
        self.stats['total_references_scraped'] += references_count
        
        # Only successful papers get references, so always count them
        if references_count > 0:
            self.papers_with_references += 1
    
    def add_failed_paper(self, error_type):
        """Record failed paper"""
        self.stats['failed_papers'] += 1
        if error_type in self.stats['error_breakdown']:
            self.stats['error_breakdown'][error_type] += 1
    
    def set_total_papers(self, total):
        """Set total number of papers"""
        self.stats['total_papers'] = total
    
    def set_timing(self, total_runtime, entry_discovery_time):
        """Set timing information"""
        self.stats['total_runtime_seconds'] = total_runtime
        self.stats['entry_discovery_time_seconds'] = entry_discovery_time
    
    def set_resources(self, max_ram, avg_ram, max_cpu, avg_cpu, disk_usage, output_size):
        """Set resource usage"""
        self.stats['max_ram_mb'] = max_ram
        self.stats['avg_ram_mb'] = avg_ram
        self.stats['max_cpu_percent'] = max_cpu
        self.stats['avg_cpu_percent'] = avg_cpu
        self.stats['max_disk_usage_mb'] = disk_usage
        self.stats['final_output_size_mb'] = output_size
    
    def finalize(self):
        """Calculate final statistics"""
        total = self.stats['total_papers']
        successful = self.stats['successful_papers']
        
        # Success rate
        if total > 0:
            self.stats['success_rate_percent'] = (successful / total) * 100
        
        # Averages
        if successful > 0:
            self.stats['avg_versions_per_paper'] = sum(self.paper_versions) / successful
            self.stats['avg_references_per_paper'] = sum(self.paper_references) / successful
            self.stats['avg_time_per_paper_seconds'] = sum(self.paper_times) / successful
            self.stats['avg_paper_size_before_bytes'] = int(sum(self.paper_sizes_before) / successful)
            self.stats['avg_paper_size_after_bytes'] = int(sum(self.paper_sizes_after) / successful)
        
        # Reference success rate
        if successful > 0:
            self.stats['reference_success_rate_percent'] = (self.papers_with_references / successful) * 100
        
        # Max disk usage from papers
        if self.paper_peak_disks:
            self.stats['max_disk_usage_mb'] = max(self.paper_peak_disks) / (1024 * 1024)
    
    def save(self, filepath):
        """Save statistics to file"""
        self.finalize()
        save_json(self.stats, filepath)
    
    def get_stats(self):
        """Get current statistics"""
        return self.stats
