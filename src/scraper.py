import os
import time
import tarfile
import gzip
import shutil
import logging
import requests
import arxiv
import threading
import re
from datetime import datetime
from src.utils import arxiv_id_to_folder_name, get_directory_size, save_json


class RateLimiter:
    """
    Simple global rate limiter with mandatory wait between API calls.
    Ensures only ONE thread calls API at a time, with wait BEFORE each call.
    """
    
    def __init__(self, seconds_between_calls=1.0):
        self.wait_time = seconds_between_calls
        self.last_call_time = 0
        self.lock = threading.Lock()
    
    def execute(self, func):
        """
        Execute a function with rate limiting.
        Waits to ensure wait_time has passed since last call, then executes.
        """
        with self.lock:
            # Wait if needed before making the call
            now = time.time()
            time_since_last = now - self.last_call_time
            if time_since_last < self.wait_time:
                sleep_duration = self.wait_time - time_since_last
                time.sleep(sleep_duration)
            
            # Execute the function
            result = func()
            
            # Record the time of this call
            self.last_call_time = time.time()
            
            return result


class ArxivScraper:
    """Main scraper for arXiv papers"""
    
    def __init__(self, config):
        self.config = config
        self.client = arxiv.Client()
        
        # Setup rate limiter for Semantic Scholar
        # Simple: with API key = 0.15s wait (~6 req/sec), without = 1.5s wait (~0.67 req/sec)
        api_key = config.get('ss_api_key')
        wait_time = 0.15 if api_key else 1.5
        self.ss_limiter = RateLimiter(wait_time)
        self.ss_headers = {}
        if api_key:
            self.ss_headers['x-api-key'] = api_key
    
    def process_paper(self, paper_id):
        """
        Process a single paper
        Returns: dict with results or None if failed
        """
        start_time = time.time()
        folder_name = arxiv_id_to_folder_name(paper_id)
        
        logging.info(f"Processing paper {paper_id}")
        
        try:
            # Get paper metadata (one API call)
            paper = self._get_paper_metadata(paper_id)
            if not paper:
                return {'error': 'paper_not_found'}
            
            # Extract version number from entry_id (no additional API call needed)
            entry_id = paper.entry_id
            if 'v' in entry_id:
                latest_version = int(entry_id.split('v')[-1])
            else:
                latest_version = 1
            
            versions = list(range(1, latest_version + 1))
            logging.info(f"  Found {len(versions)} version(s)")
            
            # Get all version dates (one HTTP request to arXiv HTML page)
            version_dates = self._get_version_dates(paper_id, len(versions))
            if not version_dates:
                # Fallback: use current date for all
                version_dates = [datetime.now().strftime('%Y-%m-%d')] * len(versions)
            
            # Create output directory
            paper_dir = os.path.join(
                self.config['output_dir'],
                self.config['student_id'],
                folder_name
            )
            os.makedirs(paper_dir, exist_ok=True)
            
            # Download and process each version
            tex_dir = os.path.join(paper_dir, 'tex')
            os.makedirs(tex_dir, exist_ok=True)
            
            size_before = 0
            size_after = 0
            peak_disk_usage = 0  # Track peak disk usage (compressed + extracted)
            all_dates = []
            
            for idx, version_num in enumerate(versions):
                version_id = f"{paper_id}v{version_num}"
                version_date = version_dates[idx] if idx < len(version_dates) else datetime.now().strftime('%Y-%m-%d')
                logging.info(f"  Downloading version v{version_num}")
                
                try:
                    size_b, size_a, v_date, peak_v = self._download_and_extract_version(
                        version_id, folder_name, tex_dir, version_date
                    )
                    size_before += size_b
                    size_after += size_a
                    peak_disk_usage = max(peak_disk_usage, peak_v)  # Track maximum
                    all_dates.append(v_date)
                except Exception as e:
                    logging.warning(f"  Failed to download v{version_num}: {e}")
                    # Continue with other versions
            
            if size_after == 0:
                return {'error': 'no_tex_source_pdf_only'}
            
            # Get references and publication venue from Semantic Scholar (one call)
            references, venue, ss_success = self._get_references(paper_id)
            
            # If Semantic Scholar failed, mark paper as failed
            if not ss_success:
                return {'error': 'semantic_scholar_error'}
            
            # Save metadata with all version dates and venue
            self._save_metadata(paper, all_dates, venue, paper_dir)
            
            # Save references (returns count of references with arXiv IDs)
            arxiv_ref_count = self._save_references(references, paper_dir)
            
            processing_time = time.time() - start_time
            
            return {
                'success': True,
                'versions': len(versions),
                'size_before': size_before,
                'size_after': size_after,
                'peak_disk': peak_disk_usage,  # Peak disk usage (compressed + extracted)
                'references': arxiv_ref_count,  # Count of saved references with arXiv IDs
                'time': processing_time
            }
            
        except Exception as e:
            logging.error(f"Error processing {paper_id}: {e}")
            return {'error': 'network_error', 'details': str(e)}
    
    def _get_paper_metadata(self, paper_id):
        """Get paper metadata from arXiv"""
        try:
            search = arxiv.Search(id_list=[paper_id])
            paper = next(self.client.results(search))
            return paper
        except Exception as e:
            logging.error(f"Failed to get metadata for {paper_id}: {e}")
            return None
    
    def _get_version_dates(self, paper_id, num_versions):
        """
        Get submission dates for all versions by scraping arXiv HTML page
        Returns: list of dates in ISO format
        """
        try:
            url = f"https://arxiv.org/abs/{paper_id}"
            response = requests.get(url, timeout=10)
            
            # Match version dates from HTML
            # Format: [v1]</a></strong> Mon, 12 Jun 2017 OR <strong>[v7]</strong> Fri, 4 Aug 2023
            pattern = r'\[v\d+\](?:</a>)?</strong>\s+([A-Za-z]+,\s+\d+\s+[A-Za-z]+\s+\d{4})'
            dates_str = re.findall(pattern, response.text)
            
            # Parse to ISO format
            dates = []
            for date_str in dates_str:
                dt = datetime.strptime(date_str, '%a, %d %b %Y')
                dates.append(dt.strftime('%Y-%m-%d'))
            
            # If we got dates for all versions, return them
            if len(dates) == num_versions:
                return dates
            
            # Fallback: return empty list (will use current date)
            logging.warning(f"Expected {num_versions} dates, got {len(dates)}")
            return []
            
        except Exception as e:
            logging.warning(f"Failed to get version dates: {e}")
            return []
    
    def _download_and_extract_version(self, version_id, folder_name, tex_dir, version_date=None):
        """
        Download and extract a specific version
        Returns: (size_before, size_after, version_date)
        """
        try:
            # Extract base paper ID and version number
            if 'v' in version_id:
                paper_id = version_id.rsplit('v', 1)[0]
                version_num = version_id.split('v')[-1]
            else:
                paper_id = version_id
                version_num = '1'
            
            # Download directly from arXiv
            download_url = f"https://arxiv.org/e-print/{paper_id}v{version_num}"
            response = requests.get(download_url, timeout=self.config.get('timeout', 30))
            
            if response.status_code != 200:
                raise Exception(f"HTTP {response.status_code}")
            
            # Use provided date or fallback to current date
            if not version_date:
                version_date = datetime.now().strftime('%Y-%m-%d')
            
            # Save to temp file
            temp_file = f"/tmp/{version_id}.tar.gz"
            with open(temp_file, 'wb') as f:
                f.write(response.content)
            
            size_before = len(response.content)
            
            # Create version folder
            version_folder = f"{folder_name}v{version_num}"
            version_dir = os.path.join(tex_dir, version_folder)
            os.makedirs(version_dir, exist_ok=True)
            
            # Extract with filtering
            self._extract_filtered(temp_file, version_dir)
            
            # Get size after extraction
            size_after = get_directory_size(version_dir)
            
            # Note: At this point, we have BOTH temp file (size_before) and extracted files (size_after)
            # This is the peak disk usage for this version
            peak_disk_for_version = size_before + size_after
            
            # Clean up temp file
            if os.path.exists(temp_file):
                os.remove(temp_file)
            
            return size_before, size_after, version_date, peak_disk_for_version
            
        except Exception as e:
            raise e
    
    def _extract_filtered(self, tar_path, output_dir):
        """
        Extract only .tex and .bib files, keep folder structure.
        Handles both tar.gz archives and plain .gz files.
        """
        try:
            # Try to open as tar.gz first
            try:
                with tarfile.open(tar_path, 'r:gz') as tar:
                    for member in tar.getmembers():
                        # Extract directories for structure
                        if member.isdir():
                            member_path = os.path.join(output_dir, member.name)
                            os.makedirs(member_path, exist_ok=True)
                        # Extract only .tex and .bib files
                        elif member.name.endswith(('.tex', '.bib')):
                            tar.extract(member, output_dir)
            except tarfile.ReadError:
                # Not a tarball, might be a single gzipped file
                logging.info(f"  Not a tarball, trying as single gzipped file")
                with gzip.open(tar_path, 'rb') as gz:
                    # Read content
                    content = gz.read()
                    
                    # Try to determine filename from content or use default
                    # For single .tex files, save as main.tex
                    if b'\\documentclass' in content or b'\\begin{document}' in content:
                        output_file = os.path.join(output_dir, 'main.tex')
                        with open(output_file, 'wb') as f:
                            f.write(content)
                        logging.info(f"  Extracted single .tex file as main.tex")
                    else:
                        # Unknown format, save as is
                        output_file = os.path.join(output_dir, 'source')
                        with open(output_file, 'wb') as f:
                            f.write(content)
                        logging.warning(f"  Extracted unknown format as 'source'")
                        
        except Exception as e:
            logging.error(f"Extraction error: {e}")
            raise
    
    def _save_metadata(self, paper, all_version_dates, venue, paper_dir):
        """Save paper metadata to JSON"""
        # Keep all version dates in order (don't deduplicate)
        # First date is submission, all dates are revised dates
        submission_date = all_version_dates[0] if all_version_dates else paper.published.strftime('%Y-%m-%d')
        revised_dates = all_version_dates if all_version_dates else [submission_date]
        
        # Use venue from Semantic Scholar if available, fallback to arXiv journal_ref
        publication_venue = venue if venue else (paper.journal_ref if paper.journal_ref else '')
        
        metadata = {
            'paper_title': paper.title,
            'authors': [author.name for author in paper.authors],
            'submission_date': submission_date,
            'revised_dates': revised_dates,
            'publication_venue': publication_venue
        }
        
        metadata_path = os.path.join(paper_dir, 'metadata.json')
        save_json(metadata, metadata_path)
        logging.info(f"  Saved metadata")
    
    def _get_references(self, paper_id):
        """
        Get references and publication venue from Semantic Scholar
        Returns: (references_list, publication_venue, success)
        """
        url = f"https://api.semanticscholar.org/graph/v1/paper/arXiv:{paper_id}"
        params = {
            'fields': 'references,references.externalIds,references.title,references.authors,references.publicationDate,references.paperId,venue'
        }
        
        max_retries = self.config.get('max_retries', 3)
        
        def make_api_call():
            """Single API call attempt"""
            try:
                response = requests.get(url, params=params, headers=self.ss_headers, timeout=10)
                return response, None
            except Exception as e:
                return None, e
        
        # Retry logic
        for attempt in range(max_retries):
            # Execute with rate limiter (1 second wait after call)
            response, error = self.ss_limiter.execute(make_api_call)
            
            if error:
                logging.warning(f"  Error getting references: {error} (attempt {attempt + 1}/{max_retries})")
                if attempt < max_retries - 1:
                    continue
                return [], '', False
            
            if response.status_code == 200:
                data = response.json()
                references = data.get('references', [])
                venue = data.get('venue', '')
                logging.info(f"  Found {len(references)} references")
                if venue:
                    logging.info(f"  Publication venue: {venue}")
                return references, venue, True
                
            elif response.status_code == 429:
                # Rate limited - wait MUCH longer (don't make rate limiter worse)
                wait_time = 30 * (attempt + 1)  # 30s, 60s, 90s
                logging.warning(f"  Semantic Scholar rate limit (429), waiting {wait_time}s (attempt {attempt + 1}/{max_retries})")
                time.sleep(wait_time)
                continue
                
            elif response.status_code == 404:
                # Paper not found - success with no references
                logging.info(f"  Paper not found in Semantic Scholar")
                return [], '', True
                
            else:
                logging.warning(f"  Semantic Scholar returned {response.status_code}")
                if attempt < max_retries - 1:
                    time.sleep(2)
                    continue
                return [], '', False
        
        # All retries exhausted
        logging.error(f"  Failed to get references after {max_retries} attempts")
        return [], '', False
    
    def _save_references(self, references, paper_dir):
        """
        Save references to JSON (only those with arXiv IDs)
        Returns: count of references saved
        """
        ref_dict = {}
        
        for ref in references:
            # Check if reference has arXiv ID
            external_ids = ref.get('externalIds', {})
            if external_ids and 'ArXiv' in external_ids:
                arxiv_id = external_ids['ArXiv']
                folder_name = arxiv_id_to_folder_name(arxiv_id)
                
                # Extract metadata
                authors = [a.get('name', '') for a in ref.get('authors', [])]
                
                ref_dict[folder_name] = {
                    'paper_title': ref.get('title', ''),
                    'authors': authors,
                    'submission_date': ref.get('publicationDate', ''),
                    'semantic_scholar_id': ref.get('paperId', '')
                }
        
        references_path = os.path.join(paper_dir, 'references.json')
        save_json(ref_dict, references_path)
        logging.info(f"  Saved {len(ref_dict)} references with arXiv IDs")
        
        return len(ref_dict)
