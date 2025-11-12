from src.utils import save_json


class Statistics:
    """Track scraping statistics"""
    
    def __init__(self):
        self.stats = {
            'total_papers': 0,
            'successful_papers': 0,
            'failed_papers': 0,
            'success_rate_percent': 0.0,
            
            'error_breakdown': {
                'no_tex_source_pdf_only': 0,
                'missing_versions': 0,
                'download_timeout': 0,
                'api_rate_limit': 0
            },
            
            'total_versions_scraped': 0,
            'avg_versions_per_paper': 0.0,
            'avg_paper_size_before_bytes': 0,
            'avg_paper_size_after_bytes': 0,
            
            'total_references_scraped': 0,
            'avg_references_per_paper': 0.0,
            'reference_success_rate_percent': 0.0,
            
            'total_runtime_seconds': 0.0,
            'entry_discovery_time_seconds': 0.0,
            'avg_time_per_paper_seconds': 0.0,
            
            'max_ram_mb': 0.0,
            'avg_ram_mb': 0.0,
            'max_cpu_percent': 0.0,
            'avg_cpu_percent': 0.0,
            
            'max_disk_usage_mb': 0.0,
            'final_output_size_mb': 0.0,
            'tex_file_percent': 0.0,
            'bib_file_percent': 0.0,
            'json_file_percent': 0.0
        }
        
        self.paper_times = []
        self.paper_sizes_before = []
        self.paper_sizes_after = []
        self.paper_versions = []
        self.paper_references = []
        self.papers_with_references = 0
    
    def add_successful_paper(self, versions_count, size_before, size_after, 
                           references_count, processing_time):
        """Record successful paper"""
        self.stats['successful_papers'] += 1
        self.stats['total_versions_scraped'] += versions_count
        
        self.paper_times.append(processing_time)
        self.paper_sizes_before.append(size_before)
        self.paper_sizes_after.append(size_after)
        self.paper_versions.append(versions_count)
        self.paper_references.append(references_count)
        
        self.stats['total_references_scraped'] += references_count
        
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
        self.stats['total_runtime_seconds'] = round(total_runtime, 3)
        self.stats['entry_discovery_time_seconds'] = round(entry_discovery_time, 3)

    def set_resources(self, max_ram, avg_ram, max_cpu, avg_cpu, disk_usage, output_size):
        """Set resource usage"""
        self.stats['max_ram_mb'] = round(max_ram, 3)
        self.stats['avg_ram_mb'] = round(avg_ram, 3)
        self.stats['max_cpu_percent'] = round(max_cpu, 3)
        self.stats['avg_cpu_percent'] = round(avg_cpu, 3)
        self.stats['max_disk_usage_mb'] = round(disk_usage, 3)
        self.stats['final_output_size_mb'] = round(output_size, 3)
    
    def set_file_percentages(self, tex_mb, bib_mb, json_mb):
        """Set file type percentages based on disk usage"""
        total = self.stats['final_output_size_mb']
        if total > 0:
            self.stats['tex_file_percent'] = round((tex_mb / total) * 100, 3)
            self.stats['bib_file_percent'] = round((bib_mb / total) * 100, 3)
            self.stats['json_file_percent'] = round((json_mb / total) * 100, 3)
        else:
            self.stats['tex_file_percent'] = 0.0
            self.stats['bib_file_percent'] = 0.0
            self.stats['json_file_percent'] = 0.0
    
    def finalize(self):
        """Calculate final statistics"""
        total = self.stats['total_papers']
        successful = self.stats['successful_papers']
        
        if total > 0:
            self.stats['success_rate_percent'] = round((successful / total) * 100, 3)
        
        if successful > 0:
            self.stats['avg_versions_per_paper'] = round(sum(self.paper_versions) / successful, 3)
            self.stats['avg_references_per_paper'] = round(sum(self.paper_references) / successful, 3)
            self.stats['avg_time_per_paper_seconds'] = round(sum(self.paper_times) / successful, 3)
            self.stats['avg_paper_size_before_bytes'] = int(sum(self.paper_sizes_before) / successful)
            self.stats['avg_paper_size_after_bytes'] = int(sum(self.paper_sizes_after) / successful)
            self.stats['reference_success_rate_percent'] = round((self.papers_with_references / successful) * 100, 3)
    
    def save(self, filepath):
        """Save statistics to file"""
        self.finalize()
        save_json(self.stats, filepath)
    
    def get_stats(self):
        """Get current statistics"""
        return self.stats
